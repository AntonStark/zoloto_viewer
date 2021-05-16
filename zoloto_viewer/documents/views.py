from background_task import background
from background_task.models import Task
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators import csrf, http
from django.utils import timezone

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
@http.require_http_methods(['GET', 'HEAD'])
def get_pdf_file(request, title):
    # with HEAD request not send file content if present
    project = get_object_or_404(Project, title=title)
    pf = ProjectFile.objects.look_for_fresh(project, ProjectFile.FileKinds.PDF_EXFOLIATION)

    if not pf:
        if not is_generate_pdf_task_queued(project.uid):
            generate_pdf_doc(str(project.uid), schedule=timezone.now())
        return HTTP_RETRY_LATER

    return FileResponse(pf.file, filename=pf.public_name) \
        if request.method == 'GET' \
        else HttpResponse(status=200)


def _make_retry_later_rep():
    rep = HttpResponse(status=323)
    rep['Retry-After'] = 20
    return rep


HTTP_RETRY_LATER = _make_retry_later_rep()
PDF_GENERATE_TASK_NAME = 'documents__project_file__pdf'


@background(name=PDF_GENERATE_TASK_NAME)
def generate_pdf_doc(project_uid):
    project = Project.objects.get(uid=project_uid)
    ProjectFile.objects.pdf_generate_file(project)


def is_generate_pdf_task_queued(project_uid):
    return Task.objects.get_task(
        task_name=PDF_GENERATE_TASK_NAME,
        args=[str(project_uid)]
    ).exists()
