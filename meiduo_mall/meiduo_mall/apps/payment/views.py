import os

from alipay import AliPay
from django.conf import settings
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import OrderInfo

from .models import Payment


class PaymentView(APIView):
    """
    支付宝支付
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        user = request.user
        # 校验订单order_id
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExits:
            return Response({'message': '订单信息有误'}, status=status.HTTP_400_BAD_REQUEST)

        # 根据订单的数据,向支付宝发起请求,获取支付链接参数
        alipay_client = AliPay(
            appid=settings.ALIPAY_APPID,
            # 默认回调路由
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            # 支付宝的公钥,验证支付宝回传消息使用,不是你自己的公钥
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),  "keys/alipay_public_key.pem"),
            # RSA 或者RSA2
            sign_type="RSA2",
            # 默认False
            debug=settings.ALIPAY_DEBUG
        )
        order_string = alipay_client.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url="http://www.meiduo.com:8080/pay_success.html",
        )

        # 需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        # 拼接链接返回前端
        alipay_url = settings.ALIPAY_GATEWAY_URL + '?' +order_string
        print(alipay_url)
        return Response({'alipay_url': alipay_url})


class PaymentStatusView(APIView):
    """
    修改支付结果状态
    """

    def put(self, request):
        # 获取请求的参数
        query_dict = request.query_params
        # 将django中的querydict转换为python的字典
        alipay_data_dict = query_dict.dict()

        sign = alipay_data_dict.pop('sign')

        # 校验请求参数是否是支付宝的
        alipay_client = AliPay(
            appid=settings.ALIPAY_APPID,
            # 默认回调url
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"keys/alipay_public_key.pem"),
            # RSA 或者 RSA2
            sign_type="RSA2",
            # 默认False
            debug=settings.ALIPAY_DEBUG
        )

        success = alipay_client.verify(alipay_data_dict, sign)

        if success:
            order_id = alipay_data_dict.get('out_trade_no')
            # 支付宝交易流水号
            trade_id = alipay_data_dict.get('trade_no')


            # 保存支付数据
            # 修改订单数据
            Payment.objects.create(order_id=order_id, trade_id=trade_id)

            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])
            return Response({'trade_id': trade_id})
        else:
            # 参数不是支付宝的，是非法请求
            return Response({'message': '非法请求'}, status=status.HTTP_403_FORBIDDEN)