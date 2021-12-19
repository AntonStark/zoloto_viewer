import json

from background_task import background
from background_task.models import Task
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators import csrf, http
from django.utils import timezone

from zoloto_viewer.viewer.models import Project
from zoloto_viewer.viewer.views import parse_return_to_page_queryparam, with_layers_group_check
from zoloto_viewer.infoplan.models import MarkerVariable
from zoloto_viewer.documents.models import ProjectFile


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_counts_file(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    pf = ProjectFile.objects.generate_counts(project)
    return FileResponse(pf.file, filename=pf.public_name)


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_picts_file(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    pf = ProjectFile.objects.generate_pict_list(project)
    return FileResponse(pf.file, filename=pf.public_name)


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_vars_file(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    pf = ProjectFile.objects.look_for_fresh(project, ProjectFile.FileKinds.CSV_VARIABLES)
    if not pf:
        pf = ProjectFile.objects.generate_vars_index_file(project)
    return FileResponse(pf.file, filename=pf.public_name)


@login_required
@csrf.csrf_exempt
@http.require_GET
def get_infoplan_file(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    pf = ProjectFile.objects.look_for_fresh(project, ProjectFile.FileKinds.TAR_INFOPLAN)
    if not pf:
        pf = ProjectFile.objects.generate_infoplan_archive(project)
    return FileResponse(pf.file, filename=pf.public_name)


@login_required
@csrf.csrf_exempt
@http.require_http_methods(['GET', 'HEAD'])
@with_layers_group_check
def get_pdf_file(request, project_id):
    # with HEAD request not send file content if present
    project = get_object_or_404(Project, id=project_id)
    pf = ProjectFile.objects.look_for_fresh(project, ProjectFile.FileKinds.PDF_EXFOLIATION)

    if not pf:
        if not is_generate_pdf_task_queued(project.uid):
            generate_pdf_doc(str(project.uid), schedule=timezone.now())
        return HTTP_RETRY_LATER

    return FileResponse(pf.file, filename=pf.public_name) \
        if request.method == 'GET' \
        else HttpResponse(status=200)


def _make_retry_later_rep(timeout):
    rep = HttpResponse(status=323)
    rep['Retry-After'] = timeout
    return rep


HTTP_RETRY_LATER = _make_retry_later_rep(timeout=10)
PDF_GENERATE_TASK_NAME = 'documents__project_file__pdf'


@background(name=PDF_GENERATE_TASK_NAME)
def generate_pdf_doc(project_uid):
    project = Project.objects.get(uid=project_uid)
    ProjectFile.objects.pdf_generate_file(project)


def is_generate_pdf_task_queued(project_uid):
    return Task.objects.get_task(
        task_name=PDF_GENERATE_TASK_NAME,
        args=[str(project_uid)]
    ).exists()


@login_required
@http.require_GET
def names_edit_view(request, project_id):
    from zoloto_viewer.documents.generators.vars_index import VarsIndexFileBuilder
    project = get_object_or_404(Project, id=project_id)
    vars_collector = VarsIndexFileBuilder(project)
    # [ (number, var_count[lang_pair], lang_pair[0], lang_pair[1]) ]
    names = vars_collector.make_rows()

    context = {
        'names': names,
        'project': project,
        'return_to_page_code': parse_return_to_page_queryparam(request, project),
        'base_url': settings.BASE_URL,
    }
    template = 'documents/names_edit_page.html'
    return render(request, template, context=context)


@login_required
@csrf.csrf_exempt
@http.require_POST
def edit_names_pair(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    try:
        req = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'request body must be json'}, status=400)

    # req schema
    # req: {replace_ru, replace_en, confirmations}
    # replace_ru, replace_en: {name_old, name_new}
    # confirmations: optional {union: true} | {delete: true}
    top_fields = ('replace_ru', 'replace_en', 'confirmations')
    if not all(key in req for key in top_fields):
        return JsonResponse({
            'error': 'request object must contain fields: ' + ', '.join(top_fields)
        }, status=400)

    replace_obj_fields = ('name_old', 'name_new')
    def validate_lang_replace(replace_obj):
        return all(key in replace_obj for key in replace_obj_fields)

    for replace_key in ('replace_ru', 'replace_en'):
        if not validate_lang_replace(req[replace_key]):
            return JsonResponse({
                'error': f'{replace_key} object must contain fields: ' + ', '.join(replace_obj_fields)
            }, status=400)

    ru_old = req['replace_ru']['name_old']
    ru_new = req['replace_ru']['name_new']
    en_old = req['replace_en']['name_old']
    en_new = req['replace_en']['name_new']
    confirmations_obj = req['confirmations']

    def confirmation(mode):
        return mode in confirmations_obj and bool(confirmations_obj[mode])

    if not ru_new and not en_new:
        if not confirmation('delete'):
            return JsonResponse({'status': 'error', 'error': 'Confirmation missing'}, status=400)
        mode = 'remove'
        target_var_ids = MarkerVariable.objects.filter_var_containing(project, ru_old, en_old)
        MarkerVariable.objects.var_replace_helper(project, ru_old, ru_new, target_var_ids)
        MarkerVariable.objects.var_replace_helper(project, en_old, en_new, target_var_ids)
    else:
        change_ru = ru_new != ru_old

        ru_regex = ru_new.replace(' ', '[\t \r\n]+')
        that_ru_already = MarkerVariable.objects \
            .filter(marker__floor__project=project, value__regex=ru_regex)
        # надо различать: требуется объединения или обычная замена
        # объединение, когда такой русский (на который меняем, ru_new) уже встречается
        if change_ru and that_ru_already.exists():
            if not confirmation('union'):
                return JsonResponse({'status': 'error', 'error': 'Confirmation missing'}, status=400)
            mode = 'union'

            prefilter_var_ids = MarkerVariable.objects.filter_var_containing(project, ru_old, en_old)
            # apply replace ru_old -> ru_new and keep var_id
            replaced_ru_ids = MarkerVariable.objects.var_replace_helper(project, ru_old, ru_new, prefilter_var_ids)
            # then conditionally apply en_old -> en_new on replaced_ru_ids
            MarkerVariable.objects.var_replace_helper(project, en_old, en_new, replaced_ru_ids)
        else:
            mode = 'replace'
            prefilter_var_ids = MarkerVariable.objects.filter_var_containing(project, ru_old, en_old)

            if change_ru:
                # если ru_new != ru_old то нужно replace ru_old -> ru_new and keep var_id
                target_var_ids = MarkerVariable.objects.var_replace_helper(project, ru_old, ru_new, prefilter_var_ids)
            else:
                # если ru_new == ru_old то просто использовать префильтер
                target_var_ids = prefilter_var_ids

            MarkerVariable.objects.var_replace_helper(project, en_old, en_new, target_var_ids)

    # todo попытка замены с пустой строки на новое имя приводит к избыточным заменам
    #  нужен список использований пары переменных вида (var_id, index_ru, index_en)
    # в случае успешной замены нужны новые имена (в подтверждение), а в остальных только подтверждение режима
    rep = {
        'status': 'success',
        'mode': mode,
    }
    if mode == 'replace':
        rep.update({'result': {
            'ru': ru_new,
            'en': en_new,
        }})
    return JsonResponse(rep)
