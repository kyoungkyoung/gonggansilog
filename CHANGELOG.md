# Changelog

프로젝트의 모든 주요 변경사항을 기록합니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 따르며,
버전 관리는 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

---

## [0.7.0] - 2026-01-18

### Added
- 📸 **입실/퇴실 기록 기능** 구현
  - Record 모델 기반 입실/퇴실 기록 생성
  - Photo 모델 기반 다중 사진 업로드
  - 카테고리별 사진 분류 (벽면, 바닥, 천장, 화장실, 주방 등)
  - 드래그 앤 드롭 사진 업로드 UI
  - 사진별 카테고리 및 설명 입력 모달
- 🔍 **입실/퇴실 비교 뷰**
  - 카테고리별 Before/After 사진 비교
  - 한눈에 상태 변화 확인 가능
- ✅ **임대인 승인 시스템**
  - 입실/퇴실 기록 승인/반려 기능
  - 반려 시 사유 입력 필수
  - 승인 상태 배지 표시 (대기중/승인됨/반려됨)
- 🖼️ **사진 관리 기능**
  - 기존 기록에 사진 추가
  - 사진 삭제 (승인 전까지)
  - 사진 정보 수정 (카테고리, 설명)
- 📋 **계약 상세 페이지 연동**
  - 입실/퇴실 기록 카드 UI
  - 상태별 색상 표시
  - 빠른 접근 버튼

---

## [0.6.0] - 2026-01-18

### Added
- 📄 **README.md** 생성 - 전체 프로젝트 가이드 문서
- 🔗 **블록체인 증거화 시스템** 계획 수립
  - KAS (Klaytn API Service) 기반
  - 해시 생성 로직 설계
  - 검증 페이지 설계
- 📱 **모바일 UI 최적화**
  - 대시보드 반응형 디자인 (하이브리드: 테이블/카드)
  - 계약 상세 페이지 모바일 최적화
  - 버튼 및 입력 요소 터치 친화적 개선
- 🚀 **배포 가이드** 추가
  - PythonAnywhere + Supabase + Cloudflare R2 아키텍처
  - 무료 티어 정보
  - 환경 변수 설정 가이드

### Changed
- 📝 개발현황.md → CHANGELOG.md로 변경
- 🎨 헤더 문구 변경: "상가 원상복구 관리" → "부동산 관리 프로그램"
- 🎨 Admin 헤더 변경: "Django 관리" → "부동산 관리 프로그램(관리자)"

---

## [0.5.0] - 2026-01-15

### Added
- 📢 **대시보드 중앙 알림 시스템**
  - 승인 대기 중인 요청 표시 (건수 포함)
  - 최근 처리된 요청 표시 (24시간, 읽지 않은 것만)
  - /accounts 페이지에서 모든 알림 확인 가능
- ✅ **알림 읽음 처리 기능**
  - `is_read_by_requester` 필드 추가
  - AJAX 기반 읽음 처리 엔드포인트
  - X 버튼 클릭 시 자동 해제

### Changed
- 🔔 알림 위치 변경: 개별 계약 페이지 → 대시보드로 이동

---

## [0.4.5] - 2026-01-10

### Added
- 💬 **승인 메시지 입력 기능**
  - 승인 시 선택적 메시지 입력 가능
  - 거절과 동일한 모달 방식
- 📝 **관리자 수정 추적 시스템**
  - 계약 수정 시 메모 필수 입력
  - ContractHistory에 'MODIFIED' 액션 타입 추가
  - 변경 내용 자동 기록
- 📜 **커스텀 Admin 히스토리 뷰**
  - ContractHistory + Django LogEntry 통합 표시
  - 날짜/시간, 사용자, 액션, 메모 4개 컬럼
  - 사용자 액션(연장/해지) + 관리자 액션 모두 표시

### Fixed
- 🐛 ValidationError가 페이지로 표시되는 문제
  - `save_model`의 검증 로직을 `ContractAdminForm.clean()`으로 이동
  - 인라인 폼 에러로 표시되도록 수정

---

## [0.4.0] - 2026-01-08

### Added
- 🔄 **계약 연장/해지 요청-승인 시스템**
  - ContractChangeRequest 모델 생성
  - 연장 요청 (기간 지정 가능)
  - 해지 요청
  - 양방향 알림 (요청자 ↔ 승인자)
- ❌ **거절 사유 입력 기능**
  - `response_note` 필드 추가
  - 거절 모달에서 필수 입력
  - 거절 사유 표시 (알림 및 Admin)
- ✅ **승인/거절 처리**
  - 승인 시 계약 기간 자동 연장 또는 해지
  - ContractHistory 자동 생성
  - 처리 시간 및 처리자 기록

### Fixed
- 🐛 timezone 미정의 오류 수정
  - `approve_change_request` 및 `reject_change_request` 뷰에 `from django.utils import timezone` 추가

---

## [0.3.0] - 2025-12-31

### Added
- 🎙️ **녹음 기능**
  - Recording 모델 생성
  - 음성 파일 업로드 (WebM)
  - 녹음 목록 조회
  - 녹음 재생 기능
- 🤖 **AI 기반 음성 처리**
  - OpenAI Whisper API 연동 (음성→텍스트)
  - GPT-4o-mini 연동 (텍스트 요약)
  - 자동 전사 및 요약 기능
- 📖 **AI_SETUP_GUIDE.md** 생성
  - OpenAI API 키 발급 방법
  - Whisper 및 GPT 설정 가이드

---

## [0.2.0] - 2025-12-29

### Added
- 📄 **계약 관리 시스템**
  - Contract 모델 확장
  - 계약 등록 (계약서 업로드)
  - 계약 목록 조회
  - 계약 상세 정보
  - 계약 수정/삭제 (관리자)
- 🔗 **계약 초대 시스템**
  - ContractInvitation 모델
  - 초대 링크 생성 (토큰 기반)
  - 만료 시간 설정 (7일)
  - 임대인 ↔ 임차인 연결
- 📊 **계약 이력 관리**
  - ContractHistory 모델
  - 등록/연장/해지 이력 추적
  - 이력 조회 기능
- 🔧 **Admin 패널 커스터마이징**
  - Contract Admin 상세 설정
  - 상태별 색상 표시
  - 필터 및 검색 기능

---

## [0.1.0] - 2025-11-27

### Added
- 🎉 **프로젝트 초기 설정**
  - Django 4.2.26 설치
  - 프로젝트 구조 생성 (config, accounts, contracts, records)
  - requirements.txt 작성
  - .gitignore 설정
- 👤 **커스텀 User 모델**
  - AbstractUser 상속
  - user_type 필드 (TENANT/LANDLORD)
  - phone_number 필드
  - social_account 필드
- 🔐 **인증 시스템**
  - 회원가입/로그인 기능
  - Django Allauth 설정
  - Google OAuth 2.0 연동
  - SocialAccountAdapter 커스터마이징
- 🌐 **사용자 유형 선택 플로우**
  - 소셜 로그인 후 사용자 유형 선택 페이지
  - 전화번호 입력 기능
- ⏰ **세션 관리**
  - 1시간 자동 로그아웃
  - 활동 시 세션 갱신
  - 브라우저 종료 시 세션 만료
- 🎨 **UI/템플릿**
  - Bootstrap 5 통합
  - base.html 기본 템플릿
  - 대시보드 (임차인/임대인 구분)
- 📚 **문서 작성**
  - PRD_상가원상복구관리서비스.md
  - GOOGLE_OAUTH_SETUP.md
  - 개발현황.md (현재 CHANGELOG.md)

### Fixed
- 🐛 Bootstrap 스타일 미적용 문제
  - URL 순서 조정 (커스텀 URLs 우선)
  - TEMPLATES['DIRS'] 설정
- 🐛 소셜 로그인 무한 루프
  - ACCOUNT_USERNAME_REQUIRED = False 설정
- 🐛 User/SocialAccount 동기화 문제
  - pre_social_login에서 이메일 기반 자동 연결

---

## 변경 유형

- **Added**: 새로운 기능 추가
- **Changed**: 기존 기능 변경
- **Deprecated**: 곧 제거될 기능
- **Removed**: 제거된 기능
- **Fixed**: 버그 수정
- **Security**: 보안 관련 변경

---

**마지막 업데이트**: 2026-01-18 (v0.7.0)
