"""
ChapterList 页面对象 - 章节列表弹窗/页面
从阅读器点击目录按钮后显示的章节列表
"""
from time import sleep
from typing import List, Optional

from selenium.webdriver.common.by import By

from page.base_page import BasePage
from utils.locator_utils import load_locators, get_locator_from_config
from utils.log_utils import global_logger as logger
from utils.screenshot_utils import take_screenshot


class ChapterList(BasePage):
    """章节列表页面对象"""

    def __init__(self, driver):
        super().__init__(driver)
        # 加载定位符配置
        self._locators = load_locators("chapter_list")
        # 获取当前平台和应用名称
        self._platform = str(self.driver.capabilities.get("platformName", "android")).lower()
        self._app_name = self.driver.capabilities.get("appName", "main")

    def _get_locator(self, element_key: str):
        """
        获取定位符（兼容三种格式：字符串key/元组/差异化字典）
        """
        if isinstance(element_key, (tuple, dict)):
            return super()._get_locator(element_key)
        return get_locator_from_config(
            self._locators, element_key, self._platform, self._app_name
        )

    # ==================== 页面验证 ====================

    def is_page_loaded(self) -> bool:
        """
        验证章节列表页面是否已加载
        """
        try:
            # 检查章节列表容器是否存在
            container = self.find_element(self._get_locator("chapter_list_container"), timeout=5)
            return container.is_displayed()
        except Exception as e:
            logger.error(f"验证章节列表页面加载失败：{e}")
            return False

    # ==================== 导航/操作 ====================

    def close_chapter_list(self):
        """
        关闭章节列表弹窗，返回阅读器页面

        :return: ReaderPage 对象
        """
        try:
            # 点击关闭按钮（列表外部的透明按钮）
            close_btn = self.wait_element_clickable(self._get_locator("close_button"), timeout=5)
            close_btn.click()
            logger.info("已关闭章节列表弹窗")
            sleep(1)

            from page.pages.reader_page import ReaderPage
            return ReaderPage(self.driver)
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "close_chapter_list_fail")
            logger.error(f"关闭章节列表失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def toggle_sort_order(self):
        """
        切换章节排序（正序/倒序）

        :return: self（支持链式调用）
        """
        try:
            sort_btn = self.wait_element_clickable(self._get_locator("sort_button"), timeout=5)
            sort_btn.click()
            logger.info("已切换章节排序")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "toggle_sort_fail")
            logger.error(f"切换排序失败，截图：{screenshot_path}，异常：{e}")
            raise e

    # ==================== 数据获取 ====================

    def get_chapter_count(self) -> int:
        """
        获取章节总数

        :return: 章节总数
        """
        try:
            # 尝试从章节总数文本中提取数字
            count_text = self.find_element(self._get_locator("chapters_count_text"), timeout=5)
            text = count_text.get_attribute("name") or count_text.text
            # 解析 "155 Chapters" 格式
            import re
            match = re.search(r'(\d+)', text)
            if match:
                count = int(match.group(1))
                logger.info(f"章节总数：{count}")
                return count
            return 0
        except Exception as e:
            # 如果无法从文本获取，尝试统计列表项数量
            logger.warning(f"从文本获取章节总数失败：{e}，尝试统计列表项")
            try:
                chapters = self.find_elements(self._get_locator("chapter_item"), timeout=5)
                return len(chapters)
            except Exception as e2:
                logger.error(f"统计章节列表失败：{e2}")
                return 0

    def get_visible_chapter_titles(self) -> List[str]:
        """
        获取当前可见的章节标题列表

        :return: 章节标题列表
        """
        try:
            chapters = self.find_elements(self._get_locator("chapter_item"), timeout=5)
            titles = []
            for chapter in chapters:
                title = chapter.get_attribute("name") or chapter.text
                if title:
                    titles.append(title)
            logger.info(f"获取到 {len(titles)} 个可见章节标题")
            return titles
        except Exception as e:
            logger.error(f"获取章节标题失败：{e}")
            return []

    def get_current_chapter_title(self) -> Optional[str]:
        """
        获取当前阅读章节的标题

        :return: 当前章节标题，或 None
        """
        try:
            current = self.find_element(self._get_locator("current_chapter_text"), timeout=5)
            title = current.get_attribute("name") or current.text
            logger.info(f"当前章节：{title}")
            return title
        except Exception as e:
            logger.warning(f"获取当前章节标题失败：{e}")
            return None

    # ==================== 章节选择 ====================

    def click_chapter_by_index(self, index: int):
        """
        点击指定索引的章节（从0开始）

        :param index: 章节索引（从0开始）
        :return: ReaderPage 对象
        """
        try:
            # 构建动态定位符
            chapter_num = index + 1
            xpath = f"//XCUIElementTypeStaticText[contains(@name, 'CHAPTER {chapter_num}') or contains(@name, 'Chapter {chapter_num}')]"

            chapter = self.wait_element_clickable((By.XPATH, xpath), timeout=10)
            chapter.click()
            logger.info(f"已点击第 {chapter_num} 章节")
            sleep(2)

            from page.pages.reader_page import ReaderPage
            return ReaderPage(self.driver)
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, f"click_chapter_{index}_fail")
            logger.error(f"点击章节失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_chapter_by_title(self, title: str):
        """
        点击指定标题的章节

        :param title: 章节标题（如 "CHAPTER 1"）
        :return: ReaderPage 对象
        """
        try:
            xpath = f"//XCUIElementTypeStaticText[@name='{title}']"
            chapter = self.wait_element_clickable((By.XPATH, xpath), timeout=10)
            chapter.click()
            logger.info(f"已点击章节：{title}")
            sleep(2)

            from page.pages.reader_page import ReaderPage
            return ReaderPage(self.driver)
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, f"click_chapter_{title}_fail")
            logger.error(f"点击章节失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_first_visible_chapter(self):
        """
        点击第一个可见的章节

        :return: ReaderPage 对象
        """
        try:
            chapter = self.wait_element_clickable(self._get_locator("chapter_item"), timeout=5)
            chapter.click()
            logger.info("已点击第一个可见章节")
            sleep(2)

            from page.pages.reader_page import ReaderPage
            return ReaderPage(self.driver)
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_first_chapter_fail")
            logger.error(f"点击第一个章节失败，截图：{screenshot_path}，异常：{e}")
            raise e

    # ==================== 滚动操作 ====================

    def scroll_to_chapter(self, index: int):
        """
        滚动到指定索引的章节

        :param index: 章节索引（从0开始）
        :return: self（支持链式调用）
        """
        try:
            chapter_num = index + 1
            xpath = f"//XCUIElementTypeStaticText[contains(@name, 'CHAPTER {chapter_num}') or contains(@name, 'Chapter {chapter_num}')]"

            # 使用 scroll 滚动到目标元素
            self.scroll_to_element((By.XPATH, xpath))
            logger.info(f"已滚动到第 {chapter_num} 章节")
            return self
        except Exception as e:
            logger.warning(f"滚动到章节失败：{e}")
            return self

    def scroll_to_top(self):
        """
        滚动到章节列表顶部

        :return: self（支持链式调用）
        """
        try:
            # 使用 swipe 向上滑动来达到顶部效果（反向滑动）
            self.swipe_down()
            logger.info("已滚动到章节列表顶部")
            return self
        except Exception as e:
            logger.warning(f"滚动到顶部失败：{e}")
            return self

    def scroll_to_bottom(self):
        """
        滚动到章节列表底部

        :return: self（支持链式调用）
        """
        try:
            self.swipe_up()
            logger.info("已滚动到章节列表底部")
            return self
        except Exception as e:
            logger.warning(f"滚动到底部失败：{e}")
            return self

    # ==================== 特殊操作 ====================

    def click_voucher_button(self):
        """
        点击 voucher 按钮（如果有）

        :return: self（支持链式调用）
        """
        try:
            voucher_btn = self.wait_element_clickable(self._get_locator("voucher_button"), timeout=5)
            voucher_btn.click()
            logger.info("已点击 voucher 按钮")
            sleep(1)
            return self
        except Exception as e:
            logger.warning(f"点击 voucher 按钮失败：{e}")
            return self

    def click_subscribe_button(self):
        """
        点击订阅按钮

        :return: self（支持链式调用）
        """
        try:
            subscribe_btn = self.wait_element_clickable(self._get_locator("subscribe_button"), timeout=5)
            subscribe_btn.click()
            logger.info("已点击订阅按钮")
            sleep(1)
            return self
        except Exception as e:
            logger.warning(f"点击订阅按钮失败：{e}")
            return self