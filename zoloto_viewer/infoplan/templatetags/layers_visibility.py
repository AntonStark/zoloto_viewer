from django import template

register = template.Library()

HIDDEN_LAYERS_PARAM = 'hide_layers'
ENABLED_LAYER_CLASS = 'enabled_layer'


@register.filter
def is_not_disabled(layer_title, disabled_layers):
    return ENABLED_LAYER_CLASS if layer_title not in disabled_layers else ''


@register.filter
def hidden_layers_url_param(disabled_layers):
    return {
        HIDDEN_LAYERS_PARAM: ' '.join(disabled_layers)
    } if disabled_layers else {}
