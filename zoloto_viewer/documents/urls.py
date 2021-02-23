from django.urls import path

from . import views


urlpatterns = [
    path('project/<str:title>/kind/<str:kind>', views.get_project_doc, name='get_project_doc'),
    path('project/<str:title>/kind/pdf', views.rebuild_pdf_files, name='rebuild_pdf_files'),
]
