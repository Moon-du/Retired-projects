import logging
import time

import requests
import telebot
from fake_useragent import UserAgent
from jsonpath import jsonpath


class ListeningLaunchpool:
    """监听launchpool项目"""

    def __init__(self):
        # 日志配置
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(funcName)s - %(message)s")
        # 生成随机user-agent
        self.ua = UserAgent()
        # 实例化session
        self.session = requests.Session()
        self.proxy_pool = {
            "proxy1": None,
            "proxy2": {"http": "http://42.193.8.164:3128"},
            "proxy3": {"http": "http://152.69.196.42:7817"},
            "proxy4": {"http": "http://138.2.46.148:7817"},
        }
        self.binance_url = "https://www.yingwangtech.club"
        # 重试次数
        self.retry_count = 0
        # 监听状态
        self.is_listen = True
        # telegram_bot
        self.chat_id = "6380950127"
        self.telegram_bot = telebot.TeleBot("7198746866:AAE1qw5pk13t40EJQm1zZUR-t6qTB4We6qw")

    def get_latest_launchpool(self):
        """获取launchpool最新项目"""
        # 生成随机user-agent请求launchpool接口
        launchpool_info, launchpool_res, coming_launchpool, completed_launchpool = None, None, None, None
        launchpool_url = f"{self.binance_url}/bapi/lending/v1/friendly/launchpool/project/listV3?type=1&pageNo=1&pageSize=1&page=1"
        headers = {
            "user-agent": self.ua.random,
            "mclient-x-tag": "tfph2mpTPAuwxbiMHoQc"
        }
        try:
            # 获取launchpool信息并解析
            launchpool_res = self.session.request("GET", launchpool_url, headers=headers, proxies=self.session.proxies)
            launchpool_info = launchpool_res.json()
            # 获取最新一期&上期launchpool信息
            completed_launchpool = jsonpath(launchpool_info, "$.data.completed.list[0].detailAbstract")[0]
            coming_launchpool = jsonpath(launchpool_info, "$.data.coming..detailAbstract")[0]
        except Exception as e:
            if launchpool_info is None:
                logging.error(f"\n错误信息：{e}"
                              f"\n获取launchpool数据失败,原始响应信息：{launchpool_res}")
                self.telegram_bot.send_message(self.chat_id, f"获取launchpool数据失败,原始响应信息：{launchpool_res}")
                # 重试次数+1
                self.retry_count += 1

        return {
            "coming_launchpool": coming_launchpool,
            "completed_launchpool": completed_launchpool
        }

    def start_bnb_contract(self):
        """开启BNB合约"""
        self.telegram_bot.send_message(self.chat_id, f"开启BNB合约")
        logging.info("开启BNB合约")

    def main(self):
        """监听launchpool信息当发布新一期launchpool时开启交易"""
        while self.is_listen:
            # 获取最新launchpool信息
            if self.retry_count >= 3:
                break
            # 切换代理避免429
            for proxy_name, proxy in self.proxy_pool.items():
                self.session.proxies = proxy
                time.sleep(2)
                announcement_info = self.get_latest_launchpool()
                if announcement_info["coming_launchpool"]:
                    logging.info(
                        f"当前代理：{proxy_name},发现新launchpool项目：{announcement_info['coming_launchpool']}")
                    # 开启BNB合约并结束监听
                    self.start_bnb_contract()
                    self.is_listen = False
                else:
                    logging.info(
                        f"当前代理：{proxy_name},未发现新launchpool项目，上期launchpool信息：{announcement_info['completed_launchpool']}")


if __name__ == "__main__":
    ListeningLaunchpool().main()
