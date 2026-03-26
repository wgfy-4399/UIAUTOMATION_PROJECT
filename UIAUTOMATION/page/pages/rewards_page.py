"""
Rewards 页面 - 任务中心/个人中心
"""
from page.base_page import BasePage
from utils.locator_utils import load_locators, get_locator_from_config
from utils.log_utils import global_logger as logger
from utils.screenshot_utils import take_screenshot
from time import sleep


class RewardsPage(BasePage):
    """Rewards/任务中心页面"""

    def __init__(self, driver):
        super().__init__(driver)
        self._locators = load_locators("rewards")
        self._platform = str(self.driver.capabilities.get("platformName", "ios")).lower()
        self._app_name = self.driver.capabilities.get("appName", "main")

    def _get_locator(self, element_key: str):
        """获取定位符"""
        if isinstance(element_key, (tuple, dict)):
            return super()._get_locator(element_key)
        return get_locator_from_config(
            self._locators, element_key, self._platform, self._app_name
        )

    # ==================== 导航 ====================

    def close_checkin_popup(self):
        """关闭签到弹窗（如果存在）"""
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
            pass
        return False

    def click_rewards_tab(self):
        """点击底部 Rewards Tab"""
        try:
            # 先尝试等待可点击，如果失败则直接点击
            try:
                element = self.wait_element_clickable(self._get_locator("rewards_tab"))
            except:
                # 如果等待可点击失败，直接查找并点击
                element = self.find_element(self._get_locator("rewards_tab"))
            element.click()
            logger.info("已点击 Rewards Tab")
            sleep(2)

            # 尝试关闭可能出现的签到弹窗
            self.close_checkin_popup()

            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_rewards_tab_fail")
            logger.error(f"点击 Rewards Tab 失败，截图：{screenshot_path}，异常：{e}")
            raise e

    # ==================== 页面标题 ====================

    def get_page_title(self):
        """获取页面标题"""
        try:
            element = self.find_element(self._get_locator("rewards_title"))
            return element.text
        except Exception as e:
            logger.error(f"获取页面标题失败：{e}")
            return None

    # ==================== 每日任务区域 ====================

    def get_total_rewards(self):
        """获取总奖励金额"""
        try:
            element = self.find_element(self._get_locator("total_rewards_text"))
            text = element.text
            # 解析文本: "Total Rewards:5469 Vouchers, Refresh every day."
            if "Total Rewards:" in text:
                rewards = text.split("Total Rewards:")[1].split(" ")[0]
                logger.info(f"获取总奖励：{rewards} Vouchers")
                return rewards
            return None
        except Exception as e:
            logger.error(f"获取总奖励失败：{e}")
            return None

    def get_countdown_timer(self):
        """获取倒计时时间"""
        try:
            element = self.find_element(self._get_locator("countdown_timer"))
            return element.text.strip()
        except Exception as e:
            logger.error(f"获取倒计时失败：{e}")
            return None

    # ==================== 任务操作 ====================

    def click_task_go_button(self, task_name: str = None):
        """
        点击任务的 GO 按钮

        :param task_name: 任务名称（可选），用于日志记录
        :return: self
        """
        try:
            go_button = self.wait_element_clickable(self._get_locator("go_button"))
            go_button.click()
            logger.info(f"已点击任务的 GO 按钮{'（' + task_name + '）' if task_name else ''}")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_go_button_fail")
            logger.error(f"点击 GO 按钮失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_play_30_task(self):
        """点击 'Play for 30 seconds' 任务的 GO 按钮"""
        return self.click_task_go_button("Play for 30 seconds")

    def click_facebook_task(self):
        """点击 'Log in with Facebook' 任务的 GO 按钮"""
        return self.click_task_go_button("Log in with Facebook")

    def click_topup_task(self):
        """点击 'Top up' 任务的 GO 按钮"""
        return self.click_task_go_button("Top up")

    def click_checkin_task(self):
        """点击签到任务的 GO 按钮"""
        return self.click_task_go_button("Check-in")

    # ==================== 任务状态检查 ====================

    def is_task_visible(self, task_name: str) -> bool:
        """
        检查任务是否可见

        :param task_name: 任务名称
        :return: True/False
        """
        try:
            locator_key = f"task_{task_name}_title"
            element = self.find_element(self._get_locator(locator_key))
            is_visible = element.is_displayed()
            logger.info(f"任务 '{task_name}' 可见：{is_visible}")
            return is_visible
        except Exception as e:
            logger.warning(f"检查任务 '{task_name}' 可见性失败：{e}")
            return False

    def get_task_progress(self, task_name: str) -> str:
        """
        获取任务进度

        :param task_name: 任务名称
        :return: 进度文本，如 "0/6"
        """
        try:
            locator_key = f"task_{task_name}_title"
            element = self.find_element(self._get_locator(locator_key))
            text = element.text
            # 从文本中提取进度，如 "Play for 30 seconds(0/6)" -> "0/6"
            if "(" in text and ")" in text:
                progress = text.split("(")[1].split(")")[0]
                logger.info(f"任务 '{task_name}' 进度：{progress}")
                return progress
            return text
        except Exception as e:
            logger.error(f"获取任务 '{task_name}' 进度失败：{e}")
            return None

    def get_task_reward(self, task_name: str) -> int:
        """
        获取任务奖励金额

        :param task_name: 任务名称
        :return: 奖励金额
        """
        try:
            locator_key = f"task_{task_name}_reward"
            element = self.find_element(self._get_locator(locator_key))
            reward_text = element.text
            reward = int(reward_text)
            logger.info(f"任务 '{task_name}' 奖励：{reward} Vouchers")
            return reward
        except Exception as e:
            logger.error(f"获取任务 '{task_name}' 奖励失败：{e}")
            return 0

    # ==================== 页面验证 ====================

    def is_page_loaded(self) -> bool:
        """验证 Rewards 页面是否已加载"""
        try:
            element = self.find_element(self._get_locator("rewards_title"))
            return element.is_displayed()
        except Exception as e:
            logger.error(f"验证 Rewards 页面加载失败：{e}")
            return False
