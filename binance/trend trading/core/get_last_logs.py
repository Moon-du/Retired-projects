import subprocess

from config.read_configuration import ReadConfiguration
from common.telegram_bot import TelegramBot


class GetLastLogs:
    """
    获取最新日志
    """

    def __init__(self):
        # 获取项目配置
        config = ReadConfiguration().config
        self.log_path = f"{config['base_path']}/logs"
        # telegram_bot设置
        self.telegram_bot = TelegramBot()

    def get_last_logs(self):
        """
        获取日志文件的最新3行数据
        """
        # 使用tail命令获取最后3行日志
        last_line = subprocess.check_output(['tail', '-n', '3', f'{self.log_path}/qt.log'], encoding='utf-8')
        self.telegram_bot.send(last_line)


if __name__ == "__main__":
    GetLastLogs().get_last_logs()
