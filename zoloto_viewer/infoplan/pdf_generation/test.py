import django
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rc

django.setup()
from zoloto_viewer.infoplan.pdf_generation import common_layout, mess_pages, models_related, plan_page
from zoloto_viewer.viewer.models import Page


def test_plan():
    C = rc.Canvas(filename, pagesize=common_layout.Definitions.PAGE_SIZE)
    plan_page.plan_page(C, P, floor_layer_markers, title, L.raw_color, L.title, L.desc)
    C.save()


def test_mess():
    C = rc.Canvas(filename, pagesize=common_layout.Definitions.PAGE_SIZE)

    longest_value, max_var_count = models_related.calc_variable_metrics(floor_layer_markers)
    message_box = mess_pages.MessageBox(C, longest_value, max_var_count)

    mess_pages.message_pages(C, sorted_markers, message_box, L.raw_color, title)
    C.save()


if __name__ == '__main__':
    pdfmetrics.registerFont(TTFont('FreePTSans', 'fonts/pt_sans.ttf'))
    filename = timezone.now().strftime('%d%m_%H%M.pdf')
    C = rc.Canvas(filename, pagesize=common_layout.Definitions.PAGE_SIZE)

    P = Page.objects.get(code='BEXF4ECSIV')
    L = P.project.layer_set.last()
    floor_layer_markers = P.marker_set.filter(layer=L)

    sorted_markers = sorted(floor_layer_markers, key=lambda m: m.ord_number())
    title = [P.floor_caption, L.title]

    test_plan()
    # test_mess()
