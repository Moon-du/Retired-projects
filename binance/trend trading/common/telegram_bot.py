import telebot
from config.read_configuration import ReadConfiguration


class TelegramBot:
    """
    设置telegram_bot
    """

    def __init__(self):
        # 获取项目配置
        config = ReadConfiguration().config
        self.chat_id = config['telegram_bot']['chat_id']
        self.bot_token = config['telegram_bot']['bot_token']
        # telegram_bot设置
        self.telegram_bot = telebot.TeleBot(self.bot_token)

    def send(self, message):
        """
        通过telegram_bot发送消息
        """
        self.telegram_bot.send_message(chat_id=self.chat_id, text=message)


if __name__ == "__main__":
    TelegramBot().send("This is a debug log.")
