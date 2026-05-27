from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.translation import get_language, gettext as _
import json
import os
from .models import Contract, ContractInvitation
from .forms import ContractForm
from .utils import get_file_preview_data, process_masked_file


@login_required
def contract_list(request):
    """계약 목록 조회"""
    from .models import ContractChangeRequest
    from datetime import timedelta
    from django.utils import timezone

    # 임차인인 경우: 내가 등록한 계약
    # 임대인인 경우: 나와 연결된 계약
    if request.user.user_type == 'TENANT':
        contracts = Contract.objects.filter(tenant=request.user)
    else:  # LANDLORD
        contracts = Contract.objects.filter(landlord=request.user)

    # 내가 승인해야 하는 대기 중인 요청
    pending_requests = ContractChangeRequest.objects.filter(
        contract__in=contracts,
        status='PENDING'
    ).exclude(
        requested_by=request.user
    ).select_related('contract', 'requested_by').order_by('-created_at')

    # 내가 요청한 것 중 최근 처리된 요청 (24시간 이내, 읽지 않은 것)
    recent_time = timezone.now() - timedelta(hours=24)
    my_processed_requests = ContractChangeRequest.objects.filter(
        contract__in=contracts,
        requested_by=request.user,
        status__in=['APPROVED', 'REJECTED'],
        responded_at__gte=recent_time,
        is_read_by_requester=False
    ).select_related('contract', 'responded_by').order_by('-responded_at')

    return render(request, 'contracts/contract_list.html', {
        'contracts': contracts,
        'pending_requests': pending_requests,
        'my_processed_requests': my_processed_requests,
    })


@login_required
def contract_detail(request, pk):
    """계약 상세 조회"""
    contract = get_object_or_404(Contract, pk=pk)

    # 권한 확인: 본인의 계약만 조회 가능
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    # 활성화된 초대가 있는지 확인
    active_invitation = None
    if request.user == contract.tenant and not contract.landlord:
        # 임차인이고 임대인이 연결되지 않은 경우, 임대인 초대 확인
        active_invitation = ContractInvitation.objects.filter(
            contract=contract,
            invited_user_type='LANDLORD',
            is_accepted=False
        ).first()
        if active_invitation and not active_invitation.is_valid():
            active_invitation = None
    elif request.user == contract.landlord and not contract.tenant:
        # 임대인이고 임차인이 연결되지 않은 경우, 임차인 초대 확인
        active_invitation = ContractInvitation.objects.filter(
            contract=contract,
            invited_user_type='TENANT',
            is_accepted=False
        ).first()
        if active_invitation and not active_invitation.is_valid():
            active_invitation = None

    # 대기 중인 변경 요청 확인 (내가 승인해야 하는 요청)
    from .models import ContractChangeRequest
    pending_request = ContractChangeRequest.objects.filter(
        contract=contract,
        status='PENDING'
    ).exclude(
        requested_by=request.user  # 내가 요청한 것은 제외
    ).first()

    # 내가 요청한 대기 중인 요청
    my_pending_request = ContractChangeRequest.objects.filter(
        contract=contract,
        status='PENDING',
        requested_by=request.user
    ).first()

    # 내가 요청한 최근 처리된 요청 (승인/거절) - 읽지 않은 것만
    from datetime import timedelta
    from django.utils import timezone
    recent_time = timezone.now() - timedelta(hours=24)  # 최근 24시간
    my_processed_request = ContractChangeRequest.objects.filter(
        contract=contract,
        requested_by=request.user,
        status__in=['APPROVED', 'REJECTED'],
        responded_at__gte=recent_time,
        is_read_by_requester=False  # 읽지 않은 것만
    ).order_by('-responded_at').first()

    # 입실/퇴실 기록 조회
    from records.models import Record
    move_in_record = Record.objects.filter(
        contract=contract,
        record_type='MOVE_IN'
    ).first()
    move_out_record = Record.objects.filter(
        contract=contract,
        record_type='MOVE_OUT'
    ).first()
    pre_move_out_record = Record.objects.filter(
        contract=contract,
        record_type='PRE_MOVE_OUT'
    ).order_by('-created_at').first()

    # Klaytn 체인 ID (블록체인 스코프 URL용)
    from django.conf import settings as django_settings
    klaytn_chain_id = getattr(django_settings, 'KLAYTN_CHAIN_ID', '1001')

    return render(request, 'contracts/contract_detail.html', {
        'contract': contract,
        'active_invitation': active_invitation,
        'pending_request': pending_request,
        'my_pending_request': my_pending_request,
        'my_processed_request': my_processed_request,
        'move_in_record': move_in_record,
        'move_out_record': move_out_record,
        'pre_move_out_record': pre_move_out_record,
        'klaytn_chain_id': klaytn_chain_id,
    })


@login_required
def contract_create(request):
    """계약 등록"""
    from core.templates_engine.models import InspectionTemplate

    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            contract = form.save(commit=False)

            # 국가 설정
            country = form.cleaned_data.get('country')
            if country:
                contract.country = country

            # 템플릿 설정
            template_id = form.cleaned_data.get('template')
            if template_id:
                try:
                    template = InspectionTemplate.objects.get(pk=template_id, is_active=True)
                    contract.template = template
                except InspectionTemplate.DoesNotExist:
                    pass

            # 사용자 타입에 따라 역할 설정
            if request.user.user_type == 'TENANT':
                contract.tenant = request.user
                # landlord는 폼에서 선택한 값 사용 (있으면)
                landlord_id = request.POST.get('landlord')
                if landlord_id:
                    from accounts.models import User
                    try:
                        contract.landlord = User.objects.get(pk=landlord_id, user_type='LANDLORD')
                    except User.DoesNotExist:
                        pass
            else:  # LANDLORD
                contract.landlord = request.user
                # tenant는 선택 또는 tenant_name/phone 입력
                tenant_id = request.POST.get('tenant')
                if tenant_id:
                    # 임차인 계정 선택한 경우
                    from accounts.models import User
                    try:
                        contract.tenant = User.objects.get(pk=tenant_id, user_type='TENANT')
                        # 임차인 이름/연락처를 자동으로 설정
                        if not contract.tenant_name:
                            contract.tenant_name = contract.tenant.username
                        if not contract.tenant_phone:
                            contract.tenant_phone = contract.tenant.phone_number or ''
                    except User.DoesNotExist:
                        messages.error(request, _('유효하지 않은 임차인입니다.'))
                        return render(request, 'contracts/contract_form.html', {
                            'form': form,
                            'title': _('계약 등록')
                        })
                # 임대인이 등록하는 경우, landlord_name/phone을 자동으로 설정
                if not contract.landlord_name:
                    contract.landlord_name = request.user.username
                if not contract.landlord_phone:
                    contract.landlord_phone = request.user.phone_number or ''

            # 마스킹 처리된 파일 경로가 있으면 사용
            processed_file_path = request.POST.get('processed_file_path')
            if processed_file_path:
                contract.contract_file = processed_file_path

            contract.save()
            messages.success(request, _('계약이 등록되었습니다!'))
            return redirect('contracts:detail', pk=contract.pk)
    else:
        form = ContractForm(user=request.user)

    return render(request, 'contracts/contract_form.html', {
        'form': form,
        'title': _('계약 등록')
    })


@login_required
def contract_update(request, pk):
    """계약 수정 (관리자 전용)"""
    contract = get_object_or_404(Contract, pk=pk)

    # 권한 확인: 관리자만 수정 가능
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, _('관리자만 계약을 수정할 수 있습니다. 계약 연장이나 해지가 필요하신 경우 해당 버튼을 이용해주세요.'))
        return redirect('contracts:detail', pk=pk)

    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, instance=contract, user=request.user)
        if form.is_valid():
            updated_contract = form.save(commit=False)

            # 보안상 이유로 이미 연결된 임대인/임차인은 변경하지 않음
            # 기존 연결 유지
            if contract.landlord:
                updated_contract.landlord = contract.landlord
            if contract.tenant:
                updated_contract.tenant = contract.tenant

            # 임차인이 수정하는 경우, landlord가 아직 연결되지 않은 경우에만 업데이트
            if request.user.user_type == 'TENANT' and not contract.landlord:
                landlord_id = request.POST.get('landlord')
                if landlord_id:
                    from accounts.models import User
                    try:
                        updated_contract.landlord = User.objects.get(pk=landlord_id, user_type='LANDLORD')
                    except User.DoesNotExist:
                        pass

            # 마스킹 처리된 파일 경로가 있으면 사용
            processed_file_path = request.POST.get('processed_file_path')
            if processed_file_path:
                updated_contract.contract_file = processed_file_path

            updated_contract.save()
            messages.success(request, _('계약 정보가 수정되었습니다!'))
            return redirect('contracts:detail', pk=contract.pk)
    else:
        form = ContractForm(instance=contract, user=request.user)

    return render(request, 'contracts/contract_form.html', {
        'form': form,
        'contract': contract,
        'title': _('계약 수정')
    })


@login_required
def contract_delete(request, pk):
    """계약 삭제 (관리자 전용)"""
    contract = get_object_or_404(Contract, pk=pk)

    # 권한 확인: 관리자만 삭제 가능
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, _('관리자만 계약을 삭제할 수 있습니다.'))
        return redirect('contracts:detail', pk=pk)

    if request.method == 'POST':
        contract.delete()
        messages.success(request, _('계약이 삭제되었습니다.'))
        return redirect('contracts:list')

    return render(request, 'contracts/contract_confirm_delete.html', {
        'contract': contract
    })


@login_required
@require_http_methods(["POST"])
def upload_temp_contract_file(request):
    """
    계약서 파일 임시 업로드 및 미리보기 데이터 반환
    """
    if 'file' not in request.FILES:
        return JsonResponse({'error': _('파일이 없습니다.')}, status=400)

    uploaded_file = request.FILES['file']

    # 파일 크기 제한 (10MB)
    if uploaded_file.size > 10 * 1024 * 1024:
        return JsonResponse({'error': _('파일 크기는 10MB 이하여야 합니다.')}, status=400)

    # 임시 디렉토리에 파일 저장
    temp_dir = 'temp_contracts'
    temp_filename = f'{request.user.id}_{uploaded_file.name}'
    temp_path = os.path.join(temp_dir, temp_filename)

    # 디렉토리 생성
    full_temp_dir = os.path.join(default_storage.location, temp_dir)
    os.makedirs(full_temp_dir, exist_ok=True)

    # 파일 저장
    saved_path = default_storage.save(temp_path, ContentFile(uploaded_file.read()))
    full_path = default_storage.path(saved_path)

    # 미리보기 데이터 생성
    preview_data = get_file_preview_data(full_path)

    if not preview_data['pages']:
        # 실패 시 임시 파일 삭제
        default_storage.delete(saved_path)
        return JsonResponse({'error': _('지원하지 않는 파일 형식입니다.')}, status=400)

    return JsonResponse({
        'success': True,
        'temp_path': saved_path,
        'file_name': uploaded_file.name,
        'preview': preview_data
    })


@login_required
@require_http_methods(["POST"])
def process_contract_masking(request):
    """
    마스킹 영역 정보를 받아서 파일 처리
    """
    try:
        data = json.loads(request.body)
        temp_path = data.get('temp_path')
        mask_areas = data.get('mask_areas', [])
        original_filename = data.get('file_name')

        if not temp_path or not original_filename:
            return JsonResponse({'error': _('필수 정보가 누락되었습니다.')}, status=400)

        # 임시 파일 경로 확인
        if not default_storage.exists(temp_path):
            return JsonResponse({'error': _('임시 파일을 찾을 수 없습니다.')}, status=404)

        full_temp_path = default_storage.path(temp_path)

        # 최종 저장 경로 설정
        from datetime import datetime
        now = datetime.now()
        final_dir = f'contracts/{now.year}/{now.month:02d}'
        final_path = os.path.join(final_dir, original_filename)

        # 디렉토리 생성
        full_final_dir = os.path.join(default_storage.location, final_dir)
        os.makedirs(full_final_dir, exist_ok=True)

        full_final_path = default_storage.path(final_path)

        # 마스킹 처리
        success = process_masked_file(full_temp_path, mask_areas, full_final_path)

        # 임시 파일 삭제
        default_storage.delete(temp_path)

        if not success:
            return JsonResponse({'error': _('파일 처리 중 오류가 발생했습니다.')}, status=500)

        return JsonResponse({
            'success': True,
            'file_path': final_path,
            'message': _('파일이 성공적으로 처리되었습니다.')
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': _('잘못된 요청 데이터입니다.')}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_invitation(request, pk):
    """계약 초대 링크 생성"""
    contract = get_object_or_404(Contract, pk=pk)

    # 권한 확인: 계약 당사자만 초대 가능
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('권한이 없습니다.'))
        return redirect('contracts:detail', pk=pk)

    # 초대할 사용자 유형 결정
    if request.user == contract.tenant:
        # 임차인이 초대하는 경우 -> 임대인 초대
        invited_user_type = 'LANDLORD'
        if contract.landlord:
            messages.warning(request, _('이미 임대인이 연결되어 있습니다.'))
            return redirect('contracts:detail', pk=pk)
    elif request.user == contract.landlord:
        # 임대인이 초대하는 경우 -> 임차인 초대
        invited_user_type = 'TENANT'
        if contract.tenant:
            messages.warning(request, _('이미 임차인이 연결되어 있습니다.'))
            return redirect('contracts:detail', pk=pk)
    else:
        messages.error(request, _('권한이 없습니다.'))
        return redirect('contracts:detail', pk=pk)

    # 기존 유효한 초대가 있는지 확인
    existing_invitation = ContractInvitation.objects.filter(
        contract=contract,
        invited_user_type=invited_user_type,
        is_accepted=False
    ).first()

    if existing_invitation and existing_invitation.is_valid():
        messages.info(request, _('이미 활성화된 초대 링크가 있습니다.'))
    else:
        # 새 초대 생성
        invitation = ContractInvitation.objects.create(
            contract=contract,
            invited_by=request.user,
            invited_user_type=invited_user_type
        )
        messages.success(request, _('초대 링크가 생성되었습니다!'))

    return redirect('contracts:detail', pk=pk)


@login_required
def accept_invitation(request, token):
    """초대 수락"""
    invitation = get_object_or_404(ContractInvitation, token=token)

    # 초대 유효성 확인
    if not invitation.is_valid():
        if invitation.is_accepted:
            messages.error(request, _('이미 수락된 초대입니다.'))
        else:
            messages.error(request, _('만료된 초대 링크입니다.'))
        return redirect('accounts:dashboard')

    # 사용자 타입 확인
    if request.user.user_type != invitation.invited_user_type:
        messages.error(request, _('이 초대는 %(user_type)s 전용입니다.') % {'user_type': invitation.get_invited_user_type_display()})
        return redirect('accounts:dashboard')

    # GET 요청: 초대 수락 확인 페이지 표시
    if request.method == 'GET':
        return render(request, 'contracts/accept_invitation.html', {
            'invitation': invitation
        })

    # POST 요청: 초대 수락 처리
    contract = invitation.contract

    if invitation.invited_user_type == 'LANDLORD':
        # 임대인으로 초대된 경우
        if contract.landlord:
            messages.error(request, _('이미 다른 임대인이 연결되어 있습니다.'))
            return redirect('accounts:dashboard')
        contract.landlord = request.user
    elif invitation.invited_user_type == 'TENANT':
        # 임차인으로 초대된 경우
        if contract.tenant:
            messages.error(request, _('이미 다른 임차인이 연결되어 있습니다.'))
            return redirect('accounts:dashboard')
        contract.tenant = request.user
    else:
        messages.error(request, _('잘못된 초대입니다.'))
        return redirect('accounts:dashboard')

    contract.save()

    # 초대 상태 업데이트
    invitation.is_accepted = True
    invitation.accepted_by = request.user
    invitation.save()

    messages.success(request, _('계약에 참여하셨습니다! (%(address)s)') % {'address': contract.address})
    return redirect('contracts:detail', pk=contract.pk)


@login_required
def contract_extend(request, pk):
    """계약 연장 요청"""
    contract = get_object_or_404(Contract, pk=pk)

    # 권한 확인: 계약 당사자만 가능
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('권한이 없습니다.'))
        return redirect('contracts:detail', pk=pk)

    # 이미 종료된 계약은 연장 불가
    if contract.get_current_status() == 'COMPLETED':
        messages.error(request, _('이미 종료된 계약은 연장할 수 없습니다.'))
        return redirect('contracts:detail', pk=pk)

    # 이미 대기 중인 변경 요청이 있는지 확인
    from .models import ContractChangeRequest
    existing_request = ContractChangeRequest.objects.filter(
        contract=contract,
        status='PENDING'
    ).first()

    if existing_request:
        messages.warning(request, _('이미 처리 대기 중인 변경 요청이 있습니다.'))
        return redirect('contracts:detail', pk=pk)

    # GET 요청: 연장 확인 페이지 표시
    if request.method == 'GET':
        return render(request, 'contracts/contract_extend.html', {
            'contract': contract
        })

    # POST 요청: 연장 요청 생성
    extend_months = int(request.POST.get('extend_months', 12))

    # 변경 요청 생성
    ContractChangeRequest.objects.create(
        contract=contract,
        request_type='EXTEND',
        requested_by=request.user,
        extend_months=extend_months,
        note=_('%(months)s개월 연장 요청') % {'months': extend_months}
    )

    # 상대방 확인
    if request.user == contract.tenant:
        other_party = _("임대인")
    else:
        other_party = _("임차인")

    messages.success(request, _('계약 연장 요청이 전송되었습니다! %(other_party)s의 승인을 기다립니다.') % {'other_party': other_party})
    return redirect('contracts:detail', pk=contract.pk)


@login_required
def contract_terminate(request, pk):
    """계약 해지 요청"""
    contract = get_object_or_404(Contract, pk=pk)

    # 권한 확인: 계약 당사자만 가능
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('권한이 없습니다.'))
        return redirect('contracts:detail', pk=pk)

    # 이미 종료된 계약은 해지 불가
    if contract.get_current_status() == 'COMPLETED':
        messages.warning(request, _('이미 종료된 계약입니다.'))
        return redirect('contracts:detail', pk=pk)

    # 이미 대기 중인 변경 요청이 있는지 확인
    from .models import ContractChangeRequest
    existing_request = ContractChangeRequest.objects.filter(
        contract=contract,
        status='PENDING'
    ).first()

    if existing_request:
        messages.warning(request, _('이미 처리 대기 중인 변경 요청이 있습니다.'))
        return redirect('contracts:detail', pk=pk)

    # GET 요청: 해지 확인 페이지 표시
    if request.method == 'GET':
        return render(request, 'contracts/contract_terminate.html', {
            'contract': contract
        })

    # POST 요청: 해지 요청 생성
    ContractChangeRequest.objects.create(
        contract=contract,
        request_type='TERMINATE',
        requested_by=request.user,
        note=_('계약 해지 요청')
    )

    # 상대방 확인
    if request.user == contract.tenant:
        other_party = _("임대인")
    else:
        other_party = _("임차인")

    messages.success(request, _('계약 해지 요청이 전송되었습니다! %(other_party)s의 승인을 기다립니다.') % {'other_party': other_party})
    return redirect('contracts:detail', pk=contract.pk)


@login_required
@require_http_methods(["POST"])
def approve_change_request(request, request_id):
    """변경 요청 승인"""
    from .models import ContractChangeRequest, ContractHistory
    from datetime import date
    from dateutil.relativedelta import relativedelta
    from django.utils import timezone

    change_request = get_object_or_404(ContractChangeRequest, pk=request_id)
    contract = change_request.contract

    # 권한 확인: 요청받은 당사자만 승인 가능
    if change_request.requested_by == request.user:
        messages.error(request, _('본인이 요청한 것은 승인할 수 없습니다.'))
        return redirect('contracts:detail', pk=contract.pk)

    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('권한이 없습니다.'))
        return redirect('contracts:detail', pk=contract.pk)

    # 이미 처리된 요청인지 확인
    if change_request.status != 'PENDING':
        messages.warning(request, _('이미 처리된 요청입니다.'))
        return redirect('contracts:detail', pk=contract.pk)

    # 승인 메시지 (선택사항)
    response_note = request.POST.get('response_note', '').strip()

    # 요청 유형에 따라 처리
    if change_request.request_type == 'EXTEND':
        # 계약 연장
        extend_months = change_request.extend_months

        # 기준 날짜 계산
        if contract.move_out_date:
            if contract.move_out_date > date.today():
                base_date = contract.move_out_date
            else:
                base_date = date.today()
        else:
            base_date = date.today()

        new_move_out_date = base_date + relativedelta(months=extend_months)
        previous_move_out_date = contract.move_out_date

        contract.move_out_date = new_move_out_date
        contract.status = 'ACTIVE'
        contract.save()

        # 계약 이력 기록
        ContractHistory.objects.create(
            contract=contract,
            action_type='EXTENDED',
            action_by=request.user,
            previous_move_out_date=previous_move_out_date,
            new_move_out_date=new_move_out_date,
            extend_months=extend_months,
            note=_('%(months)s개월 연장 승인 (요청자: %(requester)s, 승인자: %(approver)s)') % {'months': extend_months, 'requester': change_request.requested_by.username, 'approver': request.user.username}
        )

        messages.success(request, _('계약 연장이 승인되었습니다! 새 퇴실 예정일: %(date)s') % {'date': new_move_out_date})

    elif change_request.request_type == 'TERMINATE':
        # 계약 해지
        previous_move_out_date = contract.move_out_date

        contract.status = 'COMPLETED'
        contract.move_out_date = date.today()
        contract.save()

        # 계약 이력 기록
        ContractHistory.objects.create(
            contract=contract,
            action_type='TERMINATED',
            action_by=request.user,
            previous_move_out_date=previous_move_out_date,
            new_move_out_date=date.today(),
            note=_('계약 해지 승인 (요청자: %(requester)s, 승인자: %(approver)s)') % {'requester': change_request.requested_by.username, 'approver': request.user.username}
        )

        messages.success(request, _('계약 해지가 승인되었습니다.'))

    # 요청 상태 업데이트
    change_request.status = 'APPROVED'
    change_request.responded_by = request.user
    change_request.responded_at = timezone.now()
    if response_note:
        change_request.response_note = response_note
    change_request.save()

    return redirect('contracts:detail', pk=contract.pk)


@login_required
@require_http_methods(["POST"])
def reject_change_request(request, request_id):
    """변경 요청 거절"""
    from .models import ContractChangeRequest
    from django.utils import timezone

    change_request = get_object_or_404(ContractChangeRequest, pk=request_id)
    contract = change_request.contract

    # 권한 확인: 요청받은 당사자만 거절 가능
    if change_request.requested_by == request.user:
        messages.error(request, _('본인이 요청한 것은 거절할 수 없습니다.'))
        return redirect('contracts:detail', pk=contract.pk)

    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('권한이 없습니다.'))
        return redirect('contracts:detail', pk=contract.pk)

    # 이미 처리된 요청인지 확인
    if change_request.status != 'PENDING':
        messages.warning(request, _('이미 처리된 요청입니다.'))
        return redirect('contracts:detail', pk=contract.pk)

    # 거절 사유 확인
    response_note = request.POST.get('response_note', '').strip()
    if not response_note:
        messages.error(request, _('거절 사유를 입력해주세요.'))
        return redirect('contracts:detail', pk=contract.pk)

    # 요청 상태 업데이트
    change_request.status = 'REJECTED'
    change_request.responded_by = request.user
    change_request.responded_at = timezone.now()
    change_request.response_note = response_note
    change_request.save()

    request_type_display = change_request.get_request_type_display()
    messages.info(request, _('%(request_type)s 요청이 거절되었습니다.') % {'request_type': request_type_display})

    return redirect('contracts:detail', pk=contract.pk)


@login_required
@require_http_methods(["POST"])
def mark_request_as_read(request, request_id):
    """변경 요청 알림 읽음 처리"""
    from .models import ContractChangeRequest

    change_request = get_object_or_404(ContractChangeRequest, pk=request_id)

    # 권한 확인: 요청자만 읽음 처리 가능
    if change_request.requested_by != request.user:
        return JsonResponse({'success': False, 'error': _('권한이 없습니다.')}, status=403)

    # 읽음 처리
    change_request.is_read_by_requester = True
    change_request.save()

    return JsonResponse({'success': True})


@login_required
@require_GET
def get_templates_api(request):
    """국가와 부동산 유형에 따른 템플릿 목록 반환 API"""
    from core.templates_engine.models import InspectionTemplate

    country = request.GET.get('country', '')
    property_type = request.GET.get('property_type', '')

    if not country or not property_type:
        return JsonResponse({'templates': []})

    # 현재 언어 확인
    current_language = get_language()

    # 해당 국가 및 부동산 유형의 활성화된 템플릿 조회
    templates = InspectionTemplate.objects.filter(
        country=country,
        property_type=property_type,
        is_active=True
    ).order_by('-is_default', 'name')

    template_list = []
    for t in templates:
        # 언어에 따른 이름 선택
        if current_language == 'ja' and t.name_ja:
            name = t.name_ja
        elif current_language == 'en' and t.name_en:
            name = t.name_en
        else:
            name = t.name

        template_list.append({
            'id': t.pk,
            'name': name,
            'is_default': t.is_default,
            'version': t.version,
            'description': t.description,
        })

    return JsonResponse({'templates': template_list})
