import re

from django.shortcuts import render

# Create your views here.
from rest_framework import status, mixins
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .utils import get_user_by_account
from meiduo_mall.apps.verifications.serializers import CheckImageCodeSerializer
from . import serializers
from .models import User


class UsernameCountView(APIView):
    '''
    判断用户名是否存在
    '''
    def get(self, request, username):
        '''
        获取指定用户名数量
        :param request:
        :param username:
        :return:
        '''
        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count
        }
        return Response(data)


class MobileCountView(APIView):
    '''
    手机号
    '''
    def get(self, request, mobile):
        '''
        获取指定手机号
        :param request:
        :param mobile:
        :return:
        '''
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }
        return Response(data)


class UserView(CreateAPIView):
    """
    用户注册
    """
    serializer_class = serializers.CreateUserSerializer


class SMSCodeTokenView(GenericAPIView):
    """
    根据账号和图片验证码，获取发送短信的token
    """
    serializer_class = CheckImageCodeSerializer

    def get(self, request, account):
        print('????')
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = get_user_by_account(account)
        if user is None:
            return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 生成发送短信的access_token
        access_token = user.generate_send_sms_token()

        # 处理手机号
        mobile = re.sub(r'(\d{3})\d{4}(\d{3})', r'\1****\2', user.mobile)

        return Response({'mobile': mobile, 'access_token': access_token})


class PasswordTokenView(GenericAPIView):
    """
    用户账号设置密码的token
    """
    serializer_class = serializers.CheckSMSCodeSerializer

    def get(self, request, account):
        '''
        根据用户账号获取修改密码的token
        :param request:
        :param account:
        :return:
        '''
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = serializer.user

        # 生成修改用户密码的access token
        access_token = user.generate_set_password_token()

        return Response({'user_id': user.id, 'access_token': access_token})


class PasswordView(mixins.UpdateModelMixin, GenericAPIView):
    '''
    用户密码
    '''

    queryset = User.objects.all()
    serializer_class = serializers.ResetPasswordSerializer

    def post(self, request, pk):
        return self.update(request, pk)