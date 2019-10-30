from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import serializers

from carts.serializers import CartSKUSerializer

from goods.models import SKU

from .models import OrderGoods
from .models import OrderInfo


class OrderSettlementSerializer(serializers.Serializer):
    """商品列表序列化器"""
    freight = serializers.DecimalField(max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True, read_only=True)


class SaveOrderSerializer(serializers.ModelSerializer):
    """
    下单数据序列化器
    """

    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        """保存订单"""
        # 获取当前下单用户
        """
                保存订单
                """
        # 获取当前下单用户
        user = self.context['request'].user

        # 创建订单编号
        # 订单编号格式 20170903153611+user.id
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        address = validated_data['address']
        pay_method = validated_data['pay_method']

        # 生成订单
        # 开启事务
        with transaction.atomic():
            # 创建保存点，记录当前数据状态
            save_id = transaction.savepoint()

            try:
                # 创建订单信息
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('9.00'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'CASH'] else OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )
                # 获取购物车信息
                redis_conn = get_redis_connection('cart')
                cart_redis = redis_conn.hgetall('cart_%s' % user.id)
                cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

                # 将bytes类型转换为int类型
                cart = {}
                # cart: {
                # sku_id: count,
                # sku_id: count
                # }
                for sku_id in cart_selected:
                    cart[int(sku_id)] = int(cart_redis[sku_id])

                # 一次查询出所有商品数据
                sku_obj_list = SKU.objects.filter(id__in=cart.keys())

                # 处理订单商品
                for sku in sku_obj_list:

                    # 判断商品库存是否充足
                    sku_count = cart[sku.id]

                    if sku.stock < sku_count:
                        # 事务回滚
                        transaction.savepoint_rollback(save_id)
                        raise serializers.ValidationError('商品库存不足')

                    # 减少商品库存
                    sku.stock -= sku_count
                    sku.sales += sku_count
                    sku.save()

                    # 累计总金额
                    order.total_count += sku_count
                    # 累计总额
                    order.total_amount += (sku.price * sku_count)

                    # 保存订单商品
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=sku_count,
                        price=sku.price,
                    )

                # 更新订单的金额数量信息
                order.save()

            except serializers.ValidationError:
                raise
            except Exception:
                # 事务回滚
                transaction.savepoint_rollback(save_id)
                raise

            # 提交事务
            transaction.savepoint_commit(save_id)

            # 清除购物车中已经结算的商品
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *cart_selected)
            pl.srem('cart_selected_%s' % user.id, *cart_selected)
            pl.execute()

            return order


class SKUGoodsSerializer(serializers.ModelSerializer):
    """订单商序列化器"""

    class Meta:
        model = SKU
        fields = ['id', 'name', 'default_image_url']


class OrderGoodsSerializer(serializers.ModelSerializer):
    """全部订单序列"""
    sku = SKUGoodsSerializer(read_only=True)

    class Meta:
        model = OrderGoods
        fields = ['id', 'order', 'sku', 'count', 'price']


class OrderAllSerializer(serializers.ModelSerializer):
    """全都订单序列化器"""
    skus = OrderGoodsSerializer(many=True, read_only=True)

    create_time = serializers.DateTimeField(label='时间', format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = OrderInfo
        fields = ['total_amount', 'order_id', 'freight', 'pay_method', 'status', 'create_time', 'skus']