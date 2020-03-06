import django
from django.db.models import Count
from django.db.models.functions import Length
from django.utils import timezone
from reportlab.lib import pagesizes, units, colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rc

django.setup()
from zoloto_viewer.infoplan.models import MarkerVariable
from zoloto_viewer.viewer.models import Page

A4_LANDSCAPE = pagesizes.landscape(pagesizes.A4)
INNER_WIDTH = 28 * units.cm
BOTTOM_MARGIN = 2 * units.cm
TOP_MARGIN = 2 * units.cm
FONT_NAME = 'FreePTSans'
FONT_SIZE = 7
BOX_PADDING = 2 * units.cm, 1 * units.cm
# todo собрать описание внешнего вида блока в одном классе и общей вёрстки в другом


def calc_variable_metrics(markers):
    longest_variable = MarkerVariable.objects.filter(marker__in=markers) \
        .annotate(val_len=Length('value')).order_by('-val_len').first()
    max_var_marker = markers.annotate(var_count=Count('markervariable')).order_by('-var_count').first()
    return longest_variable.value, max_var_marker.var_count


def determine_mess_box_size(canvas, longest_value, max_var_count):
    text_width = canvas.stringWidth(longest_value[:50])
    box_width = text_width + FONT_SIZE
    box_height = (max_var_count + 2) * 1.5 * FONT_SIZE   # 1.5 for interline space
    return box_width, box_height


def generate_box_offset(area_width, area_height, box_width, box_height):
    """returns x, y to place box while possible"""
    min_padding_h, min_padding_v = BOX_PADDING

    if area_height < box_height:
        raise ValueError(f'area_height < box_height, area_height={area_height}, box_height={box_height}')
    rows = int((area_height - box_height) // (box_height + min_padding_v)) + 1
    # padding_h = (area_height - rows * box_height) / (rows - 1 if rows > 1 else 1)

    if area_width < box_width:
        raise ValueError(f'area_width < box_width, area_width={area_width}, box_width={box_width}')
    cols = int((area_width - box_width) // (box_width + min_padding_h)) + 1
    # padding_v = (area_width - cols * box_width) / (cols - 1 if cols > 1 else 1)

    for r in range(rows):
        y = area_height - box_height - r * (box_height + min_padding_v)
        for c in range(cols):
            x = c * (box_width + min_padding_h)
            yield x, y


def set_color(canvas, color):
    model = color.get('model', None)
    values = color.get('values', None)
    if model == 'CMYK' and len(values) == 4:
        canvas.setFillColorCMYK(*[v / 100. for v in values])
    elif model == 'RGB' and len(values) == 3:
        canvas.setFillColorRGB(*[v / 255. for v in values])


def draw_message(canvas, marker, offset, size):
    x_start, y_start = offset
    canvas.rect(x_start, y_start, size[0], size[1], stroke=0, fill=1)

    canvas.saveState()
    canvas.setFillColor(colors.white)
    variables = list(map(lambda v: v.value, MarkerVariable.objects.vars_of_marker(marker)))
    lines = [marker.number, ''] + variables
    y_pos = reversed([y_start + 1.5 * FONT_SIZE * l for l in range(len(lines))])
    for l, y in zip(lines, y_pos):
        canvas.drawString(x_start + 0.5 * FONT_SIZE, y + 0.5 * FONT_SIZE, l)

    canvas.restoreState()


def calc_params(canvas, markers_queryset):
    canvas.setFont(FONT_NAME, FONT_SIZE)
    longest_value, max_var_count = calc_variable_metrics(markers_queryset)
    box_size = determine_mess_box_size(canvas, longest_value, max_var_count)
    area_size = (A4_LANDSCAPE[0] - INNER_WIDTH) / 2, BOTTOM_MARGIN
    return area_size, box_size


def build_page(canvas, markers_iter, layer_color, area_size, box_size):
    area_height = A4_LANDSCAPE[1] - BOTTOM_MARGIN - TOP_MARGIN
    area_left, area_bottom = area_size
    box_width, box_height = box_size

    canvas.setFont(FONT_NAME, FONT_SIZE)
    set_color(canvas, layer_color)

    was_messages = False
    positions = generate_box_offset(INNER_WIDTH, area_height, box_width, box_height)
    for offset_x, offset_y in positions:
        box_offset = area_left + offset_x, area_bottom + offset_y
        try:
            draw_message(canvas, next(markers_iter), box_offset, box_size)
        except StopIteration:
            break
        was_messages = True

    if was_messages:
        canvas.showPage()
    return was_messages


if __name__ == '__main__':
    pdfmetrics.registerFont(TTFont(FONT_NAME, 'pt_sans.ttf'))

    floor_6 = Page.objects.get(code='BEXF4ECSIV')
    L = floor_6.project.layer_set.first()
    floor_layer_markers = floor_6.marker_set.filter(layer=L)

    C = rc.Canvas(timezone.now().strftime('%d%m_%H%M.pdf'), pagesize=A4_LANDSCAPE)
    area_size, box_size = calc_params(C, floor_layer_markers)

    sorted_markers = iter(sorted(floor_layer_markers, key=lambda m: m.ord_number()))
    maybe_next = True
    while maybe_next:
        maybe_next = build_page(C, sorted_markers, L.raw_color, area_size, box_size)
    C.save()
