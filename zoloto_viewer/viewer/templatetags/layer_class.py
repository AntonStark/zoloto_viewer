from django import template

register = template.Library()

ENABLED_LAYER_CLASS = 'enabled_layer'


@register.filter
def is_enabled(layer_title, enabled):
    return ENABLED_LAYER_CLASS if layer_title in enabled else ''
