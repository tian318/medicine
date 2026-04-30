import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError, TooManyRedirects


class Session:
    def __init__(self):
        self.session = requests.Session()

    def get(self, url, code=200, **kwargs):
        try:
            response = self.session.get(url, **kwargs)
            if response.status_code == code:
                return response
            else:
                return None
        except Timeout:
            print("请求超时")
            return None
        except ConnectionError:
            print("连接错误")
            return None
        except HTTPError as e:
            print(f"HTTP错误: {e}")
            return None
        except TooManyRedirects:
            print("重定向次数过多")
            return None
        except RequestException as e:
            print(f"请求发生错误: {e}")
            return None

    def post(self, url, data=None, json=None, code=200, **kwargs):
        try:
            # 发起POST请求
            response = self.session.post(url, data=data, json=json, **kwargs)

            # 检查HTTP响应状态码
            if response.status_code == code:
                return response
            else:
                return None

        # 处理不同类型的异常
        except Timeout:
            print("请求超时")
            return None
        except ConnectionError:
            print("连接错误")
            return None
        except HTTPError as e:
            print(f"HTTP错误: {e}")
            return None
        except TooManyRedirects:
            print("重定向次数过多")
            return None
        except RequestException as e:
            print(f"请求发生错误: {e}")
            return None
