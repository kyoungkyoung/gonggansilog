from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from datetime import timedelta
from .models import Record, Photo


class RecordForm(forms.ModelForm):
    """입실/퇴실 기록 폼"""

    class Meta:
        model = Record
        fields = ['record_type', 'notes']
        widgets = {
            'record_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '특이사항이나 메모를 입력하세요 (선택사항)'
            }),
        }
        labels = {
            'record_type': '기록 유형',
            'notes': '메모',
        }


class LandlordCreateRecordForm(forms.ModelForm):
    """임대인 기록 생성 + 마감일 설정 폼"""

    upload_deadline = forms.DateTimeField(
        label='업로드 마감일',
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
        }),
        help_text='임차인이 사진을 업로드할 수 있는 마감일입니다.'
    )

    deadline_days = forms.IntegerField(
        label='마감일까지 일수',
        required=False,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '예: 7',
        }),
        help_text='오늘부터 며칠 후를 마감일로 설정할지 입력하세요. 위 날짜 선택보다 우선합니다.'
    )

    class Meta:
        model = Record
        fields = ['record_type', 'notes']
        widgets = {
            'record_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '특이사항이나 메모를 입력하세요 (선택사항)'
            }),
        }
        labels = {
            'record_type': '기록 유형',
            'notes': '메모',
        }

    def clean(self):
        cleaned_data = super().clean()
        deadline_days = cleaned_data.get('deadline_days')
        upload_deadline = cleaned_data.get('upload_deadline')

        # deadline_days가 입력되면 해당 값으로 마감일 설정
        if deadline_days:
            cleaned_data['upload_deadline'] = timezone.now() + timedelta(days=deadline_days)
        elif upload_deadline:
            if upload_deadline < timezone.now():
                raise forms.ValidationError('마감일은 현재 시간 이후로 설정해야 합니다.')
        else:
            # 둘 다 없으면 에러
            raise forms.ValidationError('마감일을 설정해주세요. 일수 또는 날짜 중 하나를 입력하세요.')

        return cleaned_data


class TenantRequestRecordForm(forms.ModelForm):
    """임차인 기록 요청 폼"""

    class Meta:
        model = Record
        fields = ['record_type', 'notes']
        widgets = {
            'record_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '요청 사유나 메모를 입력하세요 (선택사항)'
            }),
        }
        labels = {
            'record_type': '기록 유형',
            'notes': '요청 메모',
        }


class ApproveRequestForm(forms.Form):
    """임차인 요청 승인 폼 (마감일 포함)"""

    upload_deadline = forms.DateTimeField(
        label='업로드 마감일',
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
        }),
    )

    deadline_days = forms.IntegerField(
        label='마감일까지 일수',
        required=False,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '예: 7',
        }),
        help_text='오늘부터 며칠 후를 마감일로 설정할지 입력하세요.'
    )

    def clean(self):
        cleaned_data = super().clean()
        deadline_days = cleaned_data.get('deadline_days')
        upload_deadline = cleaned_data.get('upload_deadline')

        if deadline_days:
            cleaned_data['upload_deadline'] = timezone.now() + timedelta(days=deadline_days)
        elif upload_deadline:
            if upload_deadline < timezone.now():
                raise forms.ValidationError('마감일은 현재 시간 이후로 설정해야 합니다.')
        else:
            # 둘 다 없으면 에러
            raise forms.ValidationError('마감일을 설정해주세요. 일수 또는 날짜 중 하나를 입력하세요.')

        return cleaned_data


class FinalApprovalForm(forms.Form):
    """최종 승인/반려 폼"""
    ACTION_CHOICES = [
        ('APPROVED', '승인'),
        ('REJECTED', '반려'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='처리'
    )

    landlord_comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '의견이나 반려 사유를 입력하세요'
        }),
        label='의견',
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        landlord_comment = cleaned_data.get('landlord_comment')

        if action == 'REJECTED' and not landlord_comment:
            raise forms.ValidationError('반려 시 사유를 입력해주세요.')

        return cleaned_data


class PhotoForm(forms.ModelForm):
    """사진 업로드 폼"""

    class Meta:
        model = Photo
        fields = ['image', 'category', 'description']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '사진에 대한 설명 (선택사항)'
            }),
        }
        labels = {
            'image': '사진',
            'category': '카테고리',
            'description': '설명',
        }


# Photo Formset (Record와 연결)
PhotoFormSet = inlineformset_factory(
    Record,
    Photo,
    form=PhotoForm,
    extra=1,
    can_delete=True,
    max_num=50,
)


class RecordApprovalForm(forms.Form):
    """기록 승인/반려 폼"""
    APPROVAL_CHOICES = [
        ('APPROVED', '승인'),
        ('REJECTED', '반려'),
    ]

    approval_status = forms.ChoiceField(
        choices=APPROVAL_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='승인 여부'
    )
    landlord_comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '의견이나 반려 사유를 입력하세요'
        }),
        label='의견',
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        approval_status = cleaned_data.get('approval_status')
        landlord_comment = cleaned_data.get('landlord_comment')

        # 반려 시 사유 필수
        if approval_status == 'REJECTED' and not landlord_comment:
            raise forms.ValidationError('반려 시 사유를 입력해주세요.')

        return cleaned_data
