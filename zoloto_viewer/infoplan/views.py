import json
import operator
import uuid
from django.conf import settings
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.views.decorators import http, csrf

from zoloto_viewer.infoplan.models import Marker, MarkerVariable


def marker_api(method):
    def _decorated_method(request, marker_uid):
        try:
            uid = uuid.UUID(marker_uid)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'after /marker/ must be uuid'}, status=400)
        return method(request, uid)
    return _decorated_method


@http.require_GET
@marker_api
def get_marker_data(_, marker_uid: uuid.UUID):
    try:
        marker = Marker.objects.get(uid=marker_uid)
    except Marker.DoesNotExist:
        raise Http404
    variables = MarkerVariable.objects.vars_of_marker(marker)

    rep = marker.to_json()
    rep.update({
        'comment': marker.comment,
        'variables': tuple(map(MarkerVariable.to_json, variables)),
    })
    rep.update({
        'layer': {'title': marker.layer.title, 'color': marker.layer.color}
    })
    return JsonResponse(rep)


@http.require_POST
@csrf.csrf_exempt
@marker_api
def update_wrong_status(request, marker_uid: uuid.UUID):
    """request.body is json object {key, wrong}"""
    try:
        req = json.loads(request.body)
        key, is_wrong = operator.itemgetter('key', 'wrong')(req)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'post body must be json'}, status=400)
    except KeyError:
        return JsonResponse({'error': 'post body must contain: \'key\', \'wrong\''}, status=400)
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
        marker.deduce_correctness()

    rep = marker.to_json()
    rep.update({'variable': target.to_json()})
    return JsonResponse(rep)


@http.require_POST
@csrf.csrf_exempt
@marker_api
def load_marker_review(request, marker_uid: uuid.UUID):
    """
    :param request: request.body is json object
                    {variables: [{key, wrong}], comment, exit_type}
                    exit_type = "button" | "blur"
    :param marker_uid: uuid.UUID type
    """
    try:
        req = json.loads(request.body)
        variables, comment, exit_type = operator.itemgetter('variables', 'comment', 'exit_type')(req)
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({
            'error': 'post body must be json with fields: \'variables\', \'comment\', \'exit_type\''
        }, status=400)
    if not isinstance(variables, list):
        return JsonResponse({'error': '\'variables\' must be json array'}, status=400)
    explicit_end_review = exit_type == 'button'

    try:
        marker = Marker.objects.get(uid=marker_uid)
    except Marker.DoesNotExist:
        raise Http404
    is_wrong_by_key = dict(map(lambda v: (v['key'], v['wrong']), variables))
    MarkerVariable.objects.reset_wrong_statuses(marker, is_wrong_by_key)
    marker.comment = comment
    marker.deduce_correctness(explicit_end_review)

    return JsonResponse(marker.to_json())


def project_page(request, **more_context):
    page_obj = more_context['page_obj']

    pdf_original = more_context['pdf_original']
    pdf_reviewed = more_context['pdf_reviewed']
    pdf_created_time = more_context['pdf_created_time']
    pdf_refresh_timeout = more_context['pdf_refresh_timeout']

    project = page_obj.project
    page_code_list = project.page_set.values_list('code', flat=True)
    layers = project.layer_set.values_list('title', 'color')
    layers_visible = set(request.GET.getlist('layer'))
    markers_by_layer = {L: page_obj.marker_set.filter(layer=L)
                        for L in project.layer_set.all()}
    im, (gb_top, gb_left, gb_bottom, gb_right) = page_obj.plan, page_obj.geometric_bounds

    context = {
        'project': project,
        'page': page_obj,
        'page_code_list': page_code_list,
        'layers': layers,
        'layers_visible': layers_visible,
        'markers_by_layer': markers_by_layer,
        'transform_params': {
            'scale': [im.width / (gb_right - gb_left), im.height / (gb_bottom - gb_top)],
            'translate': [-gb_left, -gb_top],
        },
        'base_url': settings.BASE_URL,

        'pdf_original': pdf_original,
        'pdf_reviewed': pdf_reviewed,
        'pdf_created_time': pdf_created_time,
        'pdf_refresh_timeout': str(pdf_refresh_timeout),
    }
    template = 'infoplan/project_page_auth.html' if request.user.is_authenticated \
        else 'infoplan/project_page.html'
    return render(request, template, context=context)
