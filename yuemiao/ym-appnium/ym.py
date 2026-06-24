import datetime
import json
import logging
import time

import requests
import selenium.common.exceptions
from appium import webdriver
from jsonpath import jsonpath
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)


class Notification:
    """钉钉群通知"""

    def __init__(self, city):
        """初始化通知属性"""
        self.city = city
        self.send_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.notification_urls = {
            "test": "https://oapi.dingtalk.com/robot/send?access_token"
                    "=0354ddbdf68e36be9e931f2555ba4b4bc4c9751af986dd9497206997cdd71968 ",
            "formal-9": "https://oapi.dingtalk.com/robot/send?access_token"
                        "=623c2eaeb43a541108bae75548c070626fc7a5c2f7403c75e95eeb661c6b42ef",
            "formal-4": "https://oapi.dingtalk.com/robot/send?access_token"
                        "=55f4877383250813c2bc9684c977c01eea81f80f9bb92e5f38ce8be05b0cbeac",
            "debug": "https://oapi.dingtalk.com/robot/send?access_token"
                     "=2fb637568180850691c13455329bf1122de97b284980f15862a95d5c55af961d",
        }
        self.isTest = False

    def send_appointment_notification(self, vaccines, department):
        """发送医院可预约通知"""
        if vaccines == 3:
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
            logging.info(f"{self.city}-{department}发送可预约通知成功")
        else:
            logging.error(f"{self.city}-{department}发送可预约通知失败，请检查~\n"
                          f"错误信息：{res}")

    def send_error_notification(self, message):
        """发送服务异常通知"""
        url = self.notification_urls["test"]
        data = {"msgtype": "text",
                "text": {
                    "content":
                        f"服务异常提醒\n"
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
            logging.info(f"{self.city}服务异常提醒发送成功")
        else:
            logging.error(f"{self.city}服务异常提醒发送失败，请检查~\n"
                          f"错误信息：{res}")


def except_handling(city, error_massage):
    """异常处理"""
    message = f"服务运行异常，尝试自动重启服务~\n异常信息：{error_massage}"
    logging.error(message)
    Notification(city).send_error_notification(message)
    Ym().start_listening()


class Ym:
    def __init__(self):
        """初始化连接属性"""
        self.appnium_server = 'http://localhost:4723/wd/hub'
        self.desired_caps = {
            "platformName": "Android",
            "deviceName": "a0af2699",
            "appPackage": "com.matthew.yuemiao",
            "appActivity": "com.matthew.yuemiao.ui.activity.HomeActivity",
        }
        self.driver = webdriver.Remote(self.appnium_server, self.desired_caps)
        self.wait = WebDriverWait(self.driver, 5)
        self.excepts = (
            selenium.common.exceptions.TimeoutException,
            selenium.common.exceptions.WebDriverException,
            selenium.common.exceptions.StaleElementReferenceException,
            selenium.common.exceptions.NoSuchElementException,
            selenium.common.exceptions.InvalidElementStateException,
        )
        self.n_appointment_notification_status = {}
        self.f_appointment_notification_status = {}
        self.CITYS, self.VACCINES = ("济南", "青岛"), (3, 4)

    def switch_city(self, city):
        """切换城市"""
        city_tv_id = "com.matthew.yuemiao:id/city_tv"
        search_city_id = "com.matthew.yuemiao:id/search"
        searched_city_xpath = f"//android.widget.TextView[@text='{city}市']"
        tv_confirm_id = "com.matthew.yuemiao:id/tv_confirm"
        try:
            self.wait.until(ec.presence_of_element_located((By.ID, city_tv_id))).click()
            self.wait.until(ec.presence_of_element_located((By.ID, search_city_id))).set_text(city)
            self.wait.until(ec.presence_of_element_located((By.XPATH, searched_city_xpath))).click()
            self.wait.until(ec.presence_of_element_located((By.ID, tv_confirm_id))).click()
        except self.excepts as error_massage:
            except_handling(city, error_massage)
        time.sleep(1)

    def switch_vaccines(self, vaccines):
        """切换疫苗"""
        hpv_l_id = "com.matthew.yuemiao:id/textView56"
        hpv_f_xpath = f"//androidx.recyclerview.widget.RecyclerView/android.widget.TextView[{vaccines}]"
        time.sleep(1)
        try:
            self.wait.until(ec.presence_of_element_located((By.ID, hpv_l_id))).click()
            self.wait.until(ec.presence_of_element_located((By.XPATH, hpv_f_xpath))).click()
        except self.excepts as error_massage:
            except_handling(vaccines, error_massage)
        time.sleep(1)

    def go_departments(self, city, vaccines):
        """进入医院列表"""
        to_open_id = "com.matthew.yuemiao:id/go"
        allow_id = "com.lbe.security.miui:id/permission_allow_foreground_only_button"
        search_city_id = "com.matthew.yuemiao:id/search"
        hpv_h_xpath = f"//androidx.cardview.widget.CardView[{vaccines}]/android.view.ViewGroup/android.widget.ImageView"
        searched_city_xpath = f"//android.widget.TextView[@text='{city}市']"
        tv_confirm_id = "com.matthew.yuemiao:id/tv_confirm"
        hpv_icon_id = "com.matthew.yuemiao:id/imageView17"
        try:
            # 开启定位
            self.wait.until(ec.presence_of_element_located((By.ID, to_open_id))).click()
            self.wait.until(ec.presence_of_element_located((By.ID, allow_id))).click()
            # 选择地址
            self.wait.until(ec.presence_of_element_located((By.ID, search_city_id))).set_text(city)
            self.wait.until(ec.presence_of_element_located((By.XPATH, searched_city_xpath))).click()
            self.wait.until(ec.presence_of_element_located((By.ID, tv_confirm_id))).click()
            # 选择HPV疫苗
            self.wait.until(ec.presence_of_element_located((By.ID, hpv_icon_id))).click()
            self.wait.until(ec.presence_of_element_located((By.XPATH, hpv_h_xpath))).click()
        except self.excepts as error_massage:
            except_handling(city, error_massage)

    def get_department_info(self, city, vaccines):
        """获取医院信息，疫苗到货后发送通知"""
        notification_status_info = {
            3: self.f_appointment_notification_status,
            4: self.n_appointment_notification_status,
        }
        for i in range(1, 6):
            department_name, vaccines_name, department_subscribe, department_lack = None, None, False, False
            department_subscribe_xpath = f"//android.view.ViewGroup[{i}]/*[@resource-id='com.matthew.yuemiao:id/textView70']"
            department_lack_xpath = f"//android.view.ViewGroup[{i}]/*[@resource-id='com.matthew.yuemiao:id/textView71']"
            vaccines_name_xpath = f"//android.view.ViewGroup[{i}]/*[@resource-id='com.matthew.yuemiao:id/textView72']"
            department_name_xpath = f"//android.view.ViewGroup[{i}]/*[@resource-id='com.matthew.yuemiao:id/textView74']"
            try:
                vaccines_name = self.wait.until(ec.presence_of_element_located((By.XPATH, vaccines_name_xpath))).text
                department_name = self.wait.until(
                    ec.presence_of_element_located((By.XPATH, department_name_xpath))).text
            except self.excepts as error_massage:
                except_handling(vaccines, error_massage)
            try:
                department_subscribe = self.driver.find_element(By.XPATH, department_subscribe_xpath).is_displayed()
            except selenium.common.exceptions.NoSuchElementException:
                pass
            except self.excepts as error_massage:
                except_handling(vaccines, error_massage)
            try:
                department_lack = self.driver.find_element(By.XPATH, department_lack_xpath).is_displayed()
            except selenium.common.exceptions.NoSuchElementException:
                pass
            except self.excepts as error_massage:
                except_handling(vaccines, error_massage)
            if department_subscribe or department_lack:
                logging.info(f"{city}-{vaccines}-{department_name}需订阅或缺货")
                notification_status_info[vaccines][department_name + vaccines_name] = 0
            else:
                logging.info(f"{city}-{vaccines}-{department_name}可预约")
                if department_name + vaccines_name in notification_status_info[vaccines]:
                    if notification_status_info[vaccines][department_name + vaccines_name] == 0:
                        Notification(city).send_appointment_notification(vaccines, department_name)
                        notification_status_info[vaccines][department_name + vaccines_name] = 1
                else:
                    Notification(city).send_appointment_notification(vaccines, department_name)
                    notification_status_info[vaccines][department_name + vaccines_name] = 1

    def start_listening(self):
        """开始监听"""
        self.go_departments(self.CITYS[0], self.VACCINES[1])
        rounds = 1
        while True:
            self.get_department_info(self.CITYS[0], self.VACCINES[1])
            self.switch_vaccines(self.VACCINES[0])
            self.get_department_info(self.CITYS[0], self.VACCINES[0])
            self.switch_vaccines(self.VACCINES[1])
            logging.info(f"--------------------------疫苗监听服务已运行{rounds}次-------------------------\n\n")
            rounds += 1


if __name__ == '__main__':
    Ym().start_listening()
