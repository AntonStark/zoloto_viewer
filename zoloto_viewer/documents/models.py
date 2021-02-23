import os
from django.db import models
from django.dispatch import receiver
from os import path


def additional_files_upload_path(obj, filename):
    return path.join(obj.project_files_dir(), f'additional_files/{filename}')


def _delete_file(fpath):
    """ Deletes file from filesystem. """
    if path.isfile(fpath):
        os.remove(fpath)


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

    @property
    def file_name(self):
        return os.path.basename(self.file.name)


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
