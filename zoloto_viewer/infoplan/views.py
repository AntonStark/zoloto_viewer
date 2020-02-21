import json
import operator
import uuid
from django.http import JsonResponse, Http404
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
    variables = MarkerVariable.objects.filter(marker=marker).all()

    rep = marker.to_json().update({
        'comment': marker.comment,
        'variables': tuple(map(MarkerVariable.to_json, variables)),
    })
    return JsonResponse(rep)


@http.require_POST
@csrf.csrf_exempt
@marker_api
def update_wrong_status(request, marker_uid: uuid.UUID):
    """request.body is json object {marker_uid, key, wrong}"""
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
        target.wrong = is_wrong
        target.save()
        marker.deduce_correctness()

    rep = marker.to_json().update({'variable': target.to_json()})
    return JsonResponse(rep)


@http.require_POST
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
        is_wrong_by_key, comment, exit_type = operator.itemgetter('variables', 'comment', 'exit_type')(req)
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({
            'error': 'post body must be json with fields: \'variables\', \'comment\', \'exit_type\''
        }, status=400)
    if not isinstance(is_wrong_by_key, list):
        return JsonResponse({'error': '\'variables\' must be json array'}, status=400)
    explicit_end_review = exit_type == 'button'

    try:
        marker = Marker.objects.get(uid=marker_uid)
    except Marker.DoesNotExist:
        raise Http404
    MarkerVariable.objects.reset_wrong_statuses(marker, is_wrong_by_key)
    marker.comment = comment
    marker.deduce_correctness(explicit_end_review)

    return JsonResponse(marker.to_json())
