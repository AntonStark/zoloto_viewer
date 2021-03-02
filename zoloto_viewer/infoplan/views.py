import json
import operator
import uuid
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.decorators import csrf, http
from django.utils.decorators import method_decorator

from zoloto_viewer.infoplan.models import Marker, MarkerVariable
from zoloto_viewer.infoplan.utils import variable_transformations as transformations
from zoloto_viewer.viewer.models import Layer, Page, Project


def marker_api(method):
    def _decorated_method(request, marker_uid):
        try:
            uid = uuid.UUID(marker_uid)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'after /marker/ must be uuid'}, status=400)
        return method(request, uid)
    return _decorated_method


@login_required
@http.require_POST
@csrf.csrf_exempt
def create_marker(request):
    fields_ = ('project', 'page', 'layer', 'position')
    try:
        req = json.loads(request.body)
        project, page, layer, position = operator.itemgetter(*fields_)(req)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'request body must be json'}, status=400)
    except KeyError:
        return JsonResponse({'error': 'json object must contain fields: ' + ', '.join(fields_)}, status=400)

    project = get_object_or_404(Project, uid=uuid.UUID(project))
    page = get_object_or_404(Page, project=project, code=page)
    layer = get_object_or_404(Layer, project=project, title=layer)

    pos_schema = ('center_x', 'center_y', 'rotation')
    center_x, center_y, rotation = operator.itemgetter(*pos_schema)(position)

    marker = Marker(layer=layer, floor=page,
                    pos_x=center_x, pos_y=center_y, rotation=rotation)

    marker.save()
    rep = marker.to_json()
    rep.update({
        'project': project.uid,
        'layer': layer.title,
        'page': page.code,
    })
    return JsonResponse(rep)


@method_decorator(csrf.csrf_exempt, name='dispatch')
class MarkerView(View):
    @method_decorator(marker_api)
    def get(self, request, marker_uid: uuid.UUID):
        try:
            marker = Marker.objects.get(uid=marker_uid)
        except Marker.DoesNotExist:
            raise Http404

        is_pretty = request.GET.get('pretty')
        filters = [
            transformations.HideMasterPageLine(),
            transformations.ReplacePictCodes()
        ] if is_pretty else []

        rep = marker.to_json()
        rep.update({
            'comments': marker.comments_json,
            'infoplan': MarkerVariable.objects.vars_by_side(marker, apply_transformations=filters),
        })
        rep.update({
            'layer': {
                'title': marker.layer.title,
                'color': marker.layer.color.hex_code,
                'kind': {'name': marker.layer.kind.name, 'sides': marker.layer.kind.sides}
            }
        })
        return JsonResponse(rep)

    @method_decorator(login_required)
    @method_decorator(marker_api)
    def patch(self, request, marker_uid: uuid.UUID):
        """Update marker position attributes: pos_x, pos_y, rotation"""
        try:
            marker = Marker.objects.get(uid=marker_uid)
        except Marker.DoesNotExist:
            raise Http404

        try:
            req = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'request body must be json'}, status=400)
        if not isinstance(req, dict):
            return JsonResponse({'error': 'request body must be json object'}, status=400)

        possible_fields = Marker.position_attrs()
        fields = {f: req[f] for f in possible_fields if f in req}

        def validate_not_empty(data: dict):
            return len(data)

        def validate_values_integer(data: dict):
            for v in data.values():
                if not isinstance(v, int):
                    return False
            return True

        if not validate_not_empty(fields):
            return JsonResponse({'error': 'json object must contain any of: ' + ', '.join(possible_fields)}, status=400)
        if not validate_values_integer(fields):
            return JsonResponse({'error': 'only integer values allowed'}, status=400)

        _changed = False
        for attr, value in fields.items():
            if getattr(marker, attr) != value:
                setattr(marker, attr, value)
                _changed = True
        if _changed:
            marker.save()

        rep = marker.to_json()
        return JsonResponse(rep)

    @method_decorator(login_required)
    @method_decorator(marker_api)
    def put(self, request, marker_uid: uuid.UUID):
        """Set variables of marker"""
        # {
        #   infoplan: [
        #       {side: 1, variables: ['a', 'b']},
        #       {side: 2, variables: []}
        #   ]
        # }
        try:
            marker = Marker.objects.get(uid=marker_uid)
        except Marker.DoesNotExist:
            raise Http404

        try:
            req = json.loads(request.body)
            infoplan = req['infoplan']
        except json.JSONDecodeError:
            return JsonResponse({'error': 'request body must be json'}, status=400)
        except KeyError:
            return JsonResponse({'error': 'json object must contain field infoplan'}, status=400)


        def validate_side_objects(data):
            def validate_obj(obj):
                try:
                    side, variables = obj['side'], obj['variables']
                except KeyError:
                    return False
                if not (isinstance(side, int) and isinstance(variables, list)):
                    return False
                for v in variables:
                    if not isinstance(v, str):
                        return False
                return True

            if not isinstance(data, list):
                return False
            for i in data:
                if not (isinstance(i, dict) and validate_obj(i)):
                    return False
            return True

        def validate_sides_count(data):
            return max(data.keys()) == marker.layer.kind.sides

        def validate_all_sides_present(data):
            return tuple(sorted(data.keys())) == tuple(range(1, marker.layer.kind.sides + 1))

        if not validate_side_objects(infoplan):
            return JsonResponse({'error': 'side obj must contain fields side and variables of types int and list[str]'},
                                status=400)
        vars_by_side = {sideObj['side']: sideObj['variables'] for sideObj in infoplan}

        if not validate_sides_count(vars_by_side):
            return JsonResponse({'error': 'wrong sides count for that marker kind'}, status=400)
        if not validate_all_sides_present(vars_by_side):
            return JsonResponse({'error': 'some side objects missing'}, status=400)

        vars_by_side = transformations.html_escape_incoming(vars_by_side)

        MarkerVariable.objects.reset_values(marker, vars_by_side)

        rep = marker.to_json()
        rep.update({
            'comments': marker.comments_json,
            'infoplan': MarkerVariable.objects.vars_by_side(marker),
        })
        rep.update({
            'layer': {
                'title': marker.layer.title,
                'color': marker.layer.color.hex_code,
                'kind': {'name': marker.layer.kind.name, 'sides': marker.layer.kind.sides}
            }
        })
        return JsonResponse(rep)

    @method_decorator(login_required)
    @method_decorator(marker_api)
    def delete(self, _, marker_uid: uuid.UUID):
        try:
            marker = Marker.objects.get(uid=marker_uid)
        except Marker.DoesNotExist:
            raise Http404
        else:
            marker.delete()
            return JsonResponse({'status': 'ok'}, status=200)


@http.require_POST
@csrf.csrf_exempt
@marker_api
def update_wrong_status(request, marker_uid: uuid.UUID):
    """request.body is json object {key, wrong}"""
    fields_ = ('key', 'wrong')
    try:
        req = json.loads(request.body)
        key, is_wrong = operator.itemgetter(*fields_)(req)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'request body must be json'}, status=400)
    except KeyError:
        return JsonResponse({'error': 'json object must contain fields: ' + ', '.join(fields_)}, status=400)
    if not isinstance(is_wrong, bool):
        return JsonResponse({'error': '\'wrong\' must be boolean'}, status=400)

    try:
        marker = Marker.objects.get(uid=marker_uid)
    except Marker.DoesNotExist:
        raise Http404

    try:
        target = MarkerVariable.objects.get(marker=marker, key=key)
    except MarkerVariable.DoesNotExist:
        raise Http404
    else:
        if not target.value:    # не позволять пометить пустую переменную
            return JsonResponse({'error': 'empty variable could not be wrong'}, status=400)
        target.wrong = is_wrong
        target.save()

    rep = marker.to_json()
    rep.update({'variable': target.to_json()})
    return JsonResponse(rep)


@http.require_POST
@csrf.csrf_exempt
@marker_api
def load_marker_review(request, marker_uid: uuid.UUID):
    """
    :param request: request.body is json object
                    {comment, exit_type}
                    exit_type = "button" | "blur"
    :param marker_uid: uuid.UUID type
    """
    fields_ = ('comment', 'exit_type')
    try:
        req = json.loads(request.body)
        comment, exit_type = operator.itemgetter(*fields_)(req)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'request body must be json'}, status=400)
    except KeyError:
        return JsonResponse({'error': 'json object must contain fields: ' + ', '.join(fields_)}, status=400)
    explicit_end_review = exit_type == 'button'

    try:
        marker = Marker.objects.get(uid=marker_uid)
    except Marker.DoesNotExist:
        raise Http404
    # always create new comment, previous comments not visible
    if comment:
        marker.markercomment_set.create(content=comment)
    marker.save()

    return JsonResponse(marker.to_json())


@login_required
@http.require_POST
@csrf.csrf_exempt
@marker_api
def resolve_marker_comments(request, marker_uid: uuid.UUID):
    try:
        marker = Marker.objects.get(uid=marker_uid)
    except Marker.DoesNotExist:
        raise Http404

    for c in marker.markercomment_set.all():
        c.resolve()
    return JsonResponse(marker.to_json())


def project_page(request, **more_context):
    page_obj = more_context['page_obj']
    page_config = more_context['page_config']

    pdf_info = more_context['docs_info']['pdf']
    pdf_original = pdf_info['pdf_original']
    pdf_created_time = pdf_info['pdf_created_time']
    pdf_refresh_timeout = pdf_info['pdf_refresh_timeout']

    project = page_obj.project
    page_code_list = project.page_set.values_list('code', 'floor_caption')
    layers = project.layer_set.values_list('title', 'color__hex_code')
    layers_visible = set(request.GET.getlist('layer'))
    markers_by_layer = {L: page_obj.marker_set.filter(layer=L)
                        for L in project.layer_set.all()}

    context = {
        'project': project,
        'page': page_obj,
        'page_config': page_config,
        'page_code_list': page_code_list,
        'layers': layers,
        'layers_visible': layers_visible,
        'markers_by_layer': markers_by_layer,

        'base_url': settings.BASE_URL,
        'marker_display_config': {
            'marker_scale': page_obj.apply_size_factor(1),
            'circle_radius': page_obj.apply_size_factor(Marker.CIRCLE_RADIUS),
            'comment_mark_radius': page_obj.apply_size_factor(Marker.COMMENT_MARK_RADIUS),
            'comment_mark_padding': page_obj.apply_size_factor(Marker.COMMENT_MARK_PADDING),
        },

        'pdf_original': pdf_original,   # todo review docs info format (enclose in own dict)
        'pdf_created_time': pdf_created_time,
        'pdf_refresh_timeout': str(pdf_refresh_timeout),
    }
    template = 'infoplan/project_page_auth.html' if request.user.is_authenticated \
        else 'infoplan/project_page.html'
    return render(request, template, context=context)
