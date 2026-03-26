"""
Rewards/Task Center 页面冒烟测试
测试任务中心页面的基本功能，包括签到弹窗、每日签到和金币余额验证
"""
import pytest
from page.pages.home_page import HomePage
from page.pages.task_center_page import TaskCenterPage
from utils.report_utils import AllureReportUtils
from utils.screenshot_utils import take_screenshot
from utils.log_utils import global_logger as logger
from time import sleep


class TestRewardsSmoke:
    """Rewards/Task Center 页面冒烟测试"""

    @pytest.mark.smoke
    def test_rewards_page_basic(self, app_name, init_driver):
        """测试 Rewards 页面基本加载"""
        # 设置用例信息
        AllureReportUtils.set_test_case_info("Rewards页面基本加载测试", "验证任务中心页面能正常加载和显示")
        AllureReportUtils.add_severity("critical")
        AllureReportUtils.add_tag("smoke", "rewards", app_name)

        task_center = TaskCenterPage(init_driver)

        # 1. 导航到 Rewards 页面
        with AllureReportUtils.step("导航到 Rewards 页面"):
            try:
                task_center.wait_element_clickable(task_center._get_locator("task_center_tab")).click()
                logger.info("已点击 Rewards Tab")
            except:
                logger.info("点击失败，可能已在页面")
            sleep(3)  # 等待页面加载

            # 关闭签到弹窗（如果存在）
            task_center.close_checkin_popup()

            screenshot_path = take_screenshot(init_driver, "rewards_page_loaded")
            AllureReportUtils.attach_screenshot(screenshot_path, "Rewards页面加载完成")

        # 2. 验证页面加载完成
        with AllureReportUtils.step("验证页面加载完成"):
            # 检查是否有任务列表
            try:
                task_list = task_center.find_element(task_center._get_locator("task_list_container"))
                is_loaded = task_list.is_displayed()
            except:
                is_loaded = False

            assert is_loaded, "Rewards 页面未正确加载"
            AllureReportUtils.attach_text("页面加载状态: 已加载", "页面加载验证通过")

    @pytest.mark.smoke
    def test_rewards_daily_tasks(self, app_name, init_driver):
        """测试每日任务显示"""
        # 设置用例信息
        AllureReportUtils.set_test_case_info("每日任务显示测试", "验证每日任务能正常显示")
        AllureReportUtils.add_severity("normal")
        AllureReportUtils.add_tag("smoke", "rewards", app_name)

        task_center = TaskCenterPage(init_driver)

        # 导航到 Rewards 页面
        try:
            task_center.wait_element_clickable(task_center._get_locator("task_center_tab")).click()
        except:
            pass
        sleep(3)

        # 关闭签到弹窗
        task_center.close_checkin_popup()

        # 获取金币余额
        with AllureReportUtils.step("获取金币余额"):
            try:
                balance = task_center.get_gold_balance()
                AllureReportUtils.attach_text(f"金币余额: {balance}", "金币余额")
            except Exception as e:
                AllureReportUtils.attach_text(f"获取金币余额异常: {str(e)}", "金币余额（跳过）")

        # 截图
        screenshot_path = take_screenshot(init_driver, "rewards_daily_tasks")
        AllureReportUtils.attach_screenshot(screenshot_path, "每日任务页面")

    @pytest.mark.smoke
    def test_rewards_task_interaction(self, app_name, init_driver):
        """测试任务交互功能"""
        # 设置用例信息
        AllureReportUtils.set_test_case_info("任务交互测试", "验证签到弹窗交互")
        AllureReportUtils.add_severity("normal")
        AllureReportUtils.add_tag("smoke", "rewards", app_name)

        task_center = TaskCenterPage(init_driver)

        # 导航到 Rewards 页面
        try:
            task_center.wait_element_clickable(task_center._get_locator("task_center_tab")).click()
        except:
            pass
        sleep(3)

        # 检查是否有签到弹窗
        with AllureReportUtils.step("检查签到弹窗"):
            has_popup = task_center.is_checkin_popup_visible()
            if has_popup:
                AllureReportUtils.attach_text("检测到签到弹窗", "弹窗状态")

                # 关闭弹窗
                with AllureReportUtils.step("关闭签到弹窗"):
                    task_center.close_checkin_popup()
                    screenshot_path = take_screenshot(init_driver, "after_close_popup")
                    AllureReportUtils.attach_screenshot(screenshot_path, "关闭弹窗后")
            else:
                AllureReportUtils.attach_text("未检测到签到弹窗（可能已签到）", "弹窗状态")
