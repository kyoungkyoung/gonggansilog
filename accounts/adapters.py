from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """소셜 로그인 어댑터"""

    def pre_social_login(self, request, sociallogin):
        """소셜 로그인 전 처리"""
        # 이미 연결된 소셜 계정인 경우
        if sociallogin.is_existing:
            return

        # 이메일로 기존 사용자 찾기
        email = sociallogin.account.extra_data.get('email', '')
        if email:
            from accounts.models import User
            try:
                # 같은 이메일의 기존 사용자가 있으면 자동 연결
                existing_user = User.objects.get(email=email)
                # 소셜 로그인 제공자 정보 추가
                if not existing_user.social_account:
                    existing_user.social_account = sociallogin.account.provider
                    existing_user.save()
                sociallogin.connect(request, existing_user)
                return
            except User.DoesNotExist:
                pass

        # 새 사용자인 경우 자동으로 생성
        if not sociallogin.user.id:
            if email:
                # username은 이메일의 @ 앞부분 사용
                base_username = email.split('@')[0]
                username = base_username

                # 중복 체크 및 번호 추가
                from accounts.models import User
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                sociallogin.user.username = username
                sociallogin.user.email = email
                sociallogin.user.user_type = ''  # 나중에 선택

    def save_user(self, request, sociallogin, form=None):
        """소셜 로그인으로 가입할 때 사용자 저장"""
        user = super().save_user(request, sociallogin, form)

        # user_type이 없으면 빈 문자열로
        if not user.user_type:
            user.user_type = ''

        # 소셜 로그인 제공자 이름 저장 (예: google)
        if not user.social_account:
            user.social_account = sociallogin.account.provider

        user.save()

        return user

    def get_login_redirect_url(self, request):
        """로그인 후 리디렉션 URL 결정"""
        # user_type이 설정되지 않았으면 선택 페이지로
        if request.user.is_authenticated and not request.user.user_type:
            return reverse('accounts:select_user_type')

        # 기본 대시보드로
        return reverse('accounts:dashboard')

    def is_auto_signup_allowed(self, request, sociallogin):
        """자동 가입 허용 여부 - 항상 True"""
        return True

    def populate_user(self, request, sociallogin, data):
        """사용자 객체에 데이터 채우기"""
        user = super().populate_user(request, sociallogin, data)
        # user_type은 나중에 선택하도록 빈 문자열
        user.user_type = ''
        # 소셜 로그인 제공자 이름 저장 (예: google)
        user.social_account = sociallogin.account.provider
        return user
