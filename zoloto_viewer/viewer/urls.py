from django.contrib import admin
from django.urls import include, path
from django.shortcuts import HttpResponsePermanentRedirect

from zoloto_viewer.viewer import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    path('projects', views.view_projects, name='projects'),
    path('', lambda request: HttpResponsePermanentRedirect(redirect_to='projects')),

    path('project/', views.load_project, name='load_project'),
    path('project/<str:title>', views.project, name='project'),
    path('project/<str:title>/edit', views.edit_project, name='edit_project'),
    path('project/<str:title>/remove', views.remove_project, name='remove_project'),
    path('project/<str:title>/add_layer', views.add_project_layer, name='add_project_layer'),
    path('project/<str:title>/pdf/generate/', views.rebuild_pdf_files, name='rebuild_pdf_files'),

    path('page/<str:page_code>', views.project_page, name='project_page'),

    path('api/', include('zoloto_viewer.infoplan.urls')),
]
