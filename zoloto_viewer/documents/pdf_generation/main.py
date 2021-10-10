import itertools
from reportlab.pdfgen import canvas
from typing import List

from zoloto_viewer.viewer.models import Project, Page, Layer
from zoloto_viewer.infoplan.models import Marker, MarkerVariable
from zoloto_viewer.infoplan.utils import variable_transformations as transformations

from . import layout, message_page_writer as message, plan_page_writer as plan


def generate_pdf(project: Project, buffer, filename):
    file_canvas = canvas.Canvas(buffer, pagesize=layout.Definitions.PAGE_SIZE)
    file_canvas.setTitle(filename)
    at_canvas_beginning = True

    def draw_plan(page, layers):
        super_title = [page.project.title, page.project.stage]
        title = [
            f'Монтажная область {page.file_title}. {page.level_subtitle}',
            (layers[0].title if len(layers) == 1 else '')
        ]

        nonlocal file_canvas
        nonlocal at_canvas_beginning
        if not at_canvas_beginning:
            file_canvas.showPage()
        plan.plan_page(file_canvas, page, layers, marker_objects_many_layers, title, super_title)
        at_canvas_beginning = False

    def draw_messages(page, layer):
        super_title = [page.project.title, page.project.stage]
        title = [
            f'Монтажная область {page.file_title}. {page.level_subtitle}',
            ''
        ]
        marker_messages = make_messages_obj(page, layer)

        nonlocal file_canvas
        nonlocal at_canvas_beginning
        if not at_canvas_beginning:
            file_canvas.showPage()
        message.message_pages(file_canvas, marker_messages, title, super_title)
        at_canvas_beginning = False

    for P in project.page_set.all():
        page_layers = Layer.objects.filter(marker__floor=P).distinct()
        draw_plan(P, page_layers)
        for one_layer in page_layers:       # type: Layer
            draw_plan(P, [one_layer])
            draw_messages(P, one_layer)
    file_canvas.save()


def make_marker_objects(floor: Page, layer: Layer):
    marker_positions = Marker.objects.get_positions(floor, layer)
    marker_numbers = Marker.objects.get_numbers(floor, layer)
    return [
        plan.Object(
            *marker_positions[marker_uid],
            number=marker_numbers[marker_uid],
            layer=layer
        )
        for marker_uid in marker_positions.keys()
        if marker_uid in marker_numbers.keys()
    ]


def marker_objects_many_layers(floor: Page, layers: List[Layer]):
    marker_positions = list(itertools.chain.from_iterable(
        make_marker_objects(floor, L)
        for L in layers
    ))
    return marker_positions


def make_messages_obj(floor: Page, layer: Layer):
    def marker_infoplan(vars_info_by_side, marker_uid, side_keys):
        return [
            (side_key, vars_info_by_side[marker_uid].get(side_key, []))
            for side_key in side_keys
        ]

    filters = [
        transformations.UnescapeHtml(),
        transformations.HideMasterPageLine(),
        transformations.UnescapeTabsText(),
        transformations.ReplacePictCodes()
    ]
    vars_by_side, _ = MarkerVariable.objects.vars_page_layer_by_side(floor, layer, apply_transformations=filters)
    marker_numbers = Marker.objects.get_numbers(floor, layer)

    res = [
        message.MessageElem(
            marker_numbers[marker_uid],
            marker_infoplan(vars_by_side, marker_uid, layer.kind.side_keys()),
            layer.kind.sides,
            layout.color_adapter(layer.color.rgb_code)
        )
        for marker_uid in marker_numbers.keys()
    ]
    return res
