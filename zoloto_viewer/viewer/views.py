from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect

from zoloto_viewer.viewer import form_stuff
from zoloto_viewer.viewer.models import Project, Layer, Page


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

    pages_data, _ = form_stuff.parse_pages(request.POST, request.FILES)
    layer_files, additional_files = form_stuff.parse_csv(request.POST, request.FILES)
    if not pages_data or not pages_data:
        return redirect('load_project')

    proj = Project(title=title)
    proj.save()

    proj.store_pages(pages_data)
    proj.create_layers(layer_files)
    proj.update_additional_files(additional_files)
    # todo client_last_modified_date must be provided by client

    return redirect('projects')


@login_required
def edit_project(request, title):
    try:
        project = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404
    if request.method != 'POST':
        pages = Page.objects.filter(project=project)
        layers = Layer.objects.filter(project=project)
        context = {
            'project': project,
            'pages_list': map(Page.serialize, pages),
            'csv_list': list(map(Layer.serialize, layers)) + project.additional_files_info(),
        }
        return render(request, 'viewer/edit_project.html', context=context)

    title = request.POST['title']
    if project.title != title:
        project.title = title
        project.save()

    csv_to_delete, pages_to_delete = form_stuff.files_to_delete(request.POST)
    for csv_name in csv_to_delete:
        Layer.remove_from_project(project, csv_name)
    for page_name in pages_to_delete:
        Page.remove_from_project(project, page_name)
    project.remove_additional_files(csv_to_delete)

    pages_data, floor_captions = form_stuff.parse_pages(request.POST, request.FILES)
    layer_files, additional_files = form_stuff.parse_csv(request.POST, request.FILES)

    errors = []
    project.store_pages(pages_data)
    try:
        project.alter_floor_captions(floor_captions)
    except IntegrityError:
        errors.append('captions not unique')
    project.create_layers(layer_files)
    project.update_additional_files(additional_files)

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

    return redirect(to='project_page', page_uid=first_page.uid)


@login_required
def project_remove(request, title):
    try:
        proj = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    proj.delete()
    return redirect(to='projects')


def project_page(request, page_uid):
    try:
        page = Page.objects.get(uid=page_uid)
    except Page.DoesNotExist:
        raise Http404

    project = page.project
    page_uid_list = Page.objects.filter(project=project).values_list('uid', flat=True)

    context = {
        'project': project,
        'page': page,
        'page_uid_list': page_uid_list,
    }
    template = 'viewer/project_page_auth.html' if request.user.is_authenticated else 'viewer/project_page.html'
    return render(request, template, context=context)
