import os
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from zoloto_viewer.infoplan.pdf_generation import layout, message, plan
from zoloto_viewer.viewer.models import Project, Page


def generate_pdf(project: Project, buffer, with_review: bool):
    pt_sans_path = os.path.join(os.path.dirname(__file__), 'fonts/pt_sans.ttf')
    pdfmetrics.registerFont(TTFont('FreePTSans', pt_sans_path))

    timestamp = timezone.now().strftime('%d%m_%H%M')
    filename = '_'.join([project.title, 'reviewed' if with_review else 'original', timestamp]) + '.pdf'
    if buffer:
        file_canvas = canvas.Canvas(buffer, pagesize=layout.Definitions.PAGE_SIZE)
    else:
        file_canvas = canvas.Canvas(filename, pagesize=layout.Definitions.PAGE_SIZE)

    first_iteration = True
    for L in project.layer_set.order_by('title').all():
        for P in Page.objects.filter(marker__layer=L).distinct():
            title = [P.floor_caption, L.title]
            floor_layer_markers = P.marker_set.filter(layer=L)

            if not first_iteration:
                file_canvas.showPage()
            plan.plan_page(file_canvas, P, floor_layer_markers,
                           title, L.raw_color, L.title, L.desc, with_review=with_review)

            file_canvas.showPage()
            message.message_pages(file_canvas, floor_layer_markers,
                                  L.raw_color, title, with_review=with_review)
            first_iteration = False
    file_canvas.setTitle(filename)      # todo construct proper file title
    file_canvas.save()
    return filename
