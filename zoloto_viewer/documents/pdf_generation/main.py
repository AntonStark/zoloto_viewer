import itertools
from reportlab.pdfgen import canvas as reportlab_canvas
from typing import List

from zoloto_viewer.viewer.models import Project, Page, Layer, LayerGroup
from zoloto_viewer.infoplan.models import Marker, MarkerFingerpost, MarkerVariable
from zoloto_viewer.infoplan.utils import variable_transformations as transformations

from . import layout, message_page_writer as message, plan_page_writer as plan


def generate_pdf(project: Project, buffer, filename):
    canvas = reportlab_canvas.Canvas(buffer, pagesize=layout.Definitions.PAGE_SIZE)
    canvas.setTitle(filename)
    at_canvas_beginning = True

    def first_page_canvas_management(method):
        def inner(*args, **kwargs):
            nonlocal canvas
            nonlocal at_canvas_beginning
            if not at_canvas_beginning:
                canvas.showPage()
            at_canvas_beginning = False

            method(*args, **kwargs)

        return inner

    @first_page_canvas_management
    def draw_plan_no_captions(page, layers):
        writer = plan.PlanPageWriterMinimal(canvas, page, layers, make_marker_objects_many_layers)
        writer.write()

    @first_page_canvas_management
    def draw_plan_active_layers_group(page, layers, active_layers):
        writer = plan.PlanPageWriterLayerGroups(canvas, page, layers, active_layers, make_marker_objects_many_layers)
        writer.write()

    @first_page_canvas_management
    def draw_messages(page, layers):
        writer = message.MessagePageWriter(canvas, page, layers, make_messages_obj_many_layers)
        writer.write()

    layer_groups = LayerGroup.objects.filter(project=project)
    for P in project.page_set.all():
        page_layers = Layer.objects.filter(marker__floor=P).distinct()
        draw_plan_no_captions(P, page_layers)
        for lg in layer_groups:     # type: LayerGroup
            active_layers = Layer.objects.filter(id__in=lg.layers)
            try:
                draw_plan_active_layers_group(P, page_layers, active_layers)
            except layout.NoMarkersInActiveGroupException:
                # handle that showPage already was called and need to skip next call
                at_canvas_beginning = True
                continue
        draw_messages(P, page_layers)
    canvas.save()


def make_marker_objects(floor: Page, layer: Layer):
    marker_positions = Marker.objects.get_positions(floor, layer)
    marker_numbers = Marker.objects.get_numbers(floor, layer)
    fingerpost_data = MarkerFingerpost.bulk_serialize(marker_numbers.keys()) if layer.kind.is_fingerpost else {}
    return [
        plan.Object(
            *marker_positions[marker_uid],
            number=marker_numbers[marker_uid],
            layer=layer,
            fingerpost_meta=fingerpost_data.get(marker_uid, {}),
        )
        for marker_uid in marker_positions.keys()
        if marker_uid in marker_numbers.keys()
    ]


def make_marker_objects_many_layers(floor: Page, layers: List[Layer]):
    marker_positions = list(itertools.chain.from_iterable(
        make_marker_objects(floor, L)
        for L in layers
    ))
    return marker_positions


def make_messages_obj(floor: Page, layer: Layer):
    def marker_infoplan(vars_info_by_side, marker_uid, side_keys):
        infoplan = vars_info_by_side.get(marker_uid, {})
        return [
            (side_key, infoplan.get(side_key, []))
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


def make_messages_obj_many_layers(floor: Page, layers: List[Layer]):
    messages = list(itertools.chain.from_iterable(
        make_messages_obj(floor, L)
        for L in layers
    ))
    return messages
