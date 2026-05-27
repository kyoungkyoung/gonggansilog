"""
Export URL 설정
"""
from django.urls import path
from . import views

app_name = 'exports'

urlpatterns = [
    # Export 옵션 페이지
    path('contract/<int:contract_id>/', views.export_options, name='options'),

    # JSON Export
    path('contract/<int:contract_id>/json/', views.export_json, name='json'),
    path('contract/<int:contract_id>/json/preview/', views.export_json_preview, name='json_preview'),

    # 이미지 ZIP Export
    path('contract/<int:contract_id>/images/', views.export_images_zip, name='images_zip'),

    # 통합 패키지 Export
    path('contract/<int:contract_id>/full/', views.export_full_package, name='full_package'),
]
