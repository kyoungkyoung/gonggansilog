from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils.translation import get_language, gettext as _
from django.core.files.base import ContentFile

from contracts.models import Contract
from records.models import Record
from .models import GeneratedReport, ReportShare
from .services import ReportGenerator
from django.utils import timezone
from datetime import timedelta


@login_required
def generate_move_in_report(request, record_pk):
    """입실 리포트 생성"""
    record = get_object_or_404(Record, pk=record_pk, record_type='MOVE_IN')
    contract = record.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('You do not have permission to access this report.'))
        return redirect('contracts:list')

    # 언어 설정
    language = request.GET.get('lang', get_language())

    try:
        generator = ReportGenerator(contract, language=language)
        result = generator.generate_move_in_report(record)

        # 리포트 기록 생성
        report = GeneratedReport.objects.create(
            contract=contract,
            record=record,
            report_type='MOVE_IN',
            language=language,
            status='COMPLETED',
            generated_by=request.user
        )
        report.file.save(result['filename'], ContentFile(result['content']))

        # PDF 직접 반환
        response = HttpResponse(result['content'], content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{result["filename"]}"'
        return response

    except Exception as e:
        messages.error(request, _('Error generating report: ') + str(e))
        return redirect('records:detail', pk=record_pk)


@login_required
def generate_move_out_report(request, record_pk):
    """퇴실 리포트 생성"""
    record = get_object_or_404(Record, pk=record_pk, record_type='MOVE_OUT')
    contract = record.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('You do not have permission to access this report.'))
        return redirect('contracts:list')

    # 언어 설정
    language = request.GET.get('lang', get_language())

    try:
        generator = ReportGenerator(contract, language=language)
        result = generator.generate_move_out_report(record)

        # 리포트 기록 생성
        report = GeneratedReport.objects.create(
            contract=contract,
            record=record,
            report_type='MOVE_OUT',
            language=language,
            status='COMPLETED',
            generated_by=request.user
        )
        report.file.save(result['filename'], ContentFile(result['content']))

        # PDF 직접 반환
        response = HttpResponse(result['content'], content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{result["filename"]}"'
        return response

    except Exception as e:
        messages.error(request, _('Error generating report: ') + str(e))
        return redirect('records:detail', pk=record_pk)


@login_required
def generate_comparison_report(request, contract_pk):
    """비교 리포트 생성"""
    contract = get_object_or_404(Contract, pk=contract_pk)

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('You do not have permission to access this report.'))
        return redirect('contracts:list')

    # 입실/퇴실 기록 확인
    move_in_record = Record.objects.filter(contract=contract, record_type='MOVE_IN').first()
    move_out_record = Record.objects.filter(contract=contract, record_type='MOVE_OUT').first()

    if not move_in_record or not move_out_record:
        messages.warning(request, _('Both move-in and move-out records are required for comparison report.'))
        return redirect('contracts:detail', pk=contract_pk)

    # 언어 설정
    language = request.GET.get('lang', get_language())

    try:
        generator = ReportGenerator(contract, language=language)
        result = generator.generate_comparison_report(move_in_record, move_out_record)

        # 리포트 기록 생성
        report = GeneratedReport.objects.create(
            contract=contract,
            report_type='COMPARISON',
            language=language,
            status='COMPLETED',
            generated_by=request.user
        )
        report.file.save(result['filename'], ContentFile(result['content']))

        # PDF 직접 반환
        response = HttpResponse(result['content'], content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{result["filename"]}"'
        return response

    except Exception as e:
        messages.error(request, _('Error generating report: ') + str(e))
        return redirect('contracts:detail', pk=contract_pk)


@login_required
def report_history(request, contract_pk):
    """계약별 리포트 이력"""
    contract = get_object_or_404(Contract, pk=contract_pk)

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('contracts:list')

    reports = GeneratedReport.objects.filter(contract=contract).order_by('-created_at')

    # 입실/퇴실 기록 조회
    move_in_record = Record.objects.filter(contract=contract, record_type='MOVE_IN').first()
    move_out_record = Record.objects.filter(contract=contract, record_type='MOVE_OUT').first()

    return render(request, 'reports/report_history.html', {
        'contract': contract,
        'reports': reports,
        'move_in_record': move_in_record,
        'move_out_record': move_out_record,
    })


@login_required
def download_report(request, report_uuid):
    """리포트 다운로드"""
    report = get_object_or_404(GeneratedReport, uuid=report_uuid)
    contract = report.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('You do not have permission to access this report.'))
        return redirect('contracts:list')

    if not report.file:
        messages.error(request, _('Report file not found.'))
        return redirect('reports:history', contract_pk=contract.pk)

    # 파일 반환
    response = HttpResponse(report.file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report.file.name.split("/")[-1]}"'
    return response


@login_required
def create_share_link(request, report_uuid):
    """리포트 공유 링크 생성"""
    report = get_object_or_404(GeneratedReport, uuid=report_uuid)
    contract = report.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('You do not have permission to share this report.'))
        return redirect('contracts:list')

    if request.method == 'POST':
        # 만료 시간 설정
        expires_days = request.POST.get('expires_days')
        expires_at = None
        if expires_days and expires_days != 'never':
            expires_at = timezone.now() + timedelta(days=int(expires_days))

        # 최대 다운로드 횟수
        max_downloads = request.POST.get('max_downloads')
        if max_downloads:
            max_downloads = int(max_downloads) if max_downloads != 'unlimited' else None
        else:
            max_downloads = None

        # 메모
        note = request.POST.get('note', '')

        # 공유 링크 생성
        share = ReportShare.objects.create(
            report=report,
            expires_at=expires_at,
            max_downloads=max_downloads,
            shared_by=request.user,
            note=note
        )

        messages.success(request, _('Share link has been created.'))
        return redirect('reports:share_detail', token=share.token)

    return render(request, 'reports/create_share.html', {
        'report': report,
        'contract': contract,
    })


@login_required
def share_detail(request, token):
    """공유 링크 상세 (관리용)"""
    share = get_object_or_404(ReportShare, token=token)
    contract = share.report.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('contracts:list')

    # 공유 링크 비활성화
    if request.method == 'POST' and request.POST.get('action') == 'deactivate':
        share.is_active = False
        share.save()
        messages.success(request, _('Share link has been deactivated.'))
        return redirect('reports:history', contract_pk=contract.pk)

    # 공유 URL 생성
    share_url = request.build_absolute_uri(f'/reports/shared/{share.token}/')

    return render(request, 'reports/share_detail.html', {
        'share': share,
        'share_url': share_url,
        'report': share.report,
        'contract': contract,
    })


def shared_report_download(request, token):
    """공유 링크로 리포트 다운로드 (로그인 불필요)"""
    share = get_object_or_404(ReportShare, token=token)

    # 유효성 확인
    if not share.is_valid():
        return render(request, 'reports/share_expired.html', {
            'message': _('This share link is no longer valid.')
        })

    report = share.report
    if not report.file:
        return render(request, 'reports/share_expired.html', {
            'message': _('Report file not found.')
        })

    # 다운로드 카운트 증가
    share.increment_download()

    # 파일 반환
    response = HttpResponse(report.file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report.file.name.split("/")[-1]}"'
    return response


@login_required
def my_shares(request):
    """내가 공유한 링크 목록"""
    shares = ReportShare.objects.filter(shared_by=request.user).order_by('-created_at')

    return render(request, 'reports/my_shares.html', {
        'shares': shares,
    })
