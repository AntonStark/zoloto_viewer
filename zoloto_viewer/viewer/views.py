from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators import csrf, http

from zoloto_viewer.infoplan import views as infoplan_views
from zoloto_viewer.viewer.models import Project, Layer, Page, PdfGenerated
from zoloto_viewer.viewer.view_helpers import project_form


@login_required
def view_projects(request):
    context = {
        'projects': Project.objects.all().order_by('-created'),
    }
    return render(request, 'viewer/view_projects.html', context=context)


@login_required
def load_project(request):
    if request.method != 'POST':
        return render(request, 'viewer/load_project.html')

    try:
        title = request.POST['title']
        if not Project.validate_title(title):
            raise ValueError
    except (KeyError, ValueError):
        return redirect('load_project')

    pages_data, _ = project_form.parse_pages(request.POST, request.FILES)
    layer_files, additional_files = project_form.parse_csv(request.POST, request.FILES)
    if not pages_data or not pages_data:
        return redirect('load_project')

    proj = Project(title=title)
    proj.save()

    proj.update_additional_files(additional_files)
    proj.store_pages(pages_data)
    proj.create_layers(layer_files)
    return redirect('projects')


@login_required
def edit_project(request, title):
    try:
        project = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404
    if request.method != 'POST':
        pages = Page.objects.filter(project=project)
        layers = Layer.objects.filter(project=project)
        context = {
            'project': project,
            'pages_list': map(Page.serialize, pages),
            'csv_list': list(map(Layer.serialize, layers)) + project.additional_files_info(),
        }
        return render(request, 'viewer/edit_project.html', context=context)

    title = request.POST['title']
    if project.title != title:
        project.title = title
        project.save()

    csv_to_delete, pages_to_delete = project_form.files_to_delete(request.POST)
    for csv_name in csv_to_delete:
        Layer.remove_from_project(project, csv_name)
    for page_name in pages_to_delete:
        Page.remove_from_project(project, page_name)
    project.remove_additional_files(csv_to_delete)

    pages_data, floor_captions = project_form.parse_pages(request.POST, request.FILES)
    layer_files, additional_files = project_form.parse_csv(request.POST, request.FILES)

    errors = []
    project.update_additional_files(additional_files)
    project.store_pages(pages_data)
    try:
        project.alter_floor_captions(floor_captions)
    except IntegrityError:
        errors.append('captions not unique')
    project.create_layers(layer_files)

    if errors:
        return redirect(to='edit_project', title=title)
    return redirect(to='projects')


@login_required
def project(request, title):
    try:
        proj = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    first_page = proj.first_page()
    if not first_page:
        raise Http404

    return redirect(to='project_page', page_code=first_page.code)


@login_required
def remove_project(request, title):
    try:
        proj = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    proj.delete()
    return redirect(to='projects')


@login_required
@http.require_POST
@csrf.csrf_exempt
def rebuild_pdf_files(request, title):
    try:
        project = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    # todo удалять прежние файлы после сохранения новых
    pdf_generated = project.generate_pdf_files()
    if not pdf_generated:
        return JsonResponse({'error': f'at least {Project.PDF_GENERATION_TIMEOUT} seconds during calls'}, status=429)
    else:
        return JsonResponse({'generation_time': project.pdf_started}, status=201)


def project_page(request, page_code):
    valid = Page.validate_code(page_code)
    if not valid:
        raise Http404
    page_obj = Page.by_code(valid)
    if not page_obj:
        raise Http404

    pdf_orig_set = page_obj.project.pdfgenerated_set.filter(mode=PdfGenerated.ORIGINAL)
    pdf_rev_set = page_obj.project.pdfgenerated_set.filter(mode=PdfGenerated.REVIEWED)
    pdf_original = pdf_orig_set.latest('created') if pdf_orig_set.exists() else None
    pdf_reviewed = pdf_rev_set.latest('created') if pdf_rev_set.exists() else None
    pdf_created_time = PdfGenerated.get_latest_time([pdf_original, pdf_reviewed])
    pdf_refresh_timeout = pdf_created_time + timedelta(seconds=Project.PDF_GENERATION_TIMEOUT)

    return infoplan_views.project_page(request, page_obj=page_obj, pdf_original=pdf_original, pdf_reviewed=pdf_reviewed,
                                       pdf_created_time=pdf_created_time, pdf_refresh_timeout=pdf_refresh_timeout)
