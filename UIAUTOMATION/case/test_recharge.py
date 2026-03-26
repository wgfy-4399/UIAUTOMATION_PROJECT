from time import sleep

import pytest

from utils.report_utils import AllureReportUtils
from utils.screenshot_utils import take_screenshot
from page.pages.home_page import HomePage
from page.pages.recharge_page import RechargePage


@pytest.mark.regression
@pytest.mark.recharge
def test_recharge_flow(app_name, device_platform, init_driver, reset_app):
    """
    充值流程回归用例：
    - 从首页进入充值页面
    - 选择充值档位并验证价格
    - 选择支付渠道
    - 点击立即支付并验证支付弹窗唤起
    """
    print("\n===== 执行充值流程回归用例 =====")

    # 1. 设置用例基本信息
    AllureReportUtils.set_test_case_info(
        "充值中心-基础流程回归",
        "验证充值页面档位选择、价格展示、支付渠道选择以及支付弹窗唤起流程"
    )
    AllureReportUtils.add_severity("normal")
    AllureReportUtils.add_tag("regression", "recharge", app_name)

    # Step 1: 从首页进入充值页面
    # 说明：此处假设充值入口位于“任务中心”或“我的钱包”等位置，
    # 当前通过直接构造 RechargePage 进入，实际项目可在此补充从首页/任务中心跳转的链路。
    with AllureReportUtils.step("从首页进入充值中心页面（当前直接构造 RechargePage 对象）"):
        home_page = HomePage(init_driver)
        recharge_page = RechargePage(init_driver)
        sleep(2)
        screenshot_path = take_screenshot(init_driver, "recharge_entry_from_home")
        AllureReportUtils.attach_screenshot(screenshot_path, "进入充值中心页面截图")

    # Step 2: 获取进入充值页时的当前余额
    with AllureReportUtils.step("获取进入充值页时的当前余额"):
        initial_balance = recharge_page.get_current_balance()
        AllureReportUtils.attach_text(f"进入充值页时的余额：{initial_balance}", "初始余额")

    # Step 3: 选择充值档位并验证价格展示
    with AllureReportUtils.step("选择第一个充值档位并验证价格展示"):
        recharge_page.select_recharge_package_by_index(0)
        price_text = recharge_page.get_package_price_by_index(0)
        AllureReportUtils.attach_text(f"第一个充值档位价格文案：{price_text}", "充值档位价格")
        assert price_text, "充值档位价格文本不应为空"
        sleep(1)
        screenshot_path = take_screenshot(init_driver, "recharge_select_package_and_price")
        AllureReportUtils.attach_screenshot(screenshot_path, "选择充值档位并展示价格截图")

    # Step 4: 选择支付渠道（按名称适配海外支付：Google / PayPal / Stripe / AppleID）
    with AllureReportUtils.step("在充值页选择支付渠道（海外支付方式）"):
        # Android 优先使用 Google / Stripe / PayPal，iOS 优先 Apple 支付
        if device_platform.lower() == "ios":
            channel_name = "Apple"
        else:
            # 默认优先 Google，其次 PayPal，再次 Stripe
            channel_name = "Google"

        recharge_page.select_payment_channel(channel_name)
        sleep(1)
        screenshot_path = take_screenshot(init_driver, "recharge_select_channel")
        AllureReportUtils.attach_screenshot(screenshot_path, f"选择支付渠道（{channel_name}）后截图")

    # Step 5: 点击立即支付并验证支付弹窗唤起
    with AllureReportUtils.step("点击立即支付并验证支付弹窗唤起（不进行真实支付）"):
        recharge_page.click_pay_now()
        sleep(2)
        popup_displayed = recharge_page.is_payment_popup_displayed()
        screenshot_path = take_screenshot(init_driver, "recharge_payment_popup")
        AllureReportUtils.attach_screenshot(screenshot_path, "支付弹窗验证截图")
        assert popup_displayed, "支付弹窗未成功唤起"

    # Step 6: （可选）再次获取余额，仅做记录，不强制断言变化
    with AllureReportUtils.step("再次获取当前余额，仅做记录（测试环境不强制校验变化）"):
        final_balance = recharge_page.get_current_balance()
        AllureReportUtils.attach_text(f"支付弹窗后当前余额：{final_balance}", "支付后余额记录")
        screenshot_path = take_screenshot(init_driver, "recharge_balance_after_popup")
        AllureReportUtils.attach_screenshot(screenshot_path, "支付弹窗后余额截图")

