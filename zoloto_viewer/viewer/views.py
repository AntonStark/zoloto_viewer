from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, Http404

from zoloto_viewer.viewer.models import Project, Page


def view_projects(request):
    context = {
        'projects': Project.objects.all(),
    }
    return render(request, 'viewer/view_projects.html', context=context)


def load_project(request):
    if request.method == 'POST':
        try:
            title = request.POST['title']       # todo use validate_slug on title
        except KeyError:
            return HttpResponseBadRequest()
        proj = Project(title=title)
        proj.save()
        default_page = Page.objects.get(project=proj, floor_caption='')
        return redirect(to='project_page', page_uid=default_page.uid)
    else:
        return render(request, 'viewer/load_project.html')


def project(request, title):
    try:
        proj = Project.objects.get(title=title)
    except Project.DoesNotExist:
        raise Http404

    pages = Page.objects.filter(project=proj)
    if not pages.exists():
        raise Http404

    return redirect(to='project_page', page_uid=pages.first().uid)


def project_page(request, page_uid):
    try:
        page = Page.objects.get(uid=page_uid)
    except Page.DoesNotExist:
        raise Http404
    project = page.project
    context = {
        'project': project,
    }
    return render(request, 'viewer/project_page.html', context=context)
