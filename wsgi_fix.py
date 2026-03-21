"""
WSGI Configuration for PythonAnywhere
إعداد ملف WSGI الصحيح للنشر
"""
import sys
import os

# إضافة مسار المشروع
project_home = '/home/mahmoudsaleh112/aluminium-hub'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# تعيين البيئة
os.environ['FLASK_ENV'] = 'production'

# استيراد التطبيق من الملف الصحيح
from api import app as application

# تعيين الإعدادات
application.config['DEBUG'] = False
application.config['ENV'] = 'production'
