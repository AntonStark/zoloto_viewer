from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators import csrf, http
from django.utils import timezone

from zoloto_viewer.viewer.models import Project
from zoloto_viewer.infoplan.models import Marker
from zoloto_viewer.documents.models import ProjectFile


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_counts_file(request, title):
    project = get_object_or_404(Project, title=title)
    pf = ProjectFile.objects.generate_counts(project)
    return FileResponse(pf.file, filename=pf.public_name)


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_picts_file(request, title):
    project = get_object_or_404(Project, title=title)
    pf = ProjectFile.objects.generate_pict_list(project)
    return FileResponse(pf.file, filename=pf.public_name)


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_vars_file(request, title):
    project = get_object_or_404(Project, title=title)
    existing_file = ProjectFile.objects.filter(
        project=project,
        kind=ProjectFile.FileKinds.CSV_VARIABLES
    ).first()   # type: ProjectFile
    if not existing_file or \
            Marker.objects.max_last_modified(project=project) > existing_file.date_created:
        existing_file = ProjectFile.objects.generate_vars_index_file(project)

    return FileResponse(existing_file.file, filename=existing_file.public_name)


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_infoplan_file(request, title):
    project = get_object_or_404(Project, title=title)
    existing_file = ProjectFile.objects.filter(
        project=project,
        kind=ProjectFile.FileKinds.TAR_INFOPLAN
    ).first()   # type: ProjectFile
    # fixme DRY: параметры дублируются сначала при проверке, а потом при создании
    if not existing_file or \
            Marker.objects.max_last_modified(project=project) > existing_file.date_created:
        existing_file = ProjectFile.objects.generate_infoplan_archive(project)

    return FileResponse(existing_file.file, filename=existing_file.public_name)


@login_required
@csrf.csrf_exempt
def get_pdf_file(request, title):
    project = get_object_or_404(Project, title=title)
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
