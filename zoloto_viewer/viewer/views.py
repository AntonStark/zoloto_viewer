from django.shortcuts import render
from zoloto_viewer.viewer.models import Project


def view_projects(request):
    context = {
        'projects': Project.objects.all(),
    }
    return render(request, 'viewer/view_projects.html', context=context)


def load_project(request):
    if request.method == 'POST':
        print(request.POST, request.FILES)
    else:
        return render(request, 'viewer/load_project.html')
