from django.urls import path

from zoloto_viewer.infoplan import views


urlpatterns = [
    path('ping/', views.ping_api, name='ping_api'),
    path('marker/', views.create_marker, name='create_marker'),
    path('marker/from_clipboard/', views.create_marker_clipboard, name='create_marker_clipboard'),
    path('marker/fetch_many/', views.fetch_markers_bulk, name='fetch_markers_bulk'),
    path('marker/submit_many/', views.submit_markers_bulk, name='submit_markers_bulk'),
    path('marker/<str:marker_uid>', views.MarkerView.as_view(), name='marker_get_data'),
    path('marker/<str:marker_uid>/variable/', views.update_wrong_status, name='variable_alter_wrong'),
    path('marker/<str:marker_uid>/review/', views.load_marker_review, name='marker_load_review'),
    path('marker/<str:marker_uid>/resolve_all_comments/', views.resolve_marker_comments,
         name='resolve_marker_comments'),
    path('marker/<str:marker_uid>/caption/', views.MarkerCaptionView.as_view(), name='marker_caption_placement'),
    path('markers/caption/', views.load_floor_captions, name='load_floor_captions'),
]
