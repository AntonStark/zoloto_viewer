from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import django
django.setup()
from zoloto_viewer.infoplan.pdf_generation import common_layout, mess_pages, plan_page
from zoloto_viewer.viewer.models import Project, Page


def generate_pdf(project: Project, with_review: bool):
    pdfmetrics.registerFont(TTFont('FreePTSans', 'fonts/pt_sans.ttf'))

    timestamp = timezone.now().strftime('%d%m_%H%M')
    filename = '_'.join([project.title, 'reviewed' if with_review else 'original', timestamp]) + '.pdf'
    file_canvas = canvas.Canvas(filename, pagesize=common_layout.Definitions.PAGE_SIZE)

    first_iteration = True
    for L in project.layer_set.order_by('title').all():
        for P in Page.objects.filter(marker__layer=L).distinct():
            title = [P.floor_caption, L.title]
            floor_layer_markers = P.marker_set.filter(layer=L)

            if not first_iteration:
                file_canvas.showPage()
            plan_page.plan_page(file_canvas, P, floor_layer_markers,
                                title, L.raw_color, L.title, L.desc, with_review=with_review)

            file_canvas.showPage()
            mess_pages.message_pages(file_canvas, floor_layer_markers,
                                     L.raw_color, title, with_review=with_review)
            first_iteration = False
    file_canvas.save()
    return filename


def generate_pdf_original(project: Project):
    return generate_pdf(project, False)


def generate_pdf_reviewed(project: Project):
    return generate_pdf(project, True)


if __name__ == '__main__':
    project = Project.objects.get(id=41)
    r = generate_pdf_original(project)
    print(r)
    r = generate_pdf_reviewed(project)
    print(r)
