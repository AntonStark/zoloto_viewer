from dataclasses import dataclass, field
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rc
from typing import Any

from zoloto_viewer.viewer.models import Layer

from . import layout


class PlanBox:
    DECLARED_PLAN_ASPECT = 365 / 227

    CAPTION_FONT_NAME = 'Helvetica'
    CAPTION_FONT_SIZE = 6
    CAPTION_DELTA = 8

    CORRECT_CIRCLE_RADIUS = 10

    def __init__(self, image_pil, image_size, indd_bounds):
        self._img = ImageReader(image_pil)
        self._img_size = image_size
        self._indd_bounds = indd_bounds

        self._box_width, self._box_height = layout.work_area_size()
        self._box_x, self._box_y = layout.plan_area_position()

        self._markers = []

    @property
    def markers(self):
        return self._markers

    @markers.setter
    def markers(self, value):
        self._markers = value

    def left_top_corner(self):
        return self._box_x, self._box_y + self._box_height

    def calc_pos(self, point):
        # нужно из points используя _indd_bounds получить координаты относительно подложки
        # и затем используя размер подложки получить координаты относительно canvas
        gb_top, gb_left, gb_bottom, gb_right = self._indd_bounds
        m_x, m_y = point
        rel_x = (m_x - gb_left) / gb_right
        can_x = self._box_x + rel_x * self._box_width
        rel_y = 1. - (m_y - gb_top) / gb_bottom      # invert y axis
        can_y = self._box_y + rel_y * self._box_height
        return can_x, can_y

    def _scale(self, point):
        gb_top, gb_left, gb_bottom, gb_right = self._indd_bounds
        factor = self._box_height / (gb_bottom - gb_top)
        return (factor * point[0], factor * point[1])

    def _draw_caption(self, canvas, marker_center, number):
        x, y = self.calc_pos(marker_center)
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

    def draw(self, canvas: rc.Canvas):
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

        for mo in self._markers:   # type: Object
            mo.draw(canvas, self)
            mo.caption().draw(canvas, self)

    def get_marker_example(self, layer_id):
        original_marker: Object = [mo for mo in self._markers if mo.layer_id == layer_id][0]
        marker_example = original_marker
        marker_example.a = 0
        return marker_example


class PlanLegend:
    def __init__(self, position, y_bottom_bound, layers_count):
        self.x, self.y = position
        scale_factor = self.deduce_scale_factor(self.y, y_bottom_bound, layers_count)
        self.font_name = layout.Definitions.DEFAULT_FONT_NAME
        self.font_size = scale_factor
        self.legend_inter = 4 * scale_factor
        self.desc_padding_left = 3 * scale_factor

    def draw(self, canvas, box, layers):
        text_font_size = self.font_size
        x_mark = self.x
        x_text = x_mark + self.desc_padding_left
        marker_font_size = 3 * text_font_size

        y_top_line = self.y + self.legend_inter
        for l in layers:
            y_top_line = y_top_line - self.legend_inter
            y_next_line = y_top_line - 1.5 * text_font_size

            object_example = Object(x=x_mark, y=y_top_line, a=0, number='', layer=l)
            object_example.draw(canvas, box, convert_pos=False, font_size=marker_font_size)

            canvas.setFont(self.font_name, text_font_size)
            canvas.setFillColor(colors.black)
            canvas.drawString(x_text, y_top_line, l.title)
            canvas.drawString(x_text, y_next_line, l.desc)

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


@dataclass
class Object:
    x: int
    y: int
    a: int
    number: str

    layer: Layer
    layer_id: int = field(init=False)
    layer_color: dict = field(init=False)
    layer_kind: int = field(init=False)

    marker: Any = field(default=None, init=False)

    def __post_init__(self):
        l = self.layer
        self.layer_id = l.id
        self.layer_color = layout.color_adapter(l.color.rgb_code)
        self.layer_kind = l.kind.id

    def __repr__(self):
        return f'<{self.__class__.__name__} number={self.number}>'

    @property
    def center(self):
        return self.x, self.y

    @property
    def position(self):
        return self.x, self.y, self.a

    def caption(self):
        if not self.marker:
            self.marker = MarkerCaption(self.number, rotation=0, obj=self)
        return self.marker

    def draw(self, canvas, box, convert_pos=True, font_size=None):
        MARKS = {
            1: '\uE901',
            2: '\uE902',
            3: '\uE903',
            4: '\uE904',
            5: '\uE900',
        }
        symbol = MARKS[self.layer_kind]
        font = layout.Definitions.MARK_FONT_NAME
        size = font_size or layout.Definitions.MARK_FONT_SIZE
        _centralize = - size / 2

        if convert_pos:
            x, y = box.calc_pos(self.center)
        else:
            x, y = self.center
        rotation = self.a

        canvas.saveState()
        layout.set_colors(canvas, self.layer_color)
        canvas.setFont(font, size)
        canvas.translate(x, y)
        canvas.rotate(-rotation)
        canvas.drawString(_centralize, _centralize, symbol)
        canvas.restoreState()


@dataclass
class MarkerCaption:
    CAPTION_FONT_NAME = 'Helvetica'
    CAPTION_FONT_SIZE = 6
    CAPTION_DELTA = 8

    number: str
    rotation: int

    obj: Object

    def __repr__(self):
        return f'<{self.__class__.__name__} number={self.number}>'

    def draw(self, canvas, box):
        x, y = box.calc_pos(self.obj.center)
        x, y = x + PlanBox.CAPTION_DELTA, y - PlanBox.CAPTION_DELTA

        canvas.setFont(self.CAPTION_FONT_NAME, self.CAPTION_FONT_SIZE)
        width = canvas.stringWidth(self.number)
        height = PlanBox.CAPTION_FONT_SIZE

        canvas.saveState()
        layout.set_colors(canvas, self.obj.layer_color)
        canvas.rect(x, y - 1, width, height, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.drawString(x, y, self.number)
        canvas.restoreState()


@dataclass
class BoundingRect:
    x: int
    y: int
    w: int
    h: int

    def intersect(self, other: 'BoundingRect'):
        pass    # todo
