import re
import uuid
from django.contrib.postgres import fields
from django.db import models
from django.utils import timezone
from os import path


class Project(models.Model):
    title = models.TextField(blank=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    def first_page(self):
        pages = Page.objects.filter(project=self)
        return pages.first() if pages.exists() else None

    @staticmethod
    def validate_title(title: str):
        return re.match(r'^[-\w]+$', title) is not None

    def store_pages(self, pages_data):
        """
        :param pages_data: file_title -> (file, caption)
        """
        for name in pages_data:
            plan, floor_caption = pages_data[name]
            Page.create_or_replace(project=self, plan=plan, indd_floor=name, floor_caption=floor_caption)

    def create_layers(self, csv_data):
        for title, data in csv_data.items():
            if title.endswith('_info'):     # *_maps_info.csv and *_layers_info.csv files not layer data
                continue
            Layer(project=self, title=title, csv_data=data, client_last_modified_date=timezone.now()).save()

    def alter_floor_captions(self, captions_dict):
        for p in Page.objects.filter(project=self):
            filename = path.basename(p.plan.name)
            if filename in captions_dict.keys():
                p.floor_caption = captions_dict[filename]
                p.save()


def csv_upload_path(obj: 'Layer', filename):
    return f'project_{obj.project.title}/layers/{filename}'


class Layer(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=256, blank=False)
    color = models.CharField(max_length=6, default='000000')

    csv_data = models.FileField(upload_to=csv_upload_path, null=False)
    client_last_modified_date = models.DateTimeField(editable=False, null=True)
    prev_csv_data = models.FileField(upload_to=csv_upload_path, null=True, default=None)

    class Meta:
        unique_together = ['project', 'title']

    # def save(self, *args, **kwargs):      # todo
    #     """
    #     Если уже есть prev_csv_data, старый файл нужно запомнить для удаления,
    #     перенести csv_data -> prev_csv_data, и записать новый файл в csv_data
    #     И только в transaction.on_commit удаляем старый файл
    #     """
    #     pass

    def serialize(self):
        return path.basename(self.csv_data.name), self.client_last_modified_date

    @staticmethod
    def remove_from_project(project, filename):
        for l in Layer.objects.filter(project=project):
            if path.basename(l.csv_data.name) == filename:
                l.delete()


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
