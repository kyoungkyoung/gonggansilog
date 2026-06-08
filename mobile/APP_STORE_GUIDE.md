# 앱스토어 배포 가이드

## 사전 준비

### Apple (iOS)
1. Apple Developer Program 가입 ($99/년)
   - https://developer.apple.com/programs/
2. App Store Connect에서 앱 등록
3. 인증서 및 프로비저닝 프로파일 생성

### Google (Android)
1. Google Play Console 개발자 계정 생성 ($25 일회성)
   - https://play.google.com/console/
2. 앱 등록 및 스토어 정보 입력
3. 서비스 계정 키 생성 (자동 배포용)

## EAS Build 설정

### 1. EAS CLI 설치
```bash
npm install -g eas-cli
eas login
```

### 2. 프로젝트 설정
```bash
cd mobile
eas build:configure
```

### 3. 앱 아이콘 준비
- `assets/icon.png` — 1024x1024px (앱 아이콘)
- `assets/splash-icon.png` — 1284x2778px (스플래시)
- `assets/android-icon-foreground.png` — 432x432px (Android 적응형)

### 4. 빌드

#### 개발용 (테스트)
```bash
eas build --platform all --profile development
```

#### 프로덕션 빌드
```bash
# iOS
eas build --platform ios --profile production

# Android
eas build --platform android --profile production
```

### 5. 스토어 제출
```bash
# iOS - App Store Connect에 업로드
eas submit --platform ios --profile production

# Android - Google Play Console에 업로드
eas submit --platform android --profile production
```

## 스토어 정보 (준비 필요)

### 앱 이름
- 한국어: 공간실록
- 영어: Space Chronicle
- 일본어: 空間実録

### 앱 설명
블록체인 기반 상가 임대차 계약 관리 서비스.
입퇴실 기록, 하자 통지, 수리 요청, 비용 관리를 한곳에서.

### 카테고리
- iOS: Business / Productivity
- Android: Business / House & Home

### 스크린샷 (필요)
- iPhone 6.7" (1290x2796) — 최소 3장
- iPhone 6.5" (1242x2688)
- iPad 12.9" (2048x2732)
- Android Phone (1080x1920) — 최소 2장

### 개인정보 처리방침
- 앱스토어 등록 시 필수
- URL 형태로 준비 필요
