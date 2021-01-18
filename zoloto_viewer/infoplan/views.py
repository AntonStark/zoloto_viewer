import json
import operator
import uuid
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.decorators import http, csrf
from django.utils.decorators import method_decorator

from zoloto_viewer.infoplan.models import Marker, MarkerVariable
from zoloto_viewer.viewer.models import Layer, Page, Project


def marker_api(method):
    def _decorated_method(request, marker_uid):
        try:
            uid = uuid.UUID(marker_uid)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'after /marker/ must be uuid'}, status=400)
        return method(request, uid)
    return _decorated_method


@http.require_POST
@csrf.csrf_exempt
def create_marker(request):
    fields_ = ('project', 'page', 'layer', 'position')
    try:
        req = json.loads(request.body)
        project, page, layer, position = operator.itemgetter(*fields_)(req)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'post body must be json'}, status=400)
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
    def get(self, _, marker_uid: uuid.UUID):
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
            'layer': {'title': marker.layer.title, 'color': marker.layer.color.hex_code}
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
        return JsonResponse({'error': 'post body must be json'}, status=400)
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
        marker.deduce_correctness()
        marker.save()

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
        return JsonResponse({'error': 'post body must be json'}, status=400)
    except KeyError:
        return JsonResponse({'error': 'json object must contain fields: ' + ', '.join(fields_)}, status=400)
    explicit_end_review = exit_type == 'button'

    try:
        marker = Marker.objects.get(uid=marker_uid)
    except Marker.DoesNotExist:
        raise Http404
    marker.comment = comment
    marker.deduce_correctness(explicit_end_review)
    marker.save()

    return JsonResponse(marker.to_json())


def project_page(request, **more_context):
    page_obj = more_context['page_obj']

    pdf_original = more_context['pdf_original']
    pdf_reviewed = more_context['pdf_reviewed']
    pdf_created_time = more_context['pdf_created_time']
    pdf_refresh_timeout = more_context['pdf_refresh_timeout']

    project = page_obj.project
    page_code_list = project.page_set.values_list('code', 'floor_caption')
    layers = project.layer_set.values_list('title', 'color__hex_code')
    layers_visible = set(request.GET.getlist('layer'))
    markers_by_layer = {L: page_obj.marker_set.filter(layer=L)
                        for L in project.layer_set.all()}

    context = {
        'project': project,
        'page': page_obj,
        'page_code_list': page_code_list,
        'layers': layers,
        'layers_visible': layers_visible,
        'markers_by_layer': markers_by_layer,
        'base_url': settings.BASE_URL,

        'pdf_original': pdf_original,
        'pdf_reviewed': pdf_reviewed,
        'pdf_created_time': pdf_created_time,
        'pdf_refresh_timeout': str(pdf_refresh_timeout),
    }
    template = 'infoplan/project_page_auth.html' if request.user.is_authenticated \
        else 'infoplan/project_page.html'
    return render(request, template, context=context)
