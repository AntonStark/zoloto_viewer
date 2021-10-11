from typing import List

from zoloto_viewer.viewer.models import Layer, Page

from . import layout
from .plan import PlanBox, PlanLegend, Object


class PlanPageWriterMinimal(layout.BasePageWriterDeducingTitle):
    _content_box = None

    def __init__(self, canvas, floor: Page, layers: List[Layer], marker_positions_getter):
        self.floor = floor
        self.layers = layers
        self._marker_positions = marker_positions_getter(floor, layers)
        self.draw_options = {
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
        self.draw_options['draw_captions'] = False
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
        self._content_box.markers = self._marker_positions
        self._content_box.draw(self.canvas, **self.draw_options)

    def _draw_legend(self):
        legend = PlanLegend(self.place_legend(), layout.Definitions.BOTTOM_LINE, len(self.layers))
        legend.draw(self.canvas, self._content_box, self.layers)


class PlanPageWriterLayerGroups(PlanPageWriterMinimal):
    def __init__(self, canvas,
                 floor: Page, layers: List[Layer], active_layers: List[Layer],
                 marker_positions_getter):
        super().__init__(canvas, floor, layers, marker_positions_getter)
        self._active_layers = active_layers
        self._marker_positions_active = [mo for mo in self._marker_positions if mo.layer in active_layers]
        # skip layer group where no markers
        if not self._marker_positions_active:
            raise NoMarkersInActiveGroupException
        self._marker_positions_inactive = [mo for mo in self._marker_positions if mo.layer not in active_layers]

    def draw_content(self):
        self.draw_options['draw_captions'] = False
        self._draw_plan_markers_inactive()
        # todo introduce opacity
        self.draw_options['draw_captions'] = True
        self._draw_plan_markers_active()
        self._draw_legend()

    def _draw_legend(self):
        legend = PlanLegend(self.place_legend(), layout.Definitions.BOTTOM_LINE, len(self._active_layers))
        legend.draw(self.canvas, self._content_box, self._active_layers)

    def _draw_plan_markers_inactive(self):
        self._content_box.markers = self._marker_positions_inactive
        self._content_box.draw(self.canvas, **self.draw_options)

    def _draw_plan_markers_active(self):
        self._content_box.markers = self._marker_positions_active
        self._content_box.draw(self.canvas, **self.draw_options)


class NoMarkersInActiveGroupException(Exception):
    pass
