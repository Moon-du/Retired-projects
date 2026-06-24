import sys
import time
from json import JSONDecodeError
from random import random

import requests
from jsonpath import jsonpath

from conf.account import Account
from conf.logger import Logger
from conf.notification import Notification
from conf.region import Region


class Listening:
    """设置监听信息"""

    def __init__(self, city, custom):
        """初始化监听属性"""
        self.city = city
        self.custom = custom
        self.custom_id = {
            "四价": 2,
            "九价": 3,
        }
        self.logging = Logger(self.city)
        self.user_info = Account(self.city).get_account_info()
        self.session = requests.Session()
        self.headers = self.user_info['headers']
        self.linkman_id = self.user_info['linkman_id']
        self.region = Region(self.city)
        self.appointment_notification_status = {}
        self.subscribe_notification_status = {4698: 0, 25752: 0, 6259: 0, 26225: 0, 26226: 0, 4453: 0, }

    def get_departments(self):
        """获取医院列表"""
        url = "https://wx.scmttec.com/department/department/getDepartments.do"
        params = {
            "offset": 0,
            "limit": 5,
            "name": "",
            "regionCode": self.region.get_region_info()['region_code'],
            "isOpen": 1,
            "longitude": self.region.get_region_info()['longitude'],
            "latitude": self.region.get_region_info()['latitude'],
            "sortType": 1,
            "vaccineCode": "",
            "customId": self.custom_id[self.custom],
        }
        try:
            departments = self.session.get(url=url, headers=self.headers, params=params).json()
            code = jsonpath(departments, "$.code")[0]
            match int(code):
                case 0000:
                    departments_names = jsonpath(departments, "$.data.rows..name")
                    departments_codes = jsonpath(departments, "$.data.rows..code")
                    vacc_ids = jsonpath(departments, "$.data.rows..depaVaccId")
                    vacc_codes = jsonpath(departments, "$.data.rows..vaccineCode")
                    return {
                        'departments_names': departments_names,
                        'departments_codes': departments_codes,
                        'vacc_ids': vacc_ids,
                        'vacc_codes': vacc_codes,
                    }
                case 1001:
                    message = (f"获取医院列表失败，请检查~\n"
                               f"错误信息：当前登录已过期，正在尝试重新登录")
                    self.logging.error(message)
                    Notification(self.city).send_error_notification(self.custom, message)
                    sys.exit(1)
                case _:
                    message = (f"获取医院列表失败，请检查~\n"
                               f"错误信息：{departments}")
                    self.logging.error(message)
                    Notification(self.city).send_error_notification(self.custom, message)
        except JSONDecodeError as error_massage:
            message = (f"获取医院列表失败，请检查~\n"
                       f"错误信息：{error_massage}")
            self.logging.error(message)
        except BaseException as error_massage:
            message = (f"获取医院列表失败，请检查~\n"
                       f"错误信息：{error_massage}")
            self.logging.error(message)
            Notification(self.city).send_error_notification(self.custom, message)

    def get_departements_status(self):
        """获取医院状态"""
        departments_status = []
        departments = self.get_departments()
        department_index = 0
        if departments:
            for vacc_id in departments['vacc_ids']:
                department = departments["departments_names"][department_index]
                url = "https://wx.scmttec.com/subscribe/subscribe/isCanSubscribe.do"
                params = {
                    "vaccineCode": departments['vacc_codes'][department_index],
                    "linkmanId": self.linkman_id,
                    "id": vacc_id,
                    "depaCode": departments['departments_codes'][department_index]
                }
                try:
                    department_info = self.session.get(url=url, headers=self.headers, params=params).json()
                    time.sleep(10+round(random(), 2))
                    code = jsonpath(department_info, "$.code")[0]
                    match int(code):
                        case 0000:
                            type_code = jsonpath(department_info, "$.data.typeCode")
                            type_code = int(str(type_code).strip("[]"))
                        case 1001:
                            message = (f"获取{department}状态失败，请检查~\n"
                                       f"错误信息：当前登录已过期，正在尝试重新登录")
                            self.logging.error(message)
                            Notification(self.city).send_error_notification(self.custom, message)
                            sys.exit(1)
                        case _:
                            type_code = 0
                            message = (f"获取{department}状态失败，请检查~\n"
                                       f"错误信息：{department_info}")
                            self.logging.error(message)
                            Notification(self.city).send_error_notification(self.custom, message)
                except JSONDecodeError as error_massage:
                    type_code = 0
                    message = (f"获取{department}状态失败，请检查~\n"
                               f"错误信息：{error_massage}")
                    self.logging.error(message)
                except BaseException as error_massage:
                    type_code = 0
                    message = (f"获取{department}状态失败，请检查~\n"
                               f"错误信息：{error_massage}")
                    self.logging.error(message)
                    Notification(self.city).send_error_notification(self.custom, message)
                departments_status.append(type_code)
                department_index += 1
            return {
                "departments_status": departments_status,
                "departments_names": departments["departments_names"],
                "vacc_ids": departments["vacc_ids"],
            }

    def start_listening(self):
        """开始监听，疫苗到货后发送通知"""
        rounds = 1
        while True:
            departements_info = self.get_departements_status()
            if departements_info:
                departements_status_index = 0
                for status in departements_info["departments_status"]:
                    department = departements_info["departments_names"][departements_status_index]
                    vacc_id = departements_info["vacc_ids"][departements_status_index]
                    match status:
                        case 1:
                            self.logging.info(f'{department}可预约')
                            if vacc_id in self.appointment_notification_status:
                                if self.appointment_notification_status[vacc_id] == 0:
                                    Notification(self.city).send_appointment_notification(self.custom, department)
                                    self.appointment_notification_status[vacc_id] = 1
                            else:
                                Notification(self.city).send_appointment_notification(self.custom, department)
                                self.appointment_notification_status[vacc_id] = 1
                            if vacc_id in self.subscribe_notification_status:
                                self.subscribe_notification_status[vacc_id] = 0
                        case 2:
                            self.logging.info(f'{department}可订阅')
                            if vacc_id in self.subscribe_notification_status:
                                if self.subscribe_notification_status[vacc_id] == 0:
                                    Notification(self.city).send_subscribe_notification(self.custom, department)
                                    self.subscribe_notification_status[vacc_id] = 1
                            self.appointment_notification_status[vacc_id] = 0
                        case 3:
                            self.logging.info(f'{department}已订阅等待到苗通知')
                            self.appointment_notification_status[vacc_id] = 0
                            if vacc_id in self.subscribe_notification_status:
                                self.subscribe_notification_status[vacc_id] = 0
                        case 4:
                            self.logging.info(f'{department}暂停订阅')
                            self.appointment_notification_status[vacc_id] = 0
                            if vacc_id in self.subscribe_notification_status:
                                self.subscribe_notification_status[vacc_id] = 0
                        case _:
                            self.logging.info(f'获取{department}状态失败')
                    departements_status_index += 1
            self.logging.info(
                f"--------------------------{self.city}{self.custom}监听已运行{rounds}次-------------------------\n\n")
            rounds += 1


if __name__ == '__main__':
    Listening("青岛", "九价").start_listening()
