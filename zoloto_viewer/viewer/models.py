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
    return path.join(obj.project_files_dir(), f'additional_files/{filename}')


class Project(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    title = models.TextField(blank=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    maps_info = models.FileField(upload_to=additional_files_upload_path, null=False, blank=True, default='')
    layers_info = models.FileField(upload_to=additional_files_upload_path, null=False, blank=True, default='')
    poi_names = models.FileField(upload_to=additional_files_upload_path, null=False, blank=True, default='')
    pict_codes = models.FileField(upload_to=additional_files_upload_path, null=False, blank=True, default='')

    layer_info_data = fields.JSONField(null=True)   # possibly not needed anymore
    maps_info_data = fields.JSONField(null=True)

    pdf_started = models.DateTimeField(null=True)

    # todo check is it still needed
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

    def rename_project(self, title):
        if title != self.title:
            self.title = title
            self.save()

    def project_files_dir(self):
        return f'project_{self.uid}'

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
                                    client_last_modified_date=timezone.now())

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
        return self.pdf_started + timedelta(seconds=Project.PDF_GENERATION_TIMEOUT) if self.pdf_started \
            else -float('Inf')


# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=Project)
def project_cleanup(sender, instance: Project, *args, **kwargs):
    project_dir = path.join(settings.MEDIA_ROOT, f'project_{instance.title}')
    if path.isdir(project_dir):
        shutil.rmtree(project_dir)


def csv_upload_next_path(obj: 'Layer', filename):
    return f'project_{obj.project.title}/layers/next_{filename}'


def csv_upload_path(obj: 'Layer', filename):
    return path.join(obj.project.project_files_dir(), f'layers/{filename}')


def csv_upload_prev_path(obj: 'Layer', filename):
    return f'project_{obj.project.title}/layers/prev_{filename}'


class MarkerKind(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16, blank=False)


class Color(models.Model):
    hex_code = models.CharField(max_length=7, default='#000000')
    rgb_code = models.CharField(max_length=16, default='rgb(0,0,0)')


class Layer(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=256, blank=False)
    desc = models.TextField(blank=True, default='')

    number = models.IntegerField(null=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, default=1)
    raw_color = fields.JSONField(null=True)
    kind = models.ForeignKey(MarkerKind, on_delete=models.PROTECT, default=1)

    client_last_modified_date = models.DateTimeField(editable=False, null=True)
    csv_data = models.FileField(upload_to=csv_upload_path, null=False, blank=False)
    sync_needed = models.BooleanField(default=False, null=False)

    class Meta:
        unique_together = [['project', 'title'], ['project', 'number']]

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
        desc, color_str = ('', '(RGB, 0, 0, 0)')
        if layer_info and title in layer_info:
            desc, color_str = layer_info[title]
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

    @staticmethod
    def title_free(project, title) -> bool:
        return not Layer.objects.filter(project=project, title=title).exists()

    @staticmethod
    def validate_title(title: str):
        if not re.match(r'^\d+_.+', title):
            raise ValueError('Expected string starting with number followed by underscore.')


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
    Marker.objects.update_variables(instance, info)

    instance.set_synced()


def plan_upload_path(obj: 'Page', filename):
    return path.join(obj.project.project_files_dir(), f'pages/{filename}')


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
        offset, bounds = (None, None)
        if maps_info and indd_floor in maps_info:
            offset, bounds = maps_info[indd_floor]
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
@receiver(models.signals.post_save, sender=Page)
def default_geometric_bounds(sender, instance: Page, *args, **kwargs):
    print('default_geometric_bounds')
    if not instance.geometric_bounds:
        print('default_geometric_bounds works')
        top = left = 0
        bottom = instance.plan.height
        right = instance.plan.width
        instance.geometric_bounds = [top, left, bottom, right]
        instance.save()

# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=Page)
def delete_page_file(sender, instance: Page, *args, **kwargs):
    """ Deletes page image on `post_delete` """
    if instance.plan:
        _delete_file(instance.plan.path)


def pdf_upload_path(obj: 'PdfGenerated', filename):
    return path.join(obj.project.project_files_dir(), f'pdf/{filename}')


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


# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=PdfGenerated)
def delete_pdf_docs(sender, instance: PdfGenerated, *args, **kwargs):
    """ Deletes pdf documents on `post_delete` """
    if instance.file:
        _delete_file(instance.file.path)


# noinspection PyUnusedLocal
@receiver(models.signals.post_save, sender=PdfGenerated)
def remove_previous_versions(sender, instance: PdfGenerated, *args, **kwargs):
    """Remove previous entries for same project and move"""
    PdfGenerated.objects.filter(project=instance.project, mode=instance.mode)\
        .exclude(id=instance.id).delete()       # exclude itself
