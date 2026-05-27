from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # 입실 리포트 생성
    path('move-in/<int:record_pk>/', views.generate_move_in_report, name='move_in'),

    # 퇴실 리포트 생성
    path('move-out/<int:record_pk>/', views.generate_move_out_report, name='move_out'),

    # 비교 리포트 생성
    path('comparison/<int:contract_pk>/', views.generate_comparison_report, name='comparison'),

    # 리포트 이력
    path('history/<int:contract_pk>/', views.report_history, name='history'),

    # 리포트 다운로드
    path('download/<uuid:report_uuid>/', views.download_report, name='download'),

    # 공유 링크 기능
    path('share/create/<uuid:report_uuid>/', views.create_share_link, name='create_share'),
    path('share/<uuid:token>/', views.share_detail, name='share_detail'),
    path('shared/<uuid:token>/', views.shared_report_download, name='shared_download'),
    path('my-shares/', views.my_shares, name='my_shares'),
]
