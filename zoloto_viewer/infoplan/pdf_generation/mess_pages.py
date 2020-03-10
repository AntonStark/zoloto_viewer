import re
from reportlab.lib import units, colors

from zoloto_viewer.infoplan.pdf_generation import common_layout as layout, models_related
from zoloto_viewer.infoplan.models import MarkerVariable


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
    FONT_NAME = 'FreePTSans'
    FONT_SIZE = 7

    PADDING_LEFT = 0.5 * FONT_SIZE
    PADDING_RIGHT = PADDING_LEFT
    PADDING_BOTTOM = 0.5 * FONT_SIZE
    PADDING_TOP = 0.1 * FONT_SIZE

    NUMBER_RECT_HEIGHT = 1.6 * FONT_SIZE
    CORRECT_MARK_RADIUS = 10
    CORRECT_MARK_FONT_SIZE = 1.5 * CORRECT_MARK_RADIUS

    def __init__(self, canvas, longest_value, max_var_count):
        mb = MessageBox
        self._canvas = canvas
        self._canvas.saveState()
        self._canvas.setFont(mb.FONT_NAME, mb.FONT_SIZE)
        text_width = self._canvas.stringWidth(longest_value)
        self._canvas.restoreState()

        text_height = (max_var_count + 2) * 1.2 * mb.FONT_SIZE          # 1.2 for interline space
        self._box_width = text_width + mb.PADDING_LEFT + mb.PADDING_RIGHT
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
            if self._canvas.stringWidth(buf + w) > self._box_width:
                lines.append(buf)
                buf = w
            else:
                buf += w
        lines.append(buf)
        self._canvas.restoreState()
        return lines

    def comment_height(self, comment):
        comment_lines = len(self.place_comment(comment))
        return (comment_lines + 1) * 1.2 * MessageBox.FONT_SIZE         # + 1 due to skip one line before comment

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

    @staticmethod
    def draw_message_v2(canvas, number, variables, position, size, layer_color,
                        correct: bool = None, comment_lines: list = None):
        """второй вариант функции с заливкой только под номером и рамкой"""
        mb = MessageBox
        canvas.saveState()
        x_start, y_start = position
        box_width, box_height = size
        set_colors(canvas, layer_color)
        canvas.rect(x_start, y_start, box_width, box_height, stroke=1, fill=0)

        canvas.setFont(mb.FONT_NAME, mb.FONT_SIZE)
        nr_w = canvas.stringWidth(number) + mb.PADDING_LEFT + mb.PADDING_RIGHT
        nr_h = mb.NUMBER_RECT_HEIGHT
        y_top = y_start + box_height
        canvas.rect(x_start, y_top - nr_h, nr_w, nr_h, stroke=0, fill=1)

        var_text = canvas.beginText(x_start + mb.PADDING_LEFT, y_top - mb.FONT_SIZE - mb.PADDING_TOP)
        var_text.setFont(mb.FONT_NAME, mb.FONT_SIZE)
        var_text.setFillColor(colors.white)
        var_text.textLine(number)
        var_text.textLine()
        for value, wrong in variables:
            if wrong:
                var_text.setFillColor(colors.red)
            else:
                var_text.setFillColor(colors.black)
            var_text.textLine(value)

        if comment_lines:
            var_text.textLine()
            var_text.setFillColor(colors.black)
            for l in comment_lines:
                var_text.textLine(l)
        canvas.drawText(var_text)
        if correct is not None:
            mb.draw_check_mark(canvas, (x_start + box_width, y_start + box_height), correct)

        canvas.restoreState()

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

    def reset(self):
        self._row_start = self._area_height - MessagesArea.PADDING_TOP - self._box_height

    def error_message(self, canvas, markers):
        canvas.setFont(MessageBox.FONT_NAME, MessageBox.FONT_SIZE)
        canvas.drawString(self._box_width + MessagesArea.PADDING_ROW, self._row_start,
                          'Недостаточно места для отображения переменных. '
                          + f'Блоки сообщений {", ".join(m.number for m in markers)} были пропущены.')


def message_pages(canvas, markers_query_set, layer_color, title, with_review=False):
    def chunk(seq, n):
        for i in range(0, len(seq), n):
            yield seq[i:i + n]

    longest_value, max_var_count = models_related.calc_variable_metrics(markers_query_set)
    message_box = MessageBox(canvas, longest_value, max_var_count)
    box_size = message_box.get_size()

    area_width, area_height = layout.work_area_size()
    area_left, area_bottom = layout.work_area_position()
    area = MessagesArea(area_width, area_height, message_box)

    layout.draw_header(canvas, title)
    layout.draw_footer(canvas)
    batch_size = area.column_count()
    markers = sorted(markers_query_set, key=lambda m: m.ord_number())
    for marker_chunk in chunk(markers, batch_size):
        comments = [m.comment for m in marker_chunk]
        max_comment_height = max(map(message_box.comment_height, comments)) if with_review else 0

        positions = area.place_row(max_comment_height)
        if not positions:
            canvas.showPage()
            layout.draw_header(canvas, title)
            layout.draw_footer(canvas)

            area.reset()
            positions = area.place_row(max_comment_height)
        if not positions:
            area.error_message(canvas, marker_chunk)

        for marker, (offset_x, offset_y) in zip(marker_chunk, positions):
            box_offset = area_left + offset_x, area_bottom + offset_y

            number = marker.number
            variables = MarkerVariable.objects.vars_of_marker(marker)
            var_data = list(map(
                lambda v: (v.value, v.wrong if with_review else False),
                variables
            ))
            correctness = marker.correct if with_review else None
            comment_lines = message_box.place_comment(marker.comment) if with_review else []

            MessageBox.draw_message_v2(canvas, number, var_data, box_offset, box_size, layer_color,
                                       correct=correctness,
                                       comment_lines=comment_lines)
