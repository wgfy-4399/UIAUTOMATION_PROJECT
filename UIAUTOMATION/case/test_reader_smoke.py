from time import sleep

import pytest

from utils.report_utils import AllureReportUtils
from utils.screenshot_utils import take_screenshot
from page.pages.home_page import HomePage
from page.pages.shelf_page import ShelfPage
from page.pages.reader_page import ReaderPage


@pytest.mark.smoke
def test_reader_smoke_flow(app_name, init_driver, reset_app):
    """
    主包阅读器冒烟流程：
    - 从首页进入书架
    - 从书架进入阅读器
    - 在阅读器中翻页、章节切换
    - 返回书架/首页
    """
    print("\n===== 执行主包阅读器冒烟用例 =====")

    # 1. 设置用例基本信息
    AllureReportUtils.set_test_case_info(
        "主包阅读器-完整冒烟流程",
        "验证从首页进入书架，再进入阅读器并完成翻页与章节切换的完整流程"
    )
    AllureReportUtils.add_severity("critical")
    AllureReportUtils.add_tag("smoke", "reader", "main_app", app_name)

    home_page = HomePage(init_driver)

    # Step 1: 从首页进入书架
    with AllureReportUtils.step("从首页点击底部【书架】Tab进入书架页面"):
        shelf_page = home_page.click_shelf_tab()
        assert isinstance(shelf_page, ShelfPage)
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "shelf_entry_from_home")
        AllureReportUtils.attach_screenshot(screenshot_path, "从首页进入书架截图")

    # Step 2: 从书架打开第一本书进入阅读器
    with AllureReportUtils.step("在书架中点击第一本书进入阅读器"):
        reader_page = shelf_page.click_book_by_index(0)
        assert isinstance(reader_page, ReaderPage)
        sleep(3)
        screenshot_path = take_screenshot(init_driver, "reader_opened_from_shelf")
        AllureReportUtils.attach_screenshot(screenshot_path, "从书架进入阅读器截图")

    # Step 3: 在阅读器中进行翻页操作
    with AllureReportUtils.step("在阅读器中向上滑动进行翻页"):
        reader_page.swipe_up()
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "reader_after_swipe")
        AllureReportUtils.attach_screenshot(screenshot_path, "阅读器翻页后截图")

    # Step 4: 在阅读器中进行章节切换（下一章）
    with AllureReportUtils.step("在阅读器中点击下一章进行章节切换"):
        # 先唤起菜单，再点击下一章
        reader_page.tap_screen_to_show_menu()
        reader_page.click_on_the_next_chapter()
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "reader_next_chapter")
        AllureReportUtils.attach_screenshot(screenshot_path, "阅读器切换到下一章截图")

    # Step 5: 返回书架/首页，完成冒烟流程
    with AllureReportUtils.step("从阅读器返回首页，结束冒烟流程（链式调用）"):
        home_page = reader_page.back_to_home()
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "back_from_reader_to_home")
        AllureReportUtils.attach_screenshot(screenshot_path, "从阅读器返回首页后页面截图")

    # 简单断言应用名合法
    assert app_name in ["main", "vest1", "vest2", "vest3"]

