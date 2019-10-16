from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework.views import APIView

# from meiduo_mall.meiduo_mall import constants
# from meiduo_mall.meiduo_mall.captcha import captcha
from . import constants
from meiduo_mall.meiduo_mall.libs.captcha.captcha import captcha


class ImageCodeView(APIView):
    """
    图片验证码
    """

    def get(self, request, image_code_id):
        """
        获取图片验证码
        :param request:
        :param image_code_id:
        :return:
        """
        # 生成验证码图片
        text, image = captcha.generate_captcha()
        print('图片验证码是：{}'.format(text))

        # 连接redis数据库
        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        print(image)
        # 指定返回的数据类型
        return HttpResponse(image, content_type="images/jpg")