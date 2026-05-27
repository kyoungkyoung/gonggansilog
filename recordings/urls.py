from django.urls import path
from . import views

app_name = 'recordings'

urlpatterns = [
    path('', views.recording_list, name='list'),
    path('create/', views.recording_create, name='create'),
    path('<int:pk>/', views.recording_detail, name='detail'),
    # 계약 연결 변경 기능 제거 (보안상 이유로 변경 불가)
    # path('<int:pk>/update-contract/', views.recording_update_contract, name='update_contract'),
    path('<int:pk>/delete/', views.recording_delete, name='delete'),
    path('<int:pk>/download-mp3/', views.recording_download_mp3, name='download_mp3'),
    path('<int:pk>/consent/', views.consent_recording, name='consent'),
    path('api/save/', views.save_recording, name='save'),
]
