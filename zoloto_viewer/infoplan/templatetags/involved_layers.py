from django import template

register = template.Library()


@register.filter
def involved_layers(markers_by_layer):
    return [layer for layer, markers in markers_by_layer.items() if markers]
