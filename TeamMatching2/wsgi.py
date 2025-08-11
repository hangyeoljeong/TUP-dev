import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TeamMatching2.settings')  # 실제 프로젝트 폴더명에 맞게 수정

application = get_wsgi_application()