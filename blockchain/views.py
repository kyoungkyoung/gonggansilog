"""
블록체인 뷰
- 계약 확정 (finalize)
- 진위 확인 (verify)
- 블록체인 상태 조회 (AJAX)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from django.utils.translation import gettext as _

from contracts.models import Contract
from .services import (
    generate_contract_hash,
    anchor_to_blockchain,
    verify_contract,
    can_finalize_contract,
    get_klaytn_scope_url,
)


@login_required
def finalize_contract(request, contract_id):
    """계약 확정 및 블록체인 앵커링"""
    contract = get_object_or_404(Contract, pk=contract_id)

    # 권한 확인 (임대인 또는 관리자)
    if request.user != contract.landlord and not request.user.is_staff:
        messages.error(request, _('계약을 확정할 권한이 없습니다.'))
        return redirect('contracts:detail', pk=contract_id)

    # 확정 가능 여부 확인
    can_finalize, reasons = can_finalize_contract(contract, request.user)

    if request.method == 'POST':
        if not can_finalize:
            for reason in reasons:
                messages.error(request, reason)
            return redirect('blockchain:finalize', contract_id=contract_id)

        # 블록체인 상태를 PENDING으로 변경
        contract.blockchain_status = 'PENDING'
        contract.save(update_fields=['blockchain_status'])

        try:
            # 해시 생성
            final_hash, metadata = generate_contract_hash(contract)

            # KAS API로 앵커링
            result = anchor_to_blockchain(contract.id, final_hash)

            if result['success']:
                # 성공 - 계약 확정 및 블록체인 정보 저장
                contract.is_finalized = True
                contract.finalized_at = timezone.now()
                contract.blockchain_status = 'ANCHORED'
                contract.blockchain_tx_hash = result['tx_hash']
                contract.blockchain_anchored_at = timezone.now()
                contract.blockchain_final_hash = final_hash
                contract.blockchain_metadata = metadata
                contract.save()

                messages.success(
                    request,
                    _('계약이 확정되었습니다. 블록체인 트랜잭션: %(tx_hash)s...') % {'tx_hash': result['tx_hash'][:20]}
                )
                return redirect('contracts:detail', pk=contract_id)
            else:
                # 실패
                contract.blockchain_status = 'FAILED'
                contract.save(update_fields=['blockchain_status'])

                messages.error(
                    request,
                    _('블록체인 앵커링 실패: %(error)s') % {'error': result.get('error', _('알 수 없는 오류'))}
                )
                return redirect('blockchain:finalize', contract_id=contract_id)

        except ValueError as e:
            contract.blockchain_status = 'FAILED'
            contract.save(update_fields=['blockchain_status'])
            messages.error(request, str(e))
            return redirect('blockchain:finalize', contract_id=contract_id)

        except Exception as e:
            contract.blockchain_status = 'FAILED'
            contract.save(update_fields=['blockchain_status'])
            messages.error(request, _('오류가 발생했습니다: %(error)s') % {'error': str(e)})
            return redirect('blockchain:finalize', contract_id=contract_id)

    # GET 요청 - 확정 확인 페이지 표시
    # 파일 통계 계산
    file_stats = {
        'contract_file': bool(contract.contract_file),
        'photo_count': sum(r.photos.count() for r in contract.records.all()),
        'recording_count': contract.recordings.count(),
    }

    # 입실 기록 정보
    move_in_record = contract.records.filter(record_type='MOVE_IN').first()

    context = {
        'contract': contract,
        'can_finalize': can_finalize,
        'reasons': reasons,
        'file_stats': file_stats,
        'move_in_record': move_in_record,
    }

    return render(request, 'blockchain/finalize_contract.html', context)


@login_required
def verify_contract_view(request, contract_id):
    """계약 진위 확인"""
    contract = get_object_or_404(Contract, pk=contract_id)

    # 권한 확인 (계약 당사자 또는 관리자)
    if (request.user != contract.landlord and
        request.user != contract.tenant and
        not request.user.is_staff):
        messages.error(request, _('이 계약의 진위를 확인할 권한이 없습니다.'))
        return redirect('contracts:detail', pk=contract_id)

    # 블록체인에 등록되지 않은 경우
    if not contract.is_finalized or not contract.blockchain_final_hash:
        messages.warning(request, _('아직 블록체인에 등록되지 않은 계약입니다.'))
        return redirect('contracts:detail', pk=contract_id)

    # 검증 수행
    verification_result = verify_contract(contract)

    # Klaytn Scope URL
    scope_url = None
    if contract.blockchain_tx_hash:
        scope_url = get_klaytn_scope_url(contract.blockchain_tx_hash)

    context = {
        'contract': contract,
        'result': verification_result,
        'scope_url': scope_url,
    }

    return render(request, 'blockchain/verify_contract.html', context)


@login_required
@require_http_methods(["GET"])
def blockchain_status(request, contract_id):
    """블록체인 상태 조회 (AJAX)"""
    contract = get_object_or_404(Contract, pk=contract_id)

    # 권한 확인
    if (request.user != contract.landlord and
        request.user != contract.tenant and
        not request.user.is_staff):
        return JsonResponse({'error': _('권한이 없습니다.')}, status=403)

    # Klaytn Scope URL
    scope_url = None
    if contract.blockchain_tx_hash:
        scope_url = get_klaytn_scope_url(contract.blockchain_tx_hash)

    data = {
        'status': contract.blockchain_status,
        'status_display': dict(Contract.BLOCKCHAIN_STATUS_CHOICES).get(
            contract.blockchain_status, _('알 수 없음')
        ),
        'tx_hash': contract.blockchain_tx_hash,
        'anchored_at': contract.blockchain_anchored_at.isoformat() if contract.blockchain_anchored_at else None,
        'is_finalized': contract.is_finalized,
        'finalized_at': contract.finalized_at.isoformat() if contract.finalized_at else None,
        'scope_url': scope_url,
    }

    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def retry_anchoring(request, contract_id):
    """앵커링 재시도 (실패한 경우)"""
    contract = get_object_or_404(Contract, pk=contract_id)

    # 권한 확인
    if request.user != contract.landlord and not request.user.is_staff:
        return JsonResponse({'error': _('권한이 없습니다.')}, status=403)

    # 실패 상태인 경우에만 재시도 가능
    if contract.blockchain_status != 'FAILED':
        return JsonResponse({'error': _('재시도할 수 없는 상태입니다.')}, status=400)

    # 상태를 PENDING으로 변경
    contract.blockchain_status = 'PENDING'
    contract.save(update_fields=['blockchain_status'])

    try:
        # 해시 생성
        final_hash, metadata = generate_contract_hash(contract)

        # KAS API로 앵커링
        result = anchor_to_blockchain(contract.id, final_hash)

        if result['success']:
            contract.is_finalized = True
            contract.finalized_at = timezone.now()
            contract.blockchain_status = 'ANCHORED'
            contract.blockchain_tx_hash = result['tx_hash']
            contract.blockchain_anchored_at = timezone.now()
            contract.blockchain_final_hash = final_hash
            contract.blockchain_metadata = metadata
            contract.save()

            return JsonResponse({
                'success': True,
                'tx_hash': result['tx_hash'],
                'message': _('블록체인 앵커링 성공')
            })
        else:
            contract.blockchain_status = 'FAILED'
            contract.save(update_fields=['blockchain_status'])

            return JsonResponse({
                'success': False,
                'error': result.get('error', _('앵커링 실패'))
            })

    except Exception as e:
        contract.blockchain_status = 'FAILED'
        contract.save(update_fields=['blockchain_status'])

        return JsonResponse({
            'success': False,
            'error': str(e)
        })
