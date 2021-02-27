from django.db.models.fields.files import ImageFieldFile
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rc

from zoloto_viewer.infoplan.pdf_generation import layout
from zoloto_viewer.viewer.models import Page


class PlanBox:
    DECLARED_PLAN_ASPECT = 365 / 227

    CAPTION_FONT_NAME = 'Helvetica'
    CAPTION_FONT_SIZE = 6
    CAPTION_DELTA = 8

    CORRECT_CIRCLE_RADIUS = 10

    def __init__(self, image_field: ImageFieldFile, indd_bounds, layer_color):
        self._img = image_field.path
        self._img_size = image_field.width, image_field.height
        self._indd_bounds = indd_bounds
        self._color = layer_color

        self._box_width, self._box_height = layout.work_area_size()
        self._box_x, self._box_y = layout.work_area_position()

        self._markers = []

    def left_top_corner(self):
        return self._box_x, self._box_y + self._box_height

    def add_marker(self, m):
        # todo rewrite according to marker kinds, then
        # todo remove Marker methods polygon_points and center_position and underlying fields
        self._markers.append((m.polygon_points(), m.center_position(), m.number, m.correct))

    def _scale(self, point):
        gb_top, gb_left, gb_bottom, gb_right = self._indd_bounds
        factor = self._box_height / (gb_bottom - gb_top)
        return (factor * point[0], factor * point[1])

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

    def _draw_review_status(self, canvas, center, correct):
        if correct is not None:
            if correct:
                canvas.setStrokeColor(colors.green)
            else:
                canvas.setStrokeColor(colors.red)
            x, y = self._calc_pos(center)
            canvas.circle(x, y, PlanBox.CORRECT_CIRCLE_RADIUS)

    def _draw_caption(self, canvas, marker_center, number):
        x, y = self._calc_pos(marker_center)
        x, y = x + PlanBox.CAPTION_DELTA, y - PlanBox.CAPTION_DELTA
        canvas.setFont(self.CAPTION_FONT_NAME, self.CAPTION_FONT_SIZE)
        width = canvas.stringWidth(number)
        height = PlanBox.CAPTION_FONT_SIZE

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

    def draw(self, canvas: rc.Canvas, with_review=False):
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

        self._set_color(canvas)
        for points, center, number, correct in self._markers:
            self._draw_marker(canvas, points)
            self._draw_caption(canvas, center, number)
            if with_review:
                self._draw_review_status(canvas, center, correct)

    def draw_marker_example(self, canvas, position):
        if not self._markers:
            return
        orig_points, orig_center = self._markers[0][:2]
        clear_points = list(map(
            lambda point: self._scale((point[0] - orig_center[0], point[1] - orig_center[1])),
            orig_points
        ))
        points = list(map(
            lambda point: (point[0] + position[0], point[1] + position[1]),
            clear_points
        ))

        path = canvas.beginPath()
        path.moveTo(*points[0])
        for p in points:
            path.lineTo(*p)
        path.close()
        self._set_color(canvas)
        canvas.drawPath(path, stroke=0, fill=1)


class PlanLegend:
    FONT_NAME = 'FreePTSans'
    FONT_SIZE = 7

    LEGEND_PADDING_TOP = 15
    LEGEND_PADDING_LEFT = 20
    DESC_PADDING_LEFT = 2 * LEGEND_PADDING_LEFT

    @staticmethod
    def draw_legend(canvas, box, layer_title, layer_desc):
        pl = PlanLegend
        x, y = box.left_top_corner()
        box.draw_marker_example(canvas, (x + pl.LEGEND_PADDING_LEFT, y - pl.LEGEND_PADDING_TOP))

        canvas.setFont(pl.FONT_NAME, pl.FONT_SIZE)
        canvas.setFillColor(colors.black)
        canvas.drawString(x + pl.DESC_PADDING_LEFT, y - pl.LEGEND_PADDING_TOP, layer_title)
        canvas.drawString(x + pl.DESC_PADDING_LEFT, y - pl.LEGEND_PADDING_TOP - 1.5 * pl.FONT_SIZE, layer_desc)


def plan_page(canvas, floor: Page, markers, title,
              layer_color, layer_title, layer_desc, with_review=False):
    box = PlanBox(floor.plan, floor.geometric_bounds, layer_color)
    for m in markers:
        box.add_marker(m)

    layout.draw_header(canvas, title)
    layout.draw_footer(canvas)
    box.draw(canvas, with_review=with_review)

    PlanLegend.draw_legend(canvas, box, layer_title, layer_desc)
