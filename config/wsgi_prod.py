"""
WSGI config for PythonAnywhere production deployment.

PythonAnywhere 웹 앱 설정에서 이 파일을 WSGI 파일로 지정하세요.
"""
import os
import sys
from dotenv import load_dotenv

# 프로젝트 경로 추가
project_home = '/home/gonggansilog/gonggansilog'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# .env 파일 로드
env_path = os.path.join(project_home, '.env')
load_dotenv(env_path)

# 프로덕션 설정 사용
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_prod'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
