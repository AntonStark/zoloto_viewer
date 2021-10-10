from typing import List

from zoloto_viewer.viewer.models import Page

from . import layout
from .plan import PlanBox, PlanLegend, Object, MarkerCaption, BoundingRect


class PlanPageWriter(layout.BasePageWriter):
    _content_box = None
    _marker_positions = None
    floor = None
    layers = None

    def __init__(self, canvas, title, super_title,
                 floor: Page, layers, marker_positions_getter):
        super().__init__(canvas, title, super_title)
        self.floor = floor
        self.layers = layers
        self._marker_positions = marker_positions_getter(floor, layers)

    @classmethod
    def place_legend(cls):
        x, y = layout.plan_area_position_left_top()
        x += layout.Definitions.PLAN_LEGEND_PADDING_LEFT
        y -= layout.Definitions.PLAN_LEGEND_PADDING_TOP
        return x, y

    def draw_content(self):
        self._draw_plan_markers()
        self._draw_legend()

    def _draw_plan_markers(self):
        self._content_box = PlanBox(self.floor.plan_pil_obj,
                                    (self.floor.plan.width, self.floor.plan.height),
                                    self.floor.geometric_bounds)
        self._content_box.markers = self._marker_positions
        self._content_box.draw(self.canvas)

    def _draw_legend(self):
        legend = PlanLegend(self.place_legend(), layout.Definitions.BOTTOM_LINE, len(self.layers))
        legend.draw(self.canvas, self._content_box, self.layers)


def plan_page(canvas, floor: Page, layers, marker_obj_getter, title, super_title):
    writer = PlanPageWriter(canvas, title, super_title, floor, layers, marker_obj_getter)
    writer.write()
