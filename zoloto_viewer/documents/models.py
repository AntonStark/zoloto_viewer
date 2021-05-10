import io
import os
from django.core.files import File
from django.db import models
from django.dispatch import receiver

from zoloto_viewer.documents import generators
from zoloto_viewer.documents.pdf_generation import main as pdf_module
from zoloto_viewer.infoplan.models import Marker
from zoloto_viewer.config.settings .storage_backends import s3_download_bytes


def additional_files_upload_path(obj: 'ProjectFile', filename):
    return os.path.join(obj.project.project_files_dir(), f'additional_files/{filename}')


def _delete_file(fpath):
    """ Deletes file from filesystem. """
    if os.path.isfile(fpath):
        os.remove(fpath)


class ProjectFilesManager(models.Manager):

    def look_for_fresh(self, project, kind):
        existing_file = ProjectFile.objects.filter(
            project=project,
            kind=kind
        ).first()
        if existing_file and existing_file.is_fresh_project_file():
            return existing_file
        else:
            return None

    def create_csv_file(self, project, kind):
        obj = self.model(project=project, kind=kind)
        obj._setup_file()
        return obj

    def create_layer_csv_file(self, project, kind, layer):
        obj = self.model(project=project, kind=kind, layer=layer)
        obj._setup_layer_file()
        return obj

    def pdf_generate_file(self, project):
        obj = self.model(project=project)
        obj._setup_pdf_file()
        return obj

    def infoplan_file(self, layer):
        return self.filter(project=layer.project, layer=layer).first()

    def generate_counts(self, project):
        return self.create_csv_file(project, self.model.FileKinds.CSV_LAYER_STATS)

    def generate_pict_list(self, project):
        return self.create_csv_file(project, self.model.FileKinds.CSV_PICT_CODES)

    def generate_vars_index_file(self, project):
        return self.create_csv_file(project, self.model.FileKinds.CSV_VARIABLES)

    def _generate_layer_infoplan(self, layer):
        return self.create_layer_csv_file(layer.project, self.model.FileKinds.CSV_INFOPLAN, layer)

    def generate_infoplan_archive(self, project):
        per_layer_csv_files = []
        for layer in project.layer_set.all():
            layer_infoplan = self.infoplan_file(layer)  # type: ProjectFile
            # `last_modified and last_modified > date_created` to treat empty layers as up-to-date
            if not (layer_infoplan and layer_infoplan.is_fresh_layer_file()):
                layer_infoplan = self._generate_layer_infoplan(layer)
            per_layer_csv_files.append(
                (s3_download_bytes(layer_infoplan.file.name),
                 layer_infoplan.public_name)
            )

        kind = self.model.FileKinds.TAR_INFOPLAN
        obj = self.model(project=project, kind=kind)
        obj._setup_archive_file(per_layer_csv_files)
        return obj


class ProjectFile(models.Model):
    """
    Отражает факт наличия файлов проекта разных видов
    """

    class FileKinds(models.IntegerChoices):
        PDF_EXFOLIATION = 1     # pdf
        CSV_LAYER_STATS = 2     # кол-во
        CSV_INFOPLAN = 3        # инфоплан одного слоя
        CSV_VARIABLES = 4       # словарь
        CSV_PICT_CODES = 5      # пикты
        TAR_INFOPLAN = 6        # архив с инфопланами по слоям

    project = models.ForeignKey('viewer.Project', on_delete=models.CASCADE)
    file = models.FileField(upload_to=additional_files_upload_path,
                            null=False, blank=True, default='')
    kind = models.IntegerField(choices=FileKinds.choices)
    date_created = models.DateTimeField(auto_now_add=True)
    layer = models.ForeignKey('viewer.Layer', on_delete=models.CASCADE, null=True)

    objects = ProjectFilesManager()

    FILE_BUILDERS = {
        FileKinds.CSV_LAYER_STATS   : generators.counts.CountFileBuilder,
        FileKinds.CSV_PICT_CODES    : generators.picts.PictListFileBuilder,
        FileKinds.CSV_VARIABLES     : generators.vars_index.VarsIndexFileBuilder,
        FileKinds.CSV_INFOPLAN      : generators.infoplan.InfoplanFileBuilder,
    }

    @staticmethod
    def make_name(kind, *, project, **extra):
        file_kinds = ProjectFile.FileKinds
        rules = {
            file_kinds.CSV_LAYER_STATS  : 'project_{project.title}_marker_counts.csv',
            file_kinds.CSV_PICT_CODES   : 'project_{project.title}_picts.csv',
            file_kinds.CSV_VARIABLES    : 'project_{project.title}_vars.csv',
            file_kinds.CSV_INFOPLAN     : 'project_{project.title}_layer_{layer.title}_infoplan.csv',
            file_kinds.TAR_INFOPLAN     : 'project_{project.title}_infoplan.tar',
            file_kinds.PDF_EXFOLIATION  : 'project_{project.title}_pdf.pdf',
        }
        return rules[kind].format(project=project, **extra)

    @property
    def file_name(self):
        return os.path.basename(self.file.name)

    @property
    def public_name(self):
        return self._make_name()

    def _make_name(self):
        extra = {}
        if self.kind == self.FileKinds.CSV_INFOPLAN:
            extra['layer'] = self.layer
        return self.__class__.make_name(self.kind, project=self.project, **extra)

    def _setup_file(self):
        builder_cls = self.FILE_BUILDERS.get(self.kind)
        if not builder_cls:
            raise NotImplementedError(f'ProjectFile.FILE_BUILDERS no value for key {self.kind}')

        builder = builder_cls(self.project)     # type: generators.AbstractCsvFileBuilder
        builder.build()
        self.file.save(self._make_name(), File(builder.buffer_bytes))

    def _setup_layer_file(self):
        builder_cls = self.FILE_BUILDERS.get(self.kind)
        if not builder_cls:
            raise NotImplementedError(f'ProjectFile.FILE_BUILDERS no value for key {self.kind}')

        builder = builder_cls(self.layer)       # type: generators.AbstractCsvFileBuilder
        builder.build()
        filename = self.__class__.make_name(self.kind, project=self.project, layer=self.layer)
        self.file.save(filename, File(builder.buffer_bytes))

    def _setup_pdf_file(self):
        self.kind = self.FileKinds.PDF_EXFOLIATION
        bytes_buf = io.BytesIO()
        filename = self.__class__.make_name(self.kind, project=self.project)
        pdf_module.generate_pdf(self.project, bytes_buf, filename)
        self.file.save(filename, File(bytes_buf))

    def _setup_archive_file(self, files):
        bytes_buf = generators.infoplan_archive.make_tar_archive(files)
        filename = self.__class__.make_name(self.kind, project=self.project)
        self.file.save(filename, File(bytes_buf))

    def is_fresh_project_file(self):
        markers_last_modified = Marker.objects.max_last_modified(project=self.project)
        marker_changes_taken = not markers_last_modified or self.date_created > markers_last_modified
        project_changes_taken = self.date_created > self.project.date_updated_include_layers_pages
        return marker_changes_taken and project_changes_taken

    def is_fresh_layer_file(self):
        layer_markers_last_modified = Marker.objects.max_last_modified(layer=self.layer)
        marker_changes_taken = not layer_markers_last_modified or self.date_created > layer_markers_last_modified
        layer_changes_taken = self.date_created > self.layer.date_updated
        return marker_changes_taken and layer_changes_taken


# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=ProjectFile)
def delete_project_file(sender, instance: ProjectFile, *args, **kwargs):
    """Deletes filesystem file on `post_delete`"""
    if instance.file:
        # _delete_file(instance.file.path)
        instance.file.delete(save=False)


# noinspection PyUnusedLocal
@receiver(models.signals.post_save, sender=ProjectFile)
def remove_previous_versions(sender, instance: ProjectFile, *args, **kwargs):
    """Remove previous entries for same project and kind"""
    same_files = ProjectFile.objects.filter(project=instance.project, kind=instance.kind)
    # csv infoplan files more than one per project, they one per layer
    if instance.kind == ProjectFile.FileKinds.CSV_INFOPLAN:
        same_files = same_files.filter(layer=instance.layer)
    # delete exclude itself
    same_files.exclude(id=instance.id).delete()
