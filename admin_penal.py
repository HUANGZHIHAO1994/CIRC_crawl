'''
地址（行政处罚）：http://www.cbirc.gov.cn/branch/beijing/view/pages/common/ItemList.html?itemPId=1851&itemId=1855&itemUrl=ItemListRightList.html&itemName=%E8%A1%8C%E6%94%BF%E5%A4%84%E7%BD%9A
这个要用到selenium和chromedriver，下载驱动用这个网址：
https://sites.google.com/a/chromium.org/chromedriver/downloads
注意驱动版本和chrome版本对应
chrome版本查询：
打开chrome浏览器， chrome://version
'''

import requests
from lxml import etree
import random
import time
import pymongo
from pymongo.errors import DuplicateKeyError
import logging  # 引入logging模块
import os.path
import time
import json
import re
import threading
import urllib.request

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from scrapy.http.response.html import HtmlResponse
from selenium.webdriver.chrome.options import Options

import pymysql
from pymysql import cursors


'''
# MongoDb 配置

LOCAL_MONGO_HOST = '127.0.0.1'
LOCAL_MONGO_PORT = 27017
DB_NAME = 'Traffic'

#  mongo数据库的Host, collection设置
client = pymongo.MongoClient(LOCAL_MONGO_HOST, LOCAL_MONGO_PORT)
collection = client[DB_NAME]["Attractions"]
'''

# linux特有
from pyvirtualdisplay import Display
display = Display(visible=0, size=(800, 800))
display.start()



LOCAL_MONGO_HOST = '127.0.0.1'
LOCAL_MONGO_PORT = 27017
DB_NAME = 'regul'

#  mongo数据库的Host, collection设置
client = pymongo.MongoClient(LOCAL_MONGO_HOST, LOCAL_MONGO_PORT)
collection = client[DB_NAME]["Admin_Penal"]    # 要修改


#  随机请求头设置
USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/44.0.2403.155 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; Avant Browser; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)',
        'Mozilla/5.0 (X11; Linux i686; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Mozilla/5.0 (X11; Linux i586; rv:63.0) Gecko/20100101 Firefox/63.0',
        'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.10; rv:62.0) Gecko/20100101 Firefox/62.0'
    ]


def admin_penal(url):
        # http_head = "http://www.cbirc.gov.cn/branch/beijing/view/pages/"
        headers = {}
        headers['User-Agent'] = random.choice(USER_AGENTS)
        chrome_options = Options()
        headers = random.choice(USER_AGENTS)
        chrome_options.add_argument('--user-agent={}'.format(headers))  # 设置请求头的User-Agent
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
        chrome_options.add_argument('--headless')  # 浏览器不提供可视化页面
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
#         chrome_options.binary_location = "/opt/google/chrome/chrome"
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.maximize_window()
        driver.get(url)
        click = driver.find_element_by_xpath('//a[@ng-click="pager.last()"]')
        driver.execute_script("arguments[0].click();", click)
        notice_page = int(driver.find_element_by_xpath('//a[@ng-click="pager.goTo(x)"]/span[@class="active"]').text)
        logger.info('notice_page:' + str(notice_page))

        try:
                while notice_page >= 1:
                        parse(driver.page_source)
                        click = driver.find_element_by_xpath('//a[@ng-click="pager.prev()"]')
                        driver.execute_script("arguments[0].click();", click)
                        driver.delete_all_cookies()
                        url = driver.current_url
                        time.sleep(1)
                        # print(page)
                        notice_page -= 1
                        logger.info("翻到第{}页".format(notice_page))
                        # print(driver.page_source)
        except WebDriverException:
                logger.error("*" * 30)
                logger.error("出现异常" + "*" * 30)
                logger.error("*" * 30)
                notice_except(url, notice_page)


def notice_except(url, notice_page):
        try:
                chrome_options = Options()
                headers = random.choice(USER_AGENTS)
                chrome_options.add_argument('--user-agent={}'.format(headers))  # 设置请求头的User-Agent
                chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
                chrome_options.add_argument('--headless')  # 浏览器不提供可视化页面
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("start-maximized")
                driver = webdriver.Chrome(chrome_options=chrome_options)
                driver.get(url)
                while notice_page >= 1:
                        parse(driver.page_source)
                        click = driver.find_element_by_xpath('//a[@ng-click="pager.prev()"]')
                        driver.execute_script("arguments[0].click();", click)
                        driver.delete_all_cookies()
                        url = driver.current_url
                        time.sleep(1)
                        # print(page)
                        notice_page -= 1
                        logger.info("翻到第{}页".format(notice_page))
        except WebDriverException:
                logger.error("*" * 30)
                logger.error("出现异常" + "*" * 30)
                logger.error("*" * 30)
                notice_except(url, notice_page)


def parse(page_source):
        tree_node = etree.HTML(page_source)
        for i in tree_node.xpath('//div[@class="list caidan-right-list"][1]//div[@class="panel active"]/div/span[@class="title"]/a'):
                url_notice_detail = http_head + i.xpath(".//@href")[0].replace("../", '')
                title = i.xpath(".//text()")[0]

                notice_detail(url_notice_detail, title)


def notice_detail(url, title):
        headers = {}
        headers['User-Agent'] = random.choice(USER_AGENTS)
        chrome_options = Options()
        headers = random.choice(USER_AGENTS)
        chrome_options.add_argument('--user-agent={}'.format(headers))  # 设置请求头的User-Agent
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
        chrome_options.add_argument('--headless')  # 浏览器不提供可视化页面
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.maximize_window()
        driver.get(url)

        try:
                try:
                        content = driver.find_element_by_xpath('//div[@class="Section0"]').text
                except:
                        content = driver.find_element_by_xpath('//div[@id="wenzhang-content"]').text
                        # print(url)
        except:
                content = ''
                logger.warning("规则又变了")
                logger.warning(url)
        # print(content)
        try:
                global id
                logger.info(str(id) + city)
                id += 1
                logger.info(title)
                logger.info(url)
                # print(content[:10])
                collection.insert_one(
                        {"_id": str(id) + city, "title": title, "url": url, "city": city,
                         "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "content": content
                         })
                time.sleep(0.2)
                driver.close()

        except DuplicateKeyError as e:
                pass



if __name__ == '__main__':
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)  # Log等级总开关
        # 第二步，创建一个handler，用于写入日志文件
        rq = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
        # log_path = os.path.dirname(os.getcwd()) + '/Logs/'
        log_path = os.getcwd() + '/Logs/'
        if not os.path.exists(log_path):
                os.makedirs(log_path)
        log_name = log_path + rq + 'penal.log'
        logfile = log_name
        st = logging.StreamHandler()
        fh = logging.FileHandler(logfile, mode='w')
        fh.setLevel(logging.DEBUG)  # 输出到file的log等级的开关
        st.setLevel(logging.DEBUG)  # 输出到file的log等级的开关
        # 第三步，定义handler的输出格式
        formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
        fh.setFormatter(formatter)
        st.setFormatter(formatter)
        # 第四步，将logger添加到handler里面
        logger.addHandler(fh)
        logger.addHandler(st)

        f = open('./province_penal.txt')
#         print(f.read().split('\n'))
        for url in f.read().split('\n')[:-1]:
                # city = "beijing"    # 要修改
                city = url.split('/')[4]
                logger.info(city)
                notice_page = 100  # 要修改

#                 admin_licence_url = 'http://www.cbirc.gov.cn/branch/{}/view/pages/common/ItemList.html?itemPId=1851&itemId=1854&itemUrl=ItemListRightList.html&itemName=%E8%A1%8C%E6%94%BF%E8%AE%B8%E5%8F%AF#1'.format(city)
                id = 1
                # page = 1
                http_head = "http://www.cbirc.gov.cn/branch/{}/view/pages/".format(city)
                admin_penal(url)


