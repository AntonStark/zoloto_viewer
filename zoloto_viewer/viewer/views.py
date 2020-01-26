from django.http import Http404
from django.shortcuts import render, redirect

from zoloto_viewer.viewer import form_stuff
from zoloto_viewer.viewer.models import Project, Layer, Page


def view_projects(request):
    context = {
        'projects': Project.objects.all().order_by('-created'),
    }
    return render(request, 'viewer/view_projects.html', context=context)


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
    csv_data = form_stuff.parse_csv(request.POST, request.FILES)
    if not pages_data or not pages_data:
        return redirect('load_project')

    proj = Project(title=title)
    proj.save()

    proj.store_pages(pages_data)
    proj.create_layers(csv_data)
    # todo client_last_modified_date must be provided by client

    return redirect('projects')


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
            'csv_list': map(Layer.serialize, layers),       # todo include non-layer csv files (from project attrs?)
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

    pages_data, floor_captions = form_stuff.parse_pages(request.POST, request.FILES)
    csv_data = form_stuff.parse_csv(request.POST, request.FILES)

    project.store_pages(pages_data)
    project.alter_floor_captions(floor_captions)
    project.create_layers(csv_data)
    return redirect('projects')


def project(request, title):
    try:
        proj = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    first_page = proj.first_page()
    if not first_page:
        raise Http404

    return redirect(to='project_page', page_uid=first_page.uid)


def project_remove(request, title):
    try:
        proj = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    proj.delete()       # todo remove files too
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
    return render(request, 'viewer/project_page.html', context=context)
