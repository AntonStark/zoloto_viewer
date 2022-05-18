import collections
import json
import operator
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.decorators import csrf, http
from django.utils.decorators import method_decorator

from zoloto_viewer.infoplan.models import Marker, MarkerComment, MarkerFingerpost, MarkerVariable, CaptionPlacement
from zoloto_viewer.infoplan.utils import variable_transformations as transformations
from zoloto_viewer.viewer.models import Layer, Page, Project, LayerGroup


@http.require_GET
def ping_api(request):
    return JsonResponse({'status': 'OK'}, status=200)


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
    marker.layer.save()     # to update layer date_updated
    rep = marker.to_json(layer=True, layer_kind=True, page=True)
    return JsonResponse(rep)


@login_required
@http.require_POST
@csrf.csrf_exempt
def create_marker_clipboard(request):
    fields_ = ('project', 'page', 'clipboard_uuid')
    try:
        req = json.loads(request.body)
        project, page, original_markers_uuids = operator.itemgetter(*fields_)(req)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'request body must be json'}, status=400)
    except KeyError:
        return JsonResponse({'error': 'json object must contain fields: ' + ', '.join(fields_)}, status=400)

    project = get_object_or_404(Project, uid=uuid.UUID(project))
    page = get_object_or_404(Page, project=project, code=page)

    markers_created = []
    for marker_uid in original_markers_uuids:
        try:
            m = Marker.objects.get(uid=uuid.UUID(marker_uid))
        except Marker.DoesNotExist:     # just skip bad uuid
            continue
        mc = m.copy(floor=page)
        mc.layer.save()     # to update layer date_updated
        markers_created.append(mc)

    rep = {
        'created': [m.to_json(layer=True, layer_kind=True, page=True) for m in markers_created]
    }
    return JsonResponse(rep)


@method_decorator(csrf.csrf_exempt, name='dispatch')
class MarkerView(View):
    @method_decorator(marker_api)
    def get(self, request, marker_uid: uuid.UUID):
        marker = get_object_or_404(Marker, uid=marker_uid)

        is_pretty = request.GET.get('pretty')
        filters = [
            transformations.HideMasterPageLine(),
            transformations.UnescapeTabs(),
            transformations.NewlinesToBr(),
            transformations.ReplacePictCodes()
        ] if is_pretty else []

        return JsonResponse(marker.serialize(filters))

    @method_decorator(login_required)
    @method_decorator(marker_api)
    def patch(self, request, marker_uid: uuid.UUID):
        """Update marker position attributes: pos_x, pos_y, rotation"""
        marker = get_object_or_404(Marker, uid=marker_uid)

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
        #   ],
        #   fingerpost_metadata: {
        #       panes: [{pane_number, enabled}]
        #   } || null,
        # }
        marker = get_object_or_404(Marker, uid=marker_uid)

        try:
            req = json.loads(request.body)
            infoplan = req['infoplan']
            fingerpost_metadata = req.get('fingerpost_metadata', None)
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

        if fingerpost_metadata:
            mf = MarkerFingerpost.objects.filter(marker=marker).first()
            mf.update_from_obj(fingerpost_metadata)

        return JsonResponse(marker.serialize())

    @method_decorator(login_required)
    @method_decorator(marker_api)
    def delete(self, _, marker_uid: uuid.UUID):
        marker = get_object_or_404(Marker, uid=marker_uid)
        # to update Layer and Page date_updated attribute
        marker.layer.save()
        marker.floor.save()
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

    marker = get_object_or_404(Marker, uid=marker_uid)

    target = get_object_or_404(MarkerVariable, marker=marker, key=key)
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

    marker = get_object_or_404(Marker, uid=marker_uid)
    # always create new comment, previous comments not visible
    if comment:
        marker.markercomment_set.create(content=comment)
    if explicit_end_review:
        marker.reviewed = True
    marker.save()

    return JsonResponse(marker.to_json())


@login_required
@http.require_POST
@csrf.csrf_exempt
@marker_api
def resolve_marker_comments(request, marker_uid: uuid.UUID):
    marker = get_object_or_404(Marker, uid=marker_uid)
    for c in marker.markercomment_set.all():
        c.resolve()
    marker.reviewed = False
    marker.save()
    return JsonResponse(marker.to_json())


@method_decorator(csrf.csrf_exempt, name='dispatch')
class MarkerCaptionView(View):
    @method_decorator(marker_api)
    def get(self, request, marker_uid: uuid.UUID):
        marker = get_object_or_404(Marker, uid=marker_uid)
        try:
            caption_placement: CaptionPlacement = marker.captionplacement
        except CaptionPlacement.DoesNotExist:
            layergroup = LayerGroup.find_by_layer(marker.layer_id)
            caption_placement = CaptionPlacement.make_default(marker, layergroup)
            caption_placement.save()

        rep = marker.to_json()
        rep.update({
            'caption_placement': {
                'data': caption_placement.data,
            }
        })
        return JsonResponse(rep)

    @method_decorator(login_required)
    @method_decorator(marker_api)
    def put(self, request, marker_uid: uuid.UUID):
        """Set data of captionplacement"""
        # {
        #   data: {
        #     offset: [0,-10],
        #     rotation: 90
        #   },
        # }
        marker = get_object_or_404(Marker, uid=marker_uid)
        try:
            caption_placement: CaptionPlacement = marker.captionplacement
        except CaptionPlacement.DoesNotExist:
            layergroup = LayerGroup.find_by_layer(marker.layer_id)
            caption_placement = CaptionPlacement.make_default(marker, layergroup)
            caption_placement.save()

        try:
            req = json.loads(request.body)
            data = req['data']
        except json.JSONDecodeError:
            return JsonResponse({'error': 'request body must be json'}, status=400)
        except KeyError:
            return JsonResponse({'error': 'json object must contain field data'}, status=400)

        offset = data.get('offset', None)
        rotation = data.get('rotation', None)
        if offset is None and rotation is None:
            return JsonResponse({'error': 'data must contain fields offset OR rotation'}, status=400)

        if offset is not None:
            caption_placement.data.update({'offset': offset})
        if rotation is not None:
            caption_placement.data.update({'rotation': rotation})
        caption_placement.save()

        rep = caption_placement.to_json()
        return JsonResponse(rep)


def load_floor_captions(request):
    floor_code = request.GET['floor']
    floor = get_object_or_404(Page, code=floor_code)

    rep_data = [
        caption.to_json()
        for caption in CaptionPlacement.objects.filter(marker__floor=floor)
            .select_related('marker', 'marker__layer', 'marker__floor').all()
    ]
    rep = {
        'data': rep_data,
    }
    return JsonResponse(rep)


def project_page(request, **more_context):
    page_obj = more_context['page_obj']
    page_config = more_context['page_config']

    project = page_obj.project
    page_code_list = project.page_set.values_list('code', 'floor_caption')
    layers = project.layer_set.all().prefetch_related('color', 'kind')
    layers_with_comments_by_page = MarkerComment.layer_with_comments_by_page(project=project)
    markers_that_page = Marker.objects.filter(floor=page_obj)\
        .prefetch_related('markercomment_set')\
        .order_by()     # turn off sorting
    markers_by_layer = collections.defaultdict(list)
    for m in markers_that_page:
        markers_by_layer[m.layer_id].append(m)
    fingerpost_data = {
        mf.marker.uid: mf
        for mf in MarkerFingerpost.objects.filter(marker__floor=page_obj)
    }    # MarkerFingerpost of that page

    hidden_layers = request.GET['hide_layers'].split(' ') if 'hide_layers' in request.GET else []

    context = {
        'project': project,
        'page': page_obj,
        'page_config': page_config,
        'page_code_list': page_code_list,
        'layers': layers,
        'layers_with_comments_by_page': layers_with_comments_by_page,
        'markers_that_page': markers_that_page,
        'markers_by_layer': markers_by_layer,
        'fingerpost_data': fingerpost_data,

        'state_data': {
            'hidden_layers': hidden_layers,
        },

        'base_url': settings.BASE_URL,
        'marker_display_config': page_obj.apply_size_factor({
            'marker_scale': 1,
            'circle_radius': Marker.CIRCLE_RADIUS,
            'comment_mark_radius': Marker.COMMENT_MARK_RADIUS,
            'comment_mark_padding': Marker.COMMENT_MARK_PADDING,
        }),
    }
    template = 'infoplan/project_page_auth.html' if request.user.is_authenticated \
        else 'infoplan/project_page.html'
    return render(request, template, context=context)
