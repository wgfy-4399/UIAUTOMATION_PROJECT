from time import sleep

from selenium.webdriver.common.by import By

from page.base_page import BasePage
from utils.locator_utils import load_locators, get_locator_from_config
from utils.screenshot_utils import take_screenshot
from utils.log_utils import global_logger as logger


class TaskCenterPage(BasePage):
    """
    任务中心公共页面对象（统一使用 YAML 配置）
    - 每日签到
    - 任务列表浏览与点击
    - 领取任务奖励
    - 查看金币余额与任务规则
    """

    def __init__(self, driver):
        super().__init__(driver)

        # 加载定位符配置
        self._locators = load_locators("task_center")

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

    # ------------------------------ 每日签到 ------------------------------

    def close_checkin_popup(self):
        """
        关闭签到弹窗（如果存在）
        :return: True 表示关闭了弹窗，False 表示没有弹窗
        """
        try:
            # 尝试查找关闭按钮
            close_button = self.find_element(self._get_locator("checkin_popup_close_button"), timeout=3)
            if close_button and close_button.is_displayed():
                close_button.click()
                logger.info("已关闭签到弹窗")
                sleep(1)
                return True
        except:
            # 没有找到弹窗，继续执行
            logger.debug("未检测到签到弹窗")
            pass
        return False

    def is_checkin_popup_visible(self) -> bool:
        """检查签到弹窗是否可见"""
        try:
            popup = self.find_element(self._get_locator("checkin_popup_checkin_button"), timeout=2)
            return popup.is_displayed()
        except:
            return False

    def click_checkin_popup_checkin(self):
        """点击签到弹窗中的签到按钮"""
        try:
            self.wait_element_clickable(self._get_locator("checkin_popup_checkin_button")).click()
            logger.info("已点击签到弹窗的签到按钮")
            sleep(2)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "checkin_popup_checkin_fail")
            logger.error(f"点击签到按钮失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def daily_check_in(self):
        """执行每日签到操作"""
        try:
            logger.info("开始执行每日签到操作")
            self.wait_element_clickable(self._get_locator("daily_check_in_button")).click()
            logger.info("已点击每日签到按钮")
            sleep(2)
            screenshot_path = take_screenshot(self.driver, "task_center_daily_check_in")
            logger.info(f"每日签到完成，截图路径：{screenshot_path}")
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "task_center_daily_check_in_fail")
            logger.error(f"每日签到失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    # ------------------------------ 任务点击 ------------------------------

    def click_task_by_index(self, index: int = 0):
        """
        点击任务列表中的某一个任务
        :param index: 任务下标（从0开始）
        """
        try:
            logger.info(f"准备点击任务中心第 {index} 个任务")
            container = self.find_element(self._get_locator("task_list_container"))
            tasks = container.find_elements(By.XPATH, ".//*")
            if not tasks:
                raise RuntimeError("任务中心中未找到任何任务元素")

            if index < 0 or index >= len(tasks):
                raise IndexError(f"任务列表下标越界：index={index}, 总数={len(tasks)}")

            tasks[index].click()
            logger.info(f"已点击任务中心第 {index} 个任务（总共 {len(tasks)} 个）")
            sleep(2)
            screenshot_path = take_screenshot(self.driver, f"task_center_click_task_{index}")
            logger.info(f"点击任务成功，截图路径：{screenshot_path}")
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "task_center_click_task_fail")
            logger.error(f"点击任务失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    # ------------------------------ 领取奖励 ------------------------------

    def claim_reward_by_index(self, index: int = 0):
        """
        领取任务奖励：
        - 定位所有可领取奖励按钮
        - 点击指定下标的奖励按钮
        :param index: 奖励按钮下标（从0开始）
        """
        try:
            logger.info(f"准备领取任务中心第 {index} 个任务奖励")
            reward_buttons = self.find_elements(self._get_locator("reward_button"))
            if not reward_buttons:
                raise RuntimeError("任务中心中未找到任何可领取奖励按钮")

            if index < 0 or index >= len(reward_buttons):
                raise IndexError(f"领取奖励下标越界：index={index}, 总数={len(reward_buttons)}")

            reward_buttons[index].click()
            logger.info(f"已点击任务中心第 {index} 个奖励按钮（总共 {len(reward_buttons)} 个）")
            sleep(2)
            screenshot_path = take_screenshot(self.driver, f"task_center_claim_reward_{index}")
            logger.info(f"领取任务奖励成功，截图路径：{screenshot_path}")
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "task_center_claim_reward_fail")
            logger.error(f"领取任务奖励失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    # ------------------------------ 金币余额 ------------------------------

    def get_gold_balance(self) -> int:
        """
        获取当前金币余额文本，并转换为整数返回
        :return: 金币余额（int）
        """
        try:
            logger.info("开始获取任务中心金币余额")
            text = self.get_element_text(self._get_locator("gold_balance_text"))
            logger.info(f"当前金币余额文本：{text}")
            # 移除非数字字符（适配“1234金币”等展示）
            digits = "".join(ch for ch in text if ch.isdigit())
            if not digits:
                raise ValueError(f"金币余额文本中未解析到数字：{text}")

            balance = int(digits)
            logger.info(f"解析后的金币余额：{balance}")
            return balance
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "task_center_get_gold_balance_fail")
            logger.error(f"获取金币余额失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    # ------------------------------ 任务规则入口 ------------------------------

    def click_task_rule_entry(self):
        """点击任务规则入口"""
        try:
            logger.info("准备点击任务规则入口")
            self.wait_element_clickable(self._get_locator("task_rule_entry")).click()
            logger.info("已点击任务规则入口")
            sleep(2)
            screenshot_path = take_screenshot(self.driver, "task_center_rule_entry")
            logger.info(f"点击任务规则入口成功，截图路径：{screenshot_path}")
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "task_center_rule_entry_fail")
            logger.error(f"点击任务规则入口失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    # ------------------------------ 返回首页 ------------------------------

    def back_to_home(self):
        """
        从任务中心返回首页
        """
        from page.pages.home_page import HomePage

        self.back()
        sleep(2)
        return HomePage(self.driver)
