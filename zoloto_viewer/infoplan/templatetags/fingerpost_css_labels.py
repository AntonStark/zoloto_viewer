from django import template

from zoloto_viewer.infoplan.models import MarkerFingerpost

register = template.Library()


@register.filter
def fingerpost_css_labels(fingerpost: MarkerFingerpost):
    return fingerpost.make_css_labels_string()
