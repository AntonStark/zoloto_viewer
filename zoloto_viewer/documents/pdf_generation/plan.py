import typing as t
from collections import namedtuple
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rc

from zoloto_viewer.viewer.models import Page

from . import layout


MarkerData = namedtuple('MarkerData', ['x', 'y', 'a', 'number', 'layer_id'])
LayerData = namedtuple('LayerData', ['id', 'title', 'description', 'color', 'kind_id'])


class PlanBox:
    DECLARED_PLAN_ASPECT = 365 / 227

    CAPTION_FONT_NAME = 'Helvetica'
    CAPTION_FONT_SIZE = 6
    CAPTION_DELTA = 8

    CORRECT_CIRCLE_RADIUS = 10

    def __init__(self, image_pil, image_size, indd_bounds, layer_colors, layer_kinds):
        self._img = ImageReader(image_pil)
        self._img_size = image_size
        self._indd_bounds = indd_bounds

        self._layer_colors = layer_colors
        self._layer_kinds = layer_kinds

        self._box_width, self._box_height = layout.work_area_size()
        self._box_x, self._box_y = layout.plan_area_position()

        self._markers = []

    def left_top_corner(self):
        return self._box_x, self._box_y + self._box_height

    def add_marker(self, layer_id, number, position):
        self._markers.append(MarkerData(*position, number=number, layer_id=layer_id))

    def _scale(self, point):
        gb_top, gb_left, gb_bottom, gb_right = self._indd_bounds
        factor = self._box_height / (gb_bottom - gb_top)
        return (factor * point[0], factor * point[1])

    def _calc_pos(self, point):
        # нужно из points используя _indd_bounds получить координаты относительно подложки
        # и затем используя размер подложки получить координаты относительно canvas
        gb_top, gb_left, gb_bottom, gb_right = self._indd_bounds
        m_x, m_y = point
        rel_x = (m_x - gb_left) / gb_right
        can_x = self._box_x + rel_x * self._box_width
        rel_y = 1. - (m_y - gb_top) / gb_bottom      # invert y axis
        can_y = self._box_y + rel_y * self._box_height
        return can_x, can_y

    def _draw_marker(self, canvas, center, rotation, layer_id, convert_pos=True, font_size=None):
        MARKS = {
            1: '\uE901',
            2: '\uE902',
            3: '\uE903',
            4: '\uE904',
            5: '\uE900',
        }
        marker_kind = self._layer_kinds[layer_id]
        symbol = MARKS[marker_kind]
        font = layout.Definitions.MARK_FONT_NAME
        size = font_size or layout.Definitions.MARK_FONT_SIZE
        _centralize = - size / 2

        if convert_pos:
            x, y = self._calc_pos(center)
        else:
            x, y = center

        canvas.saveState()
        self._set_color(canvas, self._layer_colors[layer_id])
        canvas.setFont(font, size)
        canvas.translate(x, y)
        canvas.rotate(-rotation)
        canvas.drawString(_centralize, _centralize, symbol)
        canvas.restoreState()

    def _draw_review_status(self, canvas, center, correct=True):
        if correct is not None:
            if correct:
                canvas.setStrokeColor(colors.green)
            else:
                canvas.setStrokeColor(colors.red)
            x, y = self._calc_pos(center)
            canvas.circle(x, y, PlanBox.CORRECT_CIRCLE_RADIUS)

    def _draw_caption(self, canvas, marker_center, number):
        x, y = self._calc_pos(marker_center)
        x, y = x + PlanBox.CAPTION_DELTA, y - PlanBox.CAPTION_DELTA
        canvas.setFont(self.CAPTION_FONT_NAME, self.CAPTION_FONT_SIZE)
        width = canvas.stringWidth(number)
        height = PlanBox.CAPTION_FONT_SIZE

        canvas.rect(x, y - 1, width, height, stroke=0, fill=1)
        canvas.saveState()
        canvas.setFillColor(colors.white)
        canvas.drawString(x, y, number)
        canvas.restoreState()

    def _set_color(self, canvas, color):
        model = color.get('model', None)
        values = color.get('values', None)
        if model == 'CMYK' and len(values) == 4:
            canvas.setFillColorCMYK(*[v / 100. for v in values])
        elif model == 'RGB' and len(values) == 3:
            canvas.setFillColorRGB(*[v / 255. for v in values])

    def draw(self, canvas: rc.Canvas, with_review=False):
        # ведущее направеление считаем так: берём отношение ширина/высота
        # если оно больше или равно заданному тогда горизонталь ведущее направление, в противном случае вертикаль
        # если это горизонталь, обновляем self._box_height
        # если вертикаль, то нужно пересчитать ширину и сдвиг слева
        actual_aspect = self._img_size[0] / self._img_size[1]
        if actual_aspect >= PlanBox.DECLARED_PLAN_ASPECT:
            self._box_height = self._box_width / actual_aspect
            canvas.drawImage(self._img, x=self._box_x, y=self._box_y,
                             width=self._box_width, preserveAspectRatio=True, anchor='sw')
        else:
            new_width = self._box_height * actual_aspect
            self._box_x += (self._box_width - new_width) / 2
            self._box_width = new_width
            canvas.drawImage(self._img, x=self._box_x, y=self._box_y,
                             height=self._box_height, preserveAspectRatio=True, anchor='sw')

        if self._markers:
            for m in self._markers:   # type: MarkerData
                center = m.x, m.y
                layer_id = m.layer_id
                self._set_color(canvas, self._layer_colors[layer_id])
                self._draw_marker(canvas, center, m.a, layer_id)
                self._draw_caption(canvas, center, m.number)
                if with_review:
                    self._draw_review_status(canvas, center)

    def draw_marker_example(self, canvas, position, layer_id, font_size):
        self._draw_marker(canvas, position, 0, layer_id, convert_pos=False, font_size=font_size)


class PlanLegend:
    def __init__(self, position, y_bottom_bound, layers_count):
        self.x, self.y = position
        scale_factor = self.deduce_scale_factor(self.y, y_bottom_bound, layers_count)
        self.font_name = layout.Definitions.DEFAULT_FONT_NAME
        self.font_size = scale_factor
        self.legend_inter = 4 * scale_factor
        self.desc_padding_left = 3 * scale_factor

    def draw_legend(self, canvas, box, layers_data):
        text_font_size = self.font_size
        x_mark = self.x
        x_text = x_mark + self.desc_padding_left
        marker_font_size = 3 * text_font_size

        y_top_line = self.y + self.legend_inter
        for ld in layers_data:   # type: LayerData
            y_top_line = y_top_line - self.legend_inter
            y_next_line = y_top_line - 1.5 * text_font_size

            box.draw_marker_example(canvas, (x_mark, y_top_line), ld.id, font_size=marker_font_size)
            canvas.setFont(self.font_name, text_font_size)
            canvas.setFillColor(colors.black)
            canvas.drawString(x_text, y_top_line, ld.title)
            canvas.drawString(x_text, y_next_line, ld.description)

    def deduce_scale_factor(self, y_top, y_bottom_bound, layers_count):
        # y_next_line = y_top - 4 * SCALE_FACTOR * (layers_count - 1) - 1.5 * SCALE_FACTOR
        # y_next_line_min = y_top - SCALE_FACTOR * (4 * layers_count - 1.5)
        try_values = [7, 6, 5, 4]

        def probe(scale_factor):
            y_min = y_top - scale_factor * (4 * layers_count - 1.5)
            is_above_bound = y_min > y_bottom_bound
            return is_above_bound

        for value in try_values:
            if probe(value):
                return value
        return try_values[-1]


def plan_page(canvas, floor: Page, marker_positions, layers_data: t.List[LayerData], title, super_title):
    layer_colors = {
        ld.id: ld.color
        for ld in layers_data
    }
    layer_kinds = {
        ld.id: ld.kind_id
        for ld in layers_data
    }
    box = PlanBox(floor.plan_pil_obj, (floor.plan.width, floor.plan.height), floor.geometric_bounds, layer_colors, layer_kinds)
    for layer_id, layer_markers in marker_positions.items():
        for number, position in layer_markers:
            box.add_marker(layer_id, number, position)

    layout.draw_header(canvas, title, super_title)
    layout.draw_footer(canvas)
    box.draw(canvas)

    x, y = layout.plan_area_position_left_top()
    x += layout.Definitions.PLAN_LEGEND_PADDING_LEFT
    y -= layout.Definitions.PLAN_LEGEND_PADDING_TOP
    pl = PlanLegend((x, y), layout.Definitions.BOTTOM_LINE, len(layers_data))
    pl.draw_legend(canvas, box, layers_data)
