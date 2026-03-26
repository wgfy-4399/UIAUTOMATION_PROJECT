from time import sleep

from selenium.webdriver.common.by import By

from page.base_page import BasePage
from utils.locator_utils import load_locators, get_locator_from_config
from utils.log_utils import global_logger as logger


class ReaderPage(BasePage):
    """阅读器页面对象（统一使用 YAML 配置）"""

    def __init__(self, driver):
        super().__init__(driver)

        # 加载定位符配置
        self._locators = load_locators("reader")

        # 获取当前平台和应用名称
        self._platform = str(self.driver.capabilities.get("platformName", "android")).lower()
        self._app_name = self.driver.capabilities.get("appName", "main")

    def _get_locator(self, locator, locator_type: str = None):
        """
        获取定位符（兼容 BasePage 差异化定位逻辑）
        :param locator: 元素键名字符串，或已解析好的定位符（元组/差异化字典）
        :param locator_type: 定位符类型（可选，None 表示从配置中读取或自动推断）
        :return: 定位符元组
        """
        if isinstance(locator, (tuple, dict)):
            return super()._get_locator(locator)

        element_key = locator
        return get_locator_from_config(
            self._locators,
            element_key,
            self._platform,
            self._app_name,
            locator_type,
        )

    def tap_screen_to_show_menu(self):
        """点击屏幕中间区域，唤起阅读器隐藏的菜单栏"""
        # 1. 获取屏幕尺寸，计算中间坐标（适配所有手机尺寸）
        screen_size = self.driver.get_window_size()
        center_x = screen_size["width"] / 2
        center_y = screen_size["height"] / 2
        logger.info(f"点击屏幕中间位置唤起菜单栏：({center_x}, {center_y})")

        self.driver.tap([(center_x, center_y)], duration=100)
        sleep(1)
        logger.info("菜单栏已唤起")

    def click_on_the_chapter_list(self):
        """唤起菜单栏后，点击章节列表按钮"""
        try:
            self.wait_element_clickable(self._get_locator("chapter_list_button")).click()
            logger.info("成功点击章节列表按钮")
            from page.pages.chapter_list_page import ChapterList

            return ChapterList(self.driver)
        except Exception as e:
            logger.error(f"点击章节列表失败：{e}")
            raise e

    def click_on_the_next_chapter(self):
        """点击下一章按钮"""
        try:
            self.wait_element_clickable(self._get_locator("next_chapter_button")).click()
            logger.info("成功点击下一章按钮")
            return self
        except Exception as e:
            logger.error(f"点击下一章失败：{e}")
            raise e

    def back_to_home(self):
        """
        从阅读器返回首页（根据当前导航结构，通常需要多次返回）
        """
        from page.pages.home_page import HomePage

        # 先返回上一级（如书架/详情页）
        self.back()
        sleep(2)
        # 再次返回预期回到首页
        self.back()
        sleep(2)
        return HomePage(self.driver)

