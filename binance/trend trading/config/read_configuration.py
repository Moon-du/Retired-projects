class ReadConfiguration:
    """
    读取配置信息
    """

    def __init__(self):
        # 设置项目配置信息
        self.config = {
            "base_path": "/Users/fengdazhuang/PycharmProjects/binance",
            "telegram_bot": {
                "chat_id": "6380950127",
                "bot_token": "7198746866:AAE1qw5pk13t40EJQm1zZUR-t6qTB4We6qw"
            },
            "rest_url": {
                "spot": "https://api.binance.com",
                "future": "https://fapi.binance.com"
            },
            "ws_url": {
                "spot": "wss://ws-api.binance.com:443/ws-api/v3",
                "future": "wss://ws-fapi.binance.com/ws-fapi/v1",
                "stream": "wss://stream.binance.com:9443/ws"
            },
            "app_key": "DFTQCdYFwNitxuwXYz8Ped5asnQdZnpdWjMp80vTL5SkuGz7UUNXiw4IbgC71j2G",
        }


if __name__ == "__main__":
    ReadConfiguration()
