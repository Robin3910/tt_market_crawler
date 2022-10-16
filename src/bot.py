from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager as CM
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from random import randint
from time import time, sleep, localtime
import json
import logging
import openpyxl
import re
import requests
from urllib.parse import unquote

DEFAULT_IMPLICIT_WAIT = 1



with open('infos/usernames.txt', 'r') as f:
    usernames = [line.strip() for line in f]


class Bot(object):

    def __init__(self, headless=False, profileDir=None):
        self.ttAuthorPageCookie = ""
        self.ttCreatorMarketCookie = ""
        self.fetchNums = 100
        self.selectors = {
            "btn_next": "//button[@class='btn-next']"
        }
        self.curUserMap = {}
        self.ttUserHeaders = {
            'authority': 'www.tiktok.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
            'Cookie': self.ttAuthorPageCookie
        }
        self.data = [
            ["core_user_id", "username", "fans", "avg_views", "brief", "engagement_rate", "price", "tt_link", "desc",
             "contact_link"]
        ]

        # Selenium config
        options = webdriver.ChromeOptions()

        # browser log
        capabilities = DesiredCapabilities.CHROME
        capabilities["goog:loggingPrefs"] = {"performance": "ALL"}

        # capabilities['loggingPrefs'] = {'browser': 'ALL'}

        options.add_argument(
            f'cookie="{self.ttCreatorMarketCookie}"')

        if profileDir:
            options.add_argument("user-data-dir=profiles/" + profileDir)

        if headless:
            options.add_argument("--headless")

        options.add_argument("--log-level=3")

        self.driver = webdriver.Chrome(
            executable_path=CM().install(), options=options, desired_capabilities=capabilities)
        self.driver.set_window_position(0, 0)
        self.driver.maximize_window()

        try:
            self.driver.get('https://creatormarketplace.tiktok.com/home')

            # 代码修改处
            cookies = self.extract_cookies(
                cookie=f'{self.ttCreatorMarketCookie}')
            # 代码结束

            year = localtime().tm_year + 1

            for key in cookies:
                cookie_dict = {
                    'domain': 'creatormarketplace.tiktok.com',
                    'name': key,
                    'value': cookies[key],
                    "expires": 'Sat, 26 Aug ' + str(year) + ' 10:34:25 GMT',
                    'path': '/',
                    'httpOnly': False,
                    'HostOnly': False,
                    'Secure': True
                }
                self.driver.add_cookie(cookie_dict)

            self.driver.refresh()

            # wait for start signal, trigger by user
            name = input()
            print(name)

            if name == "beiens":
                self.__fetch_info()
                self.__run_crawler()

            self.__random_sleep__(730, 740)

            exit(0)

        except Exception as e:
            print(str(e))

    def typeMessage(self, user, message):
        # Go to page and type message
        if self.__wait_for_element__(self.selectors['next_button'], "xpath"):
            self.__get_element__(
                self.selectors['next_button'], "xpath").click()
            self.__random_sleep__()

        for msg in message:
            if self.__wait_for_element__(self.selectors['textarea'], "xpath"):
                self.__type_slow__(self.selectors['textarea'], "xpath", msg)
                self.__random_sleep__()

            if self.__wait_for_element__(self.selectors['send'], "xpath"):
                self.__get_element__(self.selectors['send'], "xpath").click()
                self.__random_sleep__(3, 5)
                print('Message sent successfully')

    def __get_element__(self, element_tag, locator):
        """Wait for element and then return when it is available"""
        try:
            locator = locator.upper()
            dr = self.driver
            if locator == 'ID' and self.is_element_present(By.ID, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_id(element_tag))
            elif locator == 'NAME' and self.is_element_present(By.NAME, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_name(element_tag))
            elif locator == 'XPATH' and self.is_element_present(By.XPATH, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_xpath(element_tag))
            elif locator == 'CSS' and self.is_element_present(By.CSS_SELECTOR, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_css_selector(element_tag))
            else:
                logging.info(f"Error: Incorrect locator = {locator}")
        except Exception as e:
            logging.error(e)
        logging.info(f"Element not found with {locator} : {element_tag}")
        return None

    def is_element_present(self, how, what):
        """Check if an element is present"""
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def __wait_for_element__(self, element_tag, locator, timeout=30):
        """Wait till element present. Max 30 seconds"""
        result = False
        self.driver.implicitly_wait(0)
        locator = locator.upper()
        for i in range(timeout):
            initTime = time()
            try:
                if locator == 'ID' and self.is_element_present(By.ID, element_tag):
                    result = True
                    break
                elif locator == 'NAME' and self.is_element_present(By.NAME, element_tag):
                    result = True
                    break
                elif locator == 'XPATH' and self.is_element_present(By.XPATH, element_tag):
                    result = True
                    break
                elif locator == 'CSS' and self.is_element_present(By.CSS_SELECTORS, element_tag):
                    result = True
                    break
                else:
                    logging.info(f"Error: Incorrect locator = {locator}")
            except Exception as e:
                logging.error(e)
                print(f"Exception when __wait_for_element__ : {e}")

            sleep(1 - (time() - initTime))
        else:
            print(
                f"Timed out. Element not found with {locator} : {element_tag}")
        self.driver.implicitly_wait(DEFAULT_IMPLICIT_WAIT)
        return result

    def __type_slow__(self, element_tag, locator, input_text=''):
        """Type the given input text"""
        try:
            self.__wait_for_element__(element_tag, locator, 5)
            self.__wait_for_element__(element_tag, locator, 5)
            element = self.__get_element__(element_tag, locator)
            actions = ActionChains(self.driver)
            actions.click(element).perform()
            # element.send_keys(input_text)
            for s in input_text:
                element.send_keys(s)
                # sleep(uniform(0.005, 0.02))

        except Exception as e:
            logging.error(e)
            print(f'Exception when __typeSlow__ : {e}')

    def __random_sleep__(self, minimum=2, maximum=7):
        t = randint(minimum, maximum)
        logging.info(f'Wait {t} seconds')
        sleep(t)

    def __scrolldown__(self):
        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

    def teardown(self):
        self.driver.close()
        self.driver.quit()

    def extract_cookies(self, cookie=""):
        """从浏览器或者request headers中拿到cookie字符串，提取为字典格式的cookies"""
        cookies = {i.split("=")[0]: i.split("=")[1] for i in cookie.split("; ")}
        return cookies

    def __find_element_and_click(self, name, locator):
        if self.__wait_for_element__(name, locator):
            self.__get_element__(
                name, locator).click()
            self.__random_sleep__()

    def __save_excel(self):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        for row in self.data:
            sheet.append(row)
        workbook.save('userinfo_' + str(time()) + '.xlsx')
        print("get userinfo task finish, save into excel")

    def __fetch_info(self):
        for entry in self.driver.get_log('performance'):
            messageObj = json.loads(entry['message'])
            messageParam = messageObj['message']['params']
            request = messageParam.get('request')
            if request is None:
                continue

            url = request.get('url')
            targetReq = re.search(r'https://creatormarketplace.tiktok.com/h/api/gateway/handler_get/\?page=(.*)', url)
            if targetReq is not None:
                headers = request.get("headers")
                headers["cookie"] = self.ttCreatorMarketCookie
                response = requests.request("GET", url, headers=headers)
                resContent = json.loads(response.content)
                if resContent["code"] == 0 and resContent["msg"] == "Success":
                    authors = resContent["data"].get("authors")
                    if authors is not None:
                        totalCount = resContent["data"].get("pagination").get("total_count")
                        totalCount = int(totalCount)
                        if self.fetchNums > totalCount:
                            self.fetchNums = totalCount
                        for author in authors:
                            if self.curUserMap.get(author.get("handle_name")):
                                continue
                            ttUserLink = f'https://www.tiktok.com/@{author.get("handle_name")}?lang=en'
                            # get tt author page
                            authorDetailRes = requests.request("GET",
                                                               ttUserLink,
                                                               headers=self.ttUserHeaders)
                            # search description
                            descSearch = re.search(r'<meta data-rh="true" name="description" content="(.*)"/>',
                                                   authorDetailRes.text, re.M | re.I)
                            desc = ""
                            if descSearch is not None:
                                desc = descSearch.group().split("/>")[0].split('content="')[1]
                            print(desc)
                            # search bio_url
                            contactLink = ""
                            contactLinkSearch = re.search(r'bioLink":\{"link":"(.*)}', authorDetailRes.text)
                            if contactLinkSearch is not None:
                                contactLink = contactLinkSearch.group().split('"')[4]
                                contactLink = unquote(contactLink)
                            print(contactLink)

                            # fetch from creator market info
                            priceObj = author.get("author_price")
                            price = ""
                            if priceObj is not None:
                                price = priceObj.get("rate") + priceObj.get("currency")
                            self.data.append(
                                [author.get("core_user_id"), author.get("handle_name"), author.get("reach"),
                                 author.get("avg_views"),
                                 author.get("brief"), author.get("engagement_rate"), price,
                                 ttUserLink, desc, contactLink])
                            print(f'-------------------fetch next one, cur num: {len(self.data)}----------------------')
                            self.__random_sleep__(5, 10)

    def __run_crawler(self):
        print("fetch info start...")

        while len(self.data) < self.fetchNums:
            print("cur process: " + str(len(self.data)) + "|target nums: " + str(self.fetchNums))
            self.__scrolldown__()
            self.__random_sleep__()
            self.__find_element_and_click(self.selectors["btn_next"], "xpath")
            self.__random_sleep__(10, 10)
            self.__fetch_info()

        self.__save_excel()


