from django.urls import path

from zoloto_viewer.infoplan import views


urlpatterns = [
    path('marker/', views.create_marker, name='create_marker'),
    path('marker/<str:marker_uid>', views.get_marker_data, name='marker_get_data'),
    path('marker/<str:marker_uid>/variable/', views.update_wrong_status, name='variable_alter_wrong'),
    path('marker/<str:marker_uid>/review/', views.load_marker_review, name='marker_load_review'),
]
