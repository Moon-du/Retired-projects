import logging
import os
from logging.handlers import TimedRotatingFileHandler

from config.read_configuration import ReadConfiguration


class LoggingConfig:
    """
    设置日志相关信息
    """

    def __init__(self, logging_tag):
        # 获取项目配置
        config = ReadConfiguration().config
        log_path = f"{config['base_path']}/logs"
        # 如果路径不存在则新建路径
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        log_file = os.path.join(log_path, f"{logging_tag}.log")
        # 根据 logging_tag 设置日志处理程序
        file_handler = (
            logging.FileHandler(log_file)  # 输出到文件，不分割
            if logging_tag != "qt" else
            TimedRotatingFileHandler(log_file, when="H", interval=1, backupCount=12)  # 保留最近12个小时的日志
        )
        handlers = [
            logging.StreamHandler(),  # 同时输出到控制台
            file_handler
        ]
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s",
            handlers=handlers
        )
        self.logging = logging.getLogger(logging_tag)

    def get_logging(self):
        """
        返回日志对象
        """
        return self.logging

    # def debug(self, message):
    #     """打印debug级别日志"""
    #     self.logging.debug(message)
    #
    # def info(self, message):
    #     """打印info级别日志"""
    #     self.logging.info(message)
    #
    # def error(self, message):
    #     """打印error级别日志"""
    #     self.logging.error(message)


if __name__ == "__main__":
    LoggingConfig("ck").get_logging().info("This is a info log.")
