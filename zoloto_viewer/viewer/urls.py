from django.urls import path
from django.shortcuts import HttpResponsePermanentRedirect

from zoloto_viewer.viewer import views


urlpatterns = [
    path('projects', views.view_projects, name='projects'),
    path('', lambda request: HttpResponsePermanentRedirect(redirect_to='projects')),
    path('load_project', views.load_project, name='load_project'),
]
