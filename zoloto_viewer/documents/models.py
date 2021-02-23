import io
import os
from datetime import timedelta
from django.core.files import File
from django.db import models
from django.dispatch import receiver
from os import path

from zoloto_viewer.infoplan.pdf_generation import main as pdf_module


def additional_files_upload_path(obj, filename):
    return path.join(obj.project_files_dir(), f'additional_files/{filename}')


def _delete_file(fpath):
    """ Deletes file from filesystem. """
    if path.isfile(fpath):
        os.remove(fpath)


class ProjectFilesManager(models.Manager):

    def docs_stats(self, project):
        pdf_set = self.filter(project=project, kind__exact=self.model.FileKinds.PDF_EXFOLIATION)
        pdf_model_obj = pdf_set.latest('date_created') if pdf_set.exists() else None
        pdf_created_time = pdf_model_obj.date_created if pdf_model_obj else None
        pdf_refresh_timeout = self.pdf_refresh_timeout(project)
        return {
            'pdf': {
                'pdf_original': pdf_model_obj,
                'pdf_created_time': pdf_created_time,
                'pdf_refresh_timeout': pdf_refresh_timeout,
            },
            # ...
        }

    def pdf_generate_file(self, project):
        obj = self.model(project=project)
        obj._setup_pdf_file()
        return obj

    def pdf_refresh_timeout(self, project):
        pdf_docs_set = self.filter(project=project, kind__exact=self.model.FileKinds.PDF_EXFOLIATION)
        latest_date = pdf_docs_set.latest('date_created') if pdf_docs_set.exists() else None
        return latest_date + timedelta(seconds=self.model.PDF_GENERATION_TIMEOUT) if latest_date \
            else -float('Inf')


class ProjectFile(models.Model):
    """
    Отражает факт наличия файлов проекта разных видов
    """

    class FileKinds(models.IntegerChoices):
        PDF_EXFOLIATION = 1     # pdf
        CSV_LAYER_STATS = 2     # кол-во
        CSV_INFOPLAN = 3        # инфоплан
        CSV_VARIABLES = 4       # словарь
        CSV_PICT_CODES = 5      # пикты

    project = models.ForeignKey('viewer.Project', on_delete=models.CASCADE)
    file = models.FileField(upload_to=additional_files_upload_path, null=False, blank=True, default='')
    kind = models.IntegerField(choices=FileKinds.choices)
    date_created = models.DateTimeField(auto_now_add=True)

    objects = ProjectFilesManager()

    PDF_GENERATION_TIMEOUT = 600

    @property
    def file_name(self):
        return os.path.basename(self.file.name)

    def _setup_pdf_file(self):
        bytes_buf = io.BytesIO()
        proposed_filename = pdf_module.generate_pdf(self.project, bytes_buf, with_review=False)
        self.file.save(proposed_filename, File(bytes_buf))
        self.kind = self.FileKinds.PDF_EXFOLIATION
        self.save()


# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=ProjectFile)
def delete_project_file(sender, instance: ProjectFile, *args, **kwargs):
    """ Deletes page image on `post_delete` """
    if instance.file:
        _delete_file(instance.file.path)


# noinspection PyUnusedLocal
@receiver(models.signals.post_save, sender=ProjectFile)
def remove_previous_versions(sender, instance: ProjectFile, *args, **kwargs):
    """Remove previous entries for same project and kind"""
    ProjectFile.objects\
        .filter(project=instance.project, kind=instance.kind)\
        .exclude(id=instance.id).delete()       # exclude itself
