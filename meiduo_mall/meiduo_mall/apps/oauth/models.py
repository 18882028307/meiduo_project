from django.conf import settings
from django.db import models

# Create your models here.
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData

from . import constants


class BaseModel(models.Model):
    """为模型类补充字段"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now_add=True, verbose_name='更新时间')

    class Meta:
        # 声明抽象模型类, 用于继承使用，数据库迁移时不会创建BaseModel的表
        abstract = True


class OAuthQQUser(BaseModel):
    """
    QQ登陆用户数据
    """
    # 定义关联数据删除时,与之关联的数据也删除
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    # 为openid字段建立索引
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name

    @staticmethod
    def generate_save_user_token(openid):
        """
        生成保存用户数据的token
        :param openid: 用户的openid
        :return: token
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        data = {'openid': openid}
        token = serializer.dumps(data)
        return token.decode()

    @staticmethod
    def check_save_user_token(token):
        """
        检验保存用户数据的token
        :param token: token
        :return: openid or None
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            return data.get('openid')
