import django
import itertools
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

    @staticmethod
    def deduce_mess_box_size(canvas, longest_value, max_var_count):
        mb = MessageBox
        canvas.saveState()
        canvas.setFont(MessageBox.FONT_NAME, MessageBox.FONT_SIZE)
        text_width = canvas.stringWidth(longest_value[:58])
        canvas.restoreState()

        text_height = (max_var_count + 2) * 1.2 * mb.FONT_SIZE       # 1.2 for interline space
        box_width = text_width + mb.PADDING_LEFT + mb.PADDING_RIGHT
        box_height = text_height + mb.PADDING_BOTTOM + mb.PADDING_TOP
        return box_width, box_height

    @staticmethod
    def draw_message(canvas, number, variables, position, size, layer_color):
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
        canvas.drawText(var_text)
        canvas.restoreState()

    @staticmethod
    def draw_message_v2(canvas, number, variables, offset, size, layer_color):
        """второй вариант функции с заливкой только под номером и рамкой"""
        mb = MessageBox
        canvas.saveState()
        x_start, y_start = offset
        box_width, box_height = size
        set_colors(canvas, layer_color)
        canvas.rect(x_start, y_start, box_width, box_height, stroke=1, fill=0)

        canvas.setFont(MessageBox.FONT_NAME, MessageBox.FONT_SIZE)
        nr_w = canvas.stringWidth(number) + mb.PADDING_LEFT + mb.PADDING_RIGHT
        nr_h = mb.NUMBER_RECT_HEIGHT
        y_top = y_start + box_height
        canvas.rect(x_start, y_top - nr_h, nr_w, nr_h, stroke=0, fill=1)

        var_text = canvas.beginText(x_start + mb.PADDING_LEFT, y_top - mb.FONT_SIZE - mb.PADDING_TOP)
        var_text.setFont(MessageBox.FONT_NAME, MessageBox.FONT_SIZE)
        var_text.setFillColor(colors.white)
        var_text.textLine(number)
        var_text.textLine()
        var_text.setFillColor(colors.black)
        for v in variables:
            var_text.textLine(v.value)
        canvas.drawText(var_text)
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

    def __init__(self, width, height, box_size):
        self._area_width = width
        self._area_height = height
        self._box_width, self._box_height = box_size

        if self._area_height < self._box_height:
            raise ValueError(f'height < box_height, area_height={self._area_height}, box_height={self._box_height}')
        if self._area_width < self._box_width:
            raise ValueError(f'width < box_width, area_width={self._area_width}, box_width={self._box_width}')

    def position_generator(self):
        """returns x, y to place box while possible"""
        ma = MessagesArea
        area_height = self._area_height - MessagesArea.PADDING_TOP
        rows = int((area_height - self._box_height) // (self._box_height + ma.PADDING_COL)) + 1
        cols = int((self._area_width - self._box_width) // (self._box_width + ma.PADDING_ROW)) + 1

        # todo предусмотреть вывод комментариев
        for r in range(rows):
            y = area_height - self._box_height - r * (self._box_height + ma.PADDING_COL)
            for c in range(cols):
                x = c * (self._box_width + ma.PADDING_ROW)
                yield x, y


def build_page(canvas, markers_iter, box_size, layer_color, title, num_iter):
    layout.draw_header(canvas, title)
    layout.draw_footer(canvas, next(num_iter))

    area_width, area_height = layout.work_area_size()
    area_left, area_bottom = layout.work_area_position()

    area = MessagesArea(area_width, area_height, box_size)
    was_messages = False
    for offset_x, offset_y in area.position_generator():
        box_offset = area_left + offset_x, area_bottom + offset_y
        try:
            marker = next(markers_iter)
        except StopIteration:
            break
        else:
            variables = MarkerVariable.objects.vars_of_marker(marker)
            MessageBox.draw_message_v2(canvas, marker.number, variables, box_offset, box_size, layer_color)
            was_messages = True

    if was_messages:
        canvas.showPage()
    return was_messages


if __name__ == '__main__':
    pdfmetrics.registerFont(TTFont(MessageBox.FONT_NAME, 'fonts/pt_sans.ttf'))
    filename = timezone.now().strftime('%d%m_%H%M.pdf')
    C = rc.Canvas(filename, pagesize=layout.Definitions.PAGE_SIZE)

    P = Page.objects.get(code='BEXF4ECSIV')
    L = P.project.layer_set.last()
    floor_layer_markers = P.marker_set.filter(layer=L)

    longest_value, max_var_count = calc_variable_metrics(floor_layer_markers)
    box_size = MessageBox.deduce_mess_box_size(C, longest_value, max_var_count)

    sorted_markers = iter(sorted(floor_layer_markers, key=lambda m: m.ord_number()))
    title = [P.floor_caption, L.title]
    page_nums = itertools.count(1)

    maybe_next = True
    while maybe_next:
        maybe_next = build_page(C, sorted_markers, box_size, L.raw_color, title, page_nums)
    C.save()
