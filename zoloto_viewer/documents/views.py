from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect
from django.views.decorators import csrf, http
from django.utils import timezone

from zoloto_viewer.viewer.models import Project
from zoloto_viewer.documents.models import ProjectFile


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_counts_file(request, title):
    try:
        project = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    pf = ProjectFile.objects.generate_counts(project)
    return FileResponse(pf.file)


@login_required
@csrf.csrf_exempt
def rebuild_pdf_files(request, title):
    try:
        project = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    deb = ''
    pdf_refresh_timeout = ProjectFile.objects.pdf_refresh_timeout(project)

    if datetime.now() < pdf_refresh_timeout:
        return JsonResponse({
            'error': f'at least {ProjectFile.PDF_GENERATION_TIMEOUT} seconds during calls',
            'try_after': str(pdf_refresh_timeout),
        }, status=429)
    pdf_generated = ProjectFile.objects.pdf_generate_file(project)

    if request.method == 'GET':
        return redirect(to=request.META.get('HTTP_REFERER', '/'))   # just push reload if GET

    from zoloto_viewer.viewer.templatetags.timedelta import timedelta_pretty
    return JsonResponse({
        'pdf_created_time': timedelta_pretty(timezone.localtime(pdf_generated.date_created)),
        'pdf_refresh_timeout': pdf_refresh_timeout,
        'pdf_original': pdf_generated.file.url,
    }, status=201)
