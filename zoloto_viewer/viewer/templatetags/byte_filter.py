import base64
from django import template

register = template.Library()


@register.filter
def as_base64(value):
    return base64.encodebytes(value.encode('utf-8')).decode('utf-8').strip('\n')
