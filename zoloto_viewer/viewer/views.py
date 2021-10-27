import json
import operator
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators import csrf, http

from zoloto_viewer.infoplan import views as infoplan_views
from zoloto_viewer.viewer.models import Color, Project, Layer, LayerGroup, MarkerKind, Page
from zoloto_viewer.viewer.view_helpers import project_form, title_short_code


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
        customer = request.POST['customer']
        stage = request.POST['stage']
        if not Project.validate_title(title):
            raise ValueError
    except (KeyError, ValueError):
        return redirect('load_project')

    pages_data, _ = project_form.parse_pages(request.POST, request.FILES)
    floor_offsets = project_form.parse_offsets(request.POST)
    floor_levels = project_form.parse_levels(request.POST)
    if not pages_data:
        return redirect('load_project')

    project_obj = Project(title=title, customer=customer, stage=stage)
    project_obj.save()

    project_obj.store_pages(pages_data)
    project_obj.alter_floor_offsets(floor_offsets)
    project_obj.alter_floor_levels(floor_levels)
    return redirect('projects')


@login_required
def edit_project(request, project_id):
    project_obj = get_object_or_404(Project, id=project_id)
    if request.method != 'POST':
        pages = Page.objects.filter(project=project_obj)
        context = {
            'project': project_obj,
            'pages': pages,
        }
        return render(request, 'viewer/edit_project.html', context=context)

    title = request.POST['title']
    customer = request.POST['customer']
    stage = request.POST['stage']
    project_obj.rename_project(customer, title, stage)

    csv_to_delete, pages_to_delete = project_form.files_to_delete(request.POST)
    for page_name in pages_to_delete:
        Page.remove_from_project(project_obj, page_name)

    pages_data, floor_captions = project_form.parse_pages(request.POST, request.FILES)
    floor_offsets = project_form.parse_offsets(request.POST)
    floor_levels = project_form.parse_levels(request.POST)

    errors = []
    project_obj.store_pages(pages_data)
    try:
        project_obj.alter_floor_captions(floor_captions)
    except IntegrityError:
        errors.append('captions not unique')
    project_obj.alter_floor_offsets(floor_offsets)
    project_obj.alter_floor_levels(floor_levels)

    if errors:
        return redirect(to='edit_project', project_id=project_obj.id)
    return redirect(to='projects')


@login_required
def project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    first_page = project.first_page()
    if not first_page:
        raise Http404

    return redirect(to='project_page', page_code=first_page.code)


@login_required
def remove_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    project.delete()
    return redirect(to='projects')


@http.require_http_methods(['GET'])
def generate_project_code(request):
    try:
        title = request.GET['title']
    except KeyError:
        return JsonResponse({'title': 'field required'}, status=400)
    codes_variants = title_short_code.make_code_candidates(title)
    already_used = set(Project.objects.all().values_list('code', flat=True))
    codes_free = [c for c in codes_variants if c not in already_used]
    return codes_free[0]


def project_page(request, page_code):
    valid = Page.validate_code(page_code)
    if not valid:
        raise Http404
    page_obj = Page.by_code(valid)
    if not page_obj:
        raise Http404

    page_config = {
        'code': page_obj.code,
        'marker_size_factors': Page.SIZE_FACTOR_ALLOWED,
        'map_scale_factors': Page.MAP_SCALE_ALLOWED,
    }

    return infoplan_views.project_page(request,
                                       page_obj=page_obj,
                                       page_config=page_config)


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
    return JsonResponse({'status': 'success'}, status=200)


@login_required
@csrf.csrf_exempt
def add_project_layer(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    last_color = Layer.max_color(project.layer_set)
    color = last_color.next() if last_color else Color.objects.first()

    try:
        return_to_page_code = request.GET['return']
    except KeyError:
        return_to_page_code = project.first_page().code
    else:
        is_valid_code = Page.validate_code(return_to_page_code)
        same_project_page = Page.by_code(return_to_page_code).project == project
        if not (is_valid_code and same_project_page):
            return_to_page_code = project.first_page().code

    context = {
        'project': project,
        'layer': None,
        'color': color,
        'maker_kind_options': MarkerKind.objects.all(),
        'return_to_page_code': return_to_page_code,
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
    return redirect(to='project_page', page_code=return_to_page_code)


@login_required
@csrf.csrf_exempt
def edit_project_layer(request, project_id, layer_title):
    project = get_object_or_404(Project, id=project_id)
    layer = get_object_or_404(Layer, project=project, title=layer_title)

    return_to_page_code = request.GET['return']
    is_valid_code = Page.validate_code(return_to_page_code)
    same_project_page = Page.by_code(return_to_page_code).project == project
    if not (is_valid_code and same_project_page):
        return_to_page_code = project.first_page().code

    context = {
        'project': project,
        'layer': layer,
        'color': layer.color,
        'maker_kind_options': MarkerKind.objects.all(),
        'return_to_page_code': return_to_page_code,
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

    return_to_page_code = request.GET['return']
    is_valid_code = Page.validate_code(return_to_page_code)
    same_project_page = Page.by_code(return_to_page_code).project == project
    if not (is_valid_code and same_project_page):
        return_to_page_code = project.first_page().code
    return redirect(to='project_page', page_code=return_to_page_code)


@login_required
@http.require_http_methods(['GET'])
def setup_layer_groups(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    context = {
        'project': project,
    }
    return render(request, 'viewer/layer_grouping.html', context=context)


def with_layers_group_check(project_view):
    @wraps(project_view)
    def decorated(request, project_id):
        project = get_object_or_404(Project, id=project_id)
        all_grouped, remains = LayerGroup.all_layers_grouped(project)
        if not all_grouped:
            if not request.GET.get('autogroup_remains'):
                return redirect(to='setup_layer_groups', project_id=project_id)
            else:
                LayerGroup.autogroup_layers(project, remains)
        # all layers grouped now
        return project_view(request, project_id)

    return decorated
