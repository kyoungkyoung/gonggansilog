from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    path('', views.contract_list, name='list'),
    path('create/', views.contract_create, name='create'),
    path('<int:pk>/', views.contract_detail, name='detail'),
    path('<int:pk>/update/', views.contract_update, name='update'),
    path('<int:pk>/delete/', views.contract_delete, name='delete'),
    # 계약 관리 (연장/해지 요청)
    path('<int:pk>/extend/', views.contract_extend, name='extend'),
    path('<int:pk>/terminate/', views.contract_terminate, name='terminate'),
    # 변경 요청 승인/거절
    path('change-request/<int:request_id>/approve/', views.approve_change_request, name='approve_change_request'),
    path('change-request/<int:request_id>/reject/', views.reject_change_request, name='reject_change_request'),
    path('change-request/<int:request_id>/mark-read/', views.mark_request_as_read, name='mark_request_as_read'),
    # 초대 관련
    path('<int:pk>/create-invitation/', views.create_invitation, name='create_invitation'),
    path('invitation/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
    # 파일 마스킹 관련 API
    path('api/upload-temp-file/', views.upload_temp_contract_file, name='upload_temp_file'),
    path('api/process-masking/', views.process_contract_masking, name='process_masking'),
    # 템플릿 API
    path('api/templates/', views.get_templates_api, name='get_templates'),
]
