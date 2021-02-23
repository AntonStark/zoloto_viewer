from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.views.decorators import csrf, http

from zoloto_viewer.viewer.models import Project, PdfGenerated
from zoloto_viewer.documents.models import ProjectFile


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_project_doc(request, title, kind):
    try:
        project = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    debug = ''


@login_required
@csrf.csrf_exempt
def rebuild_pdf_files(request, title):
    try:
        project = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    pdf_generated = project.generate_pdf_files()
    if not pdf_generated:
        return JsonResponse({
            'error': f'at least {Project.PDF_GENERATION_TIMEOUT} seconds during calls',
            'try_after': str(project.pdf_refresh_timeout()),
        }, status=429)

    if request.method == 'GET':
        return redirect(to=request.META.get('HTTP_REFERER', '/'))   # just push reload if GET

    from zoloto_viewer.viewer.templatetags.timedelta import timedelta_pretty
    pdf_gen_orig, pdf_gen_rev = pdf_generated
    return JsonResponse({
        'pdf_created_time': timedelta_pretty(PdfGenerated.get_latest_time(pdf_generated)),
        'pdf_refresh_timeout': project.pdf_refresh_timeout(),
        'pdf_original': pdf_gen_orig.file.url,
        'pdf_reviewed': pdf_gen_rev.file.url,
    }, status=201)
