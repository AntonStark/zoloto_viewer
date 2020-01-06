from django.urls import path
from django.shortcuts import HttpResponsePermanentRedirect

from zoloto_viewer.viewer import views


urlpatterns = [
    path('projects', views.view_projects, name='projects'),
    path('', lambda request: HttpResponsePermanentRedirect(redirect_to='projects')),
    path('load_project', views.load_project, name='load_project'),

    path('project/<str:title>', views.project, name='project'),
    path('project/<str:title>/remove', views.project_remove, name='project_remove'),
    path('page/<str:page_uid>', views.project_page, name='project_page'),
]
