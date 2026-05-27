from django.urls import path
from . import views

app_name = 'records'

urlpatterns = [
    # 계약별 기록 목록
    path('contract/<int:contract_id>/', views.record_list, name='list'),

    # 기록 생성 (기존 - 호환성 유지)
    path('contract/<int:contract_id>/create/', views.record_create, name='create'),

    # 임대인: 기록 생성 + 마감일 설정
    path('contract/<int:contract_id>/create-record/', views.landlord_create_record, name='landlord_create'),

    # 임차인: 기록 등록 요청
    path('contract/<int:contract_id>/request-record/', views.tenant_request_record, name='tenant_request'),

    # 기록 상세
    path('<int:pk>/', views.record_detail, name='detail'),

    # 입실/퇴실 비교
    path('contract/<int:contract_id>/compare/', views.record_compare, name='compare'),

    # 기록 승인/반려 (기존 - 호환성 유지)
    path('<int:pk>/approve/', views.record_approve, name='approve'),

    # 임대인: 임차인 요청 승인 (REQUESTED -> OPEN)
    path('<int:pk>/approve-request/', views.approve_tenant_request, name='approve_request'),

    # 임대인: 최종 승인/반려
    path('<int:pk>/final-approve/', views.final_approve, name='final_approve'),

    # 임차인: 제출
    path('<int:pk>/submit/', views.submit_record, name='submit'),

    # 사진 추가
    path('<int:pk>/add-photos/', views.add_photos, name='add_photos'),

    # 사진 삭제
    path('photo/<int:photo_id>/delete/', views.delete_photo, name='delete_photo'),

    # 사진 수정
    path('photo/<int:photo_id>/update/', views.update_photo, name='update_photo'),

    # 사진 개별 승인
    path('photo/<int:photo_id>/approve/', views.approve_photo, name='approve_photo'),

    # 사진 개별 반려
    path('photo/<int:photo_id>/reject/', views.reject_photo, name='reject_photo'),

    # 알림 읽음 처리
    path('<int:pk>/mark-read/', views.mark_record_read, name='mark_read'),

    # 템플릿 구조 API
    path('<int:pk>/api/template-structure/', views.get_template_structure_api, name='template_structure'),

    # 하자 통지
    path('contract/<int:contract_id>/defects/', views.defect_list, name='defect_list'),
    path('contract/<int:contract_id>/defects/create/', views.defect_create, name='defect_create'),
    path('defect/<int:pk>/', views.defect_detail, name='defect_detail'),
    path('defect/<int:pk>/respond/', views.defect_respond, name='defect_respond'),

    # 수리 요청
    path('contract/<int:contract_id>/repairs/', views.repair_list, name='repair_list'),
    path('contract/<int:contract_id>/repairs/create/', views.repair_create, name='repair_create'),
    path('repair/<int:pk>/', views.repair_detail, name='repair_detail'),
    path('repair/<int:pk>/update-status/', views.repair_update_status, name='repair_update_status'),
    path('repair/<int:pk>/comment/', views.repair_add_comment, name='repair_add_comment'),

    # 비용/영수증
    path('contract/<int:contract_id>/expenses/', views.expense_list, name='expense_list'),
    path('contract/<int:contract_id>/expenses/create/', views.expense_create, name='expense_create'),
    path('expense/<int:pk>/', views.expense_detail, name='expense_detail'),
]
