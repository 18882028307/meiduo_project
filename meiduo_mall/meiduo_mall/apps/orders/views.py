from decimal import Decimal

from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import SKU

from .serializers import OrderAllSerializer
from .models import OrderInfo
from .serializers import OrderSettlementSerializer

from .serializers import SaveOrderSerializer


class OrderSettlementView(APIView):
    """订单结算"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        获取
        """
        user = request.user

        # 从购物车中获取用户勾选要结算的商品信息
        redis_conn = get_redis_connection('cart')
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(redis_cart[sku_id])

        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]
            sku.selected = True

        # 运费
        freight = Decimal('9.00')

        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})
        return Response(serializer.data)


class SaveOrderView(CreateAPIView, ListAPIView):
    """保存订单"""

    permission_classes = [IsAuthenticated]
    serializer_class = SaveOrderSerializer

    def get(self, request, *args, **kwargs):
        """全部订单"""
        self.serializer_class = OrderAllSerializer
        # 获取当前登录用户
        user = request.user
        # 根据user获取所有订单信息
        orders = OrderInfo.objects.filter(user_id=user.id).all().order_by('-create_time')
        count = orders.count()

        queryset = self.filter_queryset(orders)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        # 创建序列化器
        # serializer = OrderAllSerializer(orders, many=True)
        return Response({'count': count, 'results': serializer.data})
