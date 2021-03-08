import django
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rc

django.setup()
from zoloto_viewer.viewer.models import Page

from . import layout, message, plan


def test_plan(with_review=False):
    C = rc.Canvas(filename, pagesize=layout.Definitions.PAGE_SIZE)
    plan.plan_page(C, P, floor_layer_markers, title, L.raw_color, L.title, L.desc, with_review=with_review)
    C.save()


def test_mess(with_review=False):
    C = rc.Canvas(filename, pagesize=layout.Definitions.PAGE_SIZE)
    message.message_pages(C, floor_layer_markers, L.raw_color, title, with_review=with_review)
    C.save()


if __name__ == '__main__':
    pdfmetrics.registerFont(TTFont('FreePTSans', 'fonts/pt_sans.ttf'))
    filename = timezone.now().strftime('%d%m_%H%M.pdf')
    C = rc.Canvas(filename, pagesize=layout.Definitions.PAGE_SIZE)

    P = Page.objects.get(uid='2d8bf8ff-9ef2-4a84-b2d5-a6ba60277b30')
    L = P.project.layer_set.filter(title='122_D_HAN').first()
    floor_layer_markers = P.marker_set.filter(layer=L)

    title = [P.floor_caption, L.title]

    # test_plan(True)
    test_mess(True)
