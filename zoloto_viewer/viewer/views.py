import base64
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, Http404, HttpResponse

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

        ignore_files = set()
        for k, v in request.POST.items():
            if k.startswith('ignore_file_'):
                ignore_files.add(v)

        floor_captions = {}
        for k, v in request.POST.items():
            if k.startswith('floor_caption_'):
                enc = k[14:]
                filename = base64.decodebytes(enc.encode('utf-8')).decode('utf-8')
                floor_captions[filename] = v

        pages = []
        for f in request.FILES.values():
            if f.name in ignore_files:
                continue

            ftype = f.content_type.split('/')[0]
            if ftype == 'image':
                pages.append(Page(floor_caption=floor_captions.get(f.name, None), plan=f))

        csv_data = []               # todo handle csv

        if not pages:
            return HttpResponseBadRequest()
        proj = Project(title=title)
        proj.save()

        for p in pages:
            p.project = proj
            p.save()
        return redirect(to='project_page', page_uid=pages[0].uid)
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
