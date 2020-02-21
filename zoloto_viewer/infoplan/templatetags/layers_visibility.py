from django import template

register = template.Library()

LAYER_PARAM = 'layer'
ENABLED_LAYER_CLASS = 'enabled_layer'


@register.filter
def is_enabled(layer_title, enabled):
    return ENABLED_LAYER_CLASS if layer_title in enabled else ''


@register.filter
def layer_params(enabled_layers):
    return '' if not enabled_layers \
        else '?' + '&'.join(f'{LAYER_PARAM}={l}' for l in enabled_layers)
