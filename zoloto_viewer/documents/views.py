from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators import csrf, http

from zoloto_viewer.viewer.models import Project
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
    pf = ProjectFile.objects.look_for_fresh(project, ProjectFile.FileKinds.CSV_VARIABLES)
    if not pf:
        pf = ProjectFile.objects.generate_vars_index_file(project)
    return FileResponse(pf.file, filename=pf.public_name)


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_infoplan_file(request, title):
    project = get_object_or_404(Project, title=title)
    pf = ProjectFile.objects.look_for_fresh(project, ProjectFile.FileKinds.TAR_INFOPLAN)
    if not pf:
        pf = ProjectFile.objects.generate_infoplan_archive(project)
    return FileResponse(pf.file, filename=pf.public_name)


@login_required
@csrf.csrf_exempt
def get_pdf_file(request, title):
    project = get_object_or_404(Project, title=title)
    # pf = ProjectFile.objects.look_for_fresh(project, ProjectFile.FileKinds.PDF_EXFOLIATION)
    pf = None   # fixme enable fresh lookup
    if not pf:
        pf = ProjectFile.objects.pdf_generate_file(project)
    return FileResponse(pf.file, filename=pf.public_name)
