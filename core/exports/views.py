"""
Export 뷰 모듈
- JSON Export
- 이미지 ZIP Export
- 통합 패키지 Export
"""
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _

from contracts.models import Contract
from .services import ContractExportService


def _check_contract_access(user, contract):
    """사용자가 계약에 접근 권한이 있는지 확인"""
    if user.is_staff:
        return True
    if contract.landlord == user:
        return True
    if contract.tenant == user:
        return True
    return False


@login_required
@require_GET
def export_json(request, contract_id):
    """
    계약 데이터 JSON Export

    Args:
        contract_id: 계약 ID

    Returns:
        JSON 파일 다운로드 응답
    """
    contract = get_object_or_404(Contract, pk=contract_id)

    # 접근 권한 확인
    if not _check_contract_access(request.user, contract):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    # JSON 생성
    service = ContractExportService(contract)
    data = service.export_json()

    # JSON 응답 생성
    response = HttpResponse(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type='application/json; charset=utf-8'
    )

    # 파일명 설정
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"contract_{contract_id}_{timestamp}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@login_required
@require_GET
def export_images_zip(request, contract_id):
    """
    계약 관련 모든 이미지 ZIP Export

    Args:
        contract_id: 계약 ID

    Returns:
        ZIP 파일 다운로드 응답
    """
    contract = get_object_or_404(Contract, pk=contract_id)

    # 접근 권한 확인
    if not _check_contract_access(request.user, contract):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    # ZIP 생성
    service = ContractExportService(contract)
    zip_buffer = service.export_images_zip()

    # ZIP 응답 생성
    response = HttpResponse(
        zip_buffer.getvalue(),
        content_type='application/zip'
    )

    # 파일명 설정
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"contract_{contract_id}_images_{timestamp}.zip"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@login_required
@require_GET
def export_full_package(request, contract_id):
    """
    JSON + 이미지 + PDF 통합 패키지 Export

    Args:
        contract_id: 계약 ID

    Returns:
        ZIP 파일 다운로드 응답
    """
    contract = get_object_or_404(Contract, pk=contract_id)

    # 접근 권한 확인
    if not _check_contract_access(request.user, contract):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    # 통합 패키지 생성
    service = ContractExportService(contract)
    include_pdf = request.GET.get('include_pdf', 'true').lower() == 'true'
    zip_buffer = service.export_full_package(include_pdf=include_pdf)

    # ZIP 응답 생성
    response = HttpResponse(
        zip_buffer.getvalue(),
        content_type='application/zip'
    )

    # 파일명 설정
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"contract_{contract_id}_full_package_{timestamp}.zip"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@login_required
def export_options(request, contract_id):
    """
    Export 옵션 선택 페이지

    Args:
        contract_id: 계약 ID
    """
    contract = get_object_or_404(Contract, pk=contract_id)

    # 접근 권한 확인
    if not _check_contract_access(request.user, contract):
        messages.error(request, _('You do not have permission to access this contract.'))
        return redirect('contracts:list')

    # 통계 정보 수집
    records_count = contract.records.count()
    photos_count = sum(r.photos.count() for r in contract.records.all())
    recordings_count = contract.recordings.count()

    # PDF 리포트 수
    from core.reports.models import GeneratedReport
    reports_count = GeneratedReport.objects.filter(
        contract=contract,
        status='COMPLETED'
    ).count()

    context = {
        'contract': contract,
        'records_count': records_count,
        'photos_count': photos_count,
        'recordings_count': recordings_count,
        'reports_count': reports_count,
    }

    return render(request, 'exports/export_options.html', context)


@login_required
@require_GET
def export_json_preview(request, contract_id):
    """
    JSON Export 미리보기 (웹에서 확인용)

    Args:
        contract_id: 계약 ID

    Returns:
        JSON 데이터
    """
    contract = get_object_or_404(Contract, pk=contract_id)

    # 접근 권한 확인
    if not _check_contract_access(request.user, contract):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    # JSON 생성
    service = ContractExportService(contract)
    data = service.export_json()

    return JsonResponse(data, json_dumps_params={'ensure_ascii': False, 'indent': 2})
