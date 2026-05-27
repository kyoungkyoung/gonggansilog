# 구글 소셜 로그인 설정 가이드

소셜 로그인 기능이 추가되었습니다! 실제로 작동하려면 구글 OAuth 설정이 필요합니다.

## 1. Google Cloud Console에서 OAuth 2.0 클라이언트 ID 생성

### 1단계: Google Cloud Console 접속
1. https://console.cloud.google.com/ 접속
2. 구글 계정으로 로그인

### 2단계: 프로젝트 생성
1. 상단의 프로젝트 선택 드롭다운 클릭
2. "새 프로젝트" 클릭
3. 프로젝트 이름 입력 (예: "상가원상복구관리")
4. "만들기" 클릭

### 3단계: OAuth 동의 화면 구성
1. 좌측 메뉴에서 "API 및 서비스" > "OAuth 동의 화면" 선택
2. 사용자 유형: "외부" 선택 후 "만들기" 클릭
3. 앱 정보 입력:
   - 앱 이름: 상가 원상복구 관리 서비스
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처 정보: 본인 이메일
4. "저장 후 계속" 클릭
5. 범위 단계에서 "저장 후 계속" (기본값 사용)
6. 테스트 사용자 추가 (선택사항)
7. "저장 후 계속" 클릭

### 4단계: OAuth 2.0 클라이언트 ID 생성
1. 좌측 메뉴에서 "API 및 서비스" > "사용자 인증 정보" 선택
2. 상단의 "+ 사용자 인증 정보 만들기" 클릭
3. "OAuth 클라이언트 ID" 선택
4. 애플리케이션 유형: "웹 애플리케이션" 선택
5. 이름 입력 (예: "Django Web App")
6. 승인된 리디렉션 URI 추가:
   ```
   http://127.0.0.1:8000/auth/google/login/callback/
   ```
7. "만들기" 클릭
8. **클라이언트 ID**와 **클라이언트 보안 비밀번호** 복사 및 저장

## 2. Django Admin에서 Social Application 등록

### 1단계: Django Admin 접속
1. http://127.0.0.1:8000/admin/ 접속
2. 관리자 계정으로 로그인 (admin / admin123)

### 2단계: Social Application 추가
1. "Sites" 섹션에서 "Sites" 클릭
2. "example.com" 클릭하여 수정
3. Domain name과 Display name을 다음과 같이 변경:
   - Domain name: `127.0.0.1:8000`
   - Display name: `로컬 개발 서버`
4. "저장" 클릭

### 3단계: Social Applications 등록
1. 왼쪽 메뉴에서 "Social applications" 클릭
2. 오른쪽 상단의 "SOCIAL APPLICATION 추가" 클릭
3. 다음 정보 입력:
   - Provider: **Google** 선택
   - Name: `Google OAuth` (임의로 지정)
   - Client id: 구글에서 복사한 **클라이언트 ID** 붙여넣기
   - Secret key: 구글에서 복사한 **클라이언트 보안 비밀번호** 붙여넣기
   - Sites: "Available sites"에서 `127.0.0.1:8000`을 선택하고 → 버튼 클릭하여 "Chosen sites"로 이동
4. "저장" 클릭

## 3. 테스트

1. http://127.0.0.1:8000/accounts/login/ 접속
2. "구글로 로그인" 버튼 클릭
3. 구글 계정 선택 및 권한 승인
4. 자동으로 회원가입 및 로그인 완료!

## 주의사항

### 개발 환경 (localhost)
- 위 설정대로 진행하면 로컬에서 테스트 가능
- 리디렉션 URI: `http://127.0.0.1:8000/auth/google/login/callback/`

### 프로덕션 환경 (실제 서버 배포 시)
1. 구글 OAuth 클라이언트에 프로덕션 URL 추가:
   ```
   https://yourdomain.com/auth/google/login/callback/
   ```
2. Django settings.py에서:
   - `ALLOWED_HOSTS`에 도메인 추가
   - `SITE_ID` 확인
3. Django Admin의 Sites에서 실제 도메인으로 변경

## 추가 소셜 로그인 제공자

다른 소셜 로그인도 추가하고 싶다면:
- 카카오: `allauth.socialaccount.providers.kakao`
- 네이버: `allauth.socialaccount.providers.naver`
- 페이스북: `allauth.socialaccount.providers.facebook`

settings.py의 `INSTALLED_APPS`에 추가하고 동일한 방식으로 설정하면 됩니다!

## 문제 해결

### "Social account not configured" 에러
→ Django Admin에서 Social Application을 올바르게 등록했는지 확인

### "Redirect URI mismatch" 에러
→ Google Cloud Console의 승인된 리디렉션 URI가 정확한지 확인

### user_type이 없다는 에러
→ 소셜 로그인 후 자동으로 'TENANT'로 설정됩니다. 필요시 대시보드에서 변경 가능하도록 구현 예정
