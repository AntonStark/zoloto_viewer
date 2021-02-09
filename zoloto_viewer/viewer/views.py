import json
import operator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators import csrf, http

from zoloto_viewer.infoplan import views as infoplan_views
from zoloto_viewer.viewer.models import Color, Project, Layer, MarkerKind, Page, PdfGenerated
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

    pages_data, _, floor_offsets = project_form.parse_pages(request.POST, request.FILES)
    if not pages_data or not pages_data:
        return redirect('load_project')

    project_obj = Project(title=title)
    project_obj.save()

    project_obj.store_pages(pages_data)
    project_obj.alter_floor_offsets(floor_offsets)
    return redirect('projects')


@login_required
def edit_project(request, title):
    try:
        project_obj = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404
    if request.method != 'POST':
        pages = Page.objects.filter(project=project_obj)
        context = {
            'project': project_obj,
            'pages': pages,
        }
        return render(request, 'viewer/edit_project.html', context=context)

    title = request.POST['title']
    project_obj.rename_project(title)

    csv_to_delete, pages_to_delete = project_form.files_to_delete(request.POST)
    for page_name in pages_to_delete:
        Page.remove_from_project(project_obj, page_name)

    pages_data, floor_captions, floor_offsets = project_form.parse_pages(request.POST, request.FILES)

    errors = []
    project_obj.store_pages(pages_data)
    try:
        project_obj.alter_floor_captions(floor_captions)
    except IntegrityError:
        errors.append('captions not unique')
    project_obj.alter_floor_offsets(floor_offsets)

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

    page_config = {
        'marker_size_factors': Page.SIZE_FACTOR_ALLOWED,
        'map_scale_factors': Page.MAP_SCALE_ALLOWED,
    }
    pdf_orig_set = page_obj.project.pdfgenerated_set.filter(mode=PdfGenerated.ORIGINAL)
    pdf_rev_set = page_obj.project.pdfgenerated_set.filter(mode=PdfGenerated.REVIEWED)
    pdf_original = pdf_orig_set.latest('created') if pdf_orig_set.exists() else None
    pdf_reviewed = pdf_rev_set.latest('created') if pdf_rev_set.exists() else None
    pdf_created_time = PdfGenerated.get_latest_time([pdf_original, pdf_reviewed])
    pdf_refresh_timeout = page_obj.project.pdf_refresh_timeout()

    return infoplan_views.project_page(request, page_obj=page_obj, page_config=page_config,
                                       pdf_original=pdf_original, pdf_reviewed=pdf_reviewed,
                                       pdf_created_time=pdf_created_time, pdf_refresh_timeout=pdf_refresh_timeout)


@login_required
@csrf.csrf_exempt
@http.require_http_methods(['PUT'])
def edit_project_page(request, page_code):
    """
    :param request: request.body is json object
                    {marker_size_factor}
    :param page_code: str
    """
    fields_ = ('marker_size_factor',)
    try:
        req = json.loads(request.body)
        marker_size_factor = operator.itemgetter(*fields_)(req)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'request body must be json'}, status=400)
    except KeyError:
        return JsonResponse({'error': 'json object must contain fields: ' + ', '.join(fields_)}, status=400)

    valid = Page.validate_code(page_code)
    if not valid:
        raise Http404
    page_obj = Page.by_code(valid)
    if not page_obj:
        raise Http404

    if not Page.validate_size_factor(marker_size_factor):
        return JsonResponse({
            'error': 'marker_size_factor bad value. '
                     'Possible values are: {allowed}.'.format(allowed=', '.join(Page.SIZE_FACTOR_ALLOWED))},
            status=400)

    page_obj.marker_size_factor = marker_size_factor
    page_obj.save()
    return HttpResponse(status=200)


@login_required
@csrf.csrf_exempt
def add_project_layer(request, title):
    try:
        project = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    last_layer = project.last_layer()
    color = last_layer.color.next() if last_layer else Color.objects.all().first()

    context = {
        'project': project,
        'layer': None,
        'color': color,
        'maker_kind_options': MarkerKind.objects.all(),
    }

    if request.method != 'POST':
        return render(request, 'viewer/project_layer.html', context=context)

    form_data = request.POST
    layer_title = form_data['layer_title']
    try:
        Layer.validate_title(layer_title)
        Layer.test_title_free(project, layer_title)
    except ValueError as e:
        messages.error(request, e.args[0])
        # next to "keep" input values
        context['layer'] = Layer(project=project, title=layer_title,
                                 desc=form_data['layer_desc'], kind_id=form_data['maker_kind'])
        return render(request, 'viewer/project_layer.html', context=context)

    Layer(project=project, title=layer_title, desc=form_data['layer_desc'],
          kind_id=form_data['maker_kind'],
          color_id=form_data['layer_color']).save()
    return redirect(to='project_page', page_code=project.first_page().code)


@login_required
@csrf.csrf_exempt
def edit_project_layer(request, project_title, layer_title):
    try:
        project = Project.objects.get(title=project_title)
    except Project.DoesNotExist:
        raise Http404
    layer = Layer.objects.filter(project=project, title=layer_title).first()
    if not layer:
        raise Http404

    context = {
        'project': project,
        'layer': layer,
        'color': layer.color,
        'maker_kind_options': MarkerKind.objects.all(),
    }

    if request.method != 'POST':
        return render(request, 'viewer/project_layer.html', context=context)

    form_data = request.POST
    layer_title = form_data['layer_title']
    try:
        Layer.validate_title(layer_title)
        Layer.test_title_free(project, layer_title, except_=layer)
    except ValueError as e:
        messages.error(request, e.args[0])
        # next to "keep" input values
        context['layer'] = Layer(project=project, title=layer_title,
                                 desc=form_data['layer_desc'], kind_id=form_data['maker_kind'])
        return render(request, 'viewer/project_layer.html', context=context)

    layer.title = form_data['layer_title']
    layer.desc = form_data['layer_desc']
    layer.kind_id = form_data['maker_kind']
    layer.save()
    return redirect(to='project_page', page_code=project.first_page().code)
