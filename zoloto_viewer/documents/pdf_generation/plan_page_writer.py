from collections import namedtuple
from typing import List

from zoloto_viewer.viewer.models import Page

from . import layout
from .plan import PlanBox, PlanLegend

LayerData = namedtuple('LayerData', ['id', 'title', 'description', 'color', 'kind_id'])


class PlanPageWriter(layout.BasePageWriter):
    _content_box = None
    _layers_data = None
    _marker_positions = None

    def __init__(self, canvas, title, super_title,
                 floor: Page, marker_positions, layers_data: List[LayerData]):
        super().__init__(canvas, title, super_title)
        self.set_params(floor, marker_positions, layers_data)

    @classmethod
    def place_legend(cls):
        x, y = layout.plan_area_position_left_top()
        x += layout.Definitions.PLAN_LEGEND_PADDING_LEFT
        y -= layout.Definitions.PLAN_LEGEND_PADDING_TOP
        return x, y

    def draw_content(self):
        for layer_id, layer_markers in self._marker_positions.items():
            for number, position in layer_markers:
                self._content_box.add_marker(layer_id, number, position)
        self._content_box.draw(self.canvas)

        pl = PlanLegend(self.place_legend(), layout.Definitions.BOTTOM_LINE, len(self._layers_data))
        pl.draw_legend(self.canvas, self._content_box, self._layers_data)

    def set_params(self, floor: Page, marker_positions, layers_data: List[LayerData]):
        layer_colors = {
            ld.id: ld.color
            for ld in layers_data
        }
        layer_kinds = {
            ld.id: ld.kind_id
            for ld in layers_data
        }
        self._layers_data = layers_data
        self._content_box = PlanBox(floor.plan_pil_obj,
                                    (floor.plan.width, floor.plan.height),
                                    floor.geometric_bounds,
                                    layer_colors, layer_kinds)
        self._marker_positions = marker_positions


def plan_page(canvas, floor: Page, marker_positions, layers_data: List[LayerData], title, super_title):
    writer = PlanPageWriter(canvas, title, super_title, floor, marker_positions, layers_data)
    writer.write()
