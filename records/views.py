from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.db import transaction

from contracts.models import Contract
from .models import Record, Photo, RecordItemResponse, DefectReport, DefectPhoto, RepairRequest, RepairPhoto, RepairComment, Expense
from .forms import (
    RecordForm, PhotoForm, RecordApprovalForm,
    LandlordCreateRecordForm, TenantRequestRecordForm,
    ApproveRequestForm, FinalApprovalForm
)


@login_required
def record_list(request, contract_id):
    """계약별 입실/퇴실 기록 목록"""
    contract = get_object_or_404(Contract, pk=contract_id)

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    records = contract.records.all().prefetch_related('photos')

    # 마감일이 지난 OPEN 상태 기록 자동 제출 처리
    for record in records:
        record.auto_submit_if_deadline_passed()

    # 입실/퇴실 기록 분리
    move_in_record = records.filter(record_type='MOVE_IN').first()
    move_out_record = records.filter(record_type='MOVE_OUT').first()

    return render(request, 'records/record_list.html', {
        'contract': contract,
        'records': records,
        'move_in_record': move_in_record,
        'move_out_record': move_out_record,
    })


@login_required
def record_create(request, contract_id):
    """입실/퇴실 기록 생성"""
    contract = get_object_or_404(Contract, pk=contract_id)

    # 권한 확인: 계약 당사자만 가능
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    # 기록 타입 확인
    record_type = request.GET.get('type', 'MOVE_IN')
    if record_type not in ['MOVE_IN', 'MOVE_OUT', 'PRE_MOVE_OUT']:
        record_type = 'MOVE_IN'

    # 이미 해당 타입의 기록이 있는지 확인
    existing_record = Record.objects.filter(
        contract=contract,
        record_type=record_type
    ).first()

    if existing_record:
        messages.warning(request, _('이미 %(record_type)s 기록이 있습니다.') % {'record_type': existing_record.get_record_type_display()})
        return redirect('records:detail', pk=existing_record.pk)

    # 퇴실 기록은 입실 기록이 있어야 생성 가능
    if record_type in ('MOVE_OUT', 'PRE_MOVE_OUT'):
        move_in_record = Record.objects.filter(
            contract=contract,
            record_type='MOVE_IN'
        ).first()
        if not move_in_record:
            messages.warning(request, _('입실 기록을 먼저 등록해주세요.'))
            return redirect('records:create', contract_id=contract_id)

    if request.method == 'POST':
        form = RecordForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                record = form.save(commit=False)
                record.contract = contract
                record.save()

                # 다중 사진 업로드 처리
                images = request.FILES.getlist('images')
                categories = request.POST.getlist('categories')
                descriptions = request.POST.getlist('descriptions')

                for i, image in enumerate(images):
                    category = categories[i] if i < len(categories) else 'OTHER'
                    description = descriptions[i] if i < len(descriptions) else ''

                    Photo.objects.create(
                        record=record,
                        image=image,
                        category=category,
                        description=description
                    )

                messages.success(request, _('%(record_type)s 기록이 등록되었습니다!') % {'record_type': record.get_record_type_display()})
                return redirect('records:detail', pk=record.pk)
    else:
        form = RecordForm(initial={'record_type': record_type})

    return render(request, 'records/record_create.html', {
        'form': form,
        'contract': contract,
        'record_type': record_type,
        'photo_categories': Photo.CATEGORY_CHOICES,
    })


@login_required
def record_detail(request, pk):
    """입실/퇴실 기록 상세"""
    record = get_object_or_404(Record, pk=pk)
    contract = record.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    # 마감일이 지났으면 자동으로 제출 상태로 변경
    if record.auto_submit_if_deadline_passed():
        messages.info(request, _('마감일이 지나 자동으로 제출 처리되었습니다.'))

    # 카테고리별로 사진 그룹화
    photos_by_category = {}
    for photo in record.photos.all():
        category = photo.category
        if category not in photos_by_category:
            photos_by_category[category] = []
        photos_by_category[category].append(photo)

    # 카테고리 순서 정렬 (CATEGORY_CHOICES 순서대로)
    category_order = [c[0] for c in Photo.CATEGORY_CHOICES]
    sorted_categories = []
    for cat_code in category_order:
        if cat_code in photos_by_category:
            cat_display = dict(Photo.CATEGORY_CHOICES).get(cat_code, cat_code)
            sorted_categories.append({
                'code': cat_code,
                'name': cat_display,
                'photos': photos_by_category[cat_code]
            })

    # 비교할 다른 기록 가져오기
    compare_record = None
    if record.record_type == 'MOVE_IN':
        compare_record = Record.objects.filter(
            contract=contract,
            record_type__in=['MOVE_OUT', 'PRE_MOVE_OUT']
        ).order_by('-created_at').first()
    elif record.record_type in ('MOVE_OUT', 'PRE_MOVE_OUT'):
        compare_record = Record.objects.filter(
            contract=contract,
            record_type='MOVE_IN'
        ).first()

    # 사진 업로드 가능 여부 (템플릿에서 사용)
    can_upload_photos = record.can_upload_photos(request.user)

    # 점검 항목 응답 (상태 체크 결과)
    item_responses = {}
    for resp in record.item_responses.select_related('template_item__section').all():
        item_responses[resp.template_item_id] = resp

    return render(request, 'records/record_detail.html', {
        'record': record,
        'contract': contract,
        'sorted_categories': sorted_categories,
        'compare_record': compare_record,
        'photo_categories': Photo.CATEGORY_CHOICES,
        'can_upload_photos': can_upload_photos,
        'item_responses': item_responses,
    })


@login_required
def record_compare(request, contract_id):
    """입실/퇴실 사진 비교"""
    contract = get_object_or_404(Contract, pk=contract_id)

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    move_in_record = Record.objects.filter(
        contract=contract,
        record_type='MOVE_IN'
    ).first()

    move_out_record = Record.objects.filter(
        contract=contract,
        record_type='MOVE_OUT'
    ).first()

    if not move_in_record or not move_out_record:
        messages.warning(request, _('입실/퇴실 기록이 모두 있어야 비교할 수 있습니다.'))
        return redirect('records:list', contract_id=contract_id)

    # 카테고리별 비교 데이터 생성
    comparison_data = []
    for cat_code, cat_name in Photo.CATEGORY_CHOICES:
        move_in_photos = list(move_in_record.photos.filter(category=cat_code))
        move_out_photos = list(move_out_record.photos.filter(category=cat_code))

        if move_in_photos or move_out_photos:
            comparison_data.append({
                'category_code': cat_code,
                'category_name': cat_name,
                'move_in_photos': move_in_photos,
                'move_out_photos': move_out_photos,
            })

    return render(request, 'records/record_compare.html', {
        'contract': contract,
        'move_in_record': move_in_record,
        'move_out_record': move_out_record,
        'comparison_data': comparison_data,
    })


@login_required
@require_http_methods(["POST"])
def record_approve(request, pk):
    """기록 승인/반려 처리 (임대인 전용) - 기존 호환성 유지"""
    record = get_object_or_404(Record, pk=pk)
    contract = record.contract

    # 권한 확인: 임대인만 승인 가능
    if contract.landlord != request.user:
        messages.error(request, _('임대인만 승인할 수 있습니다.'))
        return redirect('records:detail', pk=pk)

    # 제출 상태에서만 처리 가능 (새로운 플로우)
    if record.status not in ['SUBMITTED', 'OPEN']:
        messages.warning(request, _('현재 상태에서는 승인/반려할 수 없습니다.'))
        return redirect('records:detail', pk=pk)

    form = RecordApprovalForm(request.POST)
    if form.is_valid():
        approval_status = form.cleaned_data['approval_status']
        landlord_comment = form.cleaned_data['landlord_comment']

        record.status = approval_status  # APPROVED or REJECTED
        record.landlord_comment = landlord_comment
        record.landlord_approved_at = timezone.now()
        record.save()

        if approval_status == 'APPROVED':
            messages.success(request, _('%(record_type)s 기록이 승인되었습니다.') % {'record_type': record.get_record_type_display()})
        else:
            messages.info(request, _('%(record_type)s 기록이 반려되었습니다.') % {'record_type': record.get_record_type_display()})
    else:
        for error in form.errors.values():
            messages.error(request, error)

    return redirect('records:detail', pk=pk)


@login_required
def add_photos(request, pk):
    """기존 기록에 사진/점검 항목 추가"""
    from core.templates_engine.models import TemplateItem

    record = get_object_or_404(Record, pk=pk)
    contract = record.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    # can_upload_photos 메서드로 업로드 가능 여부 확인
    if not record.can_upload_photos(request.user):
        if record.status == 'APPROVED':
            messages.warning(request, _('승인된 기록에는 사진을 추가할 수 없습니다.'))
        elif record.status == 'REQUESTED':
            messages.warning(request, _('아직 승인되지 않은 요청입니다. 임대인의 승인을 기다려주세요.'))
        elif record.status == 'SUBMITTED':
            messages.warning(request, _('이미 제출된 기록입니다. 임대인의 처리를 기다려주세요.'))
        elif record.is_deadline_passed():
            messages.warning(request, _('업로드 마감일이 지났습니다. 임대인에게 마감일 연장을 요청해주세요.'))
        else:
            messages.warning(request, _('현재 상태에서는 사진을 추가할 수 없습니다.'))
        return redirect('records:detail', pk=pk)

    # 템플릿 확인
    template = record.template or contract.template
    use_template = template is not None

    if request.method == 'POST':
        # 1) 사진 업로드 처리
        images = request.FILES.getlist('images')
        categories = request.POST.getlist('categories')
        template_items = request.POST.getlist('template_items')
        descriptions = request.POST.getlist('descriptions')

        photo_count = 0
        for i, image in enumerate(images):
            category = categories[i] if i < len(categories) else 'OTHER'
            description = descriptions[i] if i < len(descriptions) else ''

            template_item = None
            if template_items and i < len(template_items) and template_items[i]:
                try:
                    template_item = TemplateItem.objects.get(pk=template_items[i])
                except TemplateItem.DoesNotExist:
                    pass

            Photo.objects.create(
                record=record,
                image=image,
                category=category,
                template_item=template_item,
                description=description
            )
            photo_count += 1

        # 2) 점검 항목 응답 저장 (RecordItemResponse)
        if use_template:
            for section in template.sections.all():
                for item in section.items.all():
                    condition_key = f'condition_{item.pk}'
                    response_key = f'response_{item.pk}'
                    notes_key = f'notes_{item.pk}'

                    condition = request.POST.get(condition_key)
                    if condition:  # 응답이 있는 경우만 저장
                        response_value = request.POST.get(response_key, '')
                        notes_val = request.POST.get(notes_key, '')

                        # CHECKBOX: on → true, 없으면 false
                        if item.item_type == 'CHECKBOX':
                            response_value = 'true' if response_value else 'false'

                        RecordItemResponse.objects.update_or_create(
                            record=record,
                            template_item=item,
                            defaults={
                                'condition_status': condition,
                                'response_value': response_value,
                                'notes': notes_val,
                            }
                        )

        if photo_count > 0:
            messages.success(request, _('%(count)s개의 사진이 추가되었습니다.') % {'count': photo_count})
        else:
            messages.success(request, _('점검 항목이 저장되었습니다.'))
        return redirect('records:detail', pk=pk)

    # 템플릿 기반 구조 생성 (GET)
    template_sections = []
    if use_template:
        current_language = get_language()
        for section in template.sections.all().order_by('order'):
            section_name = section.get_name_by_language(current_language)

            items = []
            for item in section.items.all().order_by('order'):
                item_name = item.get_name_by_language(current_language)
                item_desc = item.get_description_by_language(current_language)

                existing_photos = record.photos.filter(template_item=item).count()
                existing_response = RecordItemResponse.objects.filter(
                    record=record, template_item=item
                ).first()

                items.append({
                    'id': item.pk,
                    'code': item.code,
                    'name': item_name,
                    'description': item_desc,
                    'item_type': item.item_type,
                    'options': item.options or [],
                    'is_required': item.is_required,
                    'min_photos': item.min_photos,
                    'max_photos': item.max_photos,
                    'existing_photos': existing_photos,
                    'existing_response': existing_response,
                    'responsibility_hint': item.get_responsibility_hint_display(),
                })

            if items:
                template_sections.append({
                    'code': section.code,
                    'name': section_name,
                    'is_required': section.is_required,
                    'items': items,
                })

    return render(request, 'records/add_photos.html', {
        'record': record,
        'contract': contract,
        'photo_categories': Photo.CATEGORY_CHOICES,
        'use_template': use_template,
        'template': template,
        'template_sections': template_sections,
        'condition_choices': RecordItemResponse.CONDITION_STATUS_CHOICES,
    })


@login_required
@require_http_methods(["POST"])
def delete_photo(request, photo_id):
    """사진 삭제"""
    photo = get_object_or_404(Photo, pk=photo_id)
    record = photo.record
    contract = record.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        return JsonResponse({'success': False, 'error': _('권한이 없습니다.')}, status=403)

    # 승인된 기록의 사진은 삭제 불가
    if record.status == 'APPROVED':
        return JsonResponse({'success': False, 'error': _('승인된 기록의 사진은 삭제할 수 없습니다.')}, status=400)

    # 마감일이 지났으면 삭제 불가
    if record.is_deadline_passed():
        return JsonResponse({'success': False, 'error': _('마감일이 지나 사진을 삭제할 수 없습니다.')}, status=400)

    photo.delete()
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def update_photo(request, photo_id):
    """사진 정보 수정 (카테고리, 설명)"""
    photo = get_object_or_404(Photo, pk=photo_id)
    record = photo.record
    contract = record.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        return JsonResponse({'success': False, 'error': _('권한이 없습니다.')}, status=403)

    # 승인된 기록의 사진은 수정 불가
    if record.status == 'APPROVED':
        return JsonResponse({'success': False, 'error': _('승인된 기록의 사진은 수정할 수 없습니다.')}, status=400)

    # 마감일이 지났으면 수정 불가
    if record.is_deadline_passed():
        return JsonResponse({'success': False, 'error': _('마감일이 지나 사진을 수정할 수 없습니다.')}, status=400)

    category = request.POST.get('category')
    description = request.POST.get('description', '')

    if category:
        photo.category = category
    photo.description = description
    photo.save()

    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def approve_photo(request, photo_id):
    """사진 개별 승인 (임대인 전용)"""
    photo = get_object_or_404(Photo, pk=photo_id)
    record = photo.record
    contract = record.contract

    # 권한 확인: 임대인만 승인 가능
    if contract.landlord != request.user:
        return JsonResponse({'success': False, 'error': _('임대인만 승인할 수 있습니다.')}, status=403)

    photo.approval_status = 'APPROVED'
    photo.rejection_reason = ''
    photo.save()

    # 모든 사진이 승인되었는지 확인 (UI 표시용, 기록 자동 승인 안함)
    all_approved = not record.photos.exclude(approval_status='APPROVED').exists()

    return JsonResponse({
        'success': True,
        'photo_status': photo.approval_status,
        'all_approved': all_approved
    })


@login_required
@require_http_methods(["POST"])
def reject_photo(request, photo_id):
    """사진 개별 반려 (임대인 전용)"""
    photo = get_object_or_404(Photo, pk=photo_id)
    record = photo.record
    contract = record.contract

    # 권한 확인: 임대인만 반려 가능
    if contract.landlord != request.user:
        return JsonResponse({'success': False, 'error': _('임대인만 반려할 수 있습니다.')}, status=403)

    reason = request.POST.get('reason', '')
    if not reason:
        return JsonResponse({'success': False, 'error': _('반려 사유를 입력해주세요.')}, status=400)

    photo.approval_status = 'REJECTED'
    photo.rejection_reason = reason
    photo.save()

    # 기록 전체 상태도 반려로 변경
    record.status = 'REJECTED'
    record.save()

    return JsonResponse({
        'success': True,
        'photo_status': photo.approval_status,
        'reason': reason
    })


# =====================================================
# 새로운 뷰: 임대인용
# =====================================================

@login_required
def landlord_create_record(request, contract_id):
    """임대인이 기록 생성 + 마감일 설정"""
    contract = get_object_or_404(Contract, pk=contract_id)

    # 권한 확인: 임대인만 가능
    if contract.landlord != request.user:
        messages.error(request, _('임대인만 기록을 생성할 수 있습니다.'))
        return redirect('contracts:detail', pk=contract_id)

    # 기록 타입 확인
    record_type = request.GET.get('type', 'MOVE_IN')
    if record_type not in ['MOVE_IN', 'MOVE_OUT', 'PRE_MOVE_OUT']:
        record_type = 'MOVE_IN'

    # 이미 해당 타입의 기록이 있는지 확인
    existing_record = Record.objects.filter(
        contract=contract,
        record_type=record_type
    ).first()

    if existing_record:
        messages.warning(request, _('이미 %(record_type)s 기록이 있습니다.') % {'record_type': existing_record.get_record_type_display()})
        return redirect('records:detail', pk=existing_record.pk)

    # 퇴실 기록은 입실 기록이 있어야 생성 가능
    if record_type in ('MOVE_OUT', 'PRE_MOVE_OUT'):
        move_in_record = Record.objects.filter(
            contract=contract,
            record_type='MOVE_IN'
        ).first()
        if not move_in_record:
            messages.warning(request, _('입실 기록을 먼저 등록해주세요.'))
            return redirect('records:landlord_create', contract_id=contract_id)

    if request.method == 'POST':
        form = LandlordCreateRecordForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                record = form.save(commit=False)
                record.contract = contract
                record.status = 'OPEN'
                record.created_by = request.user
                record.upload_deadline = form.cleaned_data.get('upload_deadline')
                # 임차인에게 알림
                record.is_read_by_tenant = False
                record.save()

                messages.success(request, _('%(record_type)s 기록이 생성되었습니다. 임차인이 사진을 업로드할 수 있습니다.') % {'record_type': record.get_record_type_display()})
                return redirect('records:detail', pk=record.pk)
    else:
        form = LandlordCreateRecordForm(initial={'record_type': record_type})

    return render(request, 'records/landlord_create_record.html', {
        'form': form,
        'contract': contract,
        'record_type': record_type,
    })


@login_required
@require_http_methods(["POST"])
def approve_tenant_request(request, pk):
    """임차인 요청 승인 (REQUESTED -> OPEN)"""
    record = get_object_or_404(Record, pk=pk)
    contract = record.contract

    # 권한 확인: 임대인만 가능
    if contract.landlord != request.user:
        messages.error(request, _('임대인만 요청을 승인할 수 있습니다.'))
        return redirect('records:detail', pk=pk)

    # 상태 확인
    if record.status != 'REQUESTED':
        messages.warning(request, _('승인 대기 중인 요청이 아닙니다.'))
        return redirect('records:detail', pk=pk)

    form = ApproveRequestForm(request.POST)
    if form.is_valid():
        record.status = 'OPEN'
        record.upload_deadline = form.cleaned_data.get('upload_deadline')
        # 임차인에게 알림
        record.is_read_by_tenant = False
        record.save()

        messages.success(request, _('%(record_type)s 요청이 승인되었습니다. 임차인이 사진을 업로드할 수 있습니다.') % {'record_type': record.get_record_type_display()})
    else:
        for error in form.errors.values():
            messages.error(request, error)

    return redirect('records:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def final_approve(request, pk):
    """최종 승인/반려 (임대인 전용)"""
    record = get_object_or_404(Record, pk=pk)
    contract = record.contract

    # 권한 확인: 임대인만 가능
    if contract.landlord != request.user:
        messages.error(request, _('임대인만 최종 승인할 수 있습니다.'))
        return redirect('records:detail', pk=pk)

    # 제출 상태에서만 처리 가능
    if record.status != 'SUBMITTED':
        messages.warning(request, _('제출된 기록만 승인/반려할 수 있습니다.'))
        return redirect('records:detail', pk=pk)

    form = FinalApprovalForm(request.POST)
    if form.is_valid():
        action = form.cleaned_data['action']
        landlord_comment = form.cleaned_data.get('landlord_comment', '')

        record.status = action  # 'APPROVED' or 'REJECTED'
        record.landlord_comment = landlord_comment
        record.landlord_approved_at = timezone.now()
        # 임차인에게 알림
        record.is_read_by_tenant = False
        record.save()

        if action == 'APPROVED':
            messages.success(request, _('%(record_type)s 기록이 최종 승인되었습니다.') % {'record_type': record.get_record_type_display()})
        else:
            messages.info(request, _('%(record_type)s 기록이 반려되었습니다. 임차인이 수정 후 다시 제출할 수 있습니다.') % {'record_type': record.get_record_type_display()})
    else:
        for error in form.errors.values():
            messages.error(request, error)

    return redirect('records:detail', pk=pk)


# =====================================================
# 새로운 뷰: 임차인용
# =====================================================

@login_required
def tenant_request_record(request, contract_id):
    """임차인이 임대인에게 기록 등록 요청"""
    contract = get_object_or_404(Contract, pk=contract_id)

    # 권한 확인: 임차인만 가능
    if contract.tenant != request.user:
        messages.error(request, _('임차인만 기록 등록을 요청할 수 있습니다.'))
        return redirect('contracts:detail', pk=contract_id)

    # 기록 타입 확인
    record_type = request.GET.get('type', 'MOVE_IN')
    if record_type not in ['MOVE_IN', 'MOVE_OUT', 'PRE_MOVE_OUT']:
        record_type = 'MOVE_IN'

    # 이미 해당 타입의 기록이 있는지 확인
    existing_record = Record.objects.filter(
        contract=contract,
        record_type=record_type
    ).first()

    if existing_record:
        messages.warning(request, _('이미 %(record_type)s 기록이 있습니다.') % {'record_type': existing_record.get_record_type_display()})
        return redirect('records:detail', pk=existing_record.pk)

    # 퇴실 기록은 입실 기록이 있어야 요청 가능
    if record_type in ('MOVE_OUT', 'PRE_MOVE_OUT'):
        move_in_record = Record.objects.filter(
            contract=contract,
            record_type='MOVE_IN'
        ).first()
        if not move_in_record:
            messages.warning(request, _('입실 기록이 먼저 등록되어야 퇴실 기록을 요청할 수 있습니다.'))
            return redirect('records:tenant_request', contract_id=contract_id)

    if request.method == 'POST':
        form = TenantRequestRecordForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                record = form.save(commit=False)
                record.contract = contract
                record.status = 'REQUESTED'
                record.created_by = request.user
                # 임대인에게 알림
                record.is_read_by_landlord = False
                record.save()

                messages.success(request, _('%(record_type)s 기록 등록이 요청되었습니다. 임대인의 승인을 기다려주세요.') % {'record_type': record.get_record_type_display()})
                return redirect('records:detail', pk=record.pk)
    else:
        form = TenantRequestRecordForm(initial={'record_type': record_type})

    return render(request, 'records/tenant_request_record.html', {
        'form': form,
        'contract': contract,
        'record_type': record_type,
    })


@login_required
@require_http_methods(["POST"])
def submit_record(request, pk):
    """사진 업로드 완료 후 제출 (임차인 전용)"""
    record = get_object_or_404(Record, pk=pk)
    contract = record.contract

    # 권한 확인: 임차인만 가능
    if contract.tenant != request.user:
        messages.error(request, _('임차인만 기록을 제출할 수 있습니다.'))
        return redirect('records:detail', pk=pk)

    # 상태 확인: OPEN 또는 REJECTED 상태에서만 제출 가능
    if record.status not in ['OPEN', 'REJECTED']:
        messages.warning(request, _('현재 상태에서는 제출할 수 없습니다.'))
        return redirect('records:detail', pk=pk)

    # 사진이 있는지 확인
    if not record.photos.exists():
        messages.warning(request, _('사진을 하나 이상 업로드한 후 제출해주세요.'))
        return redirect('records:detail', pk=pk)

    # 필수 점검 항목 확인
    template = record.template or contract.template
    if template:
        from core.templates_engine.models import TemplateItem
        required_items = TemplateItem.objects.filter(
            section__template=template,
            is_required=True
        )
        missing = []
        for item in required_items:
            if item.item_type == 'PHOTO':
                if not record.photos.filter(template_item=item).exists():
                    missing.append(item.name_ko)
            else:
                if not record.item_responses.filter(template_item=item).exclude(response_value='').exists():
                    missing.append(item.name_ko)
        if missing:
            messages.warning(request, _('필수 항목이 완료되지 않았습니다: %(items)s') % {'items': ', '.join(missing)})
            return redirect('records:detail', pk=pk)

    # 마감일 체크
    if record.is_deadline_passed():
        messages.error(request, _('마감일이 지났습니다. 임대인에게 문의해주세요.'))
        return redirect('records:detail', pk=pk)

    record.status = 'SUBMITTED'
    record.submitted_at = timezone.now()
    # 제출하면 임대인 알림 읽음 상태 초기화
    record.is_read_by_landlord = False
    record.save()

    messages.success(request, _('기록이 제출되었습니다. 임대인의 최종 승인을 기다려주세요.'))
    return redirect('records:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def mark_record_read(request, pk):
    """기록 알림 읽음 처리"""
    record = get_object_or_404(Record, pk=pk)
    contract = record.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        return JsonResponse({'success': False, 'error': _('권한이 없습니다.')}, status=403)

    # 사용자 유형에 따라 읽음 처리
    if request.user == contract.landlord:
        record.is_read_by_landlord = True
    else:
        record.is_read_by_tenant = True
    record.save(update_fields=['is_read_by_landlord', 'is_read_by_tenant', 'updated_at'])

    return JsonResponse({'success': True})


@login_required
@require_GET
def get_template_structure_api(request, pk):
    """기록의 템플릿 구조 반환 API"""
    record = get_object_or_404(Record, pk=pk)
    contract = record.contract

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        return JsonResponse({'success': False, 'error': _('권한이 없습니다.')}, status=403)

    # 템플릿 확인
    template = record.template or contract.template
    if not template:
        return JsonResponse({
            'success': True,
            'use_template': False,
            'sections': []
        })

    current_language = get_language()

    # 템플릿 구조 반환
    sections_data = []
    for section in template.sections.all().order_by('order'):
        # 언어에 따른 섹션명 선택
        if current_language == 'ja' and section.name_ja:
            section_name = section.name_ja
        elif current_language == 'en' and section.name_en:
            section_name = section.name_en
        else:
            section_name = section.name_ko

        items_data = []
        for item in section.items.all().order_by('order'):
            # 언어에 따른 항목명 선택
            if current_language == 'ja' and item.name_ja:
                item_name = item.name_ja
            elif current_language == 'en' and item.name_en:
                item_name = item.name_en
            else:
                item_name = item.name_ko

            # 기존 업로드된 사진 수
            existing_photos = record.photos.filter(template_item=item).count()

            items_data.append({
                'id': item.pk,
                'code': item.code,
                'name': item_name,
                'item_type': item.item_type,
                'is_required': item.is_required,
                'min_photos': item.min_photos,
                'max_photos': item.max_photos,
                'responsibility_hint': item.responsibility_hint,
                'existing_photos': existing_photos,
            })

        sections_data.append({
            'id': section.pk,
            'code': section.code,
            'name': section_name,
            'is_required': section.is_required,
            'items': items_data,
        })

    return JsonResponse({
        'success': True,
        'use_template': True,
        'template_name': template.name,
        'sections': sections_data,
    })


# ========== 하자 통지 기록 ==========

@login_required
def defect_list(request, contract_id):
    """계약별 하자 통지 목록"""
    contract = get_object_or_404(Contract, pk=contract_id)

    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    defects = DefectReport.objects.filter(contract=contract).order_by('-created_at')

    return render(request, 'records/defect_list.html', {
        'contract': contract,
        'defects': defects,
    })


@login_required
def defect_create(request, contract_id):
    """하자 신고 (임차인/임대인 모두 가능)"""
    contract = get_object_or_404(Contract, pk=contract_id)

    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        location = request.POST.get('location', '').strip()
        severity = request.POST.get('severity', 'MINOR')

        if not title or not description:
            messages.error(request, _('제목과 설명을 입력해주세요.'))
            return render(request, 'records/defect_create.html', {
                'contract': contract,
            })

        defect = DefectReport.objects.create(
            contract=contract,
            reported_by=request.user,
            title=title,
            description=description,
            location=location,
            severity=severity,
            is_read_by_landlord=request.user == contract.landlord,
            is_read_by_tenant=request.user == contract.tenant,
        )

        # 사진 첨부
        images = request.FILES.getlist('images')
        for image in images:
            DefectPhoto.objects.create(
                defect_report=defect,
                image=image,
            )

        messages.success(request, _('하자 통지가 등록되었습니다.'))
        return redirect('records:defect_detail', pk=defect.pk)

    return render(request, 'records/defect_create.html', {
        'contract': contract,
    })


@login_required
def defect_detail(request, pk):
    """하자 통지 상세"""
    defect = get_object_or_404(DefectReport, pk=pk)
    contract = defect.contract

    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    # 읽음 처리
    if request.user == contract.landlord and not defect.is_read_by_landlord:
        defect.is_read_by_landlord = True
        defect.save(update_fields=['is_read_by_landlord'])
    elif request.user == contract.tenant and not defect.is_read_by_tenant:
        defect.is_read_by_tenant = True
        defect.save(update_fields=['is_read_by_tenant'])

    return render(request, 'records/defect_detail.html', {
        'defect': defect,
        'contract': contract,
    })


@login_required
@require_http_methods(["POST"])
def defect_respond(request, pk):
    """하자 통지 응답 (임대인)"""
    defect = get_object_or_404(DefectReport, pk=pk)
    contract = defect.contract

    if contract.landlord != request.user:
        messages.error(request, _('임대인만 응답할 수 있습니다.'))
        return redirect('records:defect_detail', pk=pk)

    action = request.POST.get('action')
    response_text = request.POST.get('response', '').strip()

    if action == 'acknowledge':
        defect.status = 'ACKNOWLEDGED'
        defect.acknowledged_at = timezone.now()
        defect.landlord_response = response_text
        defect.is_read_by_tenant = False
        defect.save()
        messages.success(request, _('하자 통지를 확인하였습니다.'))

    elif action == 'in_progress':
        defect.status = 'IN_PROGRESS'
        defect.landlord_response = response_text
        defect.is_read_by_tenant = False
        defect.save()
        messages.success(request, _('처리 중으로 변경되었습니다.'))

    elif action == 'resolve':
        if not response_text:
            messages.error(request, _('해결 내용을 입력해주세요.'))
            return redirect('records:defect_detail', pk=pk)
        defect.status = 'RESOLVED'
        defect.resolved_at = timezone.now()
        defect.landlord_response = response_text
        defect.is_read_by_tenant = False
        defect.save()
        messages.success(request, _('하자가 해결 처리되었습니다.'))

    return redirect('records:defect_detail', pk=pk)


# ========== 수리 요청/응답 ==========

@login_required
def repair_list(request, contract_id):
    """계약별 수리 요청 목록"""
    contract = get_object_or_404(Contract, pk=contract_id)
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    repairs = RepairRequest.objects.filter(contract=contract).order_by('-created_at')
    return render(request, 'records/repair_list.html', {
        'contract': contract,
        'repairs': repairs,
    })


@login_required
def repair_create(request, contract_id):
    """수리 요청 생성"""
    contract = get_object_or_404(Contract, pk=contract_id)
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    defect_id = request.GET.get('defect')
    defect = None
    if defect_id:
        defect = DefectReport.objects.filter(pk=defect_id, contract=contract).first()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        location = request.POST.get('location', '').strip()
        defect_link_id = request.POST.get('defect_report')

        if not title or not description:
            messages.error(request, _('제목과 설명을 입력해주세요.'))
            return render(request, 'records/repair_create.html', {
                'contract': contract, 'defect': defect,
            })

        defect_link = None
        if defect_link_id:
            defect_link = DefectReport.objects.filter(pk=defect_link_id, contract=contract).first()

        repair = RepairRequest.objects.create(
            contract=contract,
            defect_report=defect_link,
            requested_by=request.user,
            title=title,
            description=description,
            location=location,
            is_read_by_landlord=request.user == contract.landlord,
            is_read_by_tenant=request.user == contract.tenant,
        )

        images = request.FILES.getlist('images')
        for image in images:
            RepairPhoto.objects.create(repair_request=repair, image=image, photo_type='ISSUE')

        messages.success(request, _('수리 요청이 등록되었습니다.'))
        return redirect('records:repair_detail', pk=repair.pk)

    open_defects = DefectReport.objects.filter(
        contract=contract, status__in=['REPORTED', 'ACKNOWLEDGED', 'IN_PROGRESS']
    )
    return render(request, 'records/repair_create.html', {
        'contract': contract, 'defect': defect, 'open_defects': open_defects,
    })


@login_required
def repair_detail(request, pk):
    """수리 요청 상세"""
    repair = get_object_or_404(RepairRequest, pk=pk)
    contract = repair.contract

    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    if request.user == contract.landlord and not repair.is_read_by_landlord:
        repair.is_read_by_landlord = True
        repair.save(update_fields=['is_read_by_landlord'])
    elif request.user == contract.tenant and not repair.is_read_by_tenant:
        repair.is_read_by_tenant = True
        repair.save(update_fields=['is_read_by_tenant'])

    return render(request, 'records/repair_detail.html', {
        'repair': repair,
        'contract': contract,
        'comments': repair.comments.select_related('author').all(),
        'issue_photos': repair.photos.filter(photo_type='ISSUE'),
        'progress_photos': repair.photos.filter(photo_type='IN_PROGRESS'),
        'completed_photos': repair.photos.filter(photo_type='COMPLETED'),
    })


@login_required
@require_http_methods(["POST"])
def repair_update_status(request, pk):
    """수리 상태 변경"""
    repair = get_object_or_404(RepairRequest, pk=pk)
    contract = repair.contract
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    action = request.POST.get('action')

    if action == 'provide_quote' and request.user == contract.landlord:
        cost = request.POST.get('estimated_cost', '').strip()
        if not cost:
            messages.error(request, _('견적 금액을 입력해주세요.'))
            return redirect('records:repair_detail', pk=pk)
        repair.status = 'QUOTE_PROVIDED'
        repair.estimated_cost = int(cost)
        repair.is_read_by_tenant = False
        repair.save()
        messages.success(request, _('견적이 제시되었습니다.'))

    elif action == 'approve_quote' and request.user == contract.tenant:
        repair.status = 'APPROVED'
        repair.approved_at = timezone.now()
        repair.is_read_by_landlord = False
        repair.save()
        messages.success(request, _('견적이 승인되었습니다.'))

    elif action == 'start_repair' and request.user == contract.landlord:
        repair.status = 'IN_PROGRESS'
        repair.started_at = timezone.now()
        repair.is_read_by_tenant = False
        repair.save()
        for image in request.FILES.getlist('images'):
            RepairPhoto.objects.create(repair_request=repair, image=image, photo_type='IN_PROGRESS')
        messages.success(request, _('수리가 시작되었습니다.'))

    elif action == 'complete_repair' and request.user == contract.landlord:
        actual_cost = request.POST.get('actual_cost', '').strip()
        repair.status = 'COMPLETED'
        repair.completed_at = timezone.now()
        if actual_cost:
            repair.actual_cost = int(actual_cost)
        repair.is_read_by_tenant = False
        repair.save()
        for image in request.FILES.getlist('images'):
            RepairPhoto.objects.create(repair_request=repair, image=image, photo_type='COMPLETED')
        messages.success(request, _('수리가 완료 처리되었습니다.'))

    elif action == 'cancel':
        repair.status = 'CANCELLED'
        repair.save()
        messages.info(request, _('수리 요청이 취소되었습니다.'))

    return redirect('records:repair_detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def repair_add_comment(request, pk):
    """수리 코멘트 추가"""
    repair = get_object_or_404(RepairRequest, pk=pk)
    contract = repair.contract
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    message_text = request.POST.get('message', '').strip()
    if message_text:
        RepairComment.objects.create(repair_request=repair, author=request.user, message=message_text)
        if request.user == contract.tenant:
            repair.is_read_by_landlord = False
        else:
            repair.is_read_by_tenant = False
        repair.save(update_fields=['is_read_by_landlord', 'is_read_by_tenant'])

    return redirect('records:repair_detail', pk=pk)


# ========== 비용/영수증 관리 ==========

@login_required
def expense_list(request, contract_id):
    """계약별 비용 목록"""
    contract = get_object_or_404(Contract, pk=contract_id)
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    expenses = Expense.objects.filter(contract=contract)
    from django.db.models import Sum
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0
    tenant_total = expenses.filter(paid_by='TENANT').aggregate(total=Sum('amount'))['total'] or 0
    landlord_total = expenses.filter(paid_by='LANDLORD').aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'records/expense_list.html', {
        'contract': contract,
        'expenses': expenses,
        'total': total,
        'tenant_total': tenant_total,
        'landlord_total': landlord_total,
    })


@login_required
def expense_create(request, contract_id):
    """비용 등록"""
    contract = get_object_or_404(Contract, pk=contract_id)
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    repair_id = request.GET.get('repair')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        amount = request.POST.get('amount', '').strip()
        category = request.POST.get('category', 'OTHER')
        paid_by = request.POST.get('paid_by', 'LANDLORD')
        expense_date = request.POST.get('expense_date', '')
        description = request.POST.get('description', '')
        repair_link_id = request.POST.get('repair_request')

        if not title or not amount or not expense_date:
            messages.error(request, _('제목, 금액, 날짜는 필수입니다.'))
            return render(request, 'records/expense_create.html', {'contract': contract})

        repair_link = None
        if repair_link_id:
            repair_link = RepairRequest.objects.filter(pk=repair_link_id, contract=contract).first()

        expense = Expense.objects.create(
            contract=contract,
            repair_request=repair_link,
            created_by=request.user,
            title=title,
            description=description,
            category=category,
            amount=int(amount),
            paid_by=paid_by,
            expense_date=expense_date,
            receipt_image=request.FILES.get('receipt_image'),
            is_read_by_landlord=request.user == contract.landlord,
            is_read_by_tenant=request.user == contract.tenant,
        )

        messages.success(request, _('비용이 등록되었습니다.'))
        return redirect('records:expense_list', contract_id=contract.pk)

    repairs = RepairRequest.objects.filter(contract=contract)
    return render(request, 'records/expense_create.html', {
        'contract': contract,
        'repairs': repairs,
        'repair_id': repair_id,
    })


@login_required
def expense_detail(request, pk):
    """비용 상세"""
    expense = get_object_or_404(Expense, pk=pk)
    contract = expense.contract
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('접근 권한이 없습니다.'))
        return redirect('contracts:list')

    # 읽음 처리
    if request.user == contract.landlord and not expense.is_read_by_landlord:
        expense.is_read_by_landlord = True
        expense.save(update_fields=['is_read_by_landlord'])
    elif request.user == contract.tenant and not expense.is_read_by_tenant:
        expense.is_read_by_tenant = True
        expense.save(update_fields=['is_read_by_tenant'])

    return render(request, 'records/expense_detail.html', {
        'expense': expense, 'contract': contract,
    })
