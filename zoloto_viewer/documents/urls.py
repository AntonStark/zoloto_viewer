from django.urls import path

from . import views


urlpatterns = [
    path('pdf/', views.rebuild_pdf_files, name='rebuild_pdf_files'),
    path('vars/', views.get_vars_file, name='get_vars_file'),
    path('count/', views.get_counts_file, name='get_counts_file'),
    path('picts/', views.get_picts_file, name='get_picts_file'),
]
