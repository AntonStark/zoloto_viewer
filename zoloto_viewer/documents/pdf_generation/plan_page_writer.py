import logging

from typing import List

from zoloto_viewer.viewer.models import Layer, Page

from . import layout
from .plan import PlanBox, PlanLegend, Object

logger = logging.getLogger(__name__)


class PlanPageWriterMinimal(layout.BasePageWriterDeducingTitle):
    _content_box = None

    def __init__(self, canvas, floor: Page, layers: List[Layer], marker_positions_getter):
        self.floor = floor
        self.layers = layers
        self._marker_positions = marker_positions_getter(floor, layers)
        self.draw_options = {
            'marker_size_factor': floor.marker_size_factor,
        }
        self._content_box = PlanBox(self.floor.plan_pil_obj,
                                    (self.floor.plan.width, self.floor.plan.height),
                                    self.floor.geometric_bounds)
        super().__init__(canvas)

    @classmethod
    def place_legend(cls):
        x, y = layout.plan_area_position_left_top()
        x += layout.Definitions.PLAN_LEGEND_PADDING_LEFT
        y -= layout.Definitions.PLAN_LEGEND_PADDING_TOP
        return x, y

    def draw_content(self):
        self._content_box.draw_plan_image(self.canvas, **self.draw_options)
        self._draw_markers(self._marker_positions)
        self._draw_legend(self.layers)

    def make_page_title(self):
        title = [
            f'Монтажная область {self.floor.file_title}. {self.floor.level_subtitle}',
            ''
        ]
        return title

    def make_page_super_title(self):
        super_title = [self.floor.project.title, self.floor.project.stage]
        return super_title

    def _draw_markers(self, objects):
        options = self.draw_options
        for mo in objects:   # type: Object
            mo.draw(self.canvas, self._content_box, **options)

    def _draw_legend(self, layers):
        legend = PlanLegend(self.place_legend(), layout.Definitions.BOTTOM_LINE, len(layers))
        legend.draw(self.canvas, self._content_box, layers)
