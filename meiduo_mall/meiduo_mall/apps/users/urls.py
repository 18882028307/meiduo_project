from django.conf.urls import url

# from meiduo_mall.meiduo_mall.apps.verifications import views
from rest_framework_jwt.views import obtain_jwt_token

from . import views
urlpatterns = [
    url(r'usernames/(?P<username>\w{5,20})/count/', views.UsernameCountView.as_view()),
    url(r'mobiles/(?P<mobile>1[345789]\d{9})/count/', views.MobileCountView.as_view()),
    url(r'users/', views.UserView.as_view()),
    # 获取登录JWT token
    url(r'authorizations/$', obtain_jwt_token)
]