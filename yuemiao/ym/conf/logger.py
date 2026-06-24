import logging
import sys
from logging import handlers
from random import random


class Logger:
    """设置项目日志相关信息"""

    def __init__(self, city):
        """初始化日志属性"""
        self.city = city
        if "win" in sys.platform:
            self.log_path = f".\\logs\\{self.city}.log"
        else:
            self.log_path = f"./logs/{self.city}.log"
        self.log_format = logging.Formatter(
            '%(asctime)s --- %(levelname)s: %(message)s')
        logger_name = str(random())
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        console_log = logging.StreamHandler()  # 输出日志到控制台
        console_log.setFormatter(self.log_format)
        self.logger.addHandler(console_log)
        file_log = handlers.TimedRotatingFileHandler(filename=self.log_path, when="D", backupCount=7,  # 输出日志到文件
                                                     encoding='utf-8')
        file_log.setFormatter(self.log_format)
        self.logger.addHandler(file_log)

    def debug(self, message):
        """打印debug级别日志"""
        self.logger.debug(message)

    def info(self, message):
        """打印info级别日志"""
        self.logger.info(message)

    def error(self, message):
        """打印error级别日志"""
        self.logger.error(message)


if __name__ == "__main__":
    Logger("vip").debug("This is a debug log.")
