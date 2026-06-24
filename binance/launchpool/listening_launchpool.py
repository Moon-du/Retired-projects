import logging

import requests
import telebot
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from jsonpath import jsonpath


class QuantitativeTrading:
    """量化交易"""

    def __init__(self):
        # 日志级别
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(funcName)s - %(message)s")
        # telegram_bot设置
        self.chat_id = "6380950127"
        self.telegram_bot = telebot.TeleBot("7198746866:AAE1qw5pk13t40EJQm1zZUR-t6qTB4We6qw")
        # 测试模式
        self.is_test = False
        # 监听状态
        self.is_listening = True
        # 交易状态 可买入：buyable 可卖出：sellable
        self.transaction_status = "buyable"
        # 买入卖出价格
        self.buy_price = 0
        self.sell_price = 0
        # 交易对
        self.base_asset = "BNB"
        self.quote_asset = "USDT"
        self.symbol = self.base_asset + self.quote_asset
        # 上次价格
        self.last_price = 1000
        # API私钥
        with open("test_private_key.pem" if self.is_test else "private_key.pem", 'rb') as f:
            self.private_key = load_pem_private_key(data=f.read(), password=None)
        # API地址
        self.bn_url = "https://testnet.binance.vision" if self.is_test else "https://api.binance.com"
        # APIKEY
        self.app_key = "V8HNJckfdayhhlqtehkOgElCVADf9to3kmJHH4jV6G8qR9zdFz9d6CFqI0I8gzri" if self.is_test \
            else "DFTQCdYFwNitxuwXYz8Ped5asnQdZnpdWjMp80vTL5SkuGz7UUNXiw4IbgC71j2G"
        # 请求头
        self.headers = {
            'X-MBX-APIKEY': self.app_key,
        }

    def get_ticker_price(self):
        """获取交易对价格"""
        ticker_price_url = f"{self.bn_url}/api/v3/ticker/price"
        ticker_price_params = {
            "symbol": self.symbol,
        }
        try:
            # 获取最新价格
            ticker_price_info = requests.get(url=ticker_price_url, params=ticker_price_params)
            match ticker_price_info.status_code:
                case 200:
                    latest_price = jsonpath(ticker_price_info.json(), "$.price")[0]
                    # logging.error(f"当前交易对{self.symbol}价格：{latest_price}")
                    return {
                        "latest_price": float(latest_price)
                    }
                case 429:
                    self.is_listening = False
                    logging.info(f"请求频率超过 API限制，暂停服务")
        except Exception as e:
            logging.info(f"获取交易对{self.symbol}最新价格失败,错误信息：{e}")
            self.telegram_bot.send_message(self.chat_id, f"获取交易对{self.symbol}最新价格失败,错误信息：{e}")

    def main(self):
        """检测价格变化判断是否有新launchpool"""
        # 价格连续下跌次数
        price_drops_num = 0
        while True:
            # 获取最新价格
            ticker_price_info = self.get_ticker_price()
            if ticker_price_info:
                latest_price = ticker_price_info["latest_price"]
                # 如果价格涨幅超过1$发送提示
                if latest_price - self.last_price >= 1 and self.transaction_status != "sellable":
                    # 判断交易状态是否可买入
                    if self.transaction_status != "buyable":
                        logging.info(f"--可能有新矿了当前交易对{self.symbol}价格：{latest_price},上次价格{self.last_price}")
                        # 执行买入操作
                        self.buy_price = latest_price
                        logging.info(f"执行买入操作：买入价格{self.buy_price},上次价格{self.last_price}")
                        self.telegram_bot.send_message(self.chat_id,
                                                       f"--可能有新矿了当前交易对{self.symbol}价格：{latest_price},上次价格{self.last_price}")
                        # 交易状态 可买入：buyable 可卖出：sellable
                        self.transaction_status = "sellable"
                        self.last_price = latest_price


                # 判断价格是否达到顶峰，连续下跌三次执行卖出操作
                elif latest_price > self.last_price and self.transaction_status == "sellable":
                    logging.info(f"--当前交易对{self.symbol}价格：{latest_price},上次价格{self.last_price}")
                    price_drops_num  = 0
                    self.last_price = latest_price
                elif latest_price < self.last_price and self.transaction_status == "sellable":
                    price_drops_num += 1
                    if price_drops_num == 3:
                        logging.info(f"执行卖出操作：买入价格{self.buy_price},卖出价格{latest_price}")
                        self.telegram_bot.send_message(self.chat_id,
                                                       f"--卖出成功买入价格{self.buy_price},卖出价格{latest_price}")
                    logging.info(f"--当前交易对{self.symbol}价格：{latest_price},上次价格{self.last_price}")
                    self.last_price = latest_price
                else:
                    logging.info(f"--当前交易对{self.symbol}价格：{latest_price},上次价格{self.last_price}")
                    # 设置上次价格
                    self.last_price = latest_price
            else:
                continue



if __name__ == '__main__':
    QuantitativeTrading().main()
