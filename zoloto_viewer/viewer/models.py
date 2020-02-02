import os
import re
import shutil
import uuid
from django.conf import settings
from django.contrib.postgres import fields
from django.db import models, transaction
from django.dispatch import receiver
from django.utils import timezone
from os import path

from zoloto_viewer.viewer.utils import additional_files


def additional_files_upload_path(obj: 'Project', filename):
    return f'project_{obj.title}/additional_files/{filename}'


class Project(models.Model):
    title = models.TextField(blank=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    maps_info = models.FileField(upload_to=additional_files_upload_path, null=False, blank=True, default='')
    layers_info = models.FileField(upload_to=additional_files_upload_path, null=False, blank=True, default='')
    poi_names = models.FileField(upload_to=additional_files_upload_path, null=False, blank=True, default='')
    pict_codes = models.FileField(upload_to=additional_files_upload_path, null=False, blank=True, default='')

    layer_info_data = fields.JSONField(null=True)

    MAPS_INFO = '_maps_info'
    LAYERS_INFO = '_layers_info'
    POI_NAMES = '_poi_names'
    PICT_CODES = '_pict_codes'

    def first_page(self):
        pages = Page.objects.filter(project=self)
        return pages.first() if pages.exists() else None

    @staticmethod
    def validate_title(title: str):
        return re.match(r'^[-\w]+$', title) is not None

    def update_additional_files(self, files_dict):
        for title, file in files_dict.items():
            file_kind = Project.is_additional_file(title)
            if file_kind == Project.MAPS_INFO:
                if self.maps_info:
                    self.maps_info.delete()
                self.maps_info = file
            elif file_kind == Project.LAYERS_INFO:
                layers_add_data = additional_files.parse_layers_info(file)
                if not layers_add_data:
                    continue
                if self.layers_info:
                    self.layers_info.delete()
                self.layers_info = file
                self.layer_info_data = layers_add_data
                transaction.on_commit(lambda: Layer.update_layers_info(self, layers_add_data))
            elif file_kind == Project.POI_NAMES:
                if self.poi_names:
                    self.poi_names.delete()
                self.poi_names = file
            elif file_kind == Project.PICT_CODES:
                if self.pict_codes:
                    self.pict_codes.delete()
                self.pict_codes = file
        self.save()

    def additional_files_info(self):
        attrs = (self.maps_info, self.layers_info, self.poi_names, self.pict_codes)
        return list(map(lambda attr: (path.basename(attr.name), ''), filter(None, attrs)))

    def remove_additional_files(self, filenames):
        if path.basename(self.maps_info.name) in filenames:
            self.maps_info.delete(save=False)
        if path.basename(self.layers_info.name) in filenames:
            self.layers_info.delete(save=False)
        if path.basename(self.poi_names.name) in filenames:
            self.poi_names.delete(save=False)
        if path.basename(self.pict_codes.name) in filenames:
            self.pict_codes.delete(save=False)
        self.save()

    def store_pages(self, pages_data):
        """
        :param pages_data: file_title -> (file, caption)
        """
        for name in pages_data:
            plan, floor_caption = pages_data[name]
            Page.create_or_replace(project=self, plan=plan, indd_floor=name, floor_caption=floor_caption)

    def create_layers(self, csv_data):
        for title, data in csv_data.items():
            Layer.create_or_replace(project=self, title=title, csv_data=data,
                                    client_last_modified_date=timezone.now(),
                                    layer_info=self.layer_info_data)

    def alter_floor_captions(self, captions_dict):
        for p in Page.objects.filter(project=self):
            filename = path.basename(p.plan.name)
            if filename in captions_dict.keys():
                p.floor_caption = captions_dict[filename]
                p.save()

    @staticmethod
    def is_additional_file(title):
        possible_suffix = (Project.MAPS_INFO, Project.LAYERS_INFO, Project.POI_NAMES, Project.PICT_CODES)
        for s in possible_suffix:
            if title.endswith(s):
                return s
        return False


# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=Project)
def project_cleanup(sender, instance: Project, *args, **kwargs):
    project_dir = path.join(settings.MEDIA_ROOT, f'project_{instance.title}')
    if path.isdir(project_dir):
        shutil.rmtree(project_dir)


def csv_upload_next_path(obj: 'Layer', filename):
    return f'project_{obj.project.title}/layers/next_{filename}'


def csv_upload_path(obj: 'Layer', filename):
    return f'project_{obj.project.title}/layers/{filename}'


def csv_upload_prev_path(obj: 'Layer', filename):
    return f'project_{obj.project.title}/layers/prev_{filename}'


class Layer(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=256, blank=False)
    color = models.CharField(max_length=7, default='#000000')
    desc = models.TextField(blank=True, default='')

    client_last_modified_date = models.DateTimeField(editable=False, null=True)
    next_csv_data = models.FileField(upload_to=csv_upload_next_path, null=False, blank=True, default='')
    csv_data = models.FileField(upload_to=csv_upload_path, null=False, blank=False)
    prev_csv_data = models.FileField(upload_to=csv_upload_prev_path, null=False, blank=True, default='')

    class Meta:
        unique_together = ['project', 'title']

    def orig_file_name(self):
        return path.basename(self.csv_data.name)

    def load_next(self, csv_file):
        if self.next_csv_data:
            self.next_csv_data.delete(save=False)
        self.next_csv_data = csv_file
        self.save()

    def serialize(self):
        return path.basename(self.csv_data.name), self.client_last_modified_date

    @staticmethod
    def remove_from_project(project, filename):
        for layer in Layer.objects.filter(project=project):
            if path.basename(layer.csv_data.name) == filename:
                layer.delete()

    @staticmethod
    def create_or_replace(project, title, csv_data, client_last_modified_date, layer_info=None):
        desc, color = layer_info[title] if title in layer_info else ('', '#000000')
        for layer in Layer.objects.filter(project=project):
            if layer.orig_file_name() == csv_data.name:
                layer.load_next(csv_data)
                layer.title = title
                layer.desc = desc
                layer.color = additional_files.color_as_hex(color)
                layer.client_last_modified_date = client_last_modified_date
                layer.save()
                return
        Layer(project=project, title=title, desc=desc, color=additional_files.color_as_hex(color), csv_data=csv_data,
              client_last_modified_date=client_last_modified_date).save()

    @staticmethod
    def update_layers_info(project, info):
        layers = Layer.objects.filter(project=project)
        for l in layers:
            if l.title not in info:
                continue
            desc, color = info[l.title]

            l.color = additional_files.color_as_hex(color)
            l.desc = desc
            l.save()


def _delete_file(fpath):
    """ Deletes file from filesystem. """
    if path.isfile(fpath):
        os.remove(fpath)


# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=Layer)
def delete_layer_files(sender, instance: Layer, *args, **kwargs):
    """ Deletes layer csv files on `post_delete` """
    if instance.next_csv_data:
        _delete_file(instance.next_csv_data.path)
    if instance.csv_data:
        _delete_file(instance.csv_data.path)
    if instance.prev_csv_data:
        _delete_file(instance.prev_csv_data.path)


def plan_upload_path(obj: 'Page', filename):
    return f'project_{obj.project.title}/pages/{filename}'


class Page(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    plan = models.ImageField(upload_to=plan_upload_path, null=True, default=None)
    indd_floor = models.TextField(blank=False, null=False, editable=False)      # текст, лежащий на слое floor
    floor_caption = models.TextField(null=True)                                 # текст, отображаемый на странице

    class Meta:
        unique_together = ['project', 'floor_caption']

    def orig_file_name(self):
        return path.basename(self.plan.name)

    def serialize(self):
        return self.floor_caption, self.orig_file_name()

    @staticmethod
    def remove_from_project(project, filename):
        for p in Page.objects.filter(project=project):
            if p.orig_file_name() == filename:
                p.delete()

    @staticmethod
    def create_or_replace(project, plan, indd_floor, floor_caption):
        # if plan with equal filename already exists just update them
        for p in Page.objects.filter(project=project):
            if p.orig_file_name() == plan.name:
                p.plan.delete(save=False)
                p.plan = plan
                p.indd_floor = indd_floor
                p.floor_caption = floor_caption
                p.save()
                return
        Page(project=project, plan=plan, indd_floor=indd_floor, floor_caption=floor_caption).save()


# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=Page)
def delete_page_file(sender, instance: Page, *args, **kwargs):
    """ Deletes page image on `post_delete` """
    if instance.plan:
        _delete_file(instance.plan.path)


class Marker(models.Model):
    """
    После загрузки нового csv данные об ошибках не должны пропадать из системы окончательно
    todo Возможно, данные связанные с проверкой маркеров стоит хранить в отдельной сущности
    """
    number = models.CharField(max_length=32, blank=False)

    layer = models.ForeignKey(Layer, on_delete=models.SET_NULL, null=True)
    floor = models.ForeignKey(Page, on_delete=models.CASCADE)

    points = fields.JSONField(default=list)
    variables = fields.JSONField(default=dict)
    checked = models.BooleanField(null=True, default=None)

    class Meta:
        unique_together = ['floor', 'number']
