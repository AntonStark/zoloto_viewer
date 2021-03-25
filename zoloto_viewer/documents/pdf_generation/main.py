import re
from reportlab.pdfgen import canvas

from zoloto_viewer.viewer.models import Project, Page, Layer
from zoloto_viewer.infoplan.models import Marker, MarkerVariable
from zoloto_viewer.infoplan.utils import variable_transformations as transformations

from . import layout, message, plan


def generate_pdf(project: Project, buffer, filename):

    if buffer:
        file_canvas = canvas.Canvas(buffer, pagesize=layout.Definitions.PAGE_SIZE)
    else:
        file_canvas = canvas.Canvas(filename, pagesize=layout.Definitions.PAGE_SIZE)

    first_iteration = True
    for L in project.layer_set.order_by('title').all():     # type: Layer
        for P in Page.objects.filter(marker__layer=L).distinct():
            title = [P.floor_caption, L.title]

            if not first_iteration:
                file_canvas.showPage()

            marker_positions = collect_marker_positions(P, L)
            legend_data = L.title, L.desc
            plan.plan_page(file_canvas, P, marker_positions,
                           title, L.kind_id, color_adapter(L.color.rgb_code), legend_data)

            file_canvas.showPage()
            marker_messages = collect_messages_data(P, L)
            message.message_pages(file_canvas, marker_messages, L.kind.sides,
                                  color_adapter(L.color.rgb_code), title)
            first_iteration = False
    file_canvas.setTitle(filename)
    file_canvas.save()
    return filename


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
    vars_by_side, markers = MarkerVariable.objects.vars_page_layer_by_size(floor, layer, apply_transformations=filters)
    marker_numbers = Marker.objects.get_numbers(floor, layer)

    res = [
        (
            marker_numbers[marker_uid],
            marker_infoplan(vars_by_side, marker_uid, layer.kind.side_keys())
        )
        for marker_uid in marker_numbers.keys()
        if marker_uid in markers
    ]
    return res
