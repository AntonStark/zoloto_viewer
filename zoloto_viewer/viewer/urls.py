from django.contrib import admin
from django.urls import include, path
from django.shortcuts import HttpResponsePermanentRedirect

from zoloto_viewer.viewer import api_views, views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    path('projects', views.view_projects, name='projects'),
    path('', lambda request: HttpResponsePermanentRedirect(redirect_to='projects')),

    path('project/', views.load_project, name='load_project'),
    path('project/<str:title>', views.project, name='project'),
    path('project/<str:title>/edit', views.edit_project, name='edit_project'),
    path('project/<str:title>/remove', views.remove_project, name='remove_project'),

    path('page/<str:page_code>', views.project_page, name='project_page'),

    path('api/marker/<str:marker_uid>', api_views.get_marker_data, name='marker_get_data'),
    path('api/marker/<str:marker_uid>/variable/', api_views.update_wrong_status, name='variable_alter_wrong'),
    path('api/marker/<str:marker_uid>/review/', api_views.load_marker_review, name='marker_load_review'),
]
