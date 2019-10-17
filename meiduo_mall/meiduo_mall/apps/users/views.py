from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView

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