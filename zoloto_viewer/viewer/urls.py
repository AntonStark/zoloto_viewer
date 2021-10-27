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
    path('project/<int:project_id>/', views.project, name='project'),
    path('project/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('project/<int:project_id>/remove/', views.remove_project, name='remove_project'),
    path('project_code/', views.generate_project_code, name='generate_project_code'),

    path('project/<int:project_id>/add_layer', views.add_project_layer, name='add_project_layer'),
    path('project/<int:project_id>/edit_layer/<str:layer_title>', views.edit_project_layer,
         name='edit_project_layer'),
    path('project/<int:project_id>/group_layers', views.setup_layer_groups, name='setup_layer_groups'),

    path('page/<str:page_code>/', views.project_page, name='project_page'),
    path('page/<str:page_code>/edit/', views.edit_project_page, name='edit_project_page'),

    path('api/', include('zoloto_viewer.infoplan.urls')),
    path('project/<int:project_id>/docs/', include('zoloto_viewer.documents.urls')),
]
