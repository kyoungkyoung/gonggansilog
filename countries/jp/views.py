from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _

from contracts.models import Contract
from .models import ContractJapanExtension, JapanRestorationItem
from .forms import ContractJapanExtensionForm


@login_required
def edit_japan_extension(request, contract_pk):
    """일본 계약 확장 정보 수정"""
    contract = get_object_or_404(Contract, pk=contract_pk)

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('You do not have permission to edit this contract.'))
        return redirect('contracts:detail', pk=contract_pk)

    # 일본 계약인지 확인
    if contract.country != 'JP':
        messages.warning(request, _('This feature is only available for Japan contracts.'))
        return redirect('contracts:detail', pk=contract_pk)

    # 기존 확장 정보 가져오기 또는 새로 생성
    try:
        extension = contract.japan_extension
    except ContractJapanExtension.DoesNotExist:
        extension = None

    if request.method == 'POST':
        form = ContractJapanExtensionForm(request.POST, instance=extension)
        if form.is_valid():
            japan_ext = form.save(commit=False)
            japan_ext.contract = contract
            japan_ext.save()
            messages.success(request, _('Japan contract information has been saved.'))
            return redirect('contracts:detail', pk=contract_pk)
    else:
        form = ContractJapanExtensionForm(instance=extension)

    return render(request, 'countries/jp/japan_extension_form.html', {
        'form': form,
        'contract': contract,
        'extension': extension,
    })


@login_required
def restoration_items_api(request):
    """일본 원상회복 항목 API"""
    category = request.GET.get('category', '')
    property_type = request.GET.get('property_type', '')
    responsibility = request.GET.get('responsibility', '')

    items = JapanRestorationItem.objects.filter(is_active=True)

    if category:
        items = items.filter(category=category)
    if property_type:
        items = items.filter(property_type__in=[property_type, 'BOTH'])
    if responsibility:
        items = items.filter(responsibility=responsibility)

    items = items.order_by('category', 'order')

    data = []
    for item in items:
        data.append({
            'id': item.id,
            'code': item.code,
            'category': item.category,
            'category_display': item.get_category_display(),
            'description_ja': item.description_ja,
            'description_en': item.description_en,
            'description_ko': item.description_ko,
            'responsibility': item.responsibility,
            'responsibility_display': item.get_responsibility_display(),
            'is_normal_wear': item.is_normal_wear,
            'cost_unit': item.cost_unit,
            'typical_cost_range': item.typical_cost_range,
            'depreciation_years': item.depreciation_years,
        })

    return JsonResponse({'items': data})


@login_required
def restoration_guide(request, contract_pk):
    """일본 원상회복 가이드 페이지"""
    contract = get_object_or_404(Contract, pk=contract_pk)

    # 권한 확인
    if contract.tenant != request.user and contract.landlord != request.user:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('contracts:list')

    # 일본 계약인지 확인
    if contract.country != 'JP':
        messages.warning(request, _('This feature is only available for Japan contracts.'))
        return redirect('contracts:detail', pk=contract_pk)

    # 카테고리별 원상회복 항목 조회
    property_type = (contract.template.property_type if contract.template else None) or 'RESIDENTIAL'
    categories = JapanRestorationItem.CATEGORY_CHOICES

    items_by_category = {}
    for cat_code, cat_name in categories:
        items = JapanRestorationItem.objects.filter(
            is_active=True,
            category=cat_code,
            property_type__in=[property_type, 'BOTH']
        ).order_by('order')
        if items.exists():
            items_by_category[cat_code] = {
                'name': cat_name,
                'items': items
            }

    return render(request, 'countries/jp/restoration_guide.html', {
        'contract': contract,
        'items_by_category': items_by_category,
        'property_type': property_type,
    })
