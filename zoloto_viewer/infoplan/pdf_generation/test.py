import django
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rc

django.setup()
from zoloto_viewer.infoplan.pdf_generation import common_layout, mess_pages, plan_page
from zoloto_viewer.viewer.models import Page


def test_plan(with_review=False):
    C = rc.Canvas(filename, pagesize=common_layout.Definitions.PAGE_SIZE)
    plan_page.plan_page(C, P, floor_layer_markers, title, L.raw_color, L.title, L.desc, with_review=with_review)
    C.save()


def test_mess(with_review=False):
    C = rc.Canvas(filename, pagesize=common_layout.Definitions.PAGE_SIZE)
    mess_pages.message_pages(C, floor_layer_markers, L.raw_color, title, with_review=with_review)
    C.save()


if __name__ == '__main__':
    pdfmetrics.registerFont(TTFont('FreePTSans', 'fonts/pt_sans.ttf'))
    filename = timezone.now().strftime('%d%m_%H%M.pdf')
    C = rc.Canvas(filename, pagesize=common_layout.Definitions.PAGE_SIZE)

    P = Page.objects.get(code='BEXF4ECSIV')
    L = P.project.layer_set.last()
    floor_layer_markers = P.marker_set.filter(layer=L)

    title = [P.floor_caption, L.title]

    test_plan(True)
    # test_mess()
