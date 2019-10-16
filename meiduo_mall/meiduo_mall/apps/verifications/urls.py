from django.conf.urls import url

from meiduo_mall.meiduo_mall.apps.verifications import views

urlpatterns = [
    url(r'image_codes/(?P<image_code_id>.+)/$', views.ImageCodeView.as_view())
]