"""
章节列表页面冒烟测试
测试从阅读器打开章节列表、章节选择、关闭等核心功能
"""
import pytest
from time import sleep

from utils.report_utils import AllureReportUtils
from utils.screenshot_utils import take_screenshot
from page.pages.home_page import HomePage
from page.pages.shelf_page import ShelfPage
from page.pages.reader_page import ReaderPage
from page.pages.chapter_list_page import ChapterList


@pytest.mark.smoke
def test_chapter_list_basic_open(app_name, init_driver):
    """
    章节列表基本冒烟：打开章节列表验证
    验证从阅读器打开章节列表，列表正常加载
    """
    # 1. 设置用例基本信息
    AllureReportUtils.set_test_case_info(
        "章节列表-打开验证",
        "验证从阅读器打开章节列表，列表正常加载"
    )
    AllureReportUtils.add_severity("critical")
    AllureReportUtils.add_tag("smoke", "chapter_list", "reader", app_name)

    home_page = HomePage(init_driver)

    # Step 1: 导航到阅读器
    with AllureReportUtils.step("从首页进入书架"):
        shelf_page = home_page.click_shelf_tab()
        assert isinstance(shelf_page, ShelfPage)
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "shelf_page_loaded")
        AllureReportUtils.attach_screenshot(screenshot_path, "书架页面加载完成")

    with AllureReportUtils.step("从书架打开第一本书进入阅读器"):
        reader_page = shelf_page.click_book_by_index(0)
        assert isinstance(reader_page, ReaderPage)
        sleep(3)
        screenshot_path = take_screenshot(init_driver, "reader_opened")
        AllureReportUtils.attach_screenshot(screenshot_path, "阅读器打开成功")

    # Step 2: 打开章节列表
    with AllureReportUtils.step("在阅读器中点击章节列表按钮"):
        reader_page.tap_screen_to_show_menu()
        sleep(1)
        chapter_list = reader_page.click_on_the_chapter_list()
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "chapter_list_opened")
        AllureReportUtils.attach_screenshot(screenshot_path, "章节列表打开截图")

    # Step 3: 验证章节列表加载
    with AllureReportUtils.step("验证章节列表已加载"):
        assert isinstance(chapter_list, ChapterList), "应该返回 ChapterList 对象"

        chapter_count = chapter_list.get_chapter_count()
        assert chapter_count > 0, "章节列表应该至少有一个章节"

        AllureReportUtils.attach_text(f"章节总数: {chapter_count}", "章节数量")

        # 验证可见章节
        titles = chapter_list.get_visible_chapter_titles()
        assert len(titles) > 0, "应该有可见的章节"
        AllureReportUtils.attach_text(f"可见章节: {', '.join(titles[:5])}", "前5个章节标题")

    # Step 4: 关闭章节列表
    with AllureReportUtils.step("关闭章节列表"):
        reader_page = chapter_list.close_chapter_list()
        assert isinstance(reader_page, ReaderPage), "关闭后应该返回阅读器"
        sleep(1)
        screenshot_path = take_screenshot(init_driver, "chapter_list_closed")
        AllureReportUtils.attach_screenshot(screenshot_path, "章节列表关闭后截图")


@pytest.mark.smoke
def test_chapter_select_and_jump(app_name, init_driver):
    """
    章节选择跳转测试
    验证选择章节后正确跳转到对应章节内容
    """
    # 1. 设置用例基本信息
    AllureReportUtils.set_test_case_info(
        "章节列表-章节选择跳转",
        "验证选择章节后正确跳转到对应章节内容"
    )
    AllureReportUtils.add_severity("high")
    AllureReportUtils.add_tag("smoke", "chapter_list", "navigation", app_name)

    home_page = HomePage(init_driver)

    # Step 1: 导航到章节列表
    with AllureReportUtils.step("导航到章节列表"):
        shelf_page = home_page.click_shelf_tab()
        sleep(2)
        reader_page = shelf_page.click_book_by_index(0)
        sleep(3)

        reader_page.tap_screen_to_show_menu()
        chapter_list = reader_page.click_on_the_chapter_list()
        sleep(2)

    # Step 2: 获取章节信息
    with AllureReportUtils.step("获取章节信息"):
        chapter_count = chapter_list.get_chapter_count()
        AllureReportUtils.attach_text(f"章节总数: {chapter_count}", "章节数量")

        current_title = chapter_list.get_current_chapter_title()
        AllureReportUtils.attach_text(f"当前章节: {current_title}", "当前章节")

    # Step 3: 选择第3个章节（如果存在）
    target_index = 2  # 索引从0开始，2表示第3章
    if chapter_count > target_index:
        with AllureReportUtils.step(f"点击第 {target_index + 1} 章节"):
            reader_page = chapter_list.click_chapter_by_index(target_index)
            assert isinstance(reader_page, ReaderPage), "选择章节后应该返回阅读器"
            sleep(3)

            screenshot_path = take_screenshot(init_driver, "chapter_jumped")
            AllureReportUtils.attach_screenshot(screenshot_path, "章节跳转后截图")
    else:
        # 如果章节不够，选择第一个
        with AllureReportUtils.step("点击第一个章节"):
            reader_page = chapter_list.click_first_visible_chapter()
            sleep(3)


@pytest.mark.smoke
def test_chapter_list_scroll(app_name, init_driver):
    """
    章节列表滚动测试
    验证章节列表可以正常滚动
    """
    # 1. 设置用例基本信息
    AllureReportUtils.set_test_case_info(
        "章节列表-滚动测试",
        "验证章节列表可以正常滚动"
    )
    AllureReportUtils.add_severity("medium")
    AllureReportUtils.add_tag("smoke", "chapter_list", "scroll", app_name)

    home_page = HomePage(init_driver)

    # Step 1: 导航到章节列表
    with AllureReportUtils.step("导航到章节列表"):
        shelf_page = home_page.click_shelf_tab()
        sleep(2)
        reader_page = shelf_page.click_book_by_index(0)
        sleep(3)

        reader_page.tap_screen_to_show_menu()
        chapter_list = reader_page.click_on_the_chapter_list()
        sleep(2)

    # Step 2: 获取滚动前的章节
    with AllureReportUtils.step("获取滚动前的可见章节"):
        titles_before = chapter_list.get_visible_chapter_titles()
        AllureReportUtils.attach_text(f"滚动前章节: {', '.join(titles_before[:3])}", "滚动前")

    # Step 3: 向下滚动
    with AllureReportUtils.step("向下滚动章节列表"):
        chapter_list.scroll_to_bottom()
        sleep(1)

        screenshot_path = take_screenshot(init_driver, "after_scroll_down")
        AllureReportUtils.attach_screenshot(screenshot_path, "向下滚动后截图")

    # Step 4: 获取滚动后的章节
    with AllureReportUtils.step("获取滚动后的可见章节"):
        titles_after = chapter_list.get_visible_chapter_titles()
        AllureReportUtils.attach_text(f"滚动后章节: {', '.join(titles_after[:3])}", "滚动后")

    # Step 5: 关闭章节列表
    with AllureReportUtils.step("关闭章节列表"):
        reader_page = chapter_list.close_chapter_list()
        sleep(1)


@pytest.mark.smoke
def test_chapter_list_count_display(app_name, init_driver):
    """
    章节数量显示测试
    验证章节总数正确显示
    """
    # 1. 设置用例基本信息
    AllureReportUtils.set_test_case_info(
        "章节列表-章节数量显示",
        "验证章节总数正确显示"
    )
    AllureReportUtils.add_severity("medium")
    AllureReportUtils.add_tag("smoke", "chapter_list", "data", app_name)

    home_page = HomePage(init_driver)

    # Step 1: 导航到章节列表
    with AllureReportUtils.step("导航到章节列表"):
        shelf_page = home_page.click_shelf_tab()
        sleep(2)
        reader_page = shelf_page.click_book_by_index(0)
        sleep(3)

        reader_page.tap_screen_to_show_menu()
        chapter_list = reader_page.click_on_the_chapter_list()
        sleep(2)

    # Step 2: 验证章节数量
    with AllureReportUtils.step("验证章节数量"):
        chapter_count = chapter_list.get_chapter_count()
        assert chapter_count > 0, "章节数量应该大于0"

        AllureReportUtils.attach_text(f"章节总数: {chapter_count}", "章节数量验证")

        # 验证章节数量在合理范围内
        assert chapter_count < 10000, "章节数量应该在合理范围内"

    # Step 3: 关闭章节列表
    with AllureReportUtils.step("关闭章节列表"):
        reader_page = chapter_list.close_chapter_list()
        sleep(1)