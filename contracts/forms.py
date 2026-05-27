from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import Contract


class ContractForm(forms.ModelForm):
    """계약 등록/수정 폼"""

    # 국가 선택 필드
    country = forms.ChoiceField(
        label=_('Country'),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_country'}),
        help_text=_('Select the country where the property is located.')
    )

    # 부동산 유형 선택 필드
    property_type = forms.ChoiceField(
        label=_('Property Type'),
        required=True,
        choices=[
            ('RESIDENTIAL', _('Residential')),
            ('COMMERCIAL', _('Commercial')),
            ('OFFICE', _('Office')),
        ],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_property_type'}),
        help_text=_('Select the type of property.')
    )

    # 템플릿 선택 필드
    template = forms.ChoiceField(
        label=_('Inspection Template'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_template'}),
        help_text=_('Select an inspection template for this contract. Leave empty to use the default.')
    )

    # 동적으로 추가될 필드들
    landlord = forms.ChoiceField(
        label=_('Select Landlord'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_('Select a registered landlord or enter details below.')
    )
    tenant = forms.ChoiceField(
        label=_('Select Tenant'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_('Select a registered tenant or enter details below.')
    )

    class Meta:
        model = Contract
        fields = [
            'address',
            'contract_date',
            'move_in_date',
            'move_out_date',
            'tenant_name',
            'tenant_phone',
            'landlord_name',
            'landlord_phone',
            'contract_file',
        ]
        widgets = {
            'address': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'contract_date': forms.DateInput(attrs={
                'class': 'form-control date-input',
                'type': 'text',
                'onfocus': "this.type='date'",
                'onblur': "if(!this.value)this.type='text'",
            }),
            'move_in_date': forms.DateInput(attrs={
                'class': 'form-control date-input',
                'type': 'text',
                'onfocus': "this.type='date'",
                'onblur': "if(!this.value)this.type='text'",
            }),
            'move_out_date': forms.DateInput(attrs={
                'class': 'form-control date-input',
                'type': 'text',
                'onfocus': "this.type='date'",
                'onblur': "if(!this.value)this.type='text'",
            }),
            'tenant_name': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'tenant_phone': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'landlord_name': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'landlord_phone': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'contract_file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        help_texts = {
            'address': _('Please enter the full address of the property.'),
            'move_out_date': _('You may leave this blank if the move-out date is unknown.'),
            'contract_file': _('Upload a copy of the contract for safekeeping.'),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 필수 필드가 아닌 것들은 required=False 설정
        self.fields['move_out_date'].required = False
        self.fields['contract_file'].required = False

        # 번역 가능한 placeholder 설정
        self.fields['address'].widget.attrs['placeholder'] = _('e.g., 123 Main Street, Suite 100')

        # 날짜 필드 placeholder
        date_placeholder = _('YYYY-MM-DD')
        self.fields['contract_date'].widget.attrs['placeholder'] = date_placeholder
        self.fields['move_in_date'].widget.attrs['placeholder'] = date_placeholder
        self.fields['move_out_date'].widget.attrs['placeholder'] = date_placeholder

        # 기존 값이 있으면 type=date로 유지 (수정 모드)
        if self.instance and self.instance.pk:
            for field_name in ['contract_date', 'move_in_date', 'move_out_date']:
                if self.initial.get(field_name) or getattr(self.instance, field_name, None):
                    self.fields[field_name].widget.attrs['type'] = 'date'
        if 'tenant_name' in self.fields:
            self.fields['tenant_name'].widget.attrs['placeholder'] = _('e.g., John Smith')
        if 'tenant_phone' in self.fields:
            self.fields['tenant_phone'].widget.attrs['placeholder'] = _('e.g., 010-1234-5678')
        if 'landlord_name' in self.fields:
            self.fields['landlord_name'].widget.attrs['placeholder'] = _('e.g., John Smith')
        if 'landlord_phone' in self.fields:
            self.fields['landlord_phone'].widget.attrs['placeholder'] = _('e.g., 010-1234-5678')

        # 국가 선택 필드 초기화
        supported_countries = getattr(settings, 'SUPPORTED_COUNTRIES', {})
        country_choices = [('', _('Select a country'))]
        for code, info in supported_countries.items():
            country_choices.append((code, f"{info.get('name_native', code)} ({info.get('name', code)})"))
        self.fields['country'].choices = country_choices
        self.fields['country'].initial = getattr(settings, 'DEFAULT_COUNTRY', 'KR')

        # 템플릿 선택 필드 초기화
        # POST 시 선택된 template ID가 유효하도록 DB에서 choices를 로드
        from core.templates_engine.models import InspectionTemplate
        template_choices = [('', _('Select a template (auto-loaded)'))]
        for t in InspectionTemplate.objects.filter(is_active=True):
            template_choices.append((str(t.pk), str(t)))
        self.fields['template'].choices = template_choices

        # 기존 인스턴스가 있는 경우 (수정 모드)
        if self.instance and self.instance.pk:
            if self.instance.country:
                self.fields['country'].initial = self.instance.country
            if self.instance.template:
                self.fields['template'].choices = [
                    ('', _('Select a template')),
                    (self.instance.template.pk, self.instance.template.name)
                ]
                self.fields['template'].initial = self.instance.template.pk

        # 사용자 타입에 따라 필드 조정
        if user:
            from accounts.models import User

            if user.user_type == 'TENANT':
                # 임차인: landlord 선택 필드 추가 (선택사항)
                landlords = User.objects.filter(user_type='LANDLORD')
                self.fields['landlord'].choices = [('', _('Not selected (enter below)'))] + [
                    (u.id, f"{u.username} ({u.email})") for u in landlords
                ]
                # tenant 관련 필드는 제거 (임차인 본인이므로)
                if 'tenant' in self.fields:
                    del self.fields['tenant']
                if 'tenant_name' in self.fields:
                    del self.fields['tenant_name']
                if 'tenant_phone' in self.fields:
                    del self.fields['tenant_phone']

            else:  # LANDLORD
                # 임대인: tenant 선택 필드 추가 (선택사항)
                tenants = User.objects.filter(user_type='TENANT')
                self.fields['tenant'].choices = [('', _('Not selected (enter below)'))] + [
                    (u.id, f"{u.username} ({u.email})") for u in tenants
                ]
                self.fields['tenant'].required = False
                # landlord 관련 필드는 제거 (임대인 본인이므로)
                if 'landlord' in self.fields:
                    del self.fields['landlord']
                if 'landlord_name' in self.fields:
                    del self.fields['landlord_name']
                if 'landlord_phone' in self.fields:
                    del self.fields['landlord_phone']
                # tenant_name, tenant_phone은 선택사항으로
                self.fields['tenant_name'].required = False
                self.fields['tenant_phone'].required = False
        else:
            # user가 없으면 관련 필드 모두 제거
            if 'landlord' in self.fields:
                del self.fields['landlord']
            if 'tenant' in self.fields:
                del self.fields['tenant']
