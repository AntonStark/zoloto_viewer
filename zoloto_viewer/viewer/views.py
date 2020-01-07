import base64
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, Http404

from zoloto_viewer.viewer.models import Project, Page


def view_projects(request):
    context = {
        'projects': Project.objects.all().order_by('-created'),
    }
    return render(request, 'viewer/view_projects.html', context=context)


def parse_pages(req_post, req_files):
    ignore_files = set()
    floor_captions = {}
    for k, v in req_post.items():
        if k.startswith('ignore_file_'):
            ignore_files.add(v)
        elif k.startswith('floor_caption_'):
            encoded = k[14:]
            filename = base64.decodebytes(encoded.encode('utf-8')).decode('utf-8')
            floor_captions[filename] = v

    pages_dict = {}
    for key in req_files.keys():
        for f in req_files.getlist(key):
            if f.name in ignore_files:
                continue

            ftype = f.content_type.split('/')[0]
            name = '.'.join(f.name.split('.')[:-1])
            if ftype == 'image':
                if name in pages_dict:
                    return None
                else:
                    pages_dict[name] = (f, floor_captions.get(f.name, None))
    return pages_dict


def load_project(request):
    if request.method != 'POST':
        return render(request, 'viewer/load_project.html')

    try:
        title = request.POST['title']
        if not Project.validate_title(title):
            raise ValueError
    except (KeyError, ValueError):
        return redirect('load_project')

    pages_data = parse_pages(request.POST, request.FILES)
    if not pages_data:
        return redirect('load_project')

    csv_data = []               # todo handle csv

    proj = Project(title=title)
    proj.save()

    for name in pages_data:
        plan, floor_caption = pages_data[name]
        Page(project=proj, plan=plan, indd_floor=name, floor_caption=floor_caption).save()

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
    return render(request, 'viewer/project_page.html', context=context)
