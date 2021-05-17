import re
from reportlab.pdfgen import canvas

from zoloto_viewer.viewer.models import Project, Page, Layer
from zoloto_viewer.infoplan.models import Marker, MarkerVariable
from zoloto_viewer.infoplan.utils import variable_transformations as transformations

from . import layout, message, plan


def generate_pdf(project: Project, buffer, filename):
    file_canvas = canvas.Canvas(buffer, pagesize=layout.Definitions.PAGE_SIZE)
    file_canvas.setTitle(filename)
    at_canvas_beginning = True

    def draw_plan(page, layers):
        title = [page.floor_caption, layers[0].title] if len(layers) == 1 else [page.floor_caption, '']
        layers_data = [
            plan.LayerData(L.id, L.title, L.desc, color_adapter(L.color.rgb_code), L.kind_id)
            for L in layers
        ]
        marker_positions = {
            L.id: collect_marker_positions(page, L)
            for L in layers
        }

        nonlocal file_canvas
        nonlocal at_canvas_beginning
        if not at_canvas_beginning:
            file_canvas.showPage()
        plan.plan_page(file_canvas, page, marker_positions, layers_data, title)
        at_canvas_beginning = False

    def draw_messages(page, layer):
        title = [page.floor_caption, layer.title]
        marker_messages = collect_messages_data(page, layer)

        nonlocal file_canvas
        nonlocal at_canvas_beginning
        if not at_canvas_beginning:
            file_canvas.showPage()
        message.message_pages(file_canvas, marker_messages, layer.kind.sides,
                              color_adapter(layer.color.rgb_code), title)
        at_canvas_beginning = False

    for P in project.page_set.all():
        page_layers = Layer.objects.filter(marker__floor=P).distinct()
        draw_plan(P, page_layers)
        for one_layer in page_layers:       # type: Layer
            draw_plan(P, [one_layer])
            draw_messages(P, one_layer)
    file_canvas.save()


def color_adapter(html_color):
    """
    Transform to inner package format
    :param html_color: string like 'rgb(36,182,255)'
    :return: {model, values} where model = 'CMYK' | 'RGB' and values: 3 or 4 int tuple
    """
    parse3 = re.match(r'^(?P<model>\w+)\((?P<values>\d+%?, ?\d+%?, ?\d+%?(?:, ?\d+%?)?)\)$', html_color)
    model, values_string = parse3.groups()
    return {
        'model': model.upper(),
        'values': [int(v.rstrip('%')) for v in values_string.split(',')]
    }


def collect_marker_positions(floor: Page, layer: Layer):
    marker_positions = Marker.objects.get_positions(floor, layer)
    marker_numbers = Marker.objects.get_numbers(floor, layer)
    return [
        (marker_numbers[marker_uid], marker_positions[marker_uid])
        for marker_uid in marker_positions.keys()
        if marker_uid in marker_numbers.keys()
    ]


def collect_messages_data(floor: Page, layer: Layer):
    def marker_infoplan(vars_info_by_side, marker_uid, side_keys):
        return [
            (side_key, vars_info_by_side.get((marker_uid, side_key), []))
            for side_key in side_keys
        ]

    filters = [
        transformations.UnescapeHtml(),
        transformations.HideMasterPageLine(),
        transformations.EliminateTabsText(),
        transformations.ReplacePictCodes()
    ]
    vars_by_side, markers = MarkerVariable.objects.vars_page_layer_by_side(floor, layer, apply_transformations=filters)
    marker_numbers = Marker.objects.get_numbers(floor, layer)

    res = [
        (
            marker_numbers[marker_uid],
            marker_infoplan(vars_by_side, marker_uid, layer.kind.side_keys())
        )
        for marker_uid in marker_numbers.keys()
    ]
    return res
