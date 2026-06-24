import asyncio
import json
import traceback

from jsonpath import jsonpath

from common.binance_wss_api import BinanceWssApi
from common.logging_config import LoggingConfig
from common.telegram_bot import TelegramBot


class QuantitativeTrading:
    """量化交易"""

    def __init__(self):
        # 设置日志
        logging_tag = "qt"
        self.logging = LoggingConfig(logging_tag).get_logging()
        # telegram_bot设置
        self.telegram_bot = TelegramBot()
        # 监听状态
        self.is_listening = True
        # wss api对象
        self.wss_api = BinanceWssApi(logging_tag)
        # websocket链接对象
        self.ws = None
        # 初始合约账户USDT余额
        self.init_balance = 0
        # 当前合约账户USDT余额
        self.balance = 0
        # 设置是否允许交易
        self.allow_transactions = True

    async def maintain_heartbeat_connection(self, trading_type):
        """
        维持心跳连接
        ws[websocket链接对象]
        trading_type[交易类型 spot:现货 future:合约]
        is_listening[监听状态]
        """
        # 每 3 分钟触发 1 次
        heartbeat_interval_time = 3
        while self.is_listening:
            await asyncio.sleep(heartbeat_interval_time * 60)
            try:
                await self.wss_api.get_session_status_ws(self.ws)
            except Exception:
                error_message = f"维持心跳异常，异常信息{traceback.format_exc()}"
                self.logging.error(error_message)
                self.telegram_bot.send(error_message)
                self.ws = await self.wss_api.login_ws(trading_type)

    async def conduct_future_transactions(self, base_asset, quote_asset, trading_volume, current_price):
        """
        进行合约交易并计算收益
        base_asset 指一个交易对的交易对象，即写在靠前部分的资产名, 比如BTCUSDT, BTC是base asset
        quote_asset 指一个交易对的定价资产，即写在靠后部分的资产名, 比如BTCUSDT, USDT是quote asset
        trading_volume: 保证金数量 USDT
        current_price：当前交易对最新价格
        """
        # 修改合约交易状态为不允许交易
        self.allow_transactions = False
        # 以50倍杠杆计算开仓数量
        quantity = round(trading_volume / (current_price + 50) * 50, 2)
        # 执行合约做多操作并在15秒后平仓然后计算收益
        await self.wss_api.submit_future_orders_ws(
            self.ws, base_asset, quote_asset,
            orders_type="MARKET", side="BUY", position_side="LONG", quantity=quantity)
        # 开仓后查询当前交易对持仓信息
        position_info = await asyncio.create_task(self.wss_api.get_symbol_position_ws(self.ws, base_asset, quote_asset))
        # 设置当前交易对仓位的止损订单
        stop_order_info = await self.wss_api.submit_future_orders_ws(
            self.ws, base_asset, quote_asset,
            orders_type="STOP_MARKET", side="SELL", position_side="LONG",
            quantity=position_info["position_amt"],
            stop_price=position_info["entry_price"] - 1)
        await asyncio.sleep(15)
        # 查询当前交易对持仓信息如果未触发止损则手动平仓
        position_info = await asyncio.create_task(self.wss_api.get_symbol_position_ws(self.ws, base_asset, quote_asset))
        if position_info["position_amt"] != 0:
            await self.wss_api.submit_future_orders_ws(
                self.ws, base_asset, quote_asset,
                orders_type="MARKET", side="SELL", position_side="LONG", quantity=position_info["position_amt"])
            # 撤销止损订单
            if stop_order_info["order_id"]:
                await self.wss_api.cancel_order_ws(self.ws, base_asset, quote_asset, stop_order_info["order_id"])
        # 计算本次收益
        last_balance = (await self.wss_api.get_future_asset_ws(self.ws, quote_asset))["balance"]
        profit = last_balance - self.balance
        self.balance = last_balance
        # 计算历史收益
        history_profit = last_balance - self.init_balance
        message = f"执行{base_asset + quote_asset}合约交易任务完毕，本次收益:{profit}{quote_asset}，历史收益{history_profit}{quote_asset}"
        self.logging.info(message)
        self.telegram_bot.send(message)
        # 修改合约交易状态为允许交易
        self.allow_transactions = True

    async def monitor_price_changes_sub_orders(self, base_asset, quote_asset, trading_volume):
        """
        监听价格变化并下单
        base_asset 指一个交易对的交易对象，即写在靠前部分的资产名, 比如BTCUSDT, BTC是base asset
        quote_asset 指一个交易对的定价资产，即写在靠后部分的资产名, 比如BTCUSDT, USDT是quote asset
        trading_volume: 保证金数量 USDT
        """
        # 订阅交易对逐笔交易数据流
        trade_streams = await self.wss_api.sub_trade_streams_ws(base_asset, quote_asset)
        # 设置价格连续上涨次数 交易对价格列表
        price_increases_num = 4
        prices = []
        while self.is_listening:
            try:
                # 获取交易对最新价格
                trade_info = json.loads(await trade_streams.recv())
                current_price = float(jsonpath(trade_info, "$.p")[0])
                self.logging.info(f"当前交易对{base_asset + quote_asset}价格为{current_price}, 原始数据{trade_info}")
                # 在价格列表中存储最新的四个价格
                prices.append(current_price) if current_price else None
                prices.pop(0) if len(prices) > price_increases_num else None
                # 如果价格连续上涨一定数值，并且交易状态为允许交易，进行合约交易并计算收益
                if len(prices) == price_increases_num:
                    if (all(prices[i] < prices[i + 1] for i in range(price_increases_num - 1))
                            and prices[-1] - prices[0] > 0.2 * (price_increases_num - 1)
                            and self.allow_transactions):
                        self.logging.info(f"检测到可能出现新的launchpool,即将进行合约交易，当前价格列表：{prices}")
                        conduct_future_transactions = asyncio.create_task(
                            self.conduct_future_transactions(base_asset, quote_asset, trading_volume,
                                                             current_price))
                        # 查询最近的归集交易方便分析数据
                        get_historical_trades_ws = asyncio.create_task(
                            self.wss_api.get_historical_trades_ws(self.ws, base_asset, quote_asset)
                        )
                    else:
                        continue
            except Exception:
                error_message = f"程序状态异常，异常信息{traceback.format_exc()}"
                if "websockets.exceptions.ConnectionClosedOK" in error_message:
                    self.logging.info("获取交易对价格订阅已超时自动关闭，稍后将重新订阅")
                else:
                    self.logging.error(error_message)
                    self.telegram_bot.send(error_message)
                # 重新订阅交易对逐笔交易数据流
                trade_streams = await self.wss_api.sub_trade_streams_ws(base_asset, quote_asset)

    async def main(self, base_asset, quote_asset, trading_volume):
        """
        维持心跳连接&监听价格变化并下单
        base_asset 指一个交易对的交易对象，即写在靠前部分的资产名, 比如BTCUSDT, BTC是base asset
        quote_asset 指一个交易对的定价资产，即写在靠后部分的资产名, 比如BTCUSDT, USDT是quote asset
        trading_volume: 保证金数量 USDT
        """
        # 链接ws并登录
        self.ws = await self.wss_api.login_ws("future")
        # 获取初始合约账户USDT余额和最新余额
        self.init_balance = (await self.wss_api.get_future_asset_ws(self.ws, quote_asset))["balance"]
        self.balance = self.init_balance
        # 运行维持ws心跳任务、获取交易对最新价格任务、监听价格变化并下单任务
        await asyncio.gather(
            self.maintain_heartbeat_connection("future"),
            self.monitor_price_changes_sub_orders(base_asset, quote_asset, trading_volume)
        )


if __name__ == '__main__':
    asyncio.run(QuantitativeTrading().main("BNB", "USDT", 10))
