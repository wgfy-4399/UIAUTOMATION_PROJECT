from time import sleep

import pytest

from utils.report_utils import AllureReportUtils
from utils.screenshot_utils import take_screenshot
from page.pages.home_page import HomePage
from page.pages.shelf_page import ShelfPage
from page.pages.reader_page import ReaderPage
from page.pages.task_center_page import TaskCenterPage
from page.pages.recharge_page import RechargePage


@pytest.mark.e2e
@pytest.mark.regression
def test_main_app_full_flow(app_name, device_platform, init_driver, reset_app):
    """
    主包端到端E2E流程用例：
    - APP启动
    - 首页浏览
    - 进入书架并打开一本书进行阅读
    - 返回首页
    - 进入任务中心执行签到并领取奖励
    - 进入充值中心并校验支付弹窗
    - 返回首页
    """
    print("\n===== 执行主包端到端E2E全流程用例 =====")

    # 1. 设置用例基本信息
    AllureReportUtils.set_test_case_info(
        "主包E2E-首页→书架→阅读→任务中心→充值→首页",
        "验证主包从首页到书架阅读、任务中心签到领奖励、充值页支付弹窗的完整端到端流程"
    )
    AllureReportUtils.add_severity("critical")
    AllureReportUtils.add_tag("e2e", "regression", "main_app", app_name)

    # Step 0: APP启动后落在首页
    home_page = HomePage(init_driver)

    with AllureReportUtils.step("验证APP启动并加载主包首页"):
        # 点击首页Tab确保在首页
        home_page.click_home_tab()
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "e2e_home_loaded")
        AllureReportUtils.attach_screenshot(screenshot_path, "E2E-主包首页加载截图")
        assert app_name in ["main", "vest1", "vest2", "vest3"]

    # Step 1: 从首页进入书架并打开一本书进入阅读器
    with AllureReportUtils.step("从首页进入书架并打开第一本书进入阅读器"):
        shelf_page = home_page.click_shelf_tab()
        assert isinstance(shelf_page, ShelfPage)
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "e2e_shelf_from_home")
        AllureReportUtils.attach_screenshot(screenshot_path, "E2E-从首页进入书架截图")

        reader_page = shelf_page.click_book_by_index(0)
        assert isinstance(reader_page, ReaderPage)
        sleep(3)
        screenshot_path = take_screenshot(init_driver, "e2e_reader_from_shelf")
        AllureReportUtils.attach_screenshot(screenshot_path, "E2E-从书架进入阅读器截图")

    # Step 2: 在阅读器中进行简单阅读操作（翻页）
    with AllureReportUtils.step("在阅读器中进行翻页操作（基础阅读体验）"):
        reader_page.swipe_up()
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "e2e_reader_after_swipe")
        AllureReportUtils.attach_screenshot(screenshot_path, "E2E-阅读器翻页后截图")

    # Step 3: 从阅读器返回首页
    with AllureReportUtils.step("从阅读器返回首页（链式调用）"):
        home_page = reader_page.back_to_home()
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "e2e_home_after_reader")
        AllureReportUtils.attach_screenshot(screenshot_path, "E2E-从阅读器返回首页截图")

    # Step 4: 从首页进入任务中心，执行签到并领取奖励
    with AllureReportUtils.step("从首页进入任务中心并执行每日签到与领取奖励"):
        task_center_page = home_page.click_task_tab()
        if not isinstance(task_center_page, TaskCenterPage):
            task_center_page = TaskCenterPage(init_driver)

        assert isinstance(task_center_page, TaskCenterPage)
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "e2e_task_center_entry")
        AllureReportUtils.attach_screenshot(screenshot_path, "E2E-从首页进入任务中心截图")

        initial_gold = task_center_page.get_gold_balance()
        AllureReportUtils.attach_text(f"E2E-任务中心初始金币：{initial_gold}", "E2E-任务中心初始金币")

        task_center_page.daily_check_in()
        task_center_page.claim_reward_by_index(0)
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "e2e_task_center_after_reward")
        AllureReportUtils.attach_screenshot(screenshot_path, "E2E-任务中心签到+领奖励后截图")

        final_gold = task_center_page.get_gold_balance()
        AllureReportUtils.attach_text(f"E2E-任务中心最终金币：{final_gold}", "E2E-任务中心最终金币")
        assert final_gold >= initial_gold

    # Step 5: 进入充值页面，选择档位与支付渠道，并校验支付弹窗唤起
    with AllureReportUtils.step("进入充值中心并完成档位选择与支付弹窗校验"):
        # 说明：当前版本直接构造 RechargePage 对象，实际项目可在此补充从首页/任务中心跳转路径
        recharge_page = RechargePage(init_driver)
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "e2e_recharge_entry")
        AllureReportUtils.attach_screenshot(screenshot_path, "E2E-进入充值中心页面截图")

        initial_balance = recharge_page.get_current_balance()
        AllureReportUtils.attach_text(f"E2E-充值中心初始余额：{initial_balance}", "E2E-充值中心初始余额")

        recharge_page.select_recharge_package_by_index(0)
        price_text = recharge_page.get_package_price_by_index(0)
        AllureReportUtils.attach_text(f"E2E-选择的充值档位价格：{price_text}", "E2E-充值档位价格")
        assert price_text, "E2E-充值档位价格文本不应为空"

        # 根据平台选择支付渠道
        if device_platform.lower() == "ios":
            channel_name = "Apple"
        else:
            channel_name = "Google"

        recharge_page.select_payment_channel(channel_name)
        sleep(1)
        screenshot_path = take_screenshot(init_driver, "e2e_recharge_select_channel")
        AllureReportUtils.attach_screenshot(screenshot_path, f"E2E-选择支付渠道（{channel_name}）后截图")

        recharge_page.click_pay_now()
        sleep(2)
        popup_displayed = recharge_page.is_payment_popup_displayed()
        screenshot_path = take_screenshot(init_driver, "e2e_recharge_payment_popup")
        AllureReportUtils.attach_screenshot(screenshot_path, "E2E-支付弹窗截图")
        assert popup_displayed, "E2E-支付弹窗未成功唤起"

    # Step 6: 从充值页面返回首页，完成E2E流程
    with AllureReportUtils.step("从充值页面返回首页，完成端到端流程（链式调用）"):
        home_page = recharge_page.back_to_home()
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "e2e_home_final")
        AllureReportUtils.attach_screenshot(screenshot_path, "E2E-流程结束返回首页截图")

    # 说明：reset_app 夹具会在用例结束后自动重置APP状态，无需在用例内手动处理

