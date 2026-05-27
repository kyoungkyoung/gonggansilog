from django.urls import path
from . import views

app_name = 'blockchain'

urlpatterns = [
    path('contract/<int:contract_id>/finalize/', views.finalize_contract, name='finalize'),
    path('contract/<int:contract_id>/verify/', views.verify_contract_view, name='verify'),
    path('contract/<int:contract_id>/status/', views.blockchain_status, name='status'),
    path('contract/<int:contract_id>/retry/', views.retry_anchoring, name='retry'),
]
