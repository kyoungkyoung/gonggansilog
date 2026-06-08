# PythonAnywhere 배포 가이드

## 1. PythonAnywhere 계정 생성
- https://www.pythonanywhere.com 에서 계정 생성
- 무료 플랜: `gonggansilog.pythonanywhere.com`

## 2. 코드 업로드
```bash
# PythonAnywhere 콘솔에서
git clone https://github.com/kyoungkyoung/gonggansilog.git
cd gonggansilog
git checkout dev_wk_app
```

## 3. 가상환경 설정
```bash
mkvirtualenv --python=/usr/bin/python3.9 gonggansilog
pip install -r requirements.txt
```

## 4. .env 파일 생성
```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력:
# DJANGO_SECRET_KEY=<새로 생성한 키>
# OPENAI_API_KEY=<실제 키>
# KLAYTN_CHAIN_ID=1001
# KLAYTN_PRIVATE_KEY=<실제 키>
```

## 5. 데이터베이스 설정
```bash
python manage.py migrate --settings=config.settings_prod
python manage.py createsuperuser --settings=config.settings_prod
python manage.py collectstatic --settings=config.settings_prod
```

## 6. 웹 앱 설정 (PythonAnywhere 대시보드)
- **Source code**: `/home/gonggansilog/gonggansilog`
- **Working directory**: `/home/gonggansilog/gonggansilog`
- **Virtualenv**: `/home/gonggansilog/.virtualenvs/gonggansilog`
- **WSGI file**: `config/wsgi_prod.py` 내용으로 교체

### Static files 매핑:
| URL | Directory |
|-----|-----------|
| `/static/` | `/home/gonggansilog/gonggansilog/staticfiles` |
| `/media/` | `/home/gonggansilog/gonggansilog/media` |

## 7. 웹 앱 리로드
- PythonAnywhere 대시보드에서 "Reload" 클릭

## 8. 확인
- `https://gonggansilog.pythonanywhere.com` 접속
- `https://gonggansilog.pythonanywhere.com/api/v1/` API 확인
- `https://gonggansilog.pythonanywhere.com/admin/` 관리자 확인
