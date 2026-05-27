from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """커스텀 User Admin"""

    # 목록 표시 필드
    list_display = ['username', 'email', 'user_type', 'phone_number', 'social_account', 'is_staff', 'date_joined']

    # 필터 옵션
    list_filter = ['user_type', 'social_account', 'is_staff', 'is_active', 'date_joined']

    # 검색 기능 (사용자명, 이메일, 전화번호로 검색)
    search_fields = ['username', 'email', 'phone_number']

    # 정렬 (최신 가입자 먼저)
    ordering = ['-date_joined']

    # 페이지당 항목 수
    list_per_page = 20

    # 상세 페이지 필드셋 (이메일 수정 가능)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('개인정보', {'fields': ('first_name', 'last_name', 'email')}),
        ('추가 정보', {'fields': ('user_type', 'phone_number', 'social_account')}),
        ('권한', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('중요한 날짜', {'fields': ('last_login', 'date_joined')}),
    )

    # 사용자 추가 시 필드셋
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type', 'phone_number'),
        }),
    )
