from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ContractJapanExtension


class ContractJapanExtensionForm(forms.ModelForm):
    """일본 계약 확장 정보 입력 폼"""

    class Meta:
        model = ContractJapanExtension
        fields = [
            'contract_type',
            'renewal_type',
            'renewal_fee',
            'key_money',
            'deposit',
            'guarantee_fee',
            'management_fee',
            'has_special_restoration_clause',
            'restoration_clause',
            'agency_name',
            'agency_license',
        ]
        widgets = {
            'contract_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'renewal_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'renewal_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 100000')
            }),
            'key_money': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 200000')
            }),
            'deposit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 200000')
            }),
            'guarantee_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 50000')
            }),
            'management_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 10000')
            }),
            'has_special_restoration_clause': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'restoration_clause': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Enter special restoration clause if any...')
            }),
            'agency_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., ABC Real Estate Co., Ltd.')
            }),
            'agency_license': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Tokyo (1) 12345')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 선택적 필드 설정
        self.fields['renewal_fee'].required = False
        self.fields['key_money'].required = False
        self.fields['deposit'].required = False
        self.fields['guarantee_fee'].required = False
        self.fields['management_fee'].required = False
        self.fields['restoration_clause'].required = False
        self.fields['agency_name'].required = False
        self.fields['agency_license'].required = False

    def clean(self):
        cleaned_data = super().clean()
        # 정기 계약인 경우 갱신 유형을 '없음'으로 강제
        if cleaned_data.get('contract_type') == 'FIXED_TERM':
            cleaned_data['renewal_type'] = 'NONE'
        return cleaned_data
