import urllib.parse
from django import template

register = template.Library()


@register.filter
def query_params(params: dict):
    return '' if not params \
        else '?' + urllib.parse.urlencode(params, safe=',')
