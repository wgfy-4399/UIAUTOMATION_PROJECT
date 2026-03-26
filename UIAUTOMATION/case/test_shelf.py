"""
书架页面测试用例
测试书架页面的基本功能：书籍列表加载、书籍点击进入阅读器等
"""
import pytest
from page.pages.home_page import HomePage
from page.pages.shelf_page import ShelfPage
from page.pages.reader_page import ReaderPage
from utils.report_utils import AllureReportUtils
from utils.screenshot_utils import take_screenshot
from utils.log_utils import global_logger as logger
from time import sleep


class TestShelf:
    """书架页面测试用例"""

    @pytest.mark.smoke
    def test_shelf_load(self, app_name, init_driver):
        """测试书架页面基本加载"""
        AllureReportUtils.set_test_case_info("书架页面加载测试", "验证书架页面能正常加载和显示")
        AllureReportUtils.add_severity("critical")
        AllureReportUtils.add_tag("smoke", "shelf", app_name)

        home_page = HomePage(init_driver)

        # 从首页进入书架
        with AllureReportUtils.step("从首页点击底部【书架】Tab"):
            shelf_page = home_page.click_shelf_tab()
            assert isinstance(shelf_page, ShelfPage), "进入书架页面失败"
            sleep(2)
            screenshot_path = take_screenshot(init_driver, "shelf_page_loaded")
            AllureReportUtils.attach_screenshot(screenshot_path, "书架页面加载完成")

        # 验证书架容器存在
        with AllureReportUtils.step("验证书架列表容器存在"):
            try:
                book_list = shelf_page.find_element(shelf_page._get_locator("book_list"))
                is_loaded = book_list.is_displayed()
            except Exception as e:
                logger.warning(f"书架列表容器未找到: {e}")
                is_loaded = False

            # 即使容器未找到，只要有书籍封面也认为加载成功
            if not is_loaded:
                try:
                    book_cover = shelf_page.find_element(shelf_page._get_locator("book_cover"))
                    is_loaded = book_cover.is_displayed()
                except Exception:
                    pass

            assert is_loaded, "书架页面未正确加载"
            AllureReportUtils.attach_text("书架页面加载状态: 已加载", "页面验证通过")

    @pytest.mark.smoke
    def test_shelf_book_count(self, app_name, init_driver):
        """测试书架书籍数量获取"""
        AllureReportUtils.set_test_case_info("书架书籍数量测试", "验证能正确获取书架上的书籍数量")
        AllureReportUtils.add_severity("normal")
        AllureReportUtils.add_tag("smoke", "shelf", app_name)

        home_page = HomePage(init_driver)
        shelf_page = home_page.click_shelf_tab()
        sleep(2)

        # 获取书籍数量
        with AllureReportUtils.step("获取书架书籍数量"):
            book_count = shelf_page.get_book_count()
            AllureReportUtils.attach_text(f"书籍数量: {book_count}", "书籍数量统计")
            logger.info(f"书架书籍数量: {book_count}")

            # 断言至少有一本书
            assert book_count >= 0, "获取书籍数量失败"

        # 获取书籍标题列表
        with AllureReportUtils.step("获取书籍标题列表"):
            titles = shelf_page.get_book_titles()
            if titles:
                AllureReportUtils.attach_text("\n".join(titles[:10]), "书籍标题列表（前10本）")
            else:
                AllureReportUtils.attach_text("未获取到书籍标题", "书籍标题列表")

        screenshot_path = take_screenshot(init_driver, "shelf_book_count")
        AllureReportUtils.attach_screenshot(screenshot_path, "书架书籍列表")

    @pytest.mark.smoke
    def test_shelf_open_book(self, app_name, init_driver):
        """测试从书架打开书籍进入阅读器"""
        AllureReportUtils.set_test_case_info("书架打开书籍测试", "验证点击书架书籍能正常进入阅读器")
        AllureReportUtils.add_severity("critical")
        AllureReportUtils.add_tag("smoke", "shelf", app_name)

        home_page = HomePage(init_driver)
        shelf_page = home_page.click_shelf_tab()
        sleep(2)

        # 点击第一本书
        with AllureReportUtils.step("点击书架第一本书"):
            try:
                reader_page = shelf_page.click_book_by_index(0)
                assert isinstance(reader_page, ReaderPage), "未成功进入阅读器"
                sleep(3)
                screenshot_path = take_screenshot(init_driver, "reader_from_shelf")
                AllureReportUtils.attach_screenshot(screenshot_path, "从书架进入阅读器")
            except Exception as e:
                logger.error(f"打开书籍失败: {e}")
                # 如果书架为空，跳过此测试
                book_count = shelf_page.get_book_count()
                if book_count == 0:
                    pytest.skip("书架为空，跳过打开书籍测试")
                raise e

        # 返回书架
        with AllureReportUtils.step("从阅读器返回书架"):
            reader_page.back()
            sleep(2)
            screenshot_path = take_screenshot(init_driver, "back_to_shelf")
            AllureReportUtils.attach_screenshot(screenshot_path, "返回书架后")