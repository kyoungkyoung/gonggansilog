# AI 녹음 전사 및 요약 기능 설정 가이드

## 개요
녹음 파일이 저장되면 자동으로:
1. **Whisper API**로 음성을 텍스트로 변환 (전사)
2. **GPT-4o-mini**로 텍스트를 요약
3. 결과를 데이터베이스에 저장

## 비용 안내
- **Whisper API**: 약 $0.006/분 (녹음 1분당 약 8원)
- **GPT-4o-mini**: 매우 저렴 (요약 1건당 약 1-2원)
- **예상 총 비용**: 5분 녹음 1건당 약 **42원**

## 설정 방법

### 1. OpenAI API 키 발급

1. https://platform.openai.com/ 접속
2. 로그인 또는 회원가입
3. 우측 상단 프로필 > "API keys" 클릭
4. "+ Create new secret key" 클릭
5. 이름 입력 (예: "상가관리앱") 후 생성
6. **API 키 복사** (한 번만 표시되므로 꼭 저장!)

### 2. 결제 수단 등록

1. 좌측 메뉴에서 "Settings" > "Billing" 클릭
2. "Add payment method" 클릭
3. 신용카드 정보 입력
4. (선택) Usage limits 설정으로 월 사용량 제한 가능

### 3. 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일 생성:

```bash
# .env 파일 생성
cd /Users/wonkyoung/claude/공간실록
touch .env
```

`.env` 파일 내용:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**중요**:
- API 키는 `sk-`로 시작합니다
- `.env` 파일은 Git에 커밋되지 않습니다 (.gitignore에 포함됨)
- API 키를 절대 공개 저장소에 업로드하지 마세요!

### 4. 서버 재시작

환경 변수를 읽어오기 위해 서버를 재시작합니다:

```bash
# 기존 서버 중지 (Ctrl+C)
# 서버 재시작
python3 manage.py runserver
```

## 사용 방법

### 녹음 생성
1. `/recordings/create/` 페이지에서 녹음 시작
2. 녹음 완료 후 저장
3. **자동으로 AI 처리 시작** (약 10-30초 소요)

### 결과 확인

#### 일반 사용자 (임대인/임차인)
- 녹음 상세 페이지에서 **AI 요약** 확인
- 처리 상태 표시:
  - 🟢 완료: 요약 내용 표시
  - 🟡 처리 중: 잠시 후 다시 확인
  - 🔴 실패: 오류 발생

#### 관리자
- Admin 페이지 > 녹음 기록
- "AI 처리 정보" 섹션 펼치기
- **전사본 (원본 텍스트)** + **요약** 모두 확인 가능

## 구현 세부사항

### 추가된 파일
```
recordings/
├── ai_services.py          # AI 처리 로직
├── models.py               # transcript, summary 등 필드 추가
├── views.py                # 자동 AI 처리 로직 추가
├── admin.py                # Admin 페이지 업데이트
└── templates/
    └── recordings/
        └── recording_detail.html  # AI 요약 표시

config/
├── settings.py             # OPENAI_API_KEY 설정
└── .env                    # API 키 저장 (생성 필요)

.env.example                # 환경 변수 템플릿
```

### 데이터베이스 필드
```python
class Recording(models.Model):
    # 기존 필드들...

    # 새로 추가된 필드
    transcript = models.TextField()          # 전사본 (관리자만)
    summary = models.TextField()             # 요약 (모두)
    processing_status = models.CharField()   # PENDING/PROCESSING/COMPLETED/FAILED
    processed_at = models.DateTimeField()    # 처리 완료 시간
```

### AI 처리 프로세스
```
녹음 저장
    ↓
상태: PROCESSING
    ↓
Whisper API 호출 → 전사본 생성
    ↓
GPT-4o-mini 호출 → 요약 생성
    ↓
DB에 저장
    ↓
상태: COMPLETED
```

## 문제 해결

### API 키 오류
```
Error: Invalid API key
```
→ `.env` 파일에 올바른 API 키가 있는지 확인
→ 서버를 재시작했는지 확인

### 처리 실패
```
processing_status = 'FAILED'
```
→ API 사용량 한도 확인
→ 오디오 파일 형식 확인 (webm 지원)
→ 서버 로그 확인: `tail -f nohup.out` 또는 터미널 출력

### 비용 관리
- OpenAI 대시보드에서 사용량 모니터링
- Usage limits 설정으로 월 최대 비용 제한
- 테스트용으로 먼저 짧은 녹음으로 확인

## 다음 단계

### 최적화 방안
1. **비동기 처리** (Celery 도입)
   - 현재: 동기 처리 (녹음 저장 시 기다림)
   - 개선: 백그라운드 작업으로 처리

2. **배치 처리**
   - 여러 녹음을 한 번에 처리

3. **캐싱**
   - 동일한 녹음 재처리 방지

### 추가 기능 아이디어
- 키워드 추출
- 감정 분석
- 중요 구절 하이라이트
- 다국어 지원

## 지원

문제가 발생하면:
1. 서버 로그 확인
2. OpenAI 대시보드에서 API 호출 로그 확인
3. `.env` 파일 설정 재확인

---

**마지막 업데이트**: 2025-12-29
**구현 완료**: ✅ 모든 기능 구현 완료
