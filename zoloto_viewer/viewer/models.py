import base64
import re
import shutil
import uuid

from django.conf import settings
from django.contrib.postgres import fields
from django.db import models
from django.dispatch import receiver
from os import path
from PIL import Image
from typing import List


def additional_files_upload_path(obj: 'Project', filename):
    return path.join(obj.project_files_dir(), f'additional_files/{filename}')


class Project(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    customer = models.TextField(blank=False, default='')
    title = models.TextField(blank=False, unique=True)
    stage = models.TextField(blank=False, default='')

    layer_info_data = fields.JSONField(null=True)   # possibly not needed anymore
    maps_info_data = fields.JSONField(null=True)

    @property
    def date_updated_include_layers_pages(self):
        last_updated_layers = self.layer_set.aggregate(value=models.Max('date_updated'))['value'] \
            if self.layer_set.exists() else self.date_updated
        last_updated_pages = self.page_set.aggregate(value=models.Max('date_updated'))['value'] \
            if self.page_set.exists() else self.date_updated
        return max([self.date_updated, last_updated_layers, last_updated_pages])

    @property
    def is_set_layers_groups_started(self):
        return LayerGroup.objects.filter(project=self).exists()

    def first_page(self):
        pages = Page.objects.filter(project=self)
        return pages.first() if pages.exists() else None

    def last_layer(self):
        layers = Layer.objects.filter(project=self)
        return layers.last() if layers.exists() else None

    @staticmethod
    def validate_title(title: str):
        return not Project.objects.filter(title=title).exists()

    def pages_by_caption(self):
        return {p.indd_floor: p for p in self.page_set.all()}

    def rename_project(self, customer, title, stage):
        changed = False
        if customer != self.customer:
            self.customer = customer
            changed = True
        if title != self.title:
            self.title = title
            changed = True
        if stage != self.stage:
            self.stage = stage
            changed = True
        if changed:
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

    def alter_floor_captions(self, captions_dict):
        for p in Page.objects.filter(project=self):
            filename = p.orig_file_name
            if filename in captions_dict.keys():
                p.floor_caption = captions_dict[filename]
                p.save()

    def alter_floor_offsets(self, floor_offsets):
        for p in Page.objects.filter(project=self):
            caption = p.floor_caption
            if caption in floor_offsets.keys():
                p.document_offset = floor_offsets[caption]
                p.save()

    def alter_floor_levels(self, floor_levels):
        for p in Page.objects.filter(project=self):
            caption = p.floor_caption
            if caption in floor_levels.keys():
                p.level = floor_levels[caption]
                p.save()


# noinspection PyUnusedLocal
@receiver(models.signals.post_delete, sender=Project)
def project_cleanup(sender, instance: Project, *args, **kwargs):
    project_dir = path.join(settings.MEDIA_ROOT, f'project_{instance.title}')
    if path.isdir(project_dir):
        shutil.rmtree(project_dir)


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
    date_updated = models.DateTimeField(auto_now=True)

    number = models.IntegerField(null=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, default=1)
    raw_color = fields.JSONField(null=True)
    kind = models.ForeignKey(MarkerKind, on_delete=models.PROTECT, default=1)

    class Meta:
        unique_together = [['project', 'title']]
        ordering = ['number']

    def save(self, *args, **kwargs):
        if self.title:
            self.number = Layer.extract_number(self.title)
        super(Layer, self).save(*args, **kwargs)

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
        }

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

    @classmethod
    def serialize_from_ids(cls, layer_ids):
        return [
            l.to_json()
            for l in Layer.objects.filter(id__in=layer_ids)
        ]


class LayerGroup(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    layers = fields.ArrayField(models.IntegerField())
    num = models.IntegerField(null=False, default=0)

    layer_ids_list = List[int]

    class Meta:
        unique_together = [['project', 'num']]
        ordering = ['num']

    def append_layers(self, layers_id_list):
        self.layers = list(set(self.layers) | set(layers_id_list))
        self.save()

    def exclude_layers(self, layer_id_list):
        self.layers = [l_id for l_id in self.layers if l_id not in layer_id_list]
        self.save()

    def save(self, *args, **kwargs):
        if not self.num and self.project:
            self.num = LayerGroup.max_project_group_num(self.project) + 1
        super(LayerGroup, self).save(*args, **kwargs)

    def to_json(self):
        return {
            'num': self.num,
            'layers': Layer.serialize_from_ids(self.layers),
        }

    @classmethod
    def add_empty(cls, project):
        cls(project=project, layers=[]).save()
        project.save()

    @classmethod
    def autogroup_layers(cls, project, layers_ids: layer_ids_list):
        def chunks(seq, n):
            for i in range(0, len(seq), n):
                yield seq[i:i + n]

        layers_per_group = 5
        for layers in chunks(layers_ids, layers_per_group):
            group = cls(project=project, layers=layers)
            group.save()
        project.save()  # to refresh date_updated

    @classmethod
    def exclude_from_groups(cls, layer_id_list):
        groups = cls.objects.filter(layers__contains=layer_id_list)
        for gr in groups:
            gr.exclude_layers(layer_id_list)

    @classmethod
    def not_grouped_layer_ids(cls, project):
        all_layers = [l.id for l in Layer.objects.filter(project=project).all()]
        grouped_layers = []
        for gr in cls.objects.filter(project=project).all():
            grouped_layers.extend(gr.layers)

        remain_layers_ids = [l_id for l_id in all_layers if l_id not in grouped_layers]
        return remain_layers_ids

    @classmethod
    def max_project_group_num(cls, project):
        groups_same_project = LayerGroup.objects.filter(project=project)
        max_num = groups_same_project.aggregate(value=models.Max('num'))['value']
        return max_num if max_num else 0

    @classmethod
    def report_groups(cls, project):
        not_grouped = cls.not_grouped_layer_ids(project)
        report = {
            'groups': [
                group.to_json()
                for group in LayerGroup.objects.filter(project=project).all()
            ],
            'not_grouped_layers': Layer.serialize_from_ids(not_grouped),
        }
        return report

    @classmethod
    def setup_groups_bulk(cls, project, layers_per_group: List[layer_ids_list]):
        existing_groups = cls.objects.filter(project=project).all()
        if len(existing_groups) < len(layers_per_group):    # need to create more
            count_to_create = len(layers_per_group) - len(existing_groups)
            for _ in range(count_to_create):
                existing_groups.append(cls(project=project))

        for group, layers_ids in zip(existing_groups, layers_per_group):
            group.layers = layers_ids
            group.save()

        if len(existing_groups) > len(layers_per_group):    # need to remove excess
            for group in existing_groups[len(layers_per_group):]:
                group.delete()

        project.save()  # just to update project.date_updated


def plan_upload_path(obj: 'Page', filename):
    return path.join(obj.project.project_files_dir(), f'pages/{filename}')


class Page(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, blank=False, unique=True)
    plan = models.ImageField(upload_to=plan_upload_path, null=True, default=None)
    date_updated = models.DateTimeField(auto_now=True)

    indd_floor = models.TextField(blank=False, null=False, editable=False)      # текст, лежащий на слое floor
    floor_caption = models.TextField(null=True)                                 # текст, отображаемый на странице
    document_offset = models.PositiveSmallIntegerField(null=True, default=None) # настройка порядка страниц
    level = models.FloatField(null=True)

    marker_size_factor = models.IntegerField(default=100)       # possible values are: {SIZE_FACTOR_ALLOWED}

    SIZE_FACTOR_ALLOWED = [50, 75, 100, 125, 150, 200]
    MAP_SCALE_ALLOWED = [100, 125, 150, 200]

    class Meta:
        unique_together = ['project', 'floor_caption']
        ordering = [models.F('document_offset').asc(nulls_last=True)]

    @property
    def geometric_bounds(self):
        top = left = 0
        bottom = self.plan.height
        right = self.plan.width
        geometric_bounds = [top, left, bottom, right]
        return geometric_bounds

    @property
    def level_subtitle(self):
        return f'Отметка {self.level:.3f}' if self.level else ''

    @property
    def file_title(self):
        return self.indd_floor

    @property
    def orig_file_name(self):
        return path.basename(self.plan.name)

    @property
    def plan_pil_obj(self):
        return Image.open(self.plan)

    @staticmethod
    def remove_from_project(project, filename):
        for p in Page.objects.filter(project=project):
            if p.orig_file_name == filename:
                p.delete()

    @staticmethod
    def create_or_replace(project, plan, indd_floor, floor_caption):
        # if plan with equal floor_caption already exists just update them
        p = Page.objects.filter(project=project, floor_caption=floor_caption).first()
        if not p:
            p = Page(project=project, plan=plan, indd_floor=indd_floor, floor_caption=floor_caption)
            p.save()
        else:
            p.plan.delete(save=False)
            p.plan = plan
            p.indd_floor = indd_floor
            p.save()
        return p

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

    def apply_size_factor(self, value: (int, dict)):
        if isinstance(value, (int, float)):
            return value * self.marker_size_factor / 100
        elif isinstance(value, dict):
            return {k: self.apply_size_factor(v)
                    for k, v in value.items()}
        else:
            raise TypeError('Page.apply_size_factor: value should be int, float or dict with values of such types')

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
        instance.plan.delete(save=False)
