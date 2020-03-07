import django

from django.utils import timezone
from django.db.models.fields.files import ImageFieldFile
from reportlab.pdfgen import canvas as rc
from reportlab.lib import pagesizes, units, colors

django.setup()
from zoloto_viewer.viewer.models import Layer, Page

A4_LANDSCAPE = pagesizes.landscape(pagesizes.A4)
INNER_WIDTH = 28 * units.cm
# FONT_SIZE_LEGEND = 7    # todo move to proper class
# FONT_SIZE_CAPTION = 6


class PlanBox:
    def __init__(self, image_field: ImageFieldFile, indd_bounds, layer_color):
        self._img = image_field.path
        self._img_size = image_field.width, image_field.height
        self._indd_bounds = indd_bounds
        self._color = layer_color

        self._box_x = None
        self._box_y = None
        self._box_width = None
        self._box_height = None

        self._markers = []
        self.CAPTION_DELTA = 8
        self.FONT_NAME = 'Helvetica'
        self.FONT_SIZE = 6

    def add_marker(self, m):
        self._markers.append((m.polygon_points(), m.center_position(), m.number))

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

    def _draw_marker(self, canvas, points):
        path = canvas.beginPath()
        path.moveTo(*self._calc_pos(points[0]))
        for p in points:
            path.lineTo(*self._calc_pos(p))
        path.close()
        canvas.drawPath(path, stroke=0, fill=1)

    def _draw_caption(self, canvas, marker_center, number):
        x, y = self._calc_pos(marker_center)
        x, y = x + self.CAPTION_DELTA, y - self.CAPTION_DELTA
        width = canvas.stringWidth(number)
        height = self.FONT_SIZE

        canvas.rect(x, y - 1, width, height, stroke=0, fill=1)
        canvas.saveState()
        canvas.setFillColor(colors.white)
        canvas.drawString(x, y, number)
        canvas.restoreState()

    def _set_color(self, canvas):
        model = self._color.get('model', None)
        values = self._color.get('values', None)
        if model == 'CMYK' and len(values) == 4:
            canvas.setFillColorCMYK(*[v / 100. for v in values])
        elif model == 'RGB' and len(values) == 3:
            canvas.setFillColorRGB(*[v / 255. for v in values])

    def draw(self, canvas: rc.Canvas, box_width):
        offset = (A4_LANDSCAPE[0] - box_width) / 2
        self._box_x = offset
        self._box_y = 0
        self._box_width = box_width
        self._box_height = self._img_size[1] / self._img_size[0] * self._box_width      # due to preserveAspectRatio

        canvas.drawImage(self._img, x=self._box_x, y=self._box_y, width=self._box_width,
                         preserveAspectRatio=True, anchor='s')
        self._set_color(canvas)
        canvas.setFont(self.FONT_NAME, self.FONT_SIZE)
        for points, center, number in self._markers:
            self._draw_marker(canvas, points)
            self._draw_caption(canvas, center, number)
        canvas.save()


def build_page(floor: Page, layer: Layer):
    box = PlanBox(floor.plan, floor.geometric_bounds, layer.raw_color)

    for m in floor.marker_set.all().filter(layer=layer):
        box.add_marker(m)

    filename = timezone.now().strftime('%d%m_%H%M.pdf')
    C = rc.Canvas(filename, pagesize=A4_LANDSCAPE)
    box.draw(C, INNER_WIDTH)


if __name__ == '__main__':
    floor_6 = Page.objects.get(code='BEXF4ECSIV')
    L = floor_6.project.layer_set.all()[0]
    build_page(floor_6, L)
