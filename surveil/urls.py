from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('camera/<str:token>/', views.camera_mode, name='camera_mode'),
    path('videos/', views.video_gallery, name='videos'),
    path('device/pair/', views.device_pair, name='device_pair'),
    # APIs
    path('api/heartbeat/<str:token>/', views.api_heartbeat, name='api_heartbeat'),
    path('api/upload/<str:token>/', views.api_upload, name='api_upload'),
    path('api/device/<str:token>/status/', views.api_device_status, name='api_device_status'),
    path('api/device/<str:token>/location/', views.api_device_location, name='api_device_location'),
    path('api/motion/<str:token>/', views.api_motion_event, name='api_motion_event'),
    path('api/toggle_recording/<int:device_id>/', views.api_toggle_recording, name='api_toggle_recording'),
]
