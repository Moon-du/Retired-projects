import datetime
import json
import sys

import requests
from jsonpath import jsonpath

from conf.logger import Logger


class Notification:
    """钉钉群通知"""

    def __init__(self, city):
        """初始化通知属性"""
        self.city = city
        self.logging = Logger(self.city)
        self.send_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.notification_urls = {
            "test": "https://oapi.dingtalk.com/robot/send?access_token"
                    "=0354ddbdf68e36be9e931f2555ba4b4bc4c9751af986dd9497206997cdd71968 ",
            "formal-9": "https://oapi.dingtalk.com/robot/send?access_token"
                    "=649a092161ceda91c94ec436ca32b5439d60af7287447e8d0767952073723b4b ",
            "formal-4": "https://oapi.dingtalk.com/robot/send?access_token"
                    "=55f4877383250813c2bc9684c977c01eea81f80f9bb92e5f38ce8be05b0cbeac",
            "debug": "https://oapi.dingtalk.com/robot/send?access_token"
                    "=2fb637568180850691c13455329bf1122de97b284980f15862a95d5c55af961d",
        }
        if "win" in sys.platform:
            self.isTest = True
        else:
            self.isTest = False

    def send_appointment_notification(self, custom, department):
        """发送医院可预约通知"""
        if custom == "四价":
            url = self.notification_urls["test" if self.isTest else "formal-4"]
        else:
            url = self.notification_urls["test" if self.isTest else "formal-9"]
        data = {"msgtype": "text",
                "text": {
                    "content":
                        f"{self.city}:  {department}\n"
                        "\n"
                        f"时间:  {self.send_time}\n"
                },
                "at": {"isAtAll": "false"}
                }
        headers = {
            'Content-Type': 'application/json',
            'Connection': 'close',
        }
        res = requests.post(url, json.dumps(data), headers=headers).json()
        errmsg = jsonpath(res, "$.errmsg")
        if 'ok' in errmsg:
            self.logging.info(f"{self.city}群发送{department}{custom}疫苗可预约通知成功")
        else:
            self.logging.error(f"{self.city}群发送{department}{custom}疫苗可预约通知失败，请检查~\n"
                               f"错误信息：{res}")

    def send_subscribe_notification(self, custom, department):
        """发送医院可订阅通知"""
        url = self.notification_urls["test" if self.isTest else "formal-9"]
        data = {"msgtype": "text",
                "text": {
                    "content":
                        f"{self.city}:  {department}\n"
                        "\n"
                        f"时间:  {self.send_time}\n"
                },
                "at": {"isAtAll": "false"}
                }
        headers = {
            'Content-Type': 'application/json',
            'Connection': 'close',
        }
        res = requests.post(url, json.dumps(data), headers=headers).json()
        errmsg = jsonpath(res, "$.errmsg")
        if 'ok' in errmsg:
            self.logging.info(f"{self.city}群发送{department}{custom}疫苗可订阅通知成功")
        else:
            self.logging.error(f"{self.city}群发送{department}{custom}疫苗可订阅通知失败，请检查~\n"
                               f"错误信息：{res}")

    def send_error_notification(self, custom, message):
        """发送服务异常通知"""
        url = self.notification_urls["test"]
        data = {"msgtype": "text",
                "text": {
                    "content":
                        f"{self.city}{custom}服务异常提醒\n"
                        "\n"
                        f"{message}\n"
                        f"时间:  {self.send_time}\n"
                },
                "at": {"isAtAll": "false"}
                }
        headers = {
            'Content-Type': 'application/json',
            'Connection': 'close',
        }
        res = requests.post(url, json.dumps(data), headers=headers).json()
        errmsg = jsonpath(res, "$.errmsg")
        if 'ok' in errmsg:
            self.logging.info(f"{self.city}群发送{custom}服务异常提醒成功")
        else:
            self.logging.error(f"{self.city}群发送{custom}服务异常提醒失败，请检查~\n"
                               f"错误信息：{res}")


if __name__ == '__main__':
    Notification("formal").send_appointment_notification("九价", "奥特曼儿童医院")
