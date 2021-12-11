from django.urls import path

from . import views


urlpatterns = [
    path('pdf/', views.get_pdf_file, name='get_pdf_file'),
    path('vars/', views.get_vars_file, name='get_vars_file'),
    path('count/', views.get_counts_file, name='get_counts_file'),
    path('picts/', views.get_picts_file, name='get_picts_file'),
    path('infoplan/', views.get_infoplan_file, name='get_infoplan_file'),
    path('names/', views.names_edit_view, name='names_edit_view')
]
