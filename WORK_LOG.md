# 공간실록 v2 - 작업 로그

## 작업일: 2026-04-18

### 배경
- 부동산 임대차 관리 서비스로, 한국어/영어/일본어 3개 언어 지원 필요
- Django 네이티브 번역(i18n) 방식을 채택 (Google Translate 위젯 대신)
- 이유: 부동산/법률 용어(보증금, 敷金, Security Deposit 등)의 정확한 번역 필요

---

### 1. 정적 번역 파일(.po) 완성

**영어 (locale/en/LC_MESSAGES/django.po)**
- 미번역 629개 문자열 채움 (msgid가 영어인 경우 msgstr = msgid)
- 오번역 199개 수정 (예: "Verification" → "Description" 같은 잘못된 매핑 교정)

**일본어 (locale/ja/LC_MESSAGES/django.po)**
- 앱 고유 미번역 27개 문자열 일본어 번역 추가
- Django 내부 문자열(venv/)은 Django 자체 로케일이 처리하므로 제외

**한국어 (locale/ko/LC_MESSAGES/django.po)**
- 기존 번역 유지, 새로 추가된 문자열만 번역

### 2. Google Translate 위젯 → Django 네이티브 언어 전환

**accounts/templates/base.html**
- Google Translate 위젯 관련 CSS/JS/HTML 제거
- Django 네이티브 언어 전환 드롭다운으로 교체
  - `{% get_available_languages %}` + `set_language` POST form 사용
  - `config/urls.py`의 `path('i18n/', include('django.conf.urls.i18n'))` 활용

### 3. 계약 폼 placeholder 번역

**contracts/forms.py**
- 하드코딩된 한국어 placeholder를 `_()` (gettext_lazy)로 변경
- `__init__`에서 placeholder 설정하여 요청 시점의 언어로 평가
- help_texts도 번역 가능하도록 수정

| 필드 | 한국어 | 영어 | 일본어 |
|------|--------|------|--------|
| 주소 | 예: 서울특별시 강남구... | e.g., 123 Main Street... | 例：東京都新宿区... |
| 이름 | 예: 홍길동 | e.g., John Smith | 例：山田太郎 |
| 전화번호 | 예: 010-1234-5678 | e.g., 010-1234-5678 | 例：090-1234-5678 |

### 4. 날짜 입력 필드 placeholder 번역

**contracts/forms.py**
- `type="date"` → `type="text"` + `onfocus="this.type='date'"` 방식으로 변경
- 브라우저 OS 로케일에 의존하지 않고, 번역된 placeholder 표시
- 클릭 시 네이티브 날짜 피커 활성화

### 5. 주소 자동 번역 (동적 데이터)

**core/address_utils.py (신규)**
- 한국어 주소를 영어 로마자/일본어로 자동 변환하는 유틸리티
- Revised Romanization 기반 한글 로마자 변환
- 주요 도시/구 이름 매핑 (서울→Seoul/ソウル, 강남→Gangnam/カンナム 등)
- 행정구역 접미사 자동 변환 (-구→-gu/区, -로→-ro/路, -길→-gil/通り)

**contracts/models.py**
- `address_en`, `address_ja` 필드 추가
- `save()` 오버라이드: 주소 저장/변경 시 자동 변환
- `get_display_address()`: 현재 언어에 맞는 주소 반환

**25개 템플릿 업데이트**
- `contract.address` → `contract.get_display_address` 일괄 교체

**변환 예시:**
| 한국어 | 영어 | 일본어 |
|--------|------|--------|
| 서울시 성동구 왕십리로 8길 4 | 4, 8-gil, Wangsimni-ro, Seongdong-gu, Seoul-si | ソウル市 ソンドン区 ワンシムニ路 8通り 4 |

### 6. 녹음 제목 자동 번역 (동적 데이터)

**recordings/models.py**
- `title_en`, `title_ja` 필드 추가
- `get_display_title()`: 현재 언어에 맞는 제목 반환

**recordings/ai_services.py**
- `translate_title()` 함수 추가: OpenAI GPT로 제목을 영어/일본어로 번역
- 저장 시점에 한 번만 번역 후 DB에 캐싱 (API 비용 절약)

**recordings/views.py**
- 녹음 저장 시 자동으로 제목 번역 실행

**3개 템플릿 업데이트**
- `recording.title` → `recording.get_display_title`

**번역 예시:**
| 한국어 | 영어 | 일본어 |
|--------|------|--------|
| MZ들 발길 끊었다..."파산 위기" | MZ generation has stopped visiting... "Bankruptcy crisis" | MZたちの足が遠のいた..."破産危機" |

---

### 마이그레이션 이력
- `contracts/migrations/0012_add_translated_address_fields.py` - address_en, address_ja 추가
- `recordings/migrations/0003_add_translated_title_fields.py` - title_en, title_ja 추가

### 정적 번역과 동적 번역 구분

| 구분 | 방식 | 예시 |
|------|------|------|
| 정적 (UI 라벨, 메시지) | Django i18n `.po` 파일 | "Dashboard" → "ダッシュボード" |
| 동적 (주소) | 로마자 변환 유틸리티 | "서울시 강남구" → "Gangnam-gu, Seoul-si" |
| 동적 (녹음 제목) | OpenAI GPT 번역 | "계약 협의" → "Contract Discussion" |

---

## 작업일: 2026-04-19 ~ 2026-05-04

### 7. PDF 리포트 시스템 수정

- **한글 폰트 깨짐 수정**: `AppleSDGothicNeo.ttc`(PostScript, 미지원) → `AppleGothic.ttf`(TTF)로 변경
- **사진 누락 수정**: 템플릿이 있어도 photo에 template_item이 없으면 카테고리 기반으로 폴백
- **사진 메모 표시 추가**: 사진 아래에 📝 메모 텍스트 표시
- **녹음 요약 섹션 추가**: 계약에 연결된 녹음의 AI 요약을 리포트에 포함
- **리포트 생성 모달**: 프로그레스 바 + 단계별 진행 표시 UI
- **계약 상세 페이지에 리포트 버튼 추가**: 입실/퇴실/비교 리포트 바로 생성 가능

### 8. 녹음 상호 동의 워크플로우

- Recording 모델에 `consent_status`, `consented_by`, `consented_at`, `consent_rejected_reason` 필드 추가
- 동의 승인/거절 뷰 및 URL (`/recordings/<pk>/consent/`)
- 녹음 상세 페이지에 동의 상태 UI + 승인 확인 모달 + 거절 사유 모달
- 녹음 목록에 동의 상태 배지 (✅ 동의완료 / ⏳ 대기 / ❌ 거절)
- 거절 시 계약 연결 자동 해제
- 대시보드에 녹음 동의 요청 알림 추가

### 9. AI 요약 모델 수정

- `gpt-5-nano` → `gpt-4o-mini`로 변경
- `max_tokens` → `max_completion_tokens` 파라미터 수정

### 10. 계약 등록 폼 수정

- 계약서 파일 마스킹 시 로딩 모달 충돌 수정 (Bootstrap Modal → CSS Overlay)
- 템플릿 선택 validation 에러 수정 (동적 choices 로드)
- 임대인/임차인 선택 UI 개선 (드롭다운 선택 or 직접 입력 토글)
- "상가 주소" → "주소"로 범용 라벨 변경

### 11. 블록체인 증거화 섹션 재배치

- 계약 상세 페이지 제일 아래로 이동
- 계약 확정 체크리스트 추가:
  - ✅/⚪ 임대인/임차인 연결 완료
  - ✅/⚪ 계약서 파일 업로드 완료
  - ✅/⚪ 입실 기록 승인 완료
- 좌측 체크리스트 + 우측 확정 버튼 레이아웃

### 12. 일본 원상회복 가이드 버그 수정

- `contract.property_type`(존재하지 않는 필드) → `contract.template.property_type`로 수정

### 13. 다수 번역 오류 수정

- fuzzy 플래그 자동 제거 및 올바른 번역 적용
- multiline 문자열 번역 누락 수정
- 오번역 다수 수정 (예: "Register" → "미등록" → "등록")

---

## 기능 구현 로드맵

### 구현 완료 (2026-05-15 ~ 2026-05-18)

| # | 기능 | 상태 | 설명 |
|---|------|------|------|
| 1 | 입주 상태 확인서 | ✅ 완료 | 체크리스트 UI + 상태 선택(정상/하자/노후/수리필요) |
| 2 | 사진 촬영 원칙 | ✅ 완료 | 촬영 가이드라인 카드(전체/근접/위치/날짜) |
| 3 | 하자 통지 기록 | ✅ 완료 | DefectReport + 사진 + 심각도 + 임대인 응답 워크플로우 |
| 4 | 수리 요청/응답 기록 | ✅ 완료 | RepairRequest + 견적/승인/착수/완료 + 코멘트 타임라인 |
| 5 | 수리비/청소비 영수증 | ✅ 완료 | Expense + 영수증 사진 + 카테고리별 합계 |
| 6 | 퇴거 전 사전 점검 | ✅ 완료 | PRE_MOVE_OUT 기록 타입 + 입실 대비 비교 |
| 7 | 퇴거 상태 확인서 | ✅ 완료 | (기존) 퇴실 기록 + 사진 + 승인 + 비교뷰 + PDF + 블록체인 |

---

## 작업일: 2026-05-15 ~ 2026-05-18

### 14. 입주 상태 확인서 + 사진 촬영 원칙 (1순위)

**RecordItemResponse 모델 추가** (records/models.py)
- 모든 템플릿 아이템에 대한 응답 저장
- `condition_status`: 정상/하자 있음/노후/수리 필요
- `response_value`: 체크박스/텍스트/선택/숫자 값
- `notes`: 항목별 메모

**add_photos 뷰/템플릿 전면 재작성**
- `item_type='PHOTO'` 필터 제거 → 모든 아이템 타입 지원
- 각 항목마다 상태 드롭다운 + 타입별 입력(사진/텍스트/체크박스/선택/숫자)
- 사진 촬영 가이드라인 카드 (전체/근접/위치/날짜)

**record_detail 점검 결과 테이블**
- 상태 배지 색상 코딩 (초록=정상, 빨강=하자, 파랑=노후, 주황=수리필요)
- submit_record에서 필수 항목 검증 강화

**PDF 리포트에 점검 결과 테이블 추가**

### 15. 하자 통지 기록 (2순위)

**DefectReport, DefectPhoto 모델** (records/models.py)
- 심각도: 경미/중요/긴급
- 상태: 신고됨 → 확인됨 → 처리중 → 해결됨
- 임대인 답변 + 읽음 상태 추적

**뷰/URL**: defect_list, defect_create, defect_detail, defect_respond
**대시보드 알림**: 임대인(새 하자 신고), 임차인(응답 알림)
**계약 상세**: 하자 통지 섹션 + 하자 신고 버튼

### 16. 수리 요청/응답 기록 (3순위)

**RepairRequest, RepairPhoto, RepairComment 모델** (records/models.py)
- 상태: 요청됨 → 견적 제시 → 승인됨 → 수리 중 → 완료
- 견적 금액 + 실제 비용 추적
- 사진 3단계: 문제/시공중/완료
- 양측 코멘트 타임라인
- 하자 신고와 연결 가능

**뷰/URL**: repair_list, repair_create, repair_detail, repair_update_status, repair_add_comment
**대시보드 알림**: 임대인(새 수리 요청, 견적 승인), 임차인(견적 제시, 착수, 완료)

### 17. 영수증 관리 (4순위)

**Expense 모델** (records/models.py)
- 카테고리: 수리비/청소비/원상복구비/기타
- 부담자: 임대인/임차인
- 영수증 사진 첨부
- 수리 요청과 연결 가능

**뷰/URL**: expense_list, expense_create, expense_detail
**비용 합계**: 전체/임대인/임차인 별도 합산
**계약 상세**: 비용 관리 섹션

### 18. 퇴거 전 사전 점검 (5순위)

- Record 모델에 `PRE_MOVE_OUT` 타입 추가
- `record_type` max_length 10→20 확장
- 입실 완료 후 & 퇴실 전에만 생성 가능
- 여러 번 생성 가능 (입실/퇴실과 달리)
- 입실 vs 사전 점검 비교 뷰 지원
- 계약 상세에 사전 점검 카드 추가

---

### 마이그레이션 이력 (추가분)
- `records/migrations/0006_add_record_item_response.py` - RecordItemResponse
- `records/migrations/0007_add_defect_report.py` - DefectReport, DefectPhoto
- `records/migrations/0008_add_repair_request.py` - RepairRequest, RepairPhoto, RepairComment
- `records/migrations/0009_add_expense.py` - Expense
- `records/migrations/0010_extend_record_type_max_length.py` - record_type max_length 확장

---

## 전체 서비스 기능 완성도

모든 핵심 기능 구현 완료. 남은 작업:
- 블록체인 메인넷 전환 (현재 테스트넷)
- 프로덕션 배포 (PythonAnywhere + Supabase)
- 사용자 피드백 기반 UI/UX 개선
