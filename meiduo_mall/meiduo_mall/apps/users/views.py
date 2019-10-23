import re

from django.shortcuts import render

# Create your views here.
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from . import constants
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


class UserDetailView(RetrieveAPIView):
    '''
    用户详情
    '''
    serializer_class = serializers.UserDetailSerializer
    # 增加权限认证，只允许通过认证的用户
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # django jwt 默认的认证，会在request里携带user用户信息
        # 如果没有用户对象，则使用匿名用户
        # print('12122222222222222333333333333333333333', self.request.user)
        return self.request.user


class EmailView(UpdateAPIView):
    """
    保存用户邮箱
    """
    # 视图使用的序列化器
    serializer_class = serializers.EmailSerializer
    # 用户权限认证
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return  self.request.user


class EmailVerifyView(APIView):
    """邮箱验证"""

    def get(self, request):
        # 获取token
        token = request.query_params.get('token')
        if not token:
            return Response({"缺少token"}, status=status.HTTP_400_BAD_REQUEST)

        # 校验保存
        result = User.check_email_verify_token(token)

        if result:
            return Response({'message': 'OK'})
        else:
            return Response({'非法的token'}, status=status.HTTP_400_BAD_REQUEST)


class AddressViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = serializers.UserAddressSerializer
    permissions = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        # 检查用户地址数据数目不能超过上限
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '保存地址数据已达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = serializers.AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)