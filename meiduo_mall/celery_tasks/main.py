from celery import Celery
import os

# 指明celery可以读取的django配置文件，并注册添加email的任务
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

# 创建celery应用
celery_app = Celery('meiduo_project')

# 导入celery配置
celery_app.config_from_object('celery_tasks.config')

# 自动注册celery任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])

