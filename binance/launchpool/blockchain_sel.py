import json
import logging
import time
from datetime import datetime


from jsonpath import jsonpath
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait


class Blockchain:
    """获取挖矿公告并开启BNB合约"""

    def __init__(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # 测试环境使用正常模式
        chrome_options = Options()
        # 生产环境使用无头模式
        # chrome_options.add_argument("--headless")
        # 禁用图片加载
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_argument("--window-size=1920x1080")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.url = "https://www.binance.com/en/support/announcement/%E6%95%B0%E5%AD%97%E8%B4%A7%E5%B8%81%E5%8F%8A%E4%BA%A4%E6%98%93%E5%AF%B9%E4%B8%8A%E6%96%B0?c=48&navId=48"

    def get_latest_announcement(self):
        """获取最新公告"""
        announcement_title, announcement_release_date, status = None, None, None
        try:
            # 检查公告是否渲染完成
            self.wait.until(ec.presence_of_element_located((By.ID, '__APP')))
            # 公告渲染完成
            status = "success"
            # 获取最新一期公告标题&发布时间
            announcement_title = self.driver.find_element(By.XPATH,
                                '//*[@id="app-wrap"]//div[@class="css-1yxx6id"]').get_attribute('textContent')
            announcement_release_date = datetime.now().timestamp()
        except TimeoutException:
            # 公告渲染失败
            status = "fail"
            logging.error(f"获取公告元数据失败,原始页面信息：\n{self.driver.page_source}")

        return {"status": status,
                "announcement_title": announcement_title,
                "announcement_release_date": announcement_release_date}

    def start_bnb_contract(self):
        """开启BNB合约"""
        logging.info("开启BNB合约")

    def main(self):
        """监听公告当发布新一期挖矿公告时开启合约"""
        is_listen = True
        error_num = 0
        # 打开浏览器访问公告页面并接受cookie
        self.driver.get(self.url)
        time.sleep(5)
        accept_btn = self.wait.until(ec.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler')))
        accept_btn.click()
        while is_listen:
            # 获取最新公告信息
            announcement_info = self.get_latest_announcement()
            if announcement_info["status"] == "success":
                announcement_title = announcement_info["announcement_title"]
                announcement_release_date = announcement_info["announcement_release_date"]
                logging.info(
                    f"最新公告标题：{announcement_title},公告发布时间：{datetime.fromtimestamp(announcement_release_date)}")
                # 监听是否有新挖矿公告
                if ("Binance Launchpool!" in announcement_title and
                        int(datetime.now().timestamp()) - announcement_release_date <= 10):
                    # 开启BNB合约
                    self.start_bnb_contract()
                    # 结束监听并关闭浏览器
                    is_listen = False
                    self.driver.quit()
                else:
                    # 刷新页面
                    time.sleep(5)
                    self.driver.refresh()
            else:
                error_num += 1
                # 连续3次获取失败，结束监听并关闭浏览器
                if error_num >= 3:
                    is_listen = False
                    self.driver.quit()
                else:
                    # 刷新页面并等待五秒
                    self.driver.refresh()
                    time.sleep(5)


if __name__ == '__main__':
    Blockchain().main()
