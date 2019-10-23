import logging
import urllib
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen

from django.conf import settings

logger = logging.getLogger('django')

class OAuthQQ(object):
    """
    用户qq登陆工具类
    """

    def __init__(self, app_id=None, app_key=None, redirect_url=None, state=None):
        self.app_id = app_id or settings.QQ_APP_ID
        self.app_key = app_key or settings.QQ_APP_KEY
        self.redirect_url = redirect_url or settings.QQ_REDIRECT_URL
        self.state = state or settings.QQ_STATE


    def generate_qq_login_url(self):
        """
        拼接用户QQ登录的链接地址
        :return: 链接地址
        """
        url = 'https://graph.qq.com/oauth2.0/authorize?'
        data = {
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_uri': self.redirect_url,
            'state': self.state,
            # 获取用户的qq的openid
            'scope': 'get_user_info'
        }
        query_string = urlencode(data)
        url += query_string
        print(url)

        return url

    def get_access_token(self, code):
        """
        获取qq的access_token
        :param code: 调用的凭据
        :return: access_token
        """
        url = 'https://graph.qq.com/oauth2.0/token?'
        req_data = {
            'grant_type': 'authorization_code',
            'client_id': self.app_id,
            'client_secret': self.app_key,
            'code': code,
            'redirect_url': self.redirect_url
        }

        url += urlencode(req_data)
        try:
            # 发送请求
            response = urlopen(url)
            # 读取QQ返回的响应体数据
            # access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE1
            response = response.read().decode()

            # 将返回的数据转换为字典
            resp_dict = parse_qs(response)

            access_token = resp_dict.get("access_token")[0]
        except Exception as e:
            # logger.error(e)
            # raise QQAPIException('获取access_token异常')
            raise QQAPIException('获取access_token异常')

        return access_token


    def get_openid(self):
        """获取QQ的OpenID"""
        params = {'access_token': self.access_token}
        url = 'https://graph.qq.com/oauth2.0/me?%s' % urllib.urlencode(params)
        response = urlopen(url)
        response = response.read().decode()

        resp_dict = parse_qs(response)
        openid = resp_dict.get("openid")[0]
        # v_str = str(response)[9:-3]  # 去掉callback的字符
        # v_json = json.loads(v_str)

        # openid = v_json['openid']
        self.openid = openid
        return openid