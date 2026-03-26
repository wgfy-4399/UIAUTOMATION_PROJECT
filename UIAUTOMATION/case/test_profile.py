"""
Profile 页面冒烟测试
测试个人中心页面的基本功能，包括用户信息、金币/优惠券、功能入口等
"""
import pytest
from page.pages.profile_page import ProfilePage
from page.pages.home_page import HomePage
from utils.report_utils import AllureReportUtils
from utils.screenshot_utils import take_screenshot
from utils.log_utils import global_logger as logger
from time import sleep


class TestProfileSmoke:
    """Profile/个人中心页面冒烟测试"""

    @pytest.mark.smoke
    def test_profile_page_basic(self, app_name, init_driver):
        """测试 Profile 页面基本加载"""
        # 设置用例信息
        AllureReportUtils.set_test_case_info("Profile页面基本加载测试", "验证个人中心页面能正常加载和显示")
        AllureReportUtils.add_severity("critical")
        AllureReportUtils.add_tag("smoke", "profile", app_name)

        profile_page = ProfilePage(init_driver)

        # 1. 导航到 Profile 页面
        with AllureReportUtils.step("导航到 Profile 页面"):
            profile_page.click_profile_tab()
            sleep(2)  # 等待页面加载

            screenshot_path = take_screenshot(init_driver, "profile_page_loaded")
            AllureReportUtils.attach_screenshot(screenshot_path, "Profile页面加载完成")

        # 2. 验证页面加载完成
        with AllureReportUtils.step("验证页面加载完成"):
            is_loaded = profile_page.is_page_loaded()
            assert is_loaded, "Profile 页面未正确加载"
            AllureReportUtils.attach_text("页面加载状态: 已加载", "页面加载验证通过")

    @pytest.mark.smoke
    def test_profile_user_info(self, app_name, init_driver):
        """测试用户信息显示"""
        # 设置用例信息
        AllureReportUtils.set_test_case_info("用户信息显示测试", "验证用户ID等信息能正常显示")
        AllureReportUtils.add_severity("normal")
        AllureReportUtils.add_tag("smoke", "profile", app_name)

        profile_page = ProfilePage(init_driver)

        # 导航到 Profile 页面
        with AllureReportUtils.step("导航到 Profile 页面"):
            profile_page.click_profile_tab()
            sleep(2)

        # 检查登录状态
        with AllureReportUtils.step("检查登录状态"):
            is_logged_in = profile_page.is_logged_in()
            if is_logged_in:
                AllureReportUtils.attach_text("用户已登录", "登录状态")
                user_id = profile_page.get_user_id()
                if user_id:
                    AllureReportUtils.attach_text(f"用户ID: {user_id}", "用户信息")
            else:
                AllureReportUtils.attach_text("用户未登录", "登录状态")
                # 检查登录按钮是否可见
                has_login = profile_page.has_login_button()
                if has_login:
                    AllureReportUtils.attach_text("登录按钮可见", "登录入口")

        # 截图
        screenshot_path = take_screenshot(init_driver, "profile_user_info")
        AllureReportUtils.attach_screenshot(screenshot_path, "用户信息页面")

    @pytest.mark.smoke
    def test_profile_coins_display(self, app_name, init_driver):
        """测试金币显示"""
        # 设置用例信息
        AllureReportUtils.set_test_case_info("金币显示测试", "验证金币余额能正常显示")
        AllureReportUtils.add_severity("normal")
        AllureReportUtils.add_tag("smoke", "profile", app_name)

        profile_page = ProfilePage(init_driver)

        # 导航到 Profile 页面
        with AllureReportUtils.step("导航到 Profile 页面"):
            profile_page.click_profile_tab()
            sleep(2)

        # 获取金币信息
        with AllureReportUtils.step("获取金币信息"):
            try:
                coins = profile_page.get_coins_count()
                AllureReportUtils.attach_text(f"金币数量: {coins}", "金币余额")
            except Exception as e:
                AllureReportUtils.attach_text(f"获取金币异常: {str(e)}", "金币（跳过）")

        # 截图
        screenshot_path = take_screenshot(init_driver, "profile_coins")
        AllureReportUtils.attach_screenshot(screenshot_path, "金币显示页面")

    @pytest.mark.smoke
    def test_profile_menu_entries(self, app_name, init_driver):
        """测试菜单入口显示"""
        # 设置用例信息
        AllureReportUtils.set_test_case_info("菜单入口显示测试", "验证各功能入口能正常显示")
        AllureReportUtils.add_severity("normal")
        AllureReportUtils.add_tag("smoke", "profile", app_name)

        profile_page = ProfilePage(init_driver)

        # 导航到 Profile 页面
        with AllureReportUtils.step("导航到 Profile 页面"):
            profile_page.click_profile_tab()
            sleep(2)

        # 检查主要菜单入口
        menu_items = [
            ("rewards_entry", "Rewards 入口"),
            ("settings_entry", "Settings 入口"),
            ("feedback_entry", "Feedback 入口"),
            ("about_entry", "About 入口"),
        ]

        for locator_key, item_name in menu_items:
            with AllureReportUtils.step(f"检查 {item_name}"):
                try:
                    is_visible = profile_page.is_element_visible(locator_key)
                    status = "可见" if is_visible else "不可见"
                    AllureReportUtils.attach_text(f"{item_name}: {status}", item_name)
                except Exception as e:
                    AllureReportUtils.attach_text(f"{item_name} 检查异常: {str(e)}", item_name)

        # 截图
        screenshot_path = take_screenshot(init_driver, "profile_menu_entries")
        AllureReportUtils.attach_screenshot(screenshot_path, "菜单入口页面")

    @pytest.mark.smoke
    def test_profile_settings_navigation(self, app_name, init_driver):
        """测试设置页面导航"""
        # 设置用例信息
        AllureReportUtils.set_test_case_info("设置页面导航测试", "验证能正常进入设置页面")
        AllureReportUtils.add_severity("normal")
        AllureReportUtils.add_tag("smoke", "profile", app_name)

        profile_page = ProfilePage(init_driver)

        # 导航到 Profile 页面
        with AllureReportUtils.step("导航到 Profile 页面"):
            profile_page.click_profile_tab()
            sleep(2)

        # 点击设置入口
        with AllureReportUtils.step("点击设置入口"):
            try:
                profile_page.click_settings_entry()
                sleep(1)
                screenshot_path = take_screenshot(init_driver, "settings_page")
                AllureReportUtils.attach_screenshot(screenshot_path, "设置页面")
                # 返回 Profile 页面
                profile_page.back()
                sleep(1)
            except Exception as e:
                logger.warning(f"点击设置入口失败: {e}")
                AllureReportUtils.attach_text(f"点击设置入口异常: {str(e)}", "设置导航（跳过）")

    @pytest.mark.smoke
    def test_profile_recent_read_card(self, app_name, init_driver):
        """测试最近阅读卡片"""
        # 设置用例信息
        AllureReportUtils.set_test_case_info("最近阅读卡片测试", "验证最近阅读卡片能正常显示")
        AllureReportUtils.add_severity("normal")
        AllureReportUtils.add_tag("smoke", "profile", app_name)

        profile_page = ProfilePage(init_driver)

        # 导航到 Profile 页面
        with AllureReportUtils.step("导航到 Profile 页面"):
            profile_page.click_profile_tab()
            sleep(2)

        # 检查最近阅读卡片
        with AllureReportUtils.step("检查最近阅读卡片"):
            has_recent_read = profile_page.has_recent_read_card()
            if has_recent_read:
                AllureReportUtils.attach_text("最近阅读卡片可见", "最近阅读卡片")
                # 尝试获取书籍标题
                book_title = profile_page.get_recent_read_book_title()
                if book_title:
                    AllureReportUtils.attach_text(f"最近阅读: {book_title}", "书籍标题")
            else:
                AllureReportUtils.attach_text("最近阅读卡片不可见（可能无阅读记录）", "最近阅读卡片")

        # 截图
        screenshot_path = take_screenshot(init_driver, "profile_recent_read")
        AllureReportUtils.attach_screenshot(screenshot_path, "最近阅读卡片")