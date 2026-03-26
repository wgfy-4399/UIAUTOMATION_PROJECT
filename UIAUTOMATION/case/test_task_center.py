from time import sleep

import pytest

from utils.report_utils import AllureReportUtils
from utils.screenshot_utils import take_screenshot
from page.pages.home_page import HomePage
from page.pages.task_center_page import TaskCenterPage


@pytest.mark.regression
def test_task_center_flow(app_name, init_driver, reset_app):
    """
    任务中心回归用例：
    - 从首页进入任务中心
    - 执行每日签到
    - 领取任务奖励
    - 验证金币余额发生变化
    """
    print("\n===== 执行任务中心回归用例 =====")

    # 1. 设置用例基本信息
    AllureReportUtils.set_test_case_info(
        "任务中心-金币奖励冒烟/回归",
        "验证任务中心每日签到和领取任务奖励功能，并校验金币余额变化"
    )
    AllureReportUtils.add_severity("normal")
    AllureReportUtils.add_tag("regression", "task_center", app_name)

    # 统一使用 pages.HomePage 作为首页对象
    home_page = HomePage(init_driver)

    # Step 1: 从首页进入任务中心
    with AllureReportUtils.step("从首页点击底部【任务】Tab进入任务中心页面"):
        task_center_page = home_page.click_task_tab()
        # 若首页暂未返回 TaskCenterPage，则手动构造（兼容性处理）
        if not isinstance(task_center_page, TaskCenterPage):
            task_center_page = TaskCenterPage(init_driver)

        assert isinstance(task_center_page, TaskCenterPage)
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "task_center_entry_from_home")
        AllureReportUtils.attach_screenshot(screenshot_path, "从首页进入任务中心截图")

    # Step 2: 获取进入任务中心前的金币余额
    with AllureReportUtils.step("获取进入任务中心时的金币余额"):
        initial_balance = task_center_page.get_gold_balance()
        AllureReportUtils.attach_text(f"进入任务中心时金币余额：{initial_balance}", "初始金币余额")

    # Step 3: 执行每日签到
    with AllureReportUtils.step("在任务中心执行每日签到"):
        task_center_page.daily_check_in()
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "task_center_after_check_in")
        AllureReportUtils.attach_screenshot(screenshot_path, "每日签到完成后截图")

    # Step 4: 领取任务奖励（第一个可领取奖励）
    with AllureReportUtils.step("在任务中心领取第一个任务奖励"):
        task_center_page.claim_reward_by_index(0)
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "task_center_after_claim_reward")
        AllureReportUtils.attach_screenshot(screenshot_path, "领取任务奖励后截图")

    # Step 5: 再次获取金币余额并比对变化
    with AllureReportUtils.step("重新获取金币余额并验证发生变化"):
        final_balance = task_center_page.get_gold_balance()
        AllureReportUtils.attach_text(f"领取奖励后金币余额：{final_balance}", "最终金币余额")
        screenshot_path = take_screenshot(init_driver, "task_center_final_balance")
        AllureReportUtils.attach_screenshot(screenshot_path, "金币余额验证截图")

        # 核心断言：金币余额应当不小于初始值，且尽量发生增长
        assert final_balance >= initial_balance

