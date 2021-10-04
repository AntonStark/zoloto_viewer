import itertools
import re
from reportlab.lib import units, colors

from . import layout


def set_colors(canvas, color):
    model = color.get('model', None)
    values = color.get('values', None)
    if model == 'CMYK' and len(values) == 4:
        canvas.setFillColorCMYK(*[v / 100. for v in values])
        canvas.setStrokeColorCMYK(*[v / 100. for v in values])
    elif model == 'RGB' and len(values) == 3:
        canvas.setFillColorRGB(*[v / 255. for v in values])
        canvas.setStrokeColorRGB(*[v / 255. for v in values])


class MessageBox:
    FONT_NAME = layout.Definitions.DEFAULT_FONT_NAME
    # FONT_NAME = layout.Definitions.MESSAGES_FONT_NAME
    FONT_SIZE = 7
    PICT_FONT_SIZE = 10

    PADDING_LEFT = 0.5 * FONT_SIZE
    PADDING_RIGHT = PADDING_LEFT
    PADDING_SIDES = PADDING_LEFT
    PADDING_BOTTOM = 0.5 * FONT_SIZE
    PADDING_TOP = 0.1 * FONT_SIZE

    NUMBER_RECT_HEIGHT = 1.6 * FONT_SIZE
    MESSAGE_SIDE_MIN_WIDTH = 50
    CORRECT_MARK_RADIUS = 10
    CORRECT_MARK_FONT_SIZE = 1.5 * CORRECT_MARK_RADIUS

    def __init__(self, canvas, text_lines, max_var_lines, sides=1):
        mb = self.__class__
        self._canvas = canvas

        self._canvas.saveState()
        self.max_text_width = self.obtain_max_width(self._canvas, text_lines)
        self._canvas.restoreState()

        # number, empty, side header = 3
        text_height = (max_var_lines + 3) * 1.2 * mb.FONT_SIZE          # 1.2 for interline space
        self._box_width = mb.PADDING_LEFT \
                          + 1 * self.max_text_width \
                          + (sides - 1) * (mb.PADDING_SIDES + self.max_text_width) \
                          + mb.PADDING_RIGHT
        self._box_height = text_height + mb.PADDING_BOTTOM + mb.PADDING_TOP

    def get_size(self):
        return self._box_width, self._box_height

    def place_comment(self, comment):
        """принимает текст коментария и возвращает набор строк, не превосходящий по ширине self._box_width"""
        self._canvas.saveState()
        self._canvas.setFont(MessageBox.FONT_NAME, MessageBox.FONT_SIZE)
        words = re.split(r'\b(?=\w)', comment)
        lines, buf = [], ''
        for w in words:
            if not w:
                continue
            if self._canvas.stringWidth(buf + w) > self._box_width:
                lines.append(buf)
                buf = w
            else:
                buf += w
        if buf:
            lines.append(buf)
        self._canvas.restoreState()
        return lines

    def comment_height(self, comment):
        comment_lines = len(self.place_comment(comment))
        if comment_lines > 0:
            comment_lines += 1  # + 1 due to skip one line before comment
        return comment_lines * 1.2 * MessageBox.FONT_SIZE

    @staticmethod
    def draw_message(canvas, number, variables, position, size, layer_color,
                     correct: bool = None, comment_lines: list = None):
        mb = MessageBox
        canvas.saveState()
        x_start, y_start = position
        box_width, box_height = size
        set_colors(canvas, layer_color)
        canvas.rect(x_start, y_start, box_width, box_height, stroke=0, fill=1)

        y_top = y_start + box_height
        var_text = canvas.beginText(x_start + mb.PADDING_LEFT, y_top - mb.FONT_SIZE - mb.PADDING_TOP)
        var_text.setFont(MessageBox.FONT_NAME, MessageBox.FONT_SIZE)
        var_text.setFillColor(colors.white)
        var_text.textLine(number)
        var_text.textLine()
        for v in variables:
            var_text.textLine(v.value)
        if comment_lines:
            var_text.textLine()
            for l in comment_lines:
                var_text.textLine(l)
        canvas.drawText(var_text)
        canvas.restoreState()

    def draw_message_v2(self, canvas, number, infoplan, position, size, layer_color,
                        correct: bool = None, comment_lines: list = None):
        """второй вариант функции с заливкой только под номером и рамкой"""
        # infoplan: [(side, vars_list)]
        mb = MessageBox
        canvas.saveState()
        x_start, y_start = position
        box_width, box_height = size
        set_colors(canvas, layer_color)
        canvas.rect(x_start, y_start, box_width, box_height, stroke=1, fill=0)

        canvas.setFont(mb.FONT_NAME, mb.FONT_SIZE)
        nr_w = canvas.stringWidth(number) + mb.PADDING_LEFT + mb.PADDING_RIGHT
        nr_h = mb.NUMBER_RECT_HEIGHT
        x_text = x_start + mb.PADDING_LEFT
        y_top = y_start + box_height
        canvas.rect(x_start, y_top - nr_h, nr_w, nr_h, stroke=0, fill=1)
        y_number = y_top - mb.FONT_SIZE - mb.PADDING_TOP
        canvas.setFillColor(colors.white)
        canvas.drawString(x_text, y_number, number)

        side_labels = {
            1: 'Сторона A',
            2: 'Сторона B',
            3: 'Сторона C',
            4: 'Сторона D',
        }
        side_count = len(infoplan)

        for side, vars_list in infoplan:
            y_text = y_number - 2 * 1.2 * mb.FONT_SIZE
            side_text = canvas.beginText(x_text + (side - 1) * (mb.PADDING_SIDES + self.max_text_width), y_text)
            side_text.setFont(mb.FONT_NAME, mb.FONT_SIZE)
            side_text.setFillColor(colors.black)

            if side_count != 1:     # не выводить "Сторона A" для односторонних
                side_header = side_labels.get(side, 'Сторона')
                side_text.textLine(side_header)
            for value in vars_list:
                MessageBox.print_var_lines(side_text, value)

            if comment_lines and side == 1:
                side_text.textLine()
                side_text.setFillColor(colors.black)
                for cl in comment_lines:
                    side_text.textLine(cl)
            canvas.drawText(side_text)
        if correct is not None:
            mb.draw_check_mark(canvas, (x_start + box_width, y_start + box_height), correct)

        canvas.restoreState()

    # CAUTION: DRY violation with print_var_lines
    @classmethod
    def obtain_max_width(cls, canvas, lines):
        def obtain_width(line):
            res = line
            res = replace_tabs(res)
            res = parse_picts(res)  # res: [(str, bool), ]

            text_font = layout.Definitions.DEFAULT_FONT_NAME
            pict_font = layout.Definitions.PICT_FONT_NAME
            w = 0
            for text, is_pict in res:
                font_name = pict_font if is_pict else text_font
                font_size = MessageBox.PICT_FONT_SIZE if is_pict else MessageBox.FONT_SIZE
                canvas.setFont(font_name, font_size)
                w += canvas.stringWidth(text)
            return w

        if not lines:
            return cls.MESSAGE_SIDE_MIN_WIDTH

        canvas.setFont(cls.FONT_NAME, cls.FONT_SIZE)
        lines += ['Сторона А']  # для простоты используем этот заголовок для всех сторон, длина почти одна у всех
        max_text_width = max(map(obtain_width, lines))
        return max_text_width

    @staticmethod
    def print_var_lines(text_obj, lines):
        for line in lines.split('\n'):
            res = line
            res = replace_tabs(res)
            res = parse_picts(res)  # res: [(str, bool), ]

            text_font = layout.Definitions.DEFAULT_FONT_NAME
            pict_font = layout.Definitions.PICT_FONT_NAME
            for text, is_pict in res:
                font_name = pict_font if is_pict else text_font
                font_size = MessageBox.PICT_FONT_SIZE if is_pict else MessageBox.FONT_SIZE
                text_obj.setFont(font_name, font_size)
                text_obj.textOut(text)
            text_obj.textLine()

    @staticmethod
    def draw_check_mark(canvas, position, correct: bool):
        x, y = position
        canvas.saveState()
        color = colors.green if correct else colors.red
        canvas.setFillColor(color)
        canvas.setStrokeColor(colors.white)
        canvas.circle(x, y, MessageBox.CORRECT_MARK_RADIUS, stroke=1, fill=1)

        canvas.setFillColor(colors.white)
        mark = 'v' if correct else 'x'
        canvas.setFontSize(MessageBox.CORRECT_MARK_FONT_SIZE)
        canvas.drawCentredString(x, y - 0.3 * MessageBox.CORRECT_MARK_FONT_SIZE, mark)
        canvas.restoreState()


class MessagesArea:
    PADDING_ROW = 2 * units.cm
    PADDING_COL = 1 * units.cm
    PADDING_TOP = 2 * units.cm

    def __init__(self, width, height, mess_box: MessageBox):
        self._area_width = width
        self._area_height = height
        self._mess_box = mess_box
        self._box_width, self._box_height = self._mess_box.get_size()
        self._row_start = self._area_height - MessagesArea.PADDING_TOP - self._box_height

        if self._area_height < self._box_height:
            raise ValueError(f'height < box_height, area_height={self._area_height}, box_height={self._box_height}')
        if self._area_width < self._box_width:
            raise ValueError(f'width < box_width, area_width={self._area_width}, box_width={self._box_width}')
        self._column_count = int((self._area_width - self._box_width) // (self._box_width + MessagesArea.PADDING_ROW)) + 1

    def column_count(self):
        return self._column_count

    def place_row(self, max_comment_height):
        if self._row_start >= self._box_height + max_comment_height:    # all comments will be ok
            positions = [(c * (self._box_width + MessagesArea.PADDING_ROW), self._row_start)
                         for c in range(self._column_count)]
            self._row_start -= self._box_height + max_comment_height + MessagesArea.PADDING_COL
            return positions
        else:
            return []

    def place_row_or_raise(self):
        if self._row_start >= self._box_height:
            positions = [(c * (self._box_width + MessagesArea.PADDING_ROW), self._row_start)
                         for c in range(self._column_count)]
            self._row_start -= self._box_height + MessagesArea.PADDING_COL
            return positions
        else:
            raise layout.NotEnoughSpaceException

    def reset(self):
        self._row_start = self._area_height - MessagesArea.PADDING_TOP - self._box_height

    def error_message(self, canvas, messages):
        canvas.setFont(MessageBox.FONT_NAME, MessageBox.FONT_SIZE)
        canvas.drawString(self._box_width + MessagesArea.PADDING_ROW, self._row_start,
                          'Недостаточно места для отображения переменных. '
                          + f'Блоки сообщений {", ".join(number for number, _ in messages)} были пропущены.')


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
