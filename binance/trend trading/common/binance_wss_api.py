import asyncio
import base64
import json
import time

import websockets
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from jsonpath import jsonpath

from common.logging_config import LoggingConfig
from common.telegram_bot import TelegramBot
from config.read_configuration import ReadConfiguration


class BinanceWssApi:
    """
    Binance Websocket API
    """

    def __init__(self, logging_tag):
        # 获取项目配置
        config = ReadConfiguration().config
        # 设置日志
        self.logging = LoggingConfig(logging_tag).get_logging()
        # telegram_bot设置
        self.telegram_bot = TelegramBot()
        # wss接口base URL
        self.ws_url = config["ws_url"]
        # API私钥
        with open(f"{config['base_path']}/config/secret_key.pem", 'rb') as f:
            self.private_key = load_pem_private_key(data=f.read(), password=None)
        # APIKEY
        self.app_key = config["app_key"]

    async def login_ws(self, trading_type):
        """
        通过ws接口登录并返回ws对象
        trading_type[交易类型 spot:现货 future:合约]
        """
        signature_params = {
            "apiKey": self.app_key,
            "timestamp": int(time.time() * 1000),
        }
        # 根据请求参数生成鉴权签名
        payload = '&'.join([f'{param}={value}' for param, value in sorted(signature_params.items())])
        signature = base64.b64encode(self.private_key.sign(payload.encode('ASCII')))
        signature_params['signature'] = signature.decode('ASCII')
        login_params = {
            "id": int(time.time() * 1000),
            "method": "session.logon",
            "params": signature_params
        }
        # 登录获取登录对象
        ws = await websockets.connect(self.ws_url[trading_type])
        await ws.send(json.dumps(login_params))
        login_info = json.loads(await ws.recv())
        login_status = jsonpath(login_info, "$.status")[0]
        match login_status:
            case 200:
                self.logging.info(f"登录成功")
            case _:
                error_message = f"登录失败，错误信息{login_info}"
                self.logging.error(error_message)
                self.telegram_bot.send(error_message)
        return ws

    async def get_session_status_ws(self, ws):
        """
        获取ws会话状态
        ws[websocket链接对象]
        """
        status_params = {
            "id": int(time.time() * 1000),
            "method": "session.status",
        }
        # 查询当前 ws会话登录状态
        await ws.send(json.dumps(status_params))
        status_info = json.loads(await ws.recv())
        login_status = jsonpath(status_info, "$.status")[0]
        match login_status:
            case 200:
                self.logging.info(f"当前会话登录状态正常，详细信息{status_info}")

    async def sub_trade_streams_ws(self, base_asset, quote_asset):
        """
        通过ws接口订阅逐笔交易数据流
        base_asset 指一个交易对的交易对象，即写在靠前部分的资产名, 比如BTCUSDT, BTC是base asset
        quote_asset 指一个交易对的定价资产，即写在靠后部分的资产名, 比如BTCUSDT, USDT是quote asset
        """
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params": [f"{(base_asset + quote_asset).lower()}@trade"],
            "id": int(time.time() * 1000)
        }
        websocket = await websockets.connect(self.ws_url["stream"])
        # 发送订阅请求
        await websocket.send(json.dumps(subscribe_message))
        sub_status = jsonpath(json.loads(await websocket.recv()), "$.result")[0]
        match sub_status:
            case None:
                self.logging.info(f"订阅交易对{base_asset + quote_asset}逐笔交易信息成功")
                return websocket
            case _:
                self.logging.error(f"订阅交易对{base_asset + quote_asset}逐笔交易信息失败")

    async def unsub_trade_streams_ws(self, ws, base_asset, quote_asset):
        """
        通过ws接口取消订阅逐笔交易数据流
        base_asset 指一个交易对的交易对象，即写在靠前部分的资产名, 比如BTCUSDT, BTC是base asset
        quote_asset 指一个交易对的定价资产，即写在靠后部分的资产名, 比如BTCUSDT, USDT是quote asset
        """
        unsubscribe_message = {
            "method": "UNSUBSCRIBE",
            "params": [f"{(base_asset + quote_asset).lower()}@trade"],
            "id": int(time.time() * 1000)
        }
        # 发送取消订阅请求
        await ws.send(json.dumps(unsubscribe_message))
        unsub_status = jsonpath(json.loads(await ws.recv()), "$.result")[0]
        match unsub_status:
            case None:
                self.logging.info(f"取消订阅交易对{base_asset + quote_asset}逐笔交易信息成功")
            case _:
                self.logging.error(f"取消订阅交易对{base_asset + quote_asset}逐笔交易信息失败")
        ws.close()

    async def get_future_asset_ws(self, ws, quote_asset):
        """
        通过ws接口获取合约账户余额
        ws[websocket链接对象]
        quote_asset: 交易对定价资产 USDT
        """
        signature_params = {
            "timestamp": int(time.time() * 1000),
        }
        future_asset_params = {
            "id": int(time.time() * 1000),
            "method": "account.balance",
            "params": signature_params
        }
        self.logging.info(f"通过ws接口获取合约账户余额请求参数:{future_asset_params}")
        await ws.send(json.dumps(future_asset_params))
        future_asset_info = json.loads(await ws.recv())
        future_asset_status = jsonpath(future_asset_info, "$.status")[0]
        match future_asset_status:
            case 200:
                # 获取USDT余额
                balance = float(jsonpath(future_asset_info, f'$.result[?(@.asset == "{quote_asset}")].balance')[0])
                self.logging.info(
                    f"查询成功，合约账户当前{quote_asset}余额为:{balance}"
                    f"\n详细信息:{future_asset_info}")
            case _:
                balance = 0
                error_message = f"查询失败,错误信息{future_asset_info}"
                self.logging.error(error_message)
                self.telegram_bot.send(error_message)
        return {
            "balance": balance
        }

    async def get_historical_trades_ws(self, ws, base_asset, quote_asset):
        """
        通过ws接口获取历史成交记录
        ws[websocket链接对象]
        base_asset 指一个交易对的交易对象，即写在靠前部分的资产名, 比如BTCUSDT, BTC是base asset
        quote_asset 指一个交易对的定价资产，即写在靠后部分的资产名, 比如BTCUSDT, USDT是quote asset
        """
        historical_trades_message = {
            "id": int(time.time() * 1000),
            "method": "trades.aggregate",
            "params": {
                "symbol": f"{(base_asset + quote_asset)}",
                "limit": 1000
            }
        }
        # 获取历史成交记录
        await ws.send(json.dumps(historical_trades_message))
        historical_trades_info = json.loads(await ws.recv())
        historical_trades_status = jsonpath(historical_trades_info, "$.status")[0]
        match historical_trades_status:
            case 200:
                self.logging.info(
                    f"获取交易对{base_asset + quote_asset}历史交易信息成功,详细信息{historical_trades_info}")
            case _:
                self.logging.error(
                    f"获取交易对{base_asset + quote_asset}历史交易信息失败,详细信息{historical_trades_info}")

    async def submit_spot_orders_ws(self, ws, base_asset, quote_asset, side, trading_volume):
        """
        通过ws接口提交现货订单
        ws[websocket链接对象]
        base_asset 指一个交易对的交易对象，即写在靠前部分的资产名, 比如BTCUSDT, BTC是base asset
        quote_asset 指一个交易对的定价资产，即写在靠后部分的资产名, 比如BTCUSDT, USDT是quote asset
        side：交易方向[BUY,SELL]
        trading_volume：交易数量[side为BUY时以为(USDT)为trading_volume为SELl时以(BTC)为trading_volume
        """
        symbol = base_asset + quote_asset
        signature_params = {
            "symbol": symbol,
            "type": "MARKET",
            "side": side,
            "timestamp": int(time.time() * 1000),
        }
        match side:
            case "BUY":
                signature_params["quoteOrderQty"] = trading_volume
            case "SELL":
                signature_params["quantity"] = trading_volume
        orders_params = {
            "id": int(time.time() * 1000),
            "method": "order.place",
            "params": signature_params
        }
        self.logging.info(f"通过ws接口提交现货订单请求参数:{orders_params}")
        await ws.send(json.dumps(orders_params))
        orders_info = json.loads(await ws.recv())
        orders_status = jsonpath(orders_info, "$.status")[0]
        match orders_status:
            case 200:
                # 获取成交金额、成交数量，并计算成交价格
                cummulative_quote_qty = float(jsonpath(orders_info, "$.result.cummulativeQuoteQty")[0])
                executed_qty = float(jsonpath(orders_info, "$.result.executedQty")[0])
                ticker_price = cummulative_quote_qty / executed_qty
                self.logging.info(
                    f"交易成功--交易对:{symbol}--交易方向:{side}--交易价格:{ticker_price}"
                    f"\n详细信息:{orders_info}")
            case _:
                cummulative_quote_qty, executed_qty = 0, 0
                error_message = f"交易失败,错误信息{orders_info}"
                self.logging.error(error_message)
                self.telegram_bot.send(error_message)
        return {
            "quantity": executed_qty,
            "cummulativeQuoteQty": cummulative_quote_qty
        }

    async def submit_future_orders_ws(self, ws, base_asset, quote_asset, **kwargs):
        """
        通过ws接口提交合约订单
        ws[websocket链接对象]
        base_asset 指一个交易对的交易对象，即写在靠前部分的资产名, 比如BTCUSDT, BTC是base asset
        quote_asset 指一个交易对的定价资产，即写在靠后部分的资产名, 比如BTCUSDT, USDT是quote asset
        type: 订单类型[MARKET 市价单，STOP_MARKET 止损市价单]
        side：交易方向[BUY,SELL]
        position_side: 持仓方向[LONG 多头,SHORT 空头]
        quantity：开仓数量单位为 BTC
        stopPrice: 触发价格
        """
        orders_params = {
            "id": int(time.time() * 1000),
            "method": "order.place",
            "params": {
                "symbol": base_asset + quote_asset,
                "type": kwargs["orders_type"],
                "side": kwargs["side"],
                "positionSide": kwargs["position_side"],
                "quantity": kwargs["quantity"],
                "timestamp": int(time.time() * 1000),
            }
        }
        if kwargs["orders_type"] == "STOP_MARKET":
            orders_params["params"]["stopPrice"] = kwargs["stop_price"]
            orders_params["params"]["closePosition"] = "true"
            del orders_params["params"]["quantity"]
        self.logging.info(f"通过ws接口提交合约订单请求参数:{orders_params}")
        await ws.send(json.dumps(orders_params))
        orders_info = json.loads(await ws.recv())
        orders_status = jsonpath(orders_info, "$.status")[0]
        match orders_status:
            case 200:
                order_id = jsonpath(orders_info, "$.result.orderId")[0]
                self.logging.info(
                    f"交易对{base_asset + quote_asset}{'开仓' if kwargs['side'] == 'BUY' else '平仓'}订单提交成功,"
                    f"{'该订单为止损订单' if kwargs['orders_type'] == 'STOP_MARKET' else ''}"
                    f"\n详细信息:{orders_info}")
                return {
                    "order_id": order_id
                }
            case _:
                self.logging.error(
                    f"交易对{base_asset + quote_asset}{'开仓' if kwargs['side'] == 'BUY' else '平仓'}订单提交失败,"
                    f"{'该订单为止损订单' if kwargs['orders_type'] == 'STOP_MARKET' else ''}"
                    f"\n错误信息:{orders_info}")

    async def get_symbol_position_ws(self, ws, base_asset, quote_asset):
        """
        通过ws接口获取当前交易对持仓信息
        ws[websocket链接对象]
        base_asset 指一个交易对的交易对象，即写在靠前部分的资产名, 比如BTCUSDT, BTC是base asset
        quote_asset 指一个交易对的定价资产，即写在靠后部分的资产名, 比如BTCUSDT, USDT是quote asset
        """
        position_params = {
            "id": int(time.time() * 1000),
            "method": "account.position",
            "params": {
                "symbol": base_asset + quote_asset,
                "timestamp": int(time.time() * 1000),
            }
        }
        self.logging.info(f"通过ws接口获取当前交易对持仓信息请求参数:{position_params}")
        await ws.send(json.dumps(position_params))
        position_info = json.loads(await ws.recv())
        position_status = jsonpath(position_info, "$.status")[0]
        match position_status:
            case 200:
                # 获取交易对做多方向的持仓均价 持仓数量
                entry_price = float(jsonpath(position_info, '$.result[?(@.positionSide == "LONG")].entryPrice')[0])
                position_amt = float(jsonpath(position_info, '$.result[?(@.positionSide == "LONG")].positionAmt')[0])
                self.logging.info(
                    f"交易对{base_asset + quote_asset} - "
                    f"持仓方向LONG - 持仓价值{entry_price * position_amt}{quote_asset} - 均价{entry_price}{quote_asset}"
                    f"\n详细信息:{position_info}")
                return {
                    "position_amt": position_amt,
                    "entry_price": entry_price
                }
            case _:
                self.logging.error(
                    f"查询交易对{base_asset + quote_asset}持仓信息失败,详细信息:{position_info}")

    async def cancel_order_ws(self, ws, base_asset, quote_asset, order_id):
        """
        通过ws接口撤销指定订单
        ws[websocket链接对象]
        base_asset 指一个交易对的交易对象，即写在靠前部分的资产名, 比如BTCUSDT, BTC是base asset
        quote_asset 指一个交易对的定价资产，即写在靠后部分的资产名, 比如BTCUSDT, USDT是quote asset
        """
        cancel_params = {
            "id": int(time.time() * 1000),
            "method": "order.cancel",
            "params": {
                "symbol": base_asset + quote_asset,
                "orderId": order_id,
                "timestamp": int(time.time() * 1000),
            }
        }
        self.logging.info(f"通过ws接口撤销指定订单请求参数:{cancel_params}")
        await ws.send(json.dumps(cancel_params))
        cancel_info = json.loads(await ws.recv())
        cancel_status = jsonpath(cancel_info, "$.status")[0]
        match cancel_status:
            case 200:
                self.logging.info(f"撤销订单成功订单id:{order_id},详细信息:{cancel_info}")
            case _:
                self.logging.error(f"撤销订单失败订单id:{order_id},详细信息:{cancel_info}")

    async def test(self):
        ws = await self.login_ws("spot")
        await self.get_session_status_ws(ws)


if __name__ == '__main__':
    asyncio.run(BinanceWssApi("qt").test())
