# 부동산 관리 프로그램 (상가 원상복구 관리 서비스)

> 블록체인 기반 임대차 계약 증거 관리 시스템

임대차 계약 시 발생하는 원상복구 분쟁을 예방하기 위한 디지털 증거 관리 플랫폼입니다. 계약서, 입실/퇴실 사진, 협의 녹음 등을 블록체인에 영구 기록하여 법적 증거력을 강화합니다.

---

## 🎯 프로젝트 목적

- **분쟁 예방**: 입실/퇴실 시점의 상태를 명확히 기록
- **법적 증거력**: 블록체인 기반 위변조 방지
- **투명한 관리**: 임대인-임차인 간 신뢰 구축
- **효율적 처리**: 계약 연장/해지 요청 자동화

---

## 📚 참고 문서

- **README.md** (이 파일) - 프로젝트 개요 및 전체 가이드 (최신 상태)
- **CHANGELOG.md** - 버전별 변경 이력 (시간순 기록)
- **PRD_상가원상복구관리서비스.md** - 제품 요구사항 정의서
- **AI_SETUP_GUIDE.md** - OpenAI API 설정 가이드
- **GOOGLE_OAUTH_SETUP.md** - Google OAuth 설정 가이드

---

## 🛠️ 기술 스택

### Backend
- **Django 4.2.26** - Python 웹 프레임워크
- **Python 3.9+**

### Database
- **개발**: SQLite3 (로컬)
- **프로덕션**: PostgreSQL (Supabase)

### Storage
- **개발**: 로컬 파일 시스템
- **프로덕션**: Cloudflare R2 (S3 호환)

### AI/ML
- **OpenAI Whisper** - 음성→텍스트 변환
- **GPT-4o-mini** - 텍스트 요약

### Blockchain
- **Kaia (구 Klaytn)** - 카카오 블록체인 플랫폼
- **Web3.py** - 블록체인 직접 트랜잭션
- **Kairos 테스트넷** - 무료 테스트 환경

### Frontend
- **Django Templates** - 서버 사이드 렌더링
- **Bootstrap 5** - 반응형 UI 프레임워킹
- **Bootstrap Icons**

### Authentication
- **Django Allauth** - 회원가입/로그인
- **Google OAuth 2.0** - 소셜 로그인

### Deployment (계획)
- **PythonAnywhere** - Django 호스팅
- **Supabase** - PostgreSQL 데이터베이스
- **Cloudflare R2** - 파일 스토리지

---

## ✅ 완료된 주요 기능

### 1. 사용자 인증 시스템
- [x] 회원가입/로그인
- [x] Google OAuth 소셜 로그인
- [x] 사용자 유형 선택 (임차인/임대인)
- [x] 세션 관리 (1시간 자동 로그아웃)

### 2. 계약 관리
- [x] 계약 등록 (계약서 업로드 포함)
- [x] 계약 목록 조회
- [x] 계약 상세 정보
- [x] 계약 수정/삭제 (관리자)
- [x] 계약 초대 링크 생성 (임대인↔임차인 연결)

### 3. 계약 연장/해지 시스템
- [x] 연장 요청 (기간 지정)
- [x] 해지 요청
- [x] 승인/거절 모달 (사유/메시지 입력)
- [x] 양방향 알림 시스템
- [x] 읽음 처리 기능

### 4. 알림 시스템
- [x] 대시보드 중앙 집중식 알림
- [x] 승인 대기 알림 (건수 표시)
- [x] 처리 완료 알림 (24시간)
- [x] 알림 자동 해제 (X 버튼)

### 5. 계약 이력 관리
- [x] ContractHistory 모델
- [x] 등록/연장/해지/수정 이력 추적
- [x] 관리자 수정 시 메모 필수
- [x] 커스텀 admin 히스토리 뷰 (ContractHistory + Django LogEntry)

### 6. 녹음 기능
- [x] 음성 녹음 및 업로드
- [x] Whisper API 음성→텍스트 변환
- [x] GPT-5-nano 자동 요약
- [x] 녹음 목록 조회
- [x] 녹음 재생 및 전사본 확인

### 7. 관리자 패널
- [x] 계약 관리 (수정 시 메모 필수)
- [x] 이력 추적 (상세 변경 내역)
- [x] 변경 요청 관리
- [x] 사용자 관리

### 8. 모바일 UI 최적화
- [x] 대시보드 반응형 디자인
- [x] 계약 목록 카드/테이블 하이브리드
- [x] 계약 상세 모바일 최적화
- [x] 버튼 및 입력 요소 터치 친화적

### 9. 입실/퇴실 기록
- [x] 입실 기록 생성 (다중 사진 업로드)
- [x] 퇴실 기록 생성
- [x] 카테고리별 사진 분류 (벽면, 바닥, 천장 등)
- [x] 입실/퇴실 사진 비교 뷰
- [x] 임대인 승인/반려 시스템
- [x] 사진 추가/삭제/수정 기능

### 10. 블록체인 증거화 시스템
- [x] Kaia 블록체인 직접 트랜잭션 방식
- [x] SHA-256 해시 생성 (계약서, 사진, 녹음)
- [x] 계약 확정 기능 (임대인만)
- [x] 블록체인 앵커링 (해시 영구 기록)
- [x] 진위 확인 페이지 (파일 무결성 검증)
- [x] Kaia Scope 연동 (트랜잭션 조회)
- [x] 지갑 생성/조회 명령어

---

## 🚧 개발 예정 기능

### Phase 1: 입실/퇴실 기록 기능 (완료) ✅

#### 1.1 기본 기능
- [x] Record 모델 및 Photo 모델 구현
- [x] 입실 기록 생성 페이지
- [x] 퇴실 기록 생성 페이지
- [x] 사진 업로드 (다중 파일, 드래그 앤 드롭)

#### 1.2 사진 분류 시스템
- [x] 카테고리별 사진 분류
  - 벽면 (동/서/남/북)
  - 바닥 (FLOOR)
  - 천장 (CEILING)
  - 문 (DOOR)
  - 창문 (WINDOW)
  - 주방/싱크대 (KITCHEN)
  - 화장실 (BATHROOM)
  - 전기/설비 (ELECTRICAL)
  - 간판 설치 부위 (SIGNBOARD)
  - 기타 (OTHER)
- [x] 카테고리별 갤러리 뷰
- [x] 사진 설명(description) 입력 기능

#### 1.3 비교 및 검증
- [x] 입실/퇴실 사진 비교 뷰
- [x] 카테고리별 Before/After 비교
- [ ] 차이점 하이라이트 (옵션) - 향후 AI 연동 예정

#### 1.4 승인 시스템
- [x] 임대인 확인/승인 기능
- [x] 반려 시 사유 입력 필수
- [x] 승인 상태 배지 표시

---

### Phase 2: 블록체인 증거화 시스템 (완료) ✅

#### 2.1 DB 스키마 확장
- [x] Contract 모델에 블록체인 필드 추가
  - `blockchain_tx_hash` (트랜잭션 해시)
  - `blockchain_anchored_at` (앵커링 시점)
  - `blockchain_final_hash` (저장한 최종 해시)
  - `blockchain_metadata` (파일별 해시 JSON)
  - `blockchain_status` (NONE/PENDING/ANCHORED/FAILED)
  - `is_finalized` (계약 확정 여부)
  - `finalized_at` (확정 시점)

#### 2.2 해시 생성 시스템
- [x] SHA-256 해시 생성 함수
- [x] 파일별 해시 추출 (계약서, 사진, 녹음)
- [x] 메타데이터 포함 해시 결합
- [x] 최종 해시 생성 (모든 해시 정렬 후 결합)

#### 2.3 Kaia 블록체인 연동 (직접 트랜잭션 방식)
- [x] Web3.py를 통한 직접 트랜잭션 전송
- [x] Kairos 테스트넷 무료 사용
- [x] 트랜잭션 input data에 해시 저장
- [x] 트랜잭션 영수증 확인

#### 2.4 오류 처리 및 재시도
- [x] 재시도 로직 구현 (최대 3회)
- [x] 지수 백오프 (exponential backoff)
- [x] 실패 시 상태 업데이트 (FAILED)
- [x] 로깅 시스템 (성공/실패 기록)

#### 2.5 계약 확정 기능
- [x] "계약 확정" 버튼 추가
- [x] 필수 조건 검증 (계약서, 입실 기록, 당사자 연결)
- [x] 확정 시 블록체인 앵커링 트리거
- [x] 확정 확인 페이지

#### 2.6 검증 페이지
- [x] 진위 확인 페이지 구현
- [x] 현재 파일 해시 재계산
- [x] DB 해시와 비교
- [x] Kaia Scope 링크 제공
- [x] 검증 결과 표시 (일치/불일치, 변조된 파일 목록)

#### 2.7 사용자 UI
- [x] 블록체인 상태 배지 표시 (등록됨/처리중/실패)
- [x] 계약 확정 배지
- [x] 진위 확인 버튼
- [x] Kaia Scope 바로가기

---

### Phase 3: 검색 및 필터 기능 (우선순위: 중간) 🟡

#### 3.1 검색 기능
- [ ] 계약 검색 (주소, 임차인/임대인 이름)
- [ ] 검색 결과 하이라이트
- [ ] 검색 기록 저장 (옵션)

#### 3.2 필터링
- [ ] 상태별 필터 (활성/종료)
- [ ] 날짜별 필터 (계약일, 만료일)
- [ ] 사용자 유형별 필터

#### 3.3 정렬
- [ ] 최신순/오래된순
- [ ] 계약일순
- [ ] 만료일순
- [ ] 주소순

---

### Phase 4: 통계 대시보드 (우선순위: 중간) 🟡

#### 4.1 요약 카드
- [ ] 활성 계약 수
- [ ] 만료 예정 계약 (30일 이내)
- [ ] 총 녹음 개수
- [ ] 총 저장 용량

#### 4.2 그래프 및 차트
- [ ] 월별 계약 등록 추이
- [ ] 연장/해지 비율
- [ ] 녹음 사용 통계

#### 4.3 빠른 액세스
- [ ] 최근 계약 목록
- [ ] 만료 임박 계약 알림
- [ ] 대기 중인 요청 바로가기

---

### Phase 5: 알림 개선 (우선순위: 낮음) 🟢

#### 5.1 이메일 알림
- [ ] SMTP 서버 설정
- [ ] 이메일 템플릿 작성
- [ ] 계약 만료 7일/3일/1일 전 자동 알림
- [ ] 변경 요청 알림

#### 5.2 알림 설정
- [ ] 알림 켜기/끄기 설정 페이지
- [ ] 알림 채널 선택 (이메일/앱)
- [ ] 알림 빈도 설정

---

### Phase 6: 추가 개선 사항 (우선순위: 낮음) 🟢

#### 6.1 문서 관리
- [ ] 추가 문서 업로드 (사업자등록증, 세금계산서 등)
- [ ] 문서 카테고리 분류
- [ ] 문서 버전 관리
- [ ] 일괄 다운로드 (ZIP)

#### 6.2 계약 초대 개선
- [ ] 이메일로 초대 링크 자동 발송
- [ ] 초대 수락 알림
- [ ] 초대 만료 시간 설정 옵션

#### 6.3 UI/UX 개선
- [ ] 다크모드
- [ ] 테마 저장 (로컬 스토리지)
- [ ] 프로필 사진 업로드
- [ ] 프로필 편집 페이지

#### 6.4 보안 강화
- [ ] 비밀번호 정책 강화
- [ ] 로그인 이력 추적
- [ ] 2단계 인증 (OTP) (옵션)

#### 6.5 데이터 내보내기
- [ ] 계약 목록 엑셀 다운로드
- [ ] 이력 엑셀 다운로드
- [ ] 통계 데이터 엑셀 다운로드

---

## 🏗️ 프로젝트 구조

```
공간실록/
├── config/                 # Django 설정
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/               # 사용자 인증
│   ├── models.py          # User 모델
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── adapters.py        # 소셜 로그인 어댑터
│   └── admin.py
├── contracts/              # 계약 관리
│   ├── models.py          # Contract, ContractHistory, ContractChangeRequest
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
├── records/                # 입실/퇴실 기록
│   ├── models.py          # Record, Photo
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── recordings/             # 녹음 기능
│   ├── models.py          # Recording
│   ├── views.py
│   ├── ai_services.py     # Whisper, GPT API
│   ├── urls.py
│   └── admin.py
├── blockchain/             # 블록체인 증거화
│   ├── services.py        # 해시 생성, Kaia 트랜잭션, 검증
│   ├── views.py           # 확정, 검증, 상태 조회 뷰
│   ├── urls.py
│   └── management/
│       └── commands/
│           ├── create_wallet.py   # 지갑 생성
│           └── check_wallet.py    # 잔액 확인
├── templates/
│   ├── base.html
│   ├── accounts/
│   ├── contracts/
│   └── recordings/
├── static/
├── media/
│   ├── contracts/         # 계약서 파일
│   └── recordings/        # 녹음 파일
├── db.sqlite3             # 개발용 DB
├── manage.py
├── requirements.txt
├── .env                   # 환경변수 (비공개)
├── .gitignore
├── README.md              # 이 파일
├── 개발현황.md            # 상세 개발 기록
├── PRD_상가원상복구관리서비스.md
├── AI_SETUP_GUIDE.md
└── GOOGLE_OAUTH_SETUP.md
```

---

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
cd ~/claude/공간실록
```

### 2. 가상환경 생성 및 활성화
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정 (.env)
```bash
# OpenAI API
OPENAI_API_KEY=your-openai-key

# Klaytn/Kaia 블록체인 (직접 트랜잭션 방식)
KLAYTN_CHAIN_ID=1001           # 테스트넷(Kairos): 1001, 메인넷: 8217
KLAYTN_PRIVATE_KEY=your-wallet-private-key
```

### 5. 데이터베이스 마이그레이션
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. 슈퍼유저 생성
```bash
python manage.py createsuperuser
```

### 7. 개발 서버 실행
```bash
python manage.py runserver
```

### 8. 접속
- **메인**: http://127.0.0.1:8000
- **대시보드**: http://127.0.0.1:8000/accounts/
- **관리자**: http://127.0.0.1:8000/admin/

---

## 🔗 블록체인 증거화 시스템 상세

### 목적
임대차 계약 시 생성된 파일들(계약서, 사진, 녹음)이 **특정 시점에 존재**했고, **그 이후 위변조되지 않았음**을 블록체인에 영구 기록하여 **법적 증거 능력을 강화**합니다.

### 왜 Kaia (구 Klaytn)?
- ✅ **카카오 블록체인** - 한국 사용자 신뢰도 높음
- ✅ **빠른 처리** - 약 1초 내외 컨펌
- ✅ **저렴한 비용** - 트랜잭션당 약 0.0008 KAIA (거의 무료)
- ✅ **무료 테스트넷** - Kairos 테스트넷 + Faucet으로 무료 테스트

### 아키텍처

```
┌─────────────┐
│   사용자    │ 파일 업로드 (계약서, 사진, 녹음)
└──────┬──────┘
       ↓
┌─────────────┐
│   서버      │ 로컬/클라우드에 원본 저장
└──────┬──────┘
       ↓
┌─────────────┐
│  해시 생성  │ 각 파일의 SHA-256 해시 추출
└──────┬──────┘
       ↓
┌─────────────┐
│  해시 병합  │ 모든 해시 정렬 후 결합
└──────┬──────┘
       ↓
┌─────────────┐
│ 최종 해시   │ SHA-256(결합된 해시)
└──────┬──────┘
       ↓
┌─────────────┐
│  Web3.py    │ Kaia 블록체인에 직접 트랜잭션
└──────┬──────┘
       ↓
┌─────────────┐
│ 블록체인    │ TxHash 반환 (영구 기록)
└──────┬──────┘
       ↓
┌─────────────┐
│  DB 저장    │ Contract 테이블에 TxHash, 메타데이터 저장
└─────────────┘
```

### 지갑 설정 방법

#### 1. 지갑 생성
```bash
python manage.py create_wallet
```

출력 예시:
```
============================================================
Klaytn 지갑 생성
============================================================
지갑 주소: 0x0acf43eDA489D2dC036306698aCda38C051383EA
개인키:    af1117ae1a26a4db633b022918c6510f2241b29d703093a867a3ad1d56586dca
```

#### 2. .env 파일에 개인키 추가
```bash
KLAYTN_CHAIN_ID=1001
KLAYTN_PRIVATE_KEY=af1117ae1a26a4db633b022918c6510f2241b29d703093a867a3ad1d56586dca
```

#### 3. Faucet에서 테스트 KAIA 받기
1. https://faucet.kaia.io 접속
2. 네트워크: **Kairos** 선택
3. 토큰: **KAIA** 선택
4. 지갑 주소 입력
5. "Run Faucet" 클릭 → 50 KAIA 지급

#### 4. 잔액 확인
```bash
python manage.py check_wallet
```

출력 예시:
```
============================================================
Klaytn/Kaia 지갑 상태
============================================================
네트워크:   테스트넷 (Kairos)
지갑 주소:  0x0acf43eDA489D2dC036306698aCda38C051383EA
잔액:       49.9992 KAIA

✓ 잔액 충분 - 블록체인 앵커링 가능
  예상 가능 트랜잭션: 약 49,999건

지갑 확인:  https://kairos.kaiascan.io/account/0x0acf43eDA489D2dC036306698aCda38C051383EA
============================================================
```

### 현재 지갑 상태

| 항목 | 상태 |
|------|------|
| 지갑 주소 | `0x0acf43eDA489D2dC036306698aCda38C051383EA` |
| 잔액 | ~49.99 KAIA |
| 예상 트랜잭션 | ~62,000건 가능 |
| 테스트 트랜잭션 | 성공 (tx: `d5df1764...`) |
| 네트워크 | Kairos 테스트넷 |

### 계약 확정 조건

"계약 확정" 버튼 활성화를 위한 필수 조건:
1. ✅ 계약서 파일 업로드됨
2. ✅ 입실 기록 존재 + 최종 승인됨
3. ✅ 임대인/임차인 모두 연결됨
4. ✅ 아직 확정되지 않음 (is_finalized=False)
5. ✅ 임대인 계정으로 로그인

### 블록체인에 기록되는 데이터

트랜잭션의 input data에 JSON 형태로 저장:
```json
{
  "type": "contract_anchor",
  "contract_id": 123,
  "hash": "a1b2c3d4e5f6...",
  "timestamp": "2025-02-25T12:00:00"
}
```

### 메타데이터 구조 (DB 저장)
```json
{
  "contract_id": 123,
  "address": "서울시 강남구...",
  "generated_at": "2025-02-25T12:00:00",
  "files": {
    "contract_file": {
      "name": "contracts/2025/02/contract.pdf",
      "hash": "abc123..."
    },
    "records": {
      "record_1": {
        "type": "MOVE_IN",
        "status": "APPROVED",
        "photos": [
          {"category": "FLOOR", "hash": "def456..."},
          {"category": "WALL_EAST", "hash": "ghi789..."}
        ]
      }
    },
    "recordings": [
      {"id": 1, "title": "계약 협의", "hash": "jkl012..."}
    ]
  }
}
```

### 진위 확인 프로세스

1. **현재 파일 해시 재계산** - 서버에 저장된 파일들로 해시 생성
2. **DB 저장 해시와 비교** - `blockchain_final_hash`와 비교
3. **일치 여부 표시**
   - ✅ 일치: "파일 무결성 확인됨 - 계약 확정 시점과 동일"
   - ❌ 불일치: "파일 변조 감지됨 - 변경된 파일 목록 표시"
4. **Kaia Scope 링크 제공** - 블록체인에서 직접 확인 가능

### URL 구조

| URL | 설명 |
|-----|------|
| `/blockchain/contract/<id>/finalize/` | 계약 확정 페이지 |
| `/blockchain/contract/<id>/verify/` | 진위 확인 페이지 |
| `/blockchain/contract/<id>/status/` | 블록체인 상태 (AJAX) |
| `/blockchain/contract/<id>/retry/` | 앵커링 재시도 (AJAX) |

### 비용 (테스트넷은 무료)

| 환경 | 트랜잭션당 비용 | 50 KAIA로 가능 건수 |
|------|---------------|-------------------|
| Kairos (테스트넷) | 무료 (Faucet) | 무제한 |
| Mainnet | ~0.0008 KAIA | ~62,500건 |

### 트랜잭션 확인

앵커링된 트랜잭션은 Kaia Scope에서 확인 가능:
- **테스트넷**: https://kairos.kaiascan.io/tx/0x{tx_hash}
- **메인넷**: https://kaiascan.io/tx/0x{tx_hash}

---

## 📦 배포 계획

### 아키텍처

```
┌──────────────────┐
│ PythonAnywhere   │ Django 앱 호스팅
└────────┬─────────┘
         │
         ├─────────────────┐
         │                 │
┌────────▼─────┐   ┌───────▼────────┐
│ Supabase     │   │ Cloudflare R2  │
│ PostgreSQL   │   │ File Storage   │
└──────────────┘   └────────────────┘
```

### 무료 티어

- **PythonAnywhere**: 무료 (제한적)
- **Supabase**: 500MB 무료
- **Cloudflare R2**: 10GB 무료

### 배포 전 체크리스트

- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` 설정
- [ ] `SECRET_KEY` 환경변수로 분리
- [ ] HTTPS 강제 (`SECURE_SSL_REDIRECT = True`)
- [ ] 정적 파일 수집 (`python manage.py collectstatic`)
- [ ] 데이터베이스 마이그레이션
- [ ] 환경변수 설정 (.env)

---

## 🐛 알려진 이슈 및 해결

### 1. Bootstrap 스타일 미적용 문제
**원인**: URL 순서가 잘못되어 allauth 기본 템플릿이 우선 적용됨

**해결**:
```python
# config/urls.py
urlpatterns = [
    path('accounts/', include('accounts.urls')),  # 커스텀 URLs 먼저
    path('auth/', include('allauth.urls')),       # allauth URLs 나중에
]
```

### 2. 소셜 로그인 후 signup 페이지 무한 루프
**원인**: `ACCOUNT_USERNAME_REQUIRED = True`로 설정

**해결**:
```python
# config/settings.py
ACCOUNT_USERNAME_REQUIRED = False
```

### 3. User/SocialAccount 동기화 문제
**원인**: Admin에서 SocialAccount 삭제 후 User가 남아 재가입 시 충돌

**해결**: `pre_social_login`에서 이메일 기반 자동 연결 로직 추가 (위 코드 참조)

### 4. ValidationError 페이지 표시
**원인**: `save_model`에서 ValidationError 발생

**해결**: 폼의 `clean()` 메서드로 이동하여 인라인 에러 표시
```python
# contracts/admin.py
class ContractAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        # 검증 로직
        if has_changes and not admin_note:
            raise ValidationError('수정 사유를 입력해주세요.')
        return cleaned_data
```

---

## 💡 개발 팁

### 1. 서버 재시작 (포트 충돌 시)
```bash
lsof -ti:8000 | xargs kill -9
source venv/bin/activate
python manage.py runserver
```

### 2. 마이그레이션 리셋 (개발 중에만!)
```bash
# 주의: 데이터 손실됨!
rm db.sqlite3
rm -rf */migrations/0*.py
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 3. 정적 파일 수집 (배포 시)
```bash
python manage.py collectstatic --noinput
```

### 4. 슈퍼유저 생성
```bash
python manage.py createsuperuser
```

### 5. Django Shell 사용
```bash
python manage.py shell
```
```python
from accounts.models import User
from contracts.models import Contract

# 사용자 조회
user = User.objects.get(username='test')

# 계약 조회
contracts = Contract.objects.filter(tenant=user)
```

---

## 📊 개발 진행률

```
전체 진행률: 약 80%

✅ 인증 시스템         100%
✅ 계약 관리           100%
✅ 계약 연장/해지      100%
✅ 알림 시스템         100%
✅ 녹음 기능           100%
✅ 이력 관리           100%
✅ 관리자 패널         100%
✅ 모바일 UI           100%
✅ 입실/퇴실 기록      100%
✅ 블록체인 증거화     100%
⏳ 검색/필터            0%
⏳ 통계 대시보드         0%
```

---

## 📝 라이센스

이 프로젝트는 개인 프로젝트입니다.

---

## 👤 개발자

**개발 지원**: Claude Code (Anthropic)
**프로젝트 관리**: wonkyoung

---

## 📞 문의

프로젝트 관련 문의사항은 GitHub Issues를 통해 남겨주세요.

---

**마지막 업데이트**: 2026-02-25
**버전**: 0.8.0
