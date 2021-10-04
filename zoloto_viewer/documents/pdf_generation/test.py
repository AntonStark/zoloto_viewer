import django
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rc

django.setup()
from zoloto_viewer.viewer.models import Page

from . import layout, main, message_page_writer as message, plan_page_writer as plan


def test_plan():
    C = rc.Canvas(filename, pagesize=layout.Definitions.PAGE_SIZE)
    marker_positions = main.collect_marker_positions(P, L)
    layers_data = [plan.LayerData(L.id, L.title, L.desc, main.color_adapter(L.color.rgb_code), L.kind_id)]
    title = [P.floor_caption, L.title]
    plan.plan_page(C, P, marker_positions, layers_data, title, ['', ''])
    C.save()


def test_mess():
    C = rc.Canvas(filename, pagesize=layout.Definitions.PAGE_SIZE)
    marker_messages = main.collect_messages_data(P, L)

    message.message_pages(C, marker_messages, L.kind.sides,
                          main.color_adapter(L.color.rgb_code), title, ['', ''])
    C.save()


if __name__ == '__main__':
    pdfmetrics.registerFont(TTFont('FreePTSans', 'fonts/pt_sans.ttf'))
    filename = timezone.now().strftime('%d%m_%H%M.pdf')
    C = rc.Canvas(filename, pagesize=layout.Definitions.PAGE_SIZE)

    P = Page.objects.get(uid='2d8bf8ff-9ef2-4a84-b2d5-a6ba60277b30')
    L = P.project.layer_set.filter(title='122_D_HAN').first()
    floor_layer_markers = P.marker_set.filter(layer=L)

    title = [P.floor_caption, L.title]

    # test_plan()
    test_mess()
