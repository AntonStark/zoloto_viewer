from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen.canvas import Canvas

ADD_FONTS_LOADED = False


class Definitions:
    PAGE_SIZE = landscape(A3)
    WIDTH, HEIGHT = PAGE_SIZE

    BOUND_LEFT = 40 * mm
    BOUND_RIGHT = WIDTH - 15 * mm

    TOP_LINE = HEIGHT - 20 * mm
    BOTTOM_LINE = 23 * mm
    AREA_HEIGHT = 227 * mm
    SECOND_LINE = BOTTOM_LINE + AREA_HEIGHT

    HEADER_FONT_SIZE = 30
    HEADER_FONT_NAME = 'Aeroport'
    HEADER_FONT_FILE = 'Aeroport-regular.ttf'

    FOOTER_FONT_SIZE = 21
    FOOTER_FONT_NAME = 'Zoloto'
    FOOTER_FONT_FILE = 'Zoloto-Display-270819.ttf'

    PADDING_FOOTER = 15.6 * mm
    PADDING_HEADER = TOP_LINE - HEADER_FONT_SIZE

    # SEPARATOR_WIDTH = 1     # N.B. need to draw rect to use other than 1


def work_area_position():
    return Definitions.BOUND_LEFT, Definitions.BOTTOM_LINE


def work_area_size():
    d = Definitions
    area_width = d.BOUND_RIGHT - d.BOUND_LEFT
    area_height = d.AREA_HEIGHT
    return area_width, area_height


def load_fonts():
    global ADD_FONTS_LOADED
    if ADD_FONTS_LOADED:
        return

    d = Definitions
    pdfmetrics.registerFont(ttfonts.TTFont(d.HEADER_FONT_NAME, d.HEADER_FONT_FILE))
    pdfmetrics.registerFont(ttfonts.TTFont(d.FOOTER_FONT_NAME, d.FOOTER_FONT_FILE))
    ADD_FONTS_LOADED = True


load_fonts()


def draw_header(canvas: Canvas, title: str):
    d = Definitions
    canvas.line(d.BOUND_LEFT, d.TOP_LINE, d.BOUND_RIGHT, d.TOP_LINE)

    canvas.setFont(d.HEADER_FONT_NAME, d.HEADER_FONT_SIZE)
    canvas.drawString(d.BOUND_LEFT, d.PADDING_HEADER, title)

    canvas.line(d.BOUND_LEFT, d.SECOND_LINE, d.BOUND_RIGHT, d.SECOND_LINE)


def draw_footer(canvas, page_num):
    d = Definitions
    canvas.line(d.BOUND_LEFT, d.BOTTOM_LINE, d.BOUND_RIGHT, d.BOTTOM_LINE)

    canvas.setFont(d.FOOTER_FONT_NAME, d.FOOTER_FONT_SIZE)
    canvas.drawString(d.BOUND_LEFT, d.PADDING_FOOTER, 'z')
    canvas.drawRightString(d.BOUND_RIGHT, d.PADDING_FOOTER, str(page_num))
