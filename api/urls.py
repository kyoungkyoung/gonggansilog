from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'contracts', views.ContractViewSet, basename='contract')
router.register(r'recordings', views.RecordingViewSet, basename='recording')
router.register(r'templates', views.TemplateViewSet, basename='template')

urlpatterns = [
    # Auth
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', views.register, name='register'),
    path('auth/me/', views.me, name='me'),
    path('auth/profile/', views.update_profile, name='update_profile'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Contract nested resources
    path('contracts/<int:contract_id>/records/', views.RecordViewSet.as_view({
        'get': 'list', 'post': 'create'
    }), name='contract-records'),
    path('contracts/<int:contract_id>/defects/', views.DefectViewSet.as_view({
        'get': 'list', 'post': 'create'
    }), name='contract-defects'),
    path('contracts/<int:contract_id>/repairs/', views.RepairViewSet.as_view({
        'get': 'list', 'post': 'create'
    }), name='contract-repairs'),
    path('contracts/<int:contract_id>/expenses/', views.ExpenseViewSet.as_view({
        'get': 'list', 'post': 'create'
    }), name='contract-expenses'),
    path('contracts/<int:contract_id>/expenses/summary/', views.ExpenseViewSet.as_view({
        'get': 'summary'
    }), name='contract-expenses-summary'),

    # Record actions
    path('records/<int:pk>/', views.RecordViewSet.as_view({
        'get': 'retrieve'
    }), name='record-detail'),
    path('records/<int:pk>/upload-photos/', views.RecordViewSet.as_view({
        'post': 'upload_photos'
    }), name='record-upload-photos'),
    path('records/<int:pk>/save-responses/', views.RecordViewSet.as_view({
        'post': 'save_responses'
    }), name='record-save-responses'),
    path('records/<int:pk>/submit/', views.RecordViewSet.as_view({
        'post': 'submit'
    }), name='record-submit'),
    path('records/<int:pk>/approve/', views.RecordViewSet.as_view({
        'post': 'approve'
    }), name='record-approve'),

    # Defect actions
    path('defects/<int:pk>/', views.DefectViewSet.as_view({
        'get': 'retrieve'
    }), name='defect-detail'),
    path('defects/<int:pk>/respond/', views.DefectViewSet.as_view({
        'post': 'respond'
    }), name='defect-respond'),

    # Repair actions
    path('repairs/<int:pk>/', views.RepairViewSet.as_view({
        'get': 'retrieve'
    }), name='repair-detail'),
    path('repairs/<int:pk>/update-status/', views.RepairViewSet.as_view({
        'post': 'update_status'
    }), name='repair-update-status'),
    path('repairs/<int:pk>/comment/', views.RepairViewSet.as_view({
        'post': 'comment'
    }), name='repair-comment'),

    # Expenses
    path('expenses/<int:pk>/', views.ExpenseViewSet.as_view({
        'get': 'retrieve'
    }), name='expense-detail'),

    # Reports
    path('reports/generate/<int:record_pk>/', views.generate_report, name='generate-report'),
    path('reports/<uuid:report_uuid>/download/', views.download_report, name='download-report'),

    # Router URLs
    path('', include(router.urls)),
]
