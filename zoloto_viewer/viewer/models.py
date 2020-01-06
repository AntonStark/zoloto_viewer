import uuid
from django.contrib.postgres import fields
from django.db import models, transaction


class Project(models.Model):
    title = models.TextField(blank=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    @transaction.atomic
    def save(self, *args, **kwargs):
        first_save = not self.pk
        super(Project, self).save(*args, **kwargs)
        if first_save:
            Page.objects.create(floor_caption='', project=self)


class Layer(models.Model):
    title = models.CharField(max_length=256, blank=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    color = models.CharField(max_length=6)

    class Meta:
        unique_together = ['project', 'title']


def plan_upload_dir(obj: 'Page', filename):
    return f'project_{obj.project.title}/pages/{filename}'


class Page(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    floor_caption = models.TextField(null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    plan = models.ImageField(upload_to=plan_upload_dir, null=True, default=None)

    class Meta:
        unique_together = ['project', 'floor_caption']


class Marker(models.Model):
    number = models.CharField(max_length=32, blank=False)

    layer = models.ForeignKey(Layer, on_delete=models.SET_NULL, null=True)
    page = models.ForeignKey(Page, on_delete=models.CASCADE)

    points = fields.JSONField(default=list)
    variables = fields.JSONField(default=dict)
    checked = models.BooleanField(null=True, default=None)
