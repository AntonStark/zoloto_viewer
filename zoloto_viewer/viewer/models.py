import base64
import io
import os
import re
import shutil
import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.postgres import fields
from django.core.files import File
from django.db import models, transaction
from django.dispatch import receiver
from django.utils import timezone
from os import path

from zoloto_viewer.viewer import data_files


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
    maps_info_data = fields.JSONField(null=True)

    pdf_started = models.DateTimeField(null=True)

    MAPS_INFO = '_maps_info'
    LAYERS_INFO = '_layers_info'
    POI_NAMES = '_poi_names'
    PICT_CODES = '_pict_codes'
    PDF_GENERATION_TIMEOUT = 600

    def first_page(self):
        pages = Page.objects.filter(project=self)
        return pages.first() if pages.exists() else None

    @staticmethod
    def validate_title(title: str):
        return re.match(r'^[-\w]+$', title) is not None \
               and not Project.objects.filter(title=title).exists()

    def pages_by_caption(self):
        return {p.indd_floor: p for p in self.page_set.all()}

    def update_maps_info(self, upload):
        maps_add_data = data_files.map.parse_maps_file(upload.file)
        if not maps_add_data:
            return

        if self.maps_info:
            self.maps_info.delete()
        self.maps_info = upload
        self.maps_info_data = maps_add_data
        transaction.on_commit(lambda: Page.update_maps_info(self, maps_add_data))

    def update_layers_info(self, upload):
        layers_add_data = data_files.layer.parse_layers_file(upload.file)
        if not layers_add_data:
            return

        if self.layers_info:
            self.layers_info.delete()
        self.layers_info = upload
        self.layer_info_data = layers_add_data
        transaction.on_commit(lambda: Layer.update_layers_info(self, layers_add_data))

    def update_additional_files(self, files_dict):
        for title, file in files_dict.items():
            file_kind = Project.is_additional_file(title)
            if file_kind == Project.MAPS_INFO:
                self.update_maps_info(file)
            elif file_kind == Project.LAYERS_INFO:
                self.update_layers_info(file)
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
            Page.create_or_replace(project=self, plan=plan,
                                   indd_floor=name, floor_caption=floor_caption,
                                   maps_info=self.maps_info_data)

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

    def generate_pdf_files(self):
        """Build new pdf files if timeout exceed"""
        if self.pdf_started and timezone.now() < self.pdf_refresh_timeout():
            return None

        orig_pdf = PdfGenerated(mode=PdfGenerated.ORIGINAL, project=self)
        reviewed_pdf = PdfGenerated(mode=PdfGenerated.REVIEWED, project=self)

        orig_pdf.setup()
        reviewed_pdf.setup()

        self.pdf_started = timezone.now()
        self.save()
        return orig_pdf, reviewed_pdf

    def pdf_refresh_timeout(self):
        return self.pdf_started + timedelta(seconds=Project.PDF_GENERATION_TIMEOUT)

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
    raw_color = fields.JSONField(null=True)
    desc = models.TextField(blank=True, default='')

    client_last_modified_date = models.DateTimeField(editable=False, null=True)
    csv_data = models.FileField(upload_to=csv_upload_path, null=False, blank=False)
    sync_needed = models.BooleanField(default=False, null=False)

    class Meta:
        unique_together = ['project', 'title']

    def orig_file_name(self):
        return path.basename(self.csv_data.name)

    def load_next_data(self, csv_file):
        if self.csv_data:
            _delete_file(self.csv_data.path)
            self.csv_data.delete(save=False)
        self.csv_data = csv_file
        self.sync_needed = True
        self.save()

    def set_synced(self):
        self.sync_needed = False
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
        desc, color_str = layer_info[title] if layer_info and title in layer_info else ('', '(RGB, 0, 0, 0)')
        color = data_files.layer.color_as_hex(color_str)
        for layer in Layer.objects.filter(project=project):
            if layer.orig_file_name() == csv_data.name:
                layer.load_next_data(csv_data)
                layer.title = title
                layer.desc = desc
                layer.color = color
                layer.raw_color = data_files.layer.color_as_json(color_str)
                layer.client_last_modified_date = client_last_modified_date
                layer.save()
                return
        Layer(project=project, title=title, desc=desc,
              color=color, raw_color=data_files.layer.color_as_json(color_str),
              csv_data=csv_data, sync_needed=True,
              client_last_modified_date=client_last_modified_date).save()

    @staticmethod
    def update_layers_info(project, layers_info):
        layers = Layer.objects.filter(project=project)
        for L in layers:
            if L.title not in layers_info:
                continue
            desc, color = layers_info[L.title]

            L.color = data_files.layer.color_as_hex(color)
            L.raw_color = data_files.layer.color_as_json(color)
            L.desc = desc
            L.save()


def _delete_file(fpath):
    """ Deletes file from filesystem. """
    if path.isfile(fpath):
        os.remove(fpath)


# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=Layer)
def delete_layer_files(sender, instance: Layer, *args, **kwargs):
    """ Deletes layer csv file on `post_delete` """
    if instance.csv_data:
        _delete_file(instance.csv_data.path)


# noinspection PyUnusedLocal
@receiver(models.signals.post_save, sender=Layer)
def process_layer_csv(sender, instance: Layer, *args, **kwargs):
    from zoloto_viewer.infoplan.models import Marker

    if not (instance.csv_data and instance.sync_needed):
        return

    raw_data = data_files.marker.parse_markers_file(instance.csv_data.file)
    info = data_files.marker.extend_markers_data(raw_data)
    #    у этого процесса есть несколько этапов:
    # 1) найти какие маркеры исчезли в новом файле, записи для них удалить
    # 2) создать записи в базе для совсем новых маркеров
    # 3) у всех обновить переменные если надо
    # todo проверять наличие изменений в переменных маркера и сбрасывать статус проверки только если изменился
    Marker.objects.remove_excess(instance, info.keys())
    Marker.objects.create_missing(instance, instance.project.pages_by_caption(), info)
    Marker.objects.update_variables(info)

    instance.set_synced()


def plan_upload_path(obj: 'Page', filename):
    return f'project_{obj.project.title}/pages/{filename}'


class Page(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, blank=False, unique=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    plan = models.ImageField(upload_to=plan_upload_path, null=True, default=None)
    indd_floor = models.TextField(blank=False, null=False, editable=False)      # текст, лежащий на слое floor
    floor_caption = models.TextField(null=True)                                 # текст, отображаемый на странице

    geometric_bounds = fields.ArrayField(models.FloatField(), null=True, default=None)
    document_offset = models.PositiveSmallIntegerField(null=True, default=None)

    class Meta:
        unique_together = ['project', 'floor_caption']
        ordering = [models.F('document_offset').asc(nulls_last=True)]

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
    def create_or_replace(project, plan, indd_floor, floor_caption, maps_info=None):
        offset, bounds = maps_info[indd_floor] if maps_info and indd_floor in maps_info else (None, None)
        # if plan with equal filename already exists just update them
        for p in Page.objects.filter(project=project):
            if p.orig_file_name() == plan.name:
                p.plan.delete(save=False)
                p.plan = plan
                p.indd_floor = indd_floor
                p.floor_caption = floor_caption
                if offset:
                    p.document_offset = offset
                if bounds:
                    p.geometric_bounds = bounds
                p.save()
                return
        Page(project=project, plan=plan, indd_floor=indd_floor, floor_caption=floor_caption,
             document_offset=offset, geometric_bounds=bounds).save()

    @staticmethod
    def validate_code(page_code):
        return page_code.upper() if isinstance(page_code, str) and len(page_code) == 10 else None

    @staticmethod
    def update_maps_info(project, maps_info):   # maps_info is { indd_floor -> (offset, bounds) }
        for P in Page.objects.filter(project=project):
            if P.indd_floor in maps_info:
                offset, bounds = maps_info[P.indd_floor]
                P.document_offset = offset
                P.geometric_bounds = bounds
                P.save()

    @staticmethod
    def by_code(page_code):
        try:
            return Page.objects.get(code=page_code)
        except Page.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        if not self.code:
            maybe_code = base64.b32encode(self.uid.bytes)[:10].decode('utf-8')
            while Page.by_code(maybe_code):     # already exists
                self.uid = uuid.uuid4()
                maybe_code = base64.b32encode(self.uid.bytes)[:10].decode('utf-8')
            self.code = maybe_code
        super(Page, self).save(*args, **kwargs)


# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=Page)
def delete_page_file(sender, instance: Page, *args, **kwargs):
    """ Deletes page image on `post_delete` """
    if instance.plan:
        _delete_file(instance.plan.path)


def pdf_upload_path(obj: 'PdfGenerated', filename):
    return f'project_{obj.project.title}/pdf/{filename}'


class PdfGenerated(models.Model):
    ORIGINAL = 'o'
    REVIEWED = 'r'
    PDF_MODE_CHOICES = [
        (ORIGINAL, 'original'),
        (REVIEWED, 'reviewed'),
    ]

    file = models.FileField(upload_to=pdf_upload_path)
    mode = models.CharField(max_length=1, choices=PDF_MODE_CHOICES)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def setup(self):
        from zoloto_viewer.infoplan.pdf_generation import main as pdf_module

        bytes_buf = io.BytesIO()
        if self.mode == PdfGenerated.ORIGINAL:
            proposed_filename = pdf_module.generate_pdf_original(self.project, bytes_buf)
        elif self.mode == PdfGenerated.REVIEWED:
            proposed_filename = pdf_module.generate_pdf_reviewed(self.project, bytes_buf)
        else:
            raise ValueError('unexpected mode value')
        self.file.save(proposed_filename, File(bytes_buf))

    @staticmethod
    def get_latest_time(*pdf_files):
        pdf_list = list(map(lambda pdf: pdf.created, filter(None, *pdf_files)))
        return timezone.localtime(max(pdf_list)) if pdf_list else None
