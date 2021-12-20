import os
import re

from abc import abstractmethod, ABC
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import Color, CMYKColor
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen.canvas import Canvas

ADD_FONTS_LOADED = False


class Definitions:
    PAGE_SIZE = landscape(A3)
    WIDTH, HEIGHT = PAGE_SIZE

    BOUND_LEFT = 40 * mm
    # BOUND_LEFT = 0          # no bounds
    BOUND_RIGHT = WIDTH - 15 * mm
    # BOUND_RIGHT = WIDTH     # no bounds

    TOP_LINE = HEIGHT - 20 * mm
    # TOP_LINE = HEIGHT       # don't draw header
    BOTTOM_LINE = 23 * mm
    # BOTTOM_LINE = 0         # don't draw footer
    LINES_PADDING = 1 * mm
    AREA_HEIGHT = 227 * mm
    # AREA_HEIGHT = HEIGHT    # use full height as no header and footer
    SECOND_LINE = BOTTOM_LINE + LINES_PADDING + AREA_HEIGHT + LINES_PADDING

    zoloto_viewer__documents__pdf_generation = os.path.dirname(__file__)
    zoloto_viewer = os.path.dirname(os.path.dirname(zoloto_viewer__documents__pdf_generation))

    DEFAULT_FONT_NAME = 'FreePTSans'
    DEFAULT_FONT_FILE = os.path.join(zoloto_viewer__documents__pdf_generation, 'fonts/pt_sans.ttf')

    PICT_FONT_NAME = 'Picts_v1'
    PICT_FONT_FILE = os.path.join(zoloto_viewer, 'static/picts_v2.ttf')

    MARK_FONT_SIZE = 16
    MARK_FONT_NAME = 'Elements_font'
    MARK_FONT_FILE = os.path.join(zoloto_viewer__documents__pdf_generation, 'fonts/z_web_elements.ttf')

    HEADER_FONT_SIZE = 30
    HEADER_FONT_NAME = 'Aeroport'
    HEADER_FONT_FILE = os.path.join(zoloto_viewer__documents__pdf_generation, 'fonts/Aeroport-regular.ttf')

    SUPER_HEADER_FONT_SIZE = 12
    SUPER_HEADER_FONT_NAME = HEADER_FONT_NAME
    SUPER_HEADER_FONT_FILE = HEADER_FONT_FILE
    SUPER_HEADER_PADDING_TOP_LINE = 5

    FOOTER_FONT_SIZE = 21
    FOOTER_FONT_NAME = 'Zoloto'
    FOOTER_FONT_FILE = os.path.join(zoloto_viewer__documents__pdf_generation, 'fonts/Zoloto-Display-010520.ttf')

    PADDING_FOOTER = 15.6 * mm
    PADDING_HEADER = TOP_LINE - HEADER_FONT_SIZE
    PADDING_SUPER_HEADER = TOP_LINE + SUPER_HEADER_PADDING_TOP_LINE

    PLAN_LEGEND_PADDING_LEFT = 10
    PLAN_LEGEND_PADDING_TOP = 20

    # MESSAGES_PADDING_LEFT = 20 * mm
    MESSAGES_PADDING_LEFT = BOUND_LEFT
    # MESSAGES_PADDING_RIGHT = MESSAGES_PADDING_LEFT
    MESSAGES_PADDING_RIGHT = BOUND_RIGHT
    MESSAGES_PADDING_ROW = 2 * cm
    MESSAGES_PADDING_COL = 1 * cm
    MESSAGES_PADDING_TOP = 2 * cm

    @classmethod
    def bottom_line_upper_bound(cls):
        return cls.BOTTOM_LINE + cls.LINES_PADDING

    # SEPARATOR_WIDTH = 1     # N.B. if other than 1, need to draw rect


def plan_area_position():
    return Definitions.BOUND_LEFT, Definitions.bottom_line_upper_bound()


def plan_area_position_left_top():
    x, y = plan_area_position()
    return x, y + Definitions.AREA_HEIGHT


def work_area_size():
    d = Definitions
    area_width = d.BOUND_RIGHT - d.BOUND_LEFT
    area_height = d.AREA_HEIGHT
    return area_width, area_height


def mess_area_position():
    return Definitions.MESSAGES_PADDING_LEFT, Definitions.bottom_line_upper_bound()


def mess_area_size():
    d = Definitions
    area_width = d.MESSAGES_PADDING_RIGHT - d.MESSAGES_PADDING_LEFT
    area_height = d.AREA_HEIGHT
    return area_width, area_height


def load_fonts():
    global ADD_FONTS_LOADED
    if ADD_FONTS_LOADED:
        return

    d = Definitions
    pdfmetrics.registerFont(ttfonts.TTFont(d.DEFAULT_FONT_NAME, d.DEFAULT_FONT_FILE))
    pdfmetrics.registerFont(ttfonts.TTFont(d.HEADER_FONT_NAME, d.HEADER_FONT_FILE))
    pdfmetrics.registerFont(ttfonts.TTFont(d.FOOTER_FONT_NAME, d.FOOTER_FONT_FILE))
    pdfmetrics.registerFont(ttfonts.TTFont(d.PICT_FONT_NAME, d.PICT_FONT_FILE))
    pdfmetrics.registerFont(ttfonts.TTFont(d.MARK_FONT_NAME, d.MARK_FONT_FILE))
    ADD_FONTS_LOADED = True


load_fonts()


def draw_header(canvas: Canvas, title, super_title):
    d = Definitions
    canvas.line(d.BOUND_LEFT, d.TOP_LINE, d.BOUND_RIGHT, d.TOP_LINE)

    canvas.setFont(d.HEADER_FONT_NAME, d.HEADER_FONT_SIZE)
    if isinstance(title, str):
        canvas.drawString(d.BOUND_LEFT, d.PADDING_HEADER, title)
    elif isinstance(title, (tuple, list)):
        if len(title) == 1:
            canvas.drawString(d.BOUND_LEFT, d.PADDING_HEADER, title[0])
        elif len(title) == 2:
            canvas.drawString(d.BOUND_LEFT, d.PADDING_HEADER, title[0])
            canvas.drawRightString(d.BOUND_RIGHT, d.PADDING_HEADER, title[1])
    else:
        raise TypeError(f'title of type {type(title)} not supported')

    canvas.setFont(d.SUPER_HEADER_FONT_NAME, d.SUPER_HEADER_FONT_SIZE)
    canvas.drawString(d.BOUND_LEFT, d.PADDING_SUPER_HEADER, super_title[0])
    canvas.drawRightString(d.BOUND_RIGHT, d.PADDING_SUPER_HEADER, super_title[1])

    canvas.line(d.BOUND_LEFT, d.SECOND_LINE, d.BOUND_RIGHT, d.SECOND_LINE)


def draw_footer(canvas):
    d = Definitions
    canvas.line(d.BOUND_LEFT, d.BOTTOM_LINE, d.BOUND_RIGHT, d.BOTTOM_LINE)

    canvas.setFont(d.FOOTER_FONT_NAME, d.FOOTER_FONT_SIZE)
    canvas.drawString(d.BOUND_LEFT, d.PADDING_FOOTER, 'z')
    canvas.drawRightString(d.BOUND_RIGHT, d.PADDING_FOOTER, str(canvas.getPageNumber()))


class AbstractPageWriter(ABC):
    def __init__(self, canvas):
        self._canvas = canvas

    @property
    def canvas(self):
        return self._canvas

    @abstractmethod
    def draw_content(self):
        pass

    @abstractmethod
    def draw_footer(self):
        pass

    @abstractmethod
    def draw_header(self):
        pass

    def write(self):
        self.draw_header()
        self.draw_footer()
        self.draw_content()


class BasePageWriter(AbstractPageWriter, ABC):
    def __init__(self, canvas, title, super_title):
        super().__init__(canvas)
        self._title = title
        self._super_title = super_title

    def draw_header(self):
        draw_header(self.canvas, self._title, self._super_title)

    def draw_footer(self):
        draw_footer(self.canvas)


class BasePageWriterDeducingTitle(BasePageWriter, ABC):
    def __init__(self, canvas):
        title = self.make_page_title()
        super_title = self.make_page_super_title()
        super().__init__(canvas, title, super_title)

    @abstractmethod
    def make_page_title(self):
        pass

    @abstractmethod
    def make_page_super_title(self):
        pass


class NotEnoughSpaceException(Exception):
    pass


class TooLargeMessageException(Exception):
    pass


class NoMarkersInActiveGroupException(Exception):
    pass


# todo move
def color_adapter(html_color):
    """
    Transform to inner package format
    :param html_color: string like 'rgb(36,182,255)'
    :return: {model, values} where model = 'CMYK' | 'RGB' and values: 3 or 4 int tuple
    """
    parse3 = re.match(r'^(?P<model>\w+)\((?P<values>\d+%?, ?\d+%?, ?\d+%?(?:, ?\d+%?)?)\)$', html_color)
    model, values_string = parse3.groups()
    return {
        'model': model.upper(),
        'values': [int(v.rstrip('%')) for v in values_string.split(',')]
    }


def set_colors(canvas, color, alpha=1):
    model = color.get('model', None)
    values = color.get('values', None)
    if model == 'CMYK' and len(values) == 4:
        color = CMYKColor(*[v / 100. for v in values])
    elif model == 'RGB' and len(values) == 3:
        color = Color(*[v / 255. for v in values])
    else:
        raise ValueError(f'Unknown color model: model={model}, values={values}')
    canvas.setFillColor(color, alpha=alpha)
    canvas.setStrokeColor(color, alpha=alpha)
