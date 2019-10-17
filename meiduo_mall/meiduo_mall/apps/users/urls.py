from django.conf.urls import url

# from meiduo_mall.meiduo_mall.apps.verifications import views
from . import views
urlpatterns = [
    url(r'usernames/(?P<username>\w{5,20})/count/', views.UsernameCountView.as_view()),
    url(r'mobiles/(?P<mobile>1[345789]\d{9})/count/', views.MobileCountView.as_view()),
]