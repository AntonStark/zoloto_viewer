from django.urls import path

from . import views


urlpatterns = [
    path('pdf/', views.rebuild_pdf_files, name='rebuild_pdf_files'),
]
