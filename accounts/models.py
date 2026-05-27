from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """커스텀 사용자 모델"""

    USER_TYPE_CHOICES = [
        ('TENANT', _('임차인')),
        ('LANDLORD', _('임대인')),
    ]

    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        blank=True,
        verbose_name=_('사용자 유형')
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='전화번호'
    )
    social_account = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='소셜 로그인',
        help_text='소셜 로그인 제공자 (예: google)'
    )

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
