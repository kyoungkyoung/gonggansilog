from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from .forms import SignUpForm


def signup(request):
    """회원가입"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, _('%(user_type)s으로 가입되었습니다!') % {'user_type': user.get_user_type_display()})
            return redirect('accounts:dashboard')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})


def user_login(request):
    """로그인"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, _('%(username)s님, 환영합니다!') % {'username': user.username})

            # user_type 또는 phone_number가 없으면 선택 페이지로
            if not user.user_type or not user.phone_number:
                return redirect('accounts:select_user_type')

            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, _('사용자명 또는 비밀번호가 올바르지 않습니다.'))

    return render(request, 'accounts/login.html')


@login_required
def user_logout(request):
    """로그아웃"""
    logout(request)
    messages.info(request, _('로그아웃되었습니다.'))
    return redirect('accounts:login')


@login_required
def dashboard(request):
    """대시보드 (로그인 후 메인 페이지)"""
    from contracts.models import Contract, ContractChangeRequest
    from records.models import Record
    from datetime import timedelta
    from django.utils import timezone

    # user_type 또는 phone_number가 없으면 선택 페이지로
    if not request.user.user_type or not request.user.phone_number:
        return redirect('accounts:select_user_type')

    # 사용자의 계약 가져오기
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
    # 입실/퇴실 기록 승인 알림용 (7일 이내)
    record_recent_time = timezone.now() - timedelta(days=7)
    my_processed_requests = ContractChangeRequest.objects.filter(
        contract__in=contracts,
        requested_by=request.user,
        status__in=['APPROVED', 'REJECTED'],
        responded_at__gte=recent_time,
        is_read_by_requester=False
    ).select_related('contract', 'responded_by').order_by('-responded_at')

    # ========== 입실/퇴실 기록 관련 알림 ==========
    record_notifications = []

    # 먼저 마감일이 지난 OPEN 상태 기록을 자동 제출 처리
    open_records_to_check = Record.objects.filter(
        contract__in=contracts,
        status='OPEN'
    )
    for record in open_records_to_check:
        record.auto_submit_if_deadline_passed()

    if request.user.user_type == 'LANDLORD':
        # 임대인: 임차인이 기록 등록 요청한 것 (REQUESTED 상태, 읽지 않은 것)
        requested_records = Record.objects.filter(
            contract__in=contracts,
            status='REQUESTED',
            is_read_by_landlord=False
        ).select_related('contract', 'created_by').order_by('-created_at')

        for record in requested_records:
            record_notifications.append({
                'type': 'requested',
                'record': record,
                'message': _('%(user)s님이 %(record_type)s 기록 등록을 요청했습니다.') % {
                    'user': record.created_by.username if record.created_by else _('임차인'),
                    'record_type': record.get_record_type_display(),
                },
                'alert_class': 'warning',
                'icon': 'bi-hourglass-split',
            })

        # 임대인: 임차인이 사진 업로드 후 제출한 것 (SUBMITTED 상태, 읽지 않은 것)
        submitted_records = Record.objects.filter(
            contract__in=contracts,
            status='SUBMITTED',
            is_read_by_landlord=False
        ).select_related('contract', 'created_by').order_by('-submitted_at')

        for record in submitted_records:
            record_notifications.append({
                'type': 'submitted',
                'record': record,
                'message': _('%(address)s의 %(record_type)s 기록이 제출되었습니다. 확인 후 승인해주세요.') % {
                    'address': record.contract.address,
                    'record_type': record.get_record_type_display(),
                },
                'alert_class': 'info',
                'icon': 'bi-send-check',
            })

    else:  # TENANT
        # 임차인: 업로드 가능한 기록 (OPEN 상태, 마감일 전, 읽지 않은 것)
        open_records = Record.objects.filter(
            contract__in=contracts,
            status='OPEN',
            is_read_by_tenant=False
        ).select_related('contract').order_by('-created_at')

        for record in open_records:
            if not record.is_deadline_passed():
                deadline_status = record.get_deadline_status()
                record_notifications.append({
                    'type': 'open',
                    'record': record,
                    'message': _('%(address)s의 %(record_type)s 기록에 사진을 업로드해주세요.') % {
                        'address': record.contract.address,
                        'record_type': record.get_record_type_display(),
                    },
                    'deadline_message': deadline_status.get('message', ''),
                    'deadline_status': deadline_status.get('status', ''),
                    'alert_class': 'warning',
                    'icon': 'bi-cloud-upload',
                })

        # 임차인: 반려된 기록 (수정 필요, 마감일 전, 읽지 않은 것)
        rejected_records = Record.objects.filter(
            contract__in=contracts,
            status='REJECTED',
            is_read_by_tenant=False
        ).select_related('contract').order_by('-landlord_approved_at')

        for record in rejected_records:
            if not record.is_deadline_passed():
                record_notifications.append({
                    'type': 'rejected',
                    'record': record,
                    'message': _('%(address)s의 %(record_type)s 기록이 반려되었습니다. 수정 후 다시 제출해주세요.') % {
                        'address': record.contract.address,
                        'record_type': record.get_record_type_display(),
                    },
                    'comment': record.landlord_comment,
                    'alert_class': 'danger',
                    'icon': 'bi-x-circle',
                })

        # 임차인: 최근 승인된 기록 (읽지 않은 것)
        approved_records = Record.objects.filter(
            contract__in=contracts,
            status='APPROVED',
            is_read_by_tenant=False
        ).select_related('contract').order_by('-landlord_approved_at')

        for record in approved_records:
            record_notifications.append({
                'type': 'approved',
                'record': record,
                'message': _('%(address)s의 %(record_type)s 기록이 최종 승인되었습니다.') % {
                    'address': record.contract.address,
                    'record_type': record.get_record_type_display(),
                },
                'comment': record.landlord_comment,
                'alert_class': 'success',
                'icon': 'bi-check-circle',
            })

    # ========== 녹음 동의 요청 알림 ==========
    from recordings.models import Recording

    recording_notifications = []

    # 내가 동의해야 하는 녹음 (상대방이 등록하고 동의 대기 중인 것)
    pending_consent_recordings = Recording.objects.filter(
        contract__in=contracts,
        consent_status='PENDING'
    ).exclude(
        user=request.user
    ).select_related('contract', 'user').order_by('-recorded_at')

    for recording in pending_consent_recordings:
        recording_notifications.append({
            'type': 'consent_pending',
            'recording': recording,
            'message': _('%(user)s님이 녹음 기록을 등록했습니다. 동의 여부를 확인해주세요.') % {
                'user': recording.user.username,
            },
            'alert_class': 'warning',
            'icon': 'bi-mic-fill',
        })

    # ========== 하자 통지 알림 ==========
    from records.models import DefectReport, RepairRequest

    defect_notifications = []

    if request.user.user_type == 'LANDLORD':
        # 임대인: 새 하자 신고 알림
        pending_defects = DefectReport.objects.filter(
            contract__in=contracts,
            status='REPORTED',
            is_read_by_landlord=False
        ).select_related('contract', 'reported_by').order_by('-created_at')

        for defect in pending_defects:
            defect_notifications.append({
                'type': 'defect_new',
                'defect': defect,
                'message': _('%(user)s님이 하자를 신고했습니다: %(title)s') % {
                    'user': defect.reported_by.username,
                    'title': defect.title,
                },
                'alert_class': 'danger' if defect.severity == 'CRITICAL' else 'warning',
                'icon': 'bi-exclamation-triangle',
            })
    else:
        # 임차인: 임대인 응답 알림
        responded_defects = DefectReport.objects.filter(
            contract__in=contracts,
            reported_by=request.user,
            status__in=['ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED'],
            is_read_by_tenant=False
        ).select_related('contract').order_by('-updated_at')

        for defect in responded_defects:
            defect_notifications.append({
                'type': 'defect_responded',
                'defect': defect,
                'message': _('하자 "%(title)s"이(가) %(status)s 상태로 변경되었습니다.') % {
                    'title': defect.title,
                    'status': defect.get_status_display(),
                },
                'alert_class': 'success' if defect.status == 'RESOLVED' else 'info',
                'icon': 'bi-check-circle' if defect.status == 'RESOLVED' else 'bi-reply',
            })

    # ========== 수리 요청 알림 ==========
    repair_notifications = []

    if request.user.user_type == 'LANDLORD':
        pending_repairs = RepairRequest.objects.filter(
            contract__in=contracts,
            status__in=['REQUESTED', 'APPROVED'],
            is_read_by_landlord=False
        ).select_related('contract', 'requested_by').order_by('-created_at')

        for repair in pending_repairs:
            repair_notifications.append({
                'type': 'repair_new',
                'repair': repair,
                'message': _('%(user)s님이 수리를 요청했습니다: %(title)s') % {
                    'user': repair.requested_by.username,
                    'title': repair.title,
                },
                'alert_class': 'primary',
                'icon': 'bi-tools',
            })
    else:
        tenant_repairs = RepairRequest.objects.filter(
            contract__in=contracts,
            requested_by=request.user,
            status__in=['QUOTE_PROVIDED', 'IN_PROGRESS', 'COMPLETED'],
            is_read_by_tenant=False
        ).select_related('contract').order_by('-updated_at')

        for repair in tenant_repairs:
            repair_notifications.append({
                'type': 'repair_update',
                'repair': repair,
                'message': _('수리 "%(title)s"이(가) %(status)s 상태입니다.') % {
                    'title': repair.title,
                    'status': repair.get_status_display(),
                },
                'alert_class': 'success' if repair.status == 'COMPLETED' else 'info',
                'icon': 'bi-check-circle' if repair.status == 'COMPLETED' else 'bi-tools',
            })

    return render(request, 'accounts/dashboard.html', {
        'pending_requests': pending_requests,
        'my_processed_requests': my_processed_requests,
        'record_notifications': record_notifications,
        'recording_notifications': recording_notifications,
        'defect_notifications': defect_notifications,
        'repair_notifications': repair_notifications,
    })


@login_required
def select_user_type(request):
    """소셜 로그인 후 사용자 유형 및 전화번호 입력"""
    # 이미 user_type과 phone_number가 모두 설정되어 있으면 대시보드로
    if request.user.user_type and request.user.phone_number:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        phone_number = request.POST.get('phone_number', '').strip()

        # 유효성 검사
        if user_type not in ['TENANT', 'LANDLORD']:
            messages.error(request, _('올바른 사용자 유형을 선택해주세요.'))
        elif not phone_number:
            messages.error(request, _('전화번호를 입력해주세요.'))
        else:
            # 저장
            request.user.user_type = user_type
            request.user.phone_number = phone_number
            request.user.save()
            messages.success(request, _('%(user_type)s으로 설정되었습니다!') % {'user_type': request.user.get_user_type_display()})
            return redirect('accounts:dashboard')

    return render(request, 'accounts/select_user_type.html')
