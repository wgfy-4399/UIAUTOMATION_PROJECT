import re
import time

from appium.webdriver.common.appiumby import AppiumBy
from page.base_page import BasePage
from page.pages.reader_page import ReaderPage
class LandingPage(BasePage):
    # ========== 元素定位器 ==========
    READ_MORE_BTN = (AppiumBy.XPATH, "//div[@class='jump-btn theme-color-1' and @onclick='jumpLink()']")
    READ_MORE_FLOAT_BTN = (AppiumBy.XPATH, "//div[@class='jump-btn-float theme-color-1' and @onclick='jumpLink()']")
    PAGE_MARKER = (AppiumBy.XPATH, "//h3[text()='Chapter 1: Departing the Past']")

    def __init__(self, driver):
        super().__init__(driver)
        self.chapter_id = None

    # ==========（一站式完成跳转） ==========
    def jump_to_app(self, url, app_package):
        try:
            self._load_landing_page(url)
            chapter_id = self.extract_chapter_id()
            self._click_read_more()
            self.switch_to_native()  # 第一步：切换到浏览器的NATIVE_APP

            # 激活目标APP
            self.driver.activate_app(app_package)
            time.sleep(5)  # 等待APP启动

            # 第二步：重新切换NATIVE_APP，绑定到目标APP的上下文（核心补充）
            self.driver.switch_to.context("NATIVE_APP")

            print(f"✅ 完整流程完成：落地页→APP跳转，目标APP：{app_package}")
            return chapter_id, ReaderPage(driver=self.driver)
        except Exception as e:
            raise RuntimeError(f"落地页跳转APP失败：{e}")

    # ========== 内部辅助方法（私有化，避免外部直接调用） ==========
    def _load_landing_page(self, url):
        """内部方法：加载落地页（补充WebView上下文切换）"""
        from utils.driver_utils import open_browser_and_visit_url
        # 打开浏览器+访问URL
        open_browser_and_visit_url(url)
        self.switch_to_webview()
        # 等待落地页加载完成
        self.find_element(self.PAGE_MARKER)
        print(f"✅ 落地页加载完成：{url}")

    def _click_read_more(self):
        """内部方法：点击Read More按钮"""
        try:
            self.click_element(self.READ_MORE_BTN)
            print("✅ 点击固定Read More按钮成功")
        except:
            self.click_element(self.READ_MORE_FLOAT_BTN)
            print("✅ 点击悬浮Read More按钮成功")

    def extract_chapter_id(self):
        try:
            page_source = self.driver.execute_script("return document.documentElement.outerHTML")
            chapter_id_match = re.search(r'chapter_id:\s*"(\d+)"', page_source)
            if chapter_id_match:
                self.chapter_id = chapter_id_match.group(1)
                print(f"✅ 提取落地页章节ID成功：{self.chapter_id}")
                return self.chapter_id
            raise Exception("未找到章节ID")
        except Exception as e:
            print(f"提取章节ID失败：{e}")
            return None
