from django.urls import path
from . import views

app_name = 'japan'

urlpatterns = [
    # 일본 계약 확장 정보 수정
    path('contract/<int:contract_pk>/extension/', views.edit_japan_extension, name='edit_extension'),

    # 원상회복 항목 API
    path('api/restoration-items/', views.restoration_items_api, name='restoration_items_api'),

    # 원상회복 가이드
    path('contract/<int:contract_pk>/restoration-guide/', views.restoration_guide, name='restoration_guide'),
]
