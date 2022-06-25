import itertools
import re

from dataclasses import dataclass, field
from reportlab.lib import colors
from typing import Any

from . import layout


@dataclass
class MessageElem:
    FONT_NAME = layout.Definitions.DEFAULT_FONT_NAME
    FONT_SIZE = 7
    PICT_FONT_SIZE = 10

    PADDING_LEFT = 0.5 * FONT_SIZE
    PADDING_RIGHT = PADDING_LEFT
    PADDING_SIDES = PADDING_LEFT
    PADDING_BOTTOM = 0.5 * FONT_SIZE
    PADDING_TOP = 0.1 * FONT_SIZE
    MIN_WIDTH = 30

    NUMBER_RECT_HEIGHT = 1.6 * FONT_SIZE
    MESSAGE_SIDE_MIN_WIDTH = 50
    CORRECT_MARK_RADIUS = 10
    CORRECT_MARK_FONT_SIZE = 1.5 * CORRECT_MARK_RADIUS

    number: str
    infoplan: list
    side_count: int
    layer_color: dict

    canvas: Any = field(init=False)
    text_lines_per_side: dict = field(init=False)
    max_var_width: int = field(init=False, default=None)
    side_heights: dict = field(init=False)

    def __post_init__(self):
        self._infoplan_to_lines()
        self._calc_side_heights()

    def draw(self, position):
        self.canvas.saveState()
        self._draw_bounds(position)
        self._draw_number(position)

        x_start, y_start = position
        y_top = y_start + self.get_height()
        y_number = y_top - self.FONT_SIZE - self.PADDING_TOP
        y_text = y_number - 2 * 1.2 * self.FONT_SIZE
        x_text = x_start + self.PADDING_LEFT

        # self.max_var_width must be set with prior call to set_canvas
        for side, _ in self.infoplan:
            x_side = x_text + (side - 1) * (self.PADDING_SIDES + self.max_var_width)
            self._draw_side(x_side, y_text, side)

        self.canvas.restoreState()

    def get_height(self):
        # number, empty = 2
        # 1.2 for interline space
        height = 2 * 1.2 * self.FONT_SIZE + max(self.side_heights.values()) + self.PADDING_BOTTOM
        return height

    def get_side_header(self, side: int) -> str:
        if self.side_count == 1:
            return ''
        elif self.side_count == 8:
            return f'Лопасть {side}'
        else:
            return {
                1: 'Сторона A',
                2: 'Сторона B',
                3: 'Сторона C',
                4: 'Сторона D',
            }.get(side, 'Сторона')

    def get_width(self):
        if self.max_var_width is None:
            raise ValueError('need to set canvas')

        width = self.PADDING_LEFT + self.side_count * self.max_var_width \
                + (self.side_count - 1) * self.PADDING_SIDES \
                + self.PADDING_RIGHT
        if width < self.MIN_WIDTH:
            width = self.MIN_WIDTH
        # not less than number width
        number_width = self._number_width()
        if width < number_width:
            width = number_width
        return width

    def set_canvas(self, canvas):
        self.canvas = canvas
        self._set_max_var_width()

    def _set_max_var_width(self):
        width_list = [
            line.get_width(self.canvas)
            for lines in self.text_lines_per_side.values()
            for line in lines
        ]
        self.max_var_width = max(width_list) if width_list else 0

    def _draw_bounds(self, position):
        x_start, y_start = position
        box_width, box_height = self.get_width(), self.get_height()
        layout.set_colors(self.canvas, self.layer_color)
        self.canvas.rect(x_start, y_start, box_width, box_height, stroke=1, fill=0)

    def _draw_number(self, position):
        x_start, y_start = position
        self.canvas.setFont(self.FONT_NAME, self.FONT_SIZE)
        nr_w = self._number_width()
        nr_h = self.NUMBER_RECT_HEIGHT
        x_text = x_start + self.PADDING_LEFT
        y_top = y_start + self.get_height()
        self.canvas.rect(x_start, y_top - nr_h, nr_w, nr_h, stroke=0, fill=1)
        y_number = y_top - self.FONT_SIZE - self.PADDING_TOP
        self.canvas.setFillColor(colors.white)
        self.canvas.drawString(x_text, y_number, self.number)

    def _draw_side(self, x_side, y_side, side_number):
        side_text = self.canvas.beginText(x_side, y_side)
        side_text.setFont(self.FONT_NAME, self.FONT_SIZE)
        side_text.setFillColor(colors.black)

        text_lines = self.text_lines_per_side[side_number]
        first_line = True
        for line in text_lines:     # type: TextPictLine
            if first_line:
                line.write_to_text_no_newline(side_text)
            else:
                line.write_to_text_newline_before(side_text)
            first_line = False
        self.canvas.drawText(side_text)

    def _infoplan_to_lines(self):
        self.text_lines_per_side = dict()
        for side, vars_list in self.infoplan:
            side_lines = []
            side_header = self.get_side_header(side)
            if side_header:
                side_lines.append(TextPictLine.from_plain(side_header))
            for v in vars_list:
                side_lines.extend(parse_var_to_lines_objs(v))
            # self.text_lines_per_side.append((side, side_lines))
            # use dict
            self.text_lines_per_side[side] = side_lines

    def _calc_side_heights(self):
        self.side_heights = dict()
        for side, lines in self.text_lines_per_side.items():
            line_heights = [
                self.PICT_FONT_SIZE if line.contains_picts() else self.FONT_SIZE
                for line in lines
            ]
            # 1.2 for interline space
            self.side_heights[side] = 1.2 * sum(line_heights)

    def _number_width(self):
        self.canvas.setFont(self.FONT_NAME, self.FONT_SIZE)
        return self.canvas.stringWidth(self.number) + self.PADDING_LEFT + self.PADDING_RIGHT


class TextPictLine:
    def __init__(self, source):
        # source: [(text: str, is_pict: bool), ]
        self._source = source

    def __repr__(self):
        return self._source.__repr__()

    def contains_picts(self):
        return any(is_pict for text, is_pict in self._source)

    @classmethod
    def from_plain(cls, text):
        return cls([(text, False)])

    def get_width(self, canvas):
        w = 0
        for text, is_pict in self._source:
            canvas.setFont(self._font_name(is_pict), self._font_size(is_pict))
            w += canvas.stringWidth(text)
        return w

    def write_to_text(self, text_obj):
        for text, is_pict in self._source:
            text_obj.setFont(self._font_name(is_pict), self._font_size(is_pict))
            text_obj.textOut(text)
        is_pict = False
        text_obj.setFont(self._font_name(is_pict), self._font_size(is_pict))
        text_obj.textLine()

    def write_to_text_no_newline(self, text_obj):
        for text, is_pict in self._source:
            text_obj.setFont(self._font_name(is_pict), self._font_size(is_pict))
            text_obj.textOut(text)

    def write_to_text_newline_before(self, text_obj):
        try:
            _, start_from_pict = self._source[0]
        except IndexError:
            start_from_pict = False
        text_obj.setFont(self._font_name(start_from_pict), self._font_size(start_from_pict))
        text_obj.textLine()

        for text, is_pict in self._source:
            if is_pict:
                text_obj.setRise(-3)
            text_obj.setFont(self._font_name(is_pict), self._font_size(is_pict))
            text_obj.textOut(text)
            if is_pict:
                text_obj.setRise(0)

    def _font_name(self, is_pict):
        font_name = layout.Definitions.PICT_FONT_NAME if is_pict \
            else layout.Definitions.DEFAULT_FONT_NAME
        return font_name

    def _font_size(self, is_pict):
        font_size = MessageElem.PICT_FONT_SIZE if is_pict \
            else MessageElem.FONT_SIZE
        return font_size


class MessagesAreaFreeBox:
    def __init__(self, width, height):
        self._width = width
        self._height = height

        self._row_mess_heights = []
        self._row_top_bound = self._height - self.padding_top()
        self._padding_left = self.row_start()

    def enough_height(self, mess_height):
        return self._row_top_bound > mess_height

    def enough_width(self, mess_width):
        return self._padding_left + mess_width < self._width

    def error_message(self, canvas, message):
        canvas.setFont(MessageElem.FONT_NAME, MessageElem.FONT_SIZE)
        canvas.drawString(self._padding_left + self.padding_col(), self._row_top_bound,
                          'Недостаточно места для отображения переменных. '
                          + f'Инфоплан {message.number} был пропущен.')

    def place_message(self, mess_width, mess_height):
        # check enough space
        if not self.enough_width(mess_width):
            self.new_row()
        if not self.enough_width(mess_width):
            raise layout.TooLargeMessageException
        if not self.enough_height(mess_height):
            raise layout.NotEnoughSpaceException

        # place
        left = self._padding_left
        bottom = self._row_top_bound - mess_height

        # update state
        self._row_mess_heights.append(mess_height)
        self._padding_left += mess_width + self.padding_col()
        return left, bottom

    def new_row(self):
        self._row_top_bound -= max(self._row_mess_heights) + self.padding_row()
        self._row_mess_heights.clear()
        self._padding_left = self.row_start()

    def padding_col(self):
        return layout.Definitions.MESSAGES_PADDING_COL

    def padding_top(self):
        return layout.Definitions.MESSAGES_PADDING_TOP

    def padding_row(self):
        return layout.Definitions.MESSAGES_PADDING_ROW

    def row_start(self):
        return 0


def replace_tabs(line: str):
    picts_collapsed = re.sub(r'<span[A-z=_" ]*>(.+?)</span>', 'P', line)
    while '\t' in picts_collapsed:
        pos = picts_collapsed.index('\t')
        spaces = 4 - pos % 4
        picts_collapsed = picts_collapsed.replace('\t', ' ' * spaces, 1)
        line = line.replace('\t', ' ' * spaces, 1)
    return line


def parse_picts(line):
    # '<span class="infoplan_icon">◻</span>\nПервая + пикта в начале\nFirst + pict in front'
    parsed = []
    while pict_tag_found := re.search(r'<span[A-z=_" ]*>(.+?)</span>', line):
        if pict_tag_found.start(0) != 0:
            pre_str = line[0: pict_tag_found.start(0)]
            parsed.append((pre_str, False))
            line = line.replace(pre_str, '')
        else:
            pict_tag, pict_code = pict_tag_found[0], pict_tag_found[1]
            parsed.append((pict_code, True))
            line = line.replace(pict_tag, '', 1)
    else:
        remainder = line
        if remainder:
            parsed.append((remainder, False))
    return parsed


def parse_var_to_lines_objs(var_lines):
    buf = []
    for line in var_lines.split('\n'):
        res = line
        res = replace_tabs(res)
        res = parse_picts(res)  # res: [(str, bool), ]
        buf.append(TextPictLine(res))
    return buf


def calc_variable_metrics(marker_messages):
    # marker_messages: [ ( number, [(side, vars_list)] ), ]
    def var_lines(value: str):
        return value.count('\n') + 1

    max_var_count = max(
        sum(var_lines(v) for v in vars_list)
        for _, infoplan in marker_messages
        for _, vars_list in infoplan
    )

    def variable_lines(variables):
        return itertools.chain.from_iterable(v.split('\n') for v in variables)

    var_lines = list(itertools.chain.from_iterable(
        variable_lines(vars_list)
        for _, infoplan in marker_messages
        for _, vars_list in infoplan
    ))
    return var_lines, max_var_count
