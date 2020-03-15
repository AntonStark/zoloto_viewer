from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def timedelta_pretty(value):
    if not value:
        return ''
    if (timezone.now() - value).days > 0:
        return value.strftime('%d/%m')
    else:
        return value.strftime('%H:%M')
