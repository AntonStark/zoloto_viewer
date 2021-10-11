from typing import List

from zoloto_viewer.viewer.models import Layer, Page

from . import layout
from .plan import PlanBox, PlanLegend, Object, MarkerCaption, BoundingRect


class PlanPageWriter(layout.BasePageWriterDeducingTitle):
    _content_box = None

    def __init__(self, canvas, floor: Page, layers: List[Layer], marker_positions_getter):
        self.floor = floor
        self.layers = layers
        self._marker_positions = marker_positions_getter(floor, layers)
        super().__init__(canvas)

    @classmethod
    def place_legend(cls):
        x, y = layout.plan_area_position_left_top()
        x += layout.Definitions.PLAN_LEGEND_PADDING_LEFT
        y -= layout.Definitions.PLAN_LEGEND_PADDING_TOP
        return x, y

    def draw_content(self):
        self._draw_plan_markers()
        self._draw_legend()

    def make_page_title(self):
        title = [
            f'Монтажная область {self.floor.file_title}. {self.floor.level_subtitle}',
            (self.layers[0].title if len(self.layers) == 1 else '')
        ]
        return title

    def make_page_super_title(self):
        super_title = [self.floor.project.title, self.floor.project.stage]
        return super_title

    def _draw_plan_markers(self):
        self._content_box = PlanBox(self.floor.plan_pil_obj,
                                    (self.floor.plan.width, self.floor.plan.height),
                                    self.floor.geometric_bounds)
        self._content_box.markers = self._marker_positions
        self._content_box.draw(self.canvas)

    def _draw_legend(self):
        legend = PlanLegend(self.place_legend(), layout.Definitions.BOTTOM_LINE, len(self.layers))
        legend.draw(self.canvas, self._content_box, self.layers)
