import json
import operator
import uuid
from django.http import Http404, HttpResponseNotAllowed, JsonResponse
from django.views.decorators import csrf, http

from zoloto_viewer.viewer.models import Marker, MarkerVariable


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

    def _var_to_dict(v: MarkerVariable):
        return {'key': v.key, 'value': v.value, 'wrong': v.wrong}

    rep = {
        'marker': marker.uid,
        'comment': marker.comment,
        'correct': marker.correct,
        'vars': tuple(map(_var_to_dict, variables)),
    }
    return JsonResponse(rep)


@csrf.csrf_exempt
@marker_api
def marker_comment(request, marker_uid: uuid.UUID):
    try:
        marker = Marker.objects.get(uid=marker_uid)
    except Marker.DoesNotExist:
        raise Http404

    if request.method == 'GET':
        return JsonResponse({'maker': marker.uid, 'comment': marker.comment, 'status': 'OK'})
    elif request.method == 'POST':
        try:
            comment = json.loads(request.body)['comment']
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'post body must be json object with field \'comment\''}, status=400)

        marker.comment = comment
        marker.save()
        return JsonResponse({'maker': marker.uid, 'status': 'OK'})
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])


@http.require_POST
@csrf.csrf_exempt
@marker_api
def update_wrong_status(request, marker_uid: uuid.UUID):
    """request.body is json object {marker_uid, key, wrong} """
    try:
        req = json.loads(request.body)
        key, wrong = operator.itemgetter('key', 'wrong')(req)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'post body must be json'}, status=400)
    except KeyError:
        return JsonResponse({'error': 'post body must contain: \'key\', \'wrong\''}, status=400)
    if not isinstance(wrong, bool):
        return JsonResponse({'error': '\'wrong\' must be boolean'}, status=400)

    try:
        target = MarkerVariable.objects.get(marker__uid=marker_uid, key=key)
    except MarkerVariable.DoesNotExist:
        raise Http404

    target.wrong = wrong
    target.save()

    rep = {'marker': target.marker_id, 'key': target.key, 'wrong': target.wrong}
    return JsonResponse(rep)
