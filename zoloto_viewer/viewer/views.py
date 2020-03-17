from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators import csrf

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

    project_obj = Project(title=title)
    project_obj.save()

    project_obj.update_additional_files(additional_files)
    project_obj.store_pages(pages_data)
    project_obj.create_layers(layer_files)
    return redirect('projects')


@login_required
def edit_project(request, title):
    try:
        project_obj = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404
    if request.method != 'POST':
        pages = Page.objects.filter(project=project_obj)
        layers = Layer.objects.filter(project=project_obj)
        context = {
            'project': project_obj,
            'pages_list': map(Page.serialize, pages),
            'csv_list': list(map(Layer.serialize, layers)) + project_obj.additional_files_info(),
        }
        return render(request, 'viewer/edit_project.html', context=context)

    title = request.POST['title']
    project_obj.rename_project(title)

    csv_to_delete, pages_to_delete = project_form.files_to_delete(request.POST)
    for csv_name in csv_to_delete:
        Layer.remove_from_project(project_obj, csv_name)
    for page_name in pages_to_delete:
        Page.remove_from_project(project_obj, page_name)
    project_obj.remove_additional_files(csv_to_delete)

    pages_data, floor_captions = project_form.parse_pages(request.POST, request.FILES)
    layer_files, additional_files = project_form.parse_csv(request.POST, request.FILES)

    errors = []
    project_obj.update_additional_files(additional_files)
    project_obj.store_pages(pages_data)
    try:
        project_obj.alter_floor_captions(floor_captions)
    except IntegrityError:
        errors.append('captions not unique')
    project_obj.create_layers(layer_files)

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
        project_obj = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    project_obj.delete()
    return redirect(to='projects')


@login_required
@csrf.csrf_exempt
def rebuild_pdf_files(request, title):
    try:
        project_obj = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    pdf_generated = project_obj.generate_pdf_files()
    if not pdf_generated:
        return JsonResponse({
            'error': f'at least {Project.PDF_GENERATION_TIMEOUT} seconds during calls',
            'try_after': str(project_obj.pdf_refresh_timeout()),
        }, status=429)
    else:
        if request.method == 'GET':
            return redirect(to=request.META.get('HTTP_REFERER', '/'))   # just push reload if GET

        from zoloto_viewer.viewer.templatetags.timedelta import timedelta_pretty
        pdf_gen_orig, pdf_gen_rev = pdf_generated
        return JsonResponse({
            'pdf_created_time': timedelta_pretty(PdfGenerated.get_latest_time(pdf_generated)),
            'pdf_refresh_timeout': project_obj.pdf_refresh_timeout(),
            'pdf_original': pdf_gen_orig.file.url,
            'pdf_reviewed': pdf_gen_rev.file.url,
        }, status=201)


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
    pdf_refresh_timeout = page_obj.project.pdf_refresh_timeout()

    return infoplan_views.project_page(request, page_obj=page_obj, pdf_original=pdf_original, pdf_reviewed=pdf_reviewed,
                                       pdf_created_time=pdf_created_time, pdf_refresh_timeout=pdf_refresh_timeout)
