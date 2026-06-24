import base64
import logging
import time

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
        self.is_test = True
        # 监听状态
        self.is_listening = True
        # 交易对
        self.base_asset = "BTC"
        self.quote_asset = "FDUSD"
        self.symbol = self.base_asset + self.quote_asset
        # 交易状态 可买入：buyable 可卖出：sellable
        self.transaction_status = "buyable"
        # 初始余额&最新余额
        self.initial_balance = 0
        self.latest_balances = 0
        # 买入金额&数量&价格
        self.cummulative_quote_qty = 1000
        self.purchase_quantity = 0
        self.purchase_price = 0
        # 累计收益
        self.accumulated_profit = 0
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

    def get_account(self):
        """获取账户信息"""
        account_url = f"{self.bn_url}/api/v3/account"
        account_params = {
            "omitZeroBalances": "true",
            "timestamp": int(time.time() * 1000),
        }
        # 根据请求参数生成鉴权签名
        payload = '&'.join([f'{param}={value}' for param, value in account_params.items()])
        signature = base64.b64encode(self.private_key.sign(payload.encode('ASCII')))
        account_params['signature'] = signature
        try:
            account_info = requests.get(url=account_url, headers=self.headers, params=account_params)
            match account_info.status_code:
                case 200:
                    account_info = account_info.json()
                    # 获取最新余额
                    latest_balances = jsonpath(account_info, f"$.balances[?(@.asset == '{self.quote_asset}')].free")[0]
                    # 设置初始余额&最新余额
                    if not self.initial_balance:
                        self.initial_balance = float(latest_balances)
                    else:
                        self.latest_balances = float(latest_balances)
                    # logging.info(f"当前账户{self.quote_asset}最新余额为：{latest_balances}")
                case 429:
                    self.is_listening = False
                    logging.info(f"请求频率超过 API限制，暂停服务")
                case 400:
                    logging.info(f"获取账户信息失败,错误信息400：{account_info.text}")
        except Exception as e:
            logging.info(f"获取账户信息失败,错误信息：{e}")
            self.telegram_bot.send_message(self.chat_id, f"获取账户信息失败,错误信息：{e}")

    def get_ticker_price(self):
        """获取最新价格"""
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

    def place_order(self, side):
        """提交订单"""
        place_order_url = f"{self.bn_url}/api/v3/order"
        # 设置订单参数方向为BUY时以为quote_asset(usdt)交易数量，方向为SELl时以base_asset(btc)为交易数量
        place_order_params = {
            "symbol": self.symbol,
            "type": "MARKET",
            "side": side,
            "timestamp": int(time.time() * 1000),
        }
        match side:
            # 买入
            case "BUY":
                place_order_params["quoteOrderQty"] = self.cummulative_quote_qty
            # 卖出
            case "SELL":
                place_order_params["quantity"] = self.purchase_quantity
        # 根据请求参数生成鉴权签名
        payload = '&'.join([f'{param}={value}' for param, value in place_order_params.items()])
        signature = base64.b64encode(self.private_key.sign(payload.encode('ASCII')))
        place_order_params['signature'] = signature
        try:
            order_info = requests.post(url=place_order_url, headers=self.headers, data=place_order_params)
            match order_info.status_code:
                case 200:
                    order_info = order_info.json()
                    order_status = jsonpath(order_info, "$.status")[0]
                    # 检测订单状态
                    match order_status:
                        # 订单完全成交
                        case "FILLED":
                            # 根据交易金额和交易数量计算平均价格
                            cummulative_quote_qty = float(jsonpath(order_info, "$.cummulativeQuoteQty")[0])
                            executed_qty = float(jsonpath(order_info, "$.executedQty")[0])
                            ticker_price = cummulative_quote_qty / executed_qty
                            match side:
                                case "BUY":
                                    # 修改交易状态为可卖出
                                    self.transaction_status = "sellable"
                                    # 设置本次订单买入数量&买入价格
                                    self.purchase_quantity = executed_qty
                                    self.purchase_price = ticker_price
                                    logging.info(
                                        f"交易成功--交易对:{self.symbol}--交易方向:{side}--买入价格:{ticker_price}")
                                case "SELL":
                                    # 修改交易状态为可买入
                                    self.transaction_status = "buyable"
                                    # 获取当前余额 计算累计利润（当前余额-初始余额）
                                    self.get_account()
                                    self.accumulated_profit = self.latest_balances - self.initial_balance
                                    logging.info(
                                        f"交易成功--交易对:{self.symbol}--交易方向:{side}"
                                        f"\n--买入价格{self.purchase_price}"
                                        f"\n--卖出价格:{ticker_price}"
                                        f"\n--累计收益{self.accumulated_profit}")
                case 429:
                    self.is_listening = False
                    logging.info(f"请求频率超过 API限制，暂停服务")
                case 400:
                    logging.info(f"提交订单失败,错误信息400：{order_info.json()}")
        except Exception as e:
            logging.info(f"提交订单失败,错误信息：{e}")
            self.telegram_bot.send_message(self.chat_id, f"提交订单失败,错误信息：{e}")

    def cancel_order(self):
        """撤销订单"""
        cancel_order_url = f"{self.bn_url}/api/v3/openOrders"
        cancel_order_params = {
            "symbol": self.symbol,
            "timestamp": int(time.time() * 1000),
        }
        # 根据请求参数生成鉴权签名
        payload = '&'.join([f'{param}={value}' for param, value in cancel_order_params.items()])
        signature = base64.b64encode(self.private_key.sign(payload.encode('ASCII')))
        cancel_order_params['signature'] = signature
        try:
            cancel_order_info = requests.delete(url=cancel_order_url, headers=self.headers, data=cancel_order_params)
            match cancel_order_info.status_code:
                case 200:
                    cancel_order_info = cancel_order_info.json()
                    cancel_order_status = jsonpath(cancel_order_info, "$.status")[0]
                    match cancel_order_status:
                        case "CANCELED":
                            logging.info(f"撤销订单成功")
                case 429:
                    self.is_listening = False
                    logging.info(f"请求频率超过 API限制，暂停服务")
                case 400:
                    logging.info(f"撤销订单失败,错误信息400：{cancel_order_info.json()}")
        except Exception as e:
            logging.info(f"撤销订单失败,错误信息：{e}")
            self.telegram_bot.send_message(self.chat_id, f"撤销订单失败,错误信息：{e}")

    def open_orders(self):
        """查询订单"""
        open_orders_url = f"{self.bn_url}/api/v3/openOrders"
        open_orders_params = {
            "symbol": self.symbol,
            "timestamp": int(time.time() * 1000),
        }
        # 根据请求参数生成鉴权签名
        payload = '&'.join([f'{param}={value}' for param, value in open_orders_params.items()])
        signature = base64.b64encode(self.private_key.sign(payload.encode('ASCII')))
        open_orders_params['signature'] = signature
        try:
            open_orders_info = requests.get(url=open_orders_url, headers=self.headers, params=open_orders_params)
            match open_orders_info.status_code:
                case 200:
                    open_orders_info = open_orders_info.json()
                    if not open_orders_info:
                        logging.info(f"交易对{self.symbol}没有未完成的订单")
                    else:
                        logging.info(f"交易对{self.symbol}有未完成的订单")
                case 429:
                    pass
                case 400:
                    logging.info(f"查询订单失败,错误信息400：{open_orders_info.json()}")
        except Exception as e:
            logging.info(f"\n查询订单失败,错误信息：{e}")
            self.telegram_bot.send_message(self.chat_id, f"查询订单失败,错误信息：{e}")

    def main(self):
        """检测价格变化并买入卖出指定交易对"""
        # 获取当前余额
        self.get_account()
        # 价格匹配次数(超过100次没有匹配到卖出价格时以市价卖出)
        matching_times = 0
        # 以当前价格买入
        self.place_order("BUY")
        while self.is_listening:
            # 检测交易状态
            match self.transaction_status:
                case "buyable":
                    self.place_order("BUY")
                case "sellable":
                    # 获取最新价格,如果最新价格大于买入价格或超过 100次没有匹配到卖出价格执行卖出操作
                    ticker_price_info = self.get_ticker_price()
                    if ticker_price_info:
                        latest_price = ticker_price_info["latest_price"]
                        if latest_price - self.purchase_price > 100 or matching_times == 100:
                            self.place_order("SELL")
                            matching_times = 0
                        else:
                            matching_times += 1
                            logging.info(
                                f"未匹配到卖出价格--买入价格：{self.purchase_price}"
                                f"--当前交易对{self.symbol}价格：{latest_price}--匹配次数{matching_times}")
                    else:
                        continue


if __name__ == '__main__':
    QuantitativeTrading().main()
