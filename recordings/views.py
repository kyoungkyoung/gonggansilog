from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import base64
import os
import tempfile
from pydub import AudioSegment
from .models import Recording
from contracts.models import Contract
from .ai_services import process_recording
from django.utils import timezone
from django.utils.translation import gettext as _


@login_required
def recording_list(request):
    """녹음 목록 조회"""
    from django.db.models import Q

    # 내가 생성한 녹음 또는 내 계약과 연결된 녹음
    if request.user.user_type == 'TENANT':
        recordings = Recording.objects.filter(
            Q(user=request.user) |  # 내가 생성한 녹음
            Q(contract__tenant=request.user)  # 내가 임차인인 계약의 녹음
        ).distinct()
    else:  # LANDLORD
        recordings = Recording.objects.filter(
            Q(user=request.user) |  # 내가 생성한 녹음
            Q(contract__landlord=request.user)  # 내가 임대인인 계약의 녹음
        ).distinct()

    return render(request, 'recordings/recording_list.html', {
        'recordings': recordings
    })


@login_required
def recording_create(request):
    """녹음 생성 (녹음 페이지)"""
    # 내 계약 목록 가져오기 (나중에 연결할 수 있도록)
    if request.user.user_type == 'TENANT':
        contracts = Contract.objects.filter(tenant=request.user)
    else:
        contracts = Contract.objects.filter(landlord=request.user)

    return render(request, 'recordings/recording_create.html', {
        'contracts': contracts
    })


@login_required
@require_http_methods(["POST"])
def save_recording(request):
    """녹음 파일 저장 API"""
    try:
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        contract_id = request.POST.get('contract_id')
        audio_data = request.POST.get('audio_data')  # Base64 encoded audio

        if not title or not audio_data:
            return JsonResponse({'error': _('제목과 녹음 데이터는 필수입니다.')}, status=400)

        # Base64 디코딩
        format, audio_str = audio_data.split(';base64,')
        ext = format.split('/')[-1]
        audio_file = ContentFile(base64.b64decode(audio_str), name=f'recording.{ext}')

        # Recording 객체 생성 (duration은 나중에 설정)
        recording = Recording(
            user=request.user,
            title=title,
            description=description,
            duration=0  # 임시값
        )

        # 계약 연결 (선택사항)
        if contract_id:
            try:
                contract = Contract.objects.get(pk=contract_id)
                # 권한 확인
                if contract.tenant == request.user or contract.landlord == request.user:
                    recording.contract = contract
                    # 상대방이 있으면 동의 대기 상태로 설정
                    other_party = None
                    if contract.tenant and contract.landlord:
                        other_party = contract.landlord if request.user == contract.tenant else contract.tenant
                    if other_party:
                        recording.consent_status = 'PENDING'
                    else:
                        recording.consent_status = 'NOT_REQUIRED'
            except Contract.DoesNotExist:
                pass

        # 파일 저장
        recording.audio_file.save(f'recording_{recording.user.id}.{ext}', audio_file)
        recording.save()

        # 실제 오디오 파일에서 길이 추출
        try:
            audio = AudioSegment.from_file(recording.audio_file.path)
            recording.duration = int(audio.duration_seconds)
            recording.save()
        except Exception as e:
            # 오디오 길이를 가져올 수 없는 경우 기본값 유지
            pass

        # 제목 번역 (영어/일본어)
        try:
            from recordings.ai_services import translate_title
            recording.title_en = translate_title(title, 'en')
            recording.title_ja = translate_title(title, 'ja')
            recording.save(update_fields=['title_en', 'title_ja'])
        except Exception as e:
            print(f"제목 번역 실패: {str(e)}")

        # AI 처리 (음성 전사 및 요약)
        try:
            success, transcript, summary = process_recording(recording)
            if success:
                recording.transcript = transcript
                recording.summary = summary
                recording.processing_status = 'COMPLETED'
                recording.processed_at = timezone.now()
                recording.save(update_fields=['transcript', 'summary', 'processing_status', 'processed_at'])
        except Exception as e:
            # AI 처리 실패 시 로깅만 하고 계속 진행
            print(f"AI 처리 실패: {str(e)}")
            pass

        return JsonResponse({
            'success': True,
            'recording_id': recording.id,
            'message': _('녹음이 저장되었습니다.')
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def recording_detail(request, pk):
    """녹음 상세 조회"""
    from django.db.models import Q

    # 녹음 권한 확인: 생성자이거나 관련 계약의 당사자
    recording = get_object_or_404(Recording, pk=pk)

    # 권한 확인
    has_permission = (
        recording.user == request.user or  # 생성자
        (recording.contract and recording.contract.tenant == request.user) or  # 임차인
        (recording.contract and recording.contract.landlord == request.user)  # 임대인
    )

    if not has_permission:
        from django.http import Http404
        raise Http404(_("녹음을 찾을 수 없습니다."))

    # 내 계약 목록 가져오기 (연결 변경을 위해)
    if request.user.user_type == 'TENANT':
        contracts = Contract.objects.filter(tenant=request.user)
    else:
        contracts = Contract.objects.filter(landlord=request.user)

    return render(request, 'recordings/recording_detail.html', {
        'recording': recording,
        'contracts': contracts
    })


# 계약 연결 변경 기능 제거 (보안상 이유로 녹음 생성 시에만 계약 연결 가능)
# @login_required
# @require_http_methods(["POST"])
# def recording_update_contract(request, pk):
#     """녹음과 계약 연결 업데이트"""
#     recording = get_object_or_404(Recording, pk=pk, user=request.user)
#     contract_id = request.POST.get('contract_id')
#
#     if contract_id:
#         try:
#             contract = Contract.objects.get(pk=contract_id)
#             # 권한 확인
#             if contract.tenant == request.user or contract.landlord == request.user:
#                 recording.contract = contract
#                 recording.save()
#                 messages.success(request, '계약이 연결되었습니다.')
#             else:
#                 messages.error(request, '권한이 없습니다.')
#         except Contract.DoesNotExist:
#             messages.error(request, '계약을 찾을 수 없습니다.')
#     else:
#         recording.contract = None
#         recording.save()
#         messages.success(request, '계약 연결이 해제되었습니다.')
#
#     return redirect('recordings:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def recording_delete(request, pk):
    """녹음 삭제"""
    recording = get_object_or_404(Recording, pk=pk, user=request.user)
    recording.delete()
    messages.success(request, _('녹음이 삭제되었습니다.'))
    return redirect('recordings:list')


@login_required
def recording_download_mp3(request, pk):
    """녹음 파일을 MP3로 변환하여 다운로드"""
    # 관리자는 모든 녹음 다운로드 가능, 일반 사용자는 본인 것만
    if request.user.is_staff or request.user.is_superuser:
        recording = get_object_or_404(Recording, pk=pk)
    else:
        recording = get_object_or_404(Recording, pk=pk, user=request.user)

    if not recording.audio_file:
        raise Http404(_("녹음 파일을 찾을 수 없습니다."))

    # 원본 파일 경로
    original_path = recording.audio_file.path

    if not os.path.exists(original_path):
        raise Http404(_("녹음 파일이 존재하지 않습니다."))

    try:
        # 임시 MP3 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
            temp_mp3_path = temp_mp3.name

        # WebM을 MP3로 변환
        audio = AudioSegment.from_file(original_path)
        audio.export(temp_mp3_path, format='mp3', bitrate='192k')

        # MP3 파일 응답
        response = FileResponse(
            open(temp_mp3_path, 'rb'),
            content_type='audio/mpeg'
        )

        # 다운로드 파일명 설정
        filename = f"{recording.title}.mp3"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # 임시 파일은 응답 후 삭제되도록 설정
        # (FileResponse가 파일을 읽은 후 자동으로 닫힘)
        def cleanup():
            try:
                os.unlink(temp_mp3_path)
            except:
                pass

        # 응답 후 정리
        response.close = cleanup

        return response

    except Exception as e:
        # 오류 발생 시 임시 파일 정리
        if 'temp_mp3_path' in locals() and os.path.exists(temp_mp3_path):
            os.unlink(temp_mp3_path)
        raise Http404(_("MP3 변환 중 오류가 발생했습니다: %(error)s") % {'error': str(e)})


@login_required
@require_http_methods(["POST"])
def consent_recording(request, pk):
    """녹음 기록 동의 처리"""
    recording = get_object_or_404(Recording, pk=pk)
    contract = recording.contract

    if not contract:
        messages.error(request, _('계약에 연결되지 않은 녹음입니다.'))
        return redirect('recordings:detail', pk=pk)

    # 상대방만 동의 가능 (녹음 생성자는 이미 동의한 것으로 간주)
    if request.user == recording.user:
        messages.error(request, _('본인이 등록한 녹음은 직접 동의할 수 없습니다.'))
        return redirect('recordings:detail', pk=pk)

    # 계약 당사자인지 확인
    if request.user != contract.tenant and request.user != contract.landlord:
        messages.error(request, _('권한이 없습니다.'))
        return redirect('recordings:list')

    # 이미 처리된 경우
    if recording.consent_status not in ('PENDING',):
        messages.info(request, _('이미 처리된 녹음입니다.'))
        return redirect('recordings:detail', pk=pk)

    action = request.POST.get('action')

    if action == 'approve':
        recording.consent_status = 'APPROVED'
        recording.consented_by = request.user
        recording.consented_at = timezone.now()
        recording.save(update_fields=['consent_status', 'consented_by', 'consented_at'])
        messages.success(request, _('녹음 기록에 동의하였습니다. 이 녹음은 공식 기록으로 인정됩니다.'))

    elif action == 'reject':
        reason = request.POST.get('reason', '')
        if not reason:
            messages.error(request, _('거절 사유를 입력해주세요.'))
            return redirect('recordings:detail', pk=pk)
        recording.consent_status = 'REJECTED'
        recording.consented_by = request.user
        recording.consented_at = timezone.now()
        recording.consent_rejected_reason = reason
        recording.contract = None  # 계약 연결 해제
        recording.save(update_fields=['consent_status', 'consented_by', 'consented_at', 'consent_rejected_reason', 'contract'])
        messages.warning(request, _('녹음 기록 동의를 거절하였습니다.'))


    return redirect('recordings:detail', pk=pk)
