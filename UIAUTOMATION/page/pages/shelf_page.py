from time import sleep

from selenium.webdriver.common.by import By

from page.base_page import BasePage
from utils.locator_utils import load_locators, get_locator_from_config
from utils.log_utils import global_logger as logger


class ShelfPage(BasePage):
    """
    书架页面对象（统一，不再区分主包/马甲包）
    - 查看书架书籍
    - 点击书籍进入阅读器
    """

    def __init__(self, driver):
        super().__init__(driver)

        # 加载定位符配置
        self._locators = load_locators("shelf")

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

    def click_book_by_index(self, index: int = 0):
        """
        点击书架中的某一本书
        :param index: 书籍下标（从0开始）
        """
        try:
            book_list_container = self.find_element(self._get_locator("book_list"))
            books = book_list_container.find_elements(By.XPATH, ".//*")
            if not books:
                raise RuntimeError("未找到任何书籍")

            if index < 0 or index >= len(books):
                raise IndexError(f"书籍下标越界：index={index}, 总数={len(books)}")

            books[index].click()
            logger.info(f"已点击书架中第 {index} 本书（总共 {len(books)} 本）")
            sleep(1)
            # 点击书籍后进入阅读器
            from page.pages.reader_page import ReaderPage

            return ReaderPage(self.driver)
        except Exception as e:
            logger.error(f"点击书籍失败：{e}")
            raise e

    def get_book_count(self) -> int:
        """
        获取书架中书籍数量
        :return: 书籍数量
        """
        try:
            book_list_container = self.find_element(self._get_locator("book_list"))
            books = book_list_container.find_elements(By.XPATH, ".//*")
            count = len(books)
            logger.info(f"书架中共有 {count} 本书")
            return count
        except Exception as e:
            logger.error(f"获取书籍数量失败：{e}")
            return 0

    def get_book_titles(self) -> list:
        """
        获取书架中所有书籍标题列表
        :return: 书籍标题列表
        """
        titles = []
        try:
            book_list_container = self.find_element(self._get_locator("book_list"))
            # 查找所有书籍元素中的标题文本
            # iOS 和 Android 都使用 StaticText 或 TextView 来显示标题
            if self._platform == "android":
                title_elements = book_list_container.find_elements(
                    By.XPATH, './/*[@resource-id[contains(., "tv_title")]]'
                )
            else:
                # iOS: 使用 XCUIElementTypeStaticText 查找标题
                title_elements = book_list_container.find_elements(
                    By.XPATH, './/XCUIElementTypeStaticText'
                )

            for el in title_elements:
                title = el.text.strip() if el.text else ""
                if title:
                    titles.append(title)

            logger.info(f"获取到 {len(titles)} 个书籍标题：{titles}")
        except Exception as e:
            logger.error(f"获取书籍标题列表失败：{e}")
        return titles

    def is_shelf_empty(self) -> bool:
        """
        检查书架是否为空
        :return: True 表示书架为空，False 表示有书籍
        """
        count = self.get_book_count()
        return count == 0

    def back_to_home(self):
        """
        从书架返回首页
        """
        from page.pages.home_page import HomePage

        self.back()
        sleep(2)
        return HomePage(self.driver)

