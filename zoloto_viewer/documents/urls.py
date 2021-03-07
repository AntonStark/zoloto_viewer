from django.urls import path

from . import views


urlpatterns = [
    path('count/', views.get_counts_file, name='get_counts_file'),
    path('pdf/', views.rebuild_pdf_files, name='rebuild_pdf_files'),
]
