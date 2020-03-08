import django
import re
from django.db.models import Count
from django.db.models.functions import Length
from django.utils import timezone
from reportlab.lib import units, colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rc

import zoloto_viewer.infoplan.pdf_generation.common_layout as layout
django.setup()
from zoloto_viewer.infoplan.models import MarkerVariable
from zoloto_viewer.viewer.models import Page


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
        var_text.setFillColor(colors.black)
        for v in variables:
            var_text.textLine(v.value)

        if comment_lines:
            var_text.textLine()
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


def calc_variable_metrics(markers):
    longest_variable = MarkerVariable.objects.filter(marker__in=markers) \
        .annotate(val_len=Length('value')).order_by('-val_len').first()
    max_var_marker = markers.annotate(var_count=Count('markervariable')).order_by('-var_count').first()
    return longest_variable.value, max_var_marker.var_count


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

    def place_row(self, markers):
        row_markers = markers[:self._column_count]

        comments = [m.comment for m in row_markers]
        max_comment_height = max(map(self._mess_box.comment_height, comments))
        if self._row_start >= self._box_height + max_comment_height:    # all comments will be ok
            positions = [(c * (self._box_width + MessagesArea.PADDING_ROW), self._row_start)
                         for c in range(self._column_count)]
            self._row_start -= self._box_height + max_comment_height + MessagesArea.PADDING_COL
            return positions
        else:
            return []

    def reset(self):
        self._row_start = self._area_height - MessagesArea.PADDING_TOP - self._box_height


def message_pages(canvas, markers, message_box, layer_color, title):
    def chunk(seq, n):
        for i in range(0, len(seq), n):
            yield seq[i:i + n]

    box_size = message_box.get_size()
    area_width, area_height = layout.work_area_size()
    area_left, area_bottom = layout.work_area_position()
    area = MessagesArea(area_width, area_height, message_box)

    layout.draw_header(canvas, title)
    layout.draw_footer(canvas)
    batch_size = area.column_count()
    for marker_chunk in chunk(markers, batch_size):
        positions = area.place_row(marker_chunk)
        if not positions:
            canvas.showPage()
            layout.draw_header(canvas, title)
            layout.draw_footer(canvas)

            area.reset()
            positions = area.place_row(marker_chunk)

        for marker, (offset_x, offset_y) in zip(marker_chunk, positions):
            box_offset = area_left + offset_x, area_bottom + offset_y
            variables = MarkerVariable.objects.vars_of_marker(marker)
            comment_lines = message_box.place_comment(marker.comment)
            MessageBox.draw_message_v2(canvas, marker.number, variables, box_offset, box_size, layer_color,
                                       correct=marker.correct,
                                       comment_lines=comment_lines)


if __name__ == '__main__':
    pdfmetrics.registerFont(TTFont(MessageBox.FONT_NAME, 'fonts/pt_sans.ttf'))
    filename = timezone.now().strftime('%d%m_%H%M.pdf')
    C = rc.Canvas(filename, pagesize=layout.Definitions.PAGE_SIZE)

    P = Page.objects.get(code='BEXF4ECSIV')
    L = P.project.layer_set.last()
    floor_layer_markers = P.marker_set.filter(layer=L)

    longest_value, max_var_count = calc_variable_metrics(floor_layer_markers)
    message_box = MessageBox(C, longest_value, max_var_count)

    sorted_markers = sorted(floor_layer_markers, key=lambda m: m.ord_number())
    title = [P.floor_caption, L.title]

    message_pages(C, sorted_markers, message_box, L.raw_color, title)
    C.save()
