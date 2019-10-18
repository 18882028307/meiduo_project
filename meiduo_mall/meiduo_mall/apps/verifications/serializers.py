import logging

from django_redis import get_redis_connection
from redis import RedisError
from rest_framework import serializers



# 将日志信息指定到配置文件中设定的日志器
logger = logging.getLogger('django')


class CheckImageCodeSerializer(serializers.Serializer):
    """
    图片验证码校验序列化器
    """
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(min_length=4, max_length=4)

    def validate(self, attrs):
        """
        校验图片验证码是否正确
        :param attrs:
        :return:
        """
        image_code_id = attrs['image_code_id']
        text = attrs['text']

        # 查询redis数据库，获取真实验证码
        redis_conn = get_redis_connection('verify_codes')
        real_image_code = redis_conn.get('img_%s' % image_code_id)

        # 过期或不存在
        if real_image_code is None:
            raise serializers.ValidationError('无效的图片验证码')

        # 验证码校验
        real_image_code = real_image_code.decode()
        if real_image_code.lower() != text.lower():
            raise serializers.ValidationError("图片验证码错误")

        # 验证完后删除redis中的图片验证码
        # 防止暴力验证
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            logger.error(e)

        # redis中发送短信验证码的标志
        # 由redis维护60s有效期
        mobile = self.context['view'].kwargs.get('mobile')
        if mobile:
            send_flag = redis_conn.get('send_flag_%s' % mobile)
            if send_flag:
                raise serializers.ValidationError("发送短信次数过于频繁")

        return attrs