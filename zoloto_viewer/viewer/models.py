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
from django.db import models
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

    def last_layer(self):
        layers = Layer.objects.filter(project=self)
        return layers.last() if layers.exists() else None

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
                                   indd_floor=name, floor_caption=floor_caption)

    def create_layers(self, csv_data):
        for title, data in csv_data.items():
            Layer.create_or_replace(project=self, title=title, csv_data=data,
                                    client_last_modified_date=timezone.now())

    def alter_floor_captions(self, captions_dict):
        for p in Page.objects.filter(project=self):
            filename = p.orig_file_name
            if filename in captions_dict.keys():
                p.floor_caption = captions_dict[filename]
                p.save()

    def alter_floor_offsets(self, floor_offsets):
        for p in Page.objects.filter(project=self):
            filename = p.orig_file_name
            if filename in floor_offsets.keys():
                p.document_offset = floor_offsets[filename]
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
    sides = models.IntegerField(default=1)
    svg_figures = models.TextField()

    class Meta:
        ordering = ['id']

    def side_keys(self):
        def key(n): return n + 1
        return [key(s) for s in range(self.sides)]


class Color(models.Model):
    hex_code = models.CharField(max_length=7, default='#000000')
    rgb_code = models.CharField(max_length=16, default='rgb(0,0,0)')

    def next(self):
        try:
            c = Color.objects.get(id=self.id + 1)
        except Color.DoesNotExist:
            c = Color.objects.get(id=1)
        return c


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
        unique_together = [['project', 'title']]
        ordering = ['-number']

    @property
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

    def save(self, *args, **kwargs):
        if not self.number and self.title:
            self.number = Layer.extract_number(self.title)
            self.save()
        super(Layer, self).save(*args, **kwargs)

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
            if layer.orig_file_name == csv_data.name:
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
    def test_title_free(project, title, except_=None):
        q = Layer.objects.filter(project=project, title=title)
        if except_:
            q = q.exclude(id__in=[except_.id])
        if q.exists():
            raise ValueError('Такой номер типа уже используется')

    @staticmethod
    def validate_title(title: str):
        if not re.match(r'^\d+_.+', title):
            raise ValueError('Номер типа должен быть вида ЧИСЛО_БУКВЫ')

    @staticmethod
    def extract_number(title: str):
        match = re.match(r'^\d+', title)
        return int(match.group(0)) if match else None

    @staticmethod
    def max_color(layers: models.QuerySet):
        color_id = layers.aggregate(value=models.aggregates.Max('color'))['value']
        return Color.objects.get(id=color_id) if color_id else None


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


def plan_upload_path(obj: 'Page', filename):
    return path.join(obj.project.project_files_dir(), f'pages/{filename}')


class Page(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, blank=False, unique=True)
    plan = models.ImageField(upload_to=plan_upload_path, null=True, default=None)

    indd_floor = models.TextField(blank=False, null=False, editable=False)      # текст, лежащий на слое floor
    floor_caption = models.TextField(null=True)                                 # текст, отображаемый на странице
    document_offset = models.PositiveSmallIntegerField(null=True, default=None) # настройка порядка страниц

    marker_size_factor = models.IntegerField(default=100)       # possible values are: {SIZE_FACTOR_ALLOWED}

    SIZE_FACTOR_ALLOWED = [50, 75, 100, 125, 150, 200]
    MAP_SCALE_ALLOWED = [100, 125, 150, 200]

    class Meta:
        unique_together = ['project', 'floor_caption']
        ordering = [models.F('document_offset').asc(nulls_last=True)]

    @property
    def orig_file_name(self):
        return path.basename(self.plan.name)

    @property
    def geometric_bounds(self):
        top = left = 0
        bottom = self.plan.height
        right = self.plan.width
        geometric_bounds = [top, left, bottom, right]
        return geometric_bounds

    @staticmethod
    def remove_from_project(project, filename):
        for p in Page.objects.filter(project=project):
            if p.orig_file_name == filename:
                p.delete()

    @staticmethod
    def create_or_replace(project, plan, indd_floor, floor_caption):
        # if plan with equal filename already exists just update them
        for p in Page.objects.filter(project=project):
            if p.orig_file_name == plan.name:
                p.plan.delete(save=False)
                p.plan = plan
                p.indd_floor = indd_floor
                p.floor_caption = floor_caption
                p.save()
                return
        Page(project=project, plan=plan, indd_floor=indd_floor, floor_caption=floor_caption).save()

    @staticmethod
    def validate_code(page_code):
        return page_code.upper() if isinstance(page_code, str) and len(page_code) == 10 else None

    @staticmethod
    def validate_size_factor(value):
        return value in Page.SIZE_FACTOR_ALLOWED

    @staticmethod
    def by_code(page_code):
        try:
            return Page.objects.get(code=page_code)
        except Page.DoesNotExist:
            return None

    def apply_size_factor(self, value):
        return value * self.marker_size_factor / 100

    def save(self, *args, **kwargs):
        if not self.code:
            maybe_code = base64.b32encode(self.uid.bytes)[:10].decode('utf-8')
            while Page.by_code(maybe_code):     # already exists
                self.uid = uuid.uuid4()
                maybe_code = base64.b32encode(self.uid.bytes)[:10].decode('utf-8')
            self.code = maybe_code
        if self.document_offset is None and self.project:
            pages_same_project = Page.objects.filter(project=self.project)
            max_offset = pages_same_project.aggregate(value=models.Max('document_offset'))['value']
            self.document_offset = max_offset + 1 if max_offset else 1
        super(Page, self).save(*args, **kwargs)


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
