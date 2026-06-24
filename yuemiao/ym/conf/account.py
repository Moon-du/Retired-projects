import sys
from json import JSONDecodeError

import requests
from jsonpath import jsonpath

from conf.logger import Logger
from conf.notification import Notification


class Account:
    """设置账号相关信息"""

    def __init__(self, city):
        """初始化账号属性"""
        self.city = city
        self.logging = Logger(self.city)
        if "win" in sys.platform:
            headers_path = ".\\conf\\headers"
        else:
            headers_path = "./conf/headers"
        with open(headers_path) as headers_obj:
            cookie_obj = headers_obj.readlines()
            for line in cookie_obj:
                if "Cookie" in line:
                    self.cookie = line.split("Cookie: ")[1].strip()
                if "tk" in line:
                    self.tk = line.split("tk: ")[1].strip()

    def get_account_info(self):
        """获取用户id,name"""
        url = "https://wx.scmttec.com/order/linkman/findByUserId.do"
        headers = {
            'tk': self.tk,
            'cookie': self.cookie,
        }
        try:
            user_info = requests.get(url=url, headers=headers).json()
            code = jsonpath(user_info, "$.code")[0]
            match int(code):
                case 0000:
                    linkman_id = str(jsonpath(user_info, "$.data[0].id")).strip("[]")
                    user_id = str(jsonpath(user_info, "$.data[0].userId")).strip("[]")
                    user_name = str(jsonpath(user_info, "$.data[0].name")).strip("[]").strip("'")
                    return {
                        'headers': headers,
                        'linkman_id': linkman_id,
                        'user_id': user_id,
                        'user_name': user_name,
                    }
                case 1001:
                    message = (f"获取用户信息失败，请检查~\n"
                               f"错误信息：当前登录已过期，正在尝试重新登录")
                    self.logging.error(message)
                    Notification(self.city).send_error_notification("", message)
                    sys.exit(1)
                case _:
                    message = (f"获取用户信息失败，请检查~\n"
                               f"错误信息：{user_info}")
                    self.logging.error(message)
                    Notification(self.city).send_error_notification("", message)
        except JSONDecodeError as error_massage:
            message = (f"获取用户信息失败，请检查~\n"
                       f"错误信息：{error_massage}")
            self.logging.error(message)
            Notification(self.city).send_error_notification("", message)
        except BaseException as error_massage:
            message = (f"获取用户信息失败，请检查~\n"
                       f"错误信息：{error_massage}")
            self.logging.error(message)
            Notification(self.city).send_error_notification("", message)


if __name__ == '__main__':
    Account("济南").get_account_info()
