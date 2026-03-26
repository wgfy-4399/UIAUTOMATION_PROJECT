"""
Profile 页面 - 个人中心（My Profile / Mine）
"""
from page.base_page import BasePage
from utils.locator_utils import load_locators, get_locator_from_config
from utils.log_utils import global_logger as logger
from utils.screenshot_utils import take_screenshot
from time import sleep


class ProfilePage(BasePage):
    """个人中心页面"""

    def __init__(self, driver):
        super().__init__(driver)
        self._locators = load_locators("profile")
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

    def click_profile_tab(self):
        """点击底部 Profile Tab"""
        try:
            self.wait_element_clickable(self._get_locator("profile_tab")).click()
            logger.info("已点击 Profile Tab")
            sleep(2)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_profile_tab_fail")
            logger.error(f"点击 Profile Tab 失败，截图：{screenshot_path}，异常：{e}")
            raise e

    # ==================== 用户信息区域 ====================

    def click_avatar(self):
        """点击头像按钮"""
        try:
            self.wait_element_clickable(self._get_locator("avatar_button")).click()
            logger.info("已点击头像按钮")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_avatar_fail")
            logger.error(f"点击头像失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_login_button(self):
        """点击登录按钮"""
        try:
            self.wait_element_clickable(self._get_locator("login_button")).click()
            logger.info("已点击登录按钮")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_login_fail")
            logger.error(f"点击登录按钮失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def is_logged_in(self) -> bool:
        """检查用户是否已登录（通过检查登录按钮是否不存在）"""
        try:
            login_btn = self.find_element(self._get_locator("login_button"), timeout=3)
            return not login_btn.is_displayed()
        except:
            return True  # 登录按钮不存在，说明已登录

    def is_first_login_reward_visible(self) -> bool:
        """检查首次登录奖励提示是否可见"""
        try:
            element = self.find_element(self._get_locator("first_login_reward"), timeout=3)
            return element.is_displayed()
        except:
            return False

    # ==================== 金币/优惠券区域 ====================

    def get_coins_count(self) -> str:
        """获取金币数量"""
        try:
            element = self.find_element(self._get_locator("coins_count"))
            count = element.text.strip()
            logger.info(f"获取金币数量：{count}")
            return count
        except Exception as e:
            logger.error(f"获取金币数量失败：{e}")
            return None

    def get_vouchers_count(self) -> str:
        """获取优惠券数量"""
        try:
            element = self.find_element(self._get_locator("vouchers_count"))
            count = element.text.strip()
            logger.info(f"获取优惠券数量：{count}")
            return count
        except Exception as e:
            logger.error(f"获取优惠券数量失败：{e}")
            return None

    def click_coins_section(self):
        """点击金币区域"""
        try:
            self.wait_element_clickable(self._get_locator("coins_section")).click()
            logger.info("已点击金币区域")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_coins_section_fail")
            logger.error(f"点击金币区域失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_vouchers_section(self):
        """点击优惠券区域"""
        try:
            self.wait_element_clickable(self._get_locator("vouchers_section")).click()
            logger.info("已点击优惠券区域")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_vouchers_section_fail")
            logger.error(f"点击优惠券区域失败，截图：{screenshot_path}，异常：{e}")
            raise e

    # ==================== 购买/订阅 ====================

    def click_purchase_button(self):
        """点击购买按钮"""
        try:
            self.wait_element_clickable(self._get_locator("purchase_button")).click()
            logger.info("已点击购买按钮")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_purchase_fail")
            logger.error(f"点击购买按钮失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_subscribe_button(self):
        """点击订阅按钮"""
        try:
            self.wait_element_clickable(self._get_locator("subscribe_button")).click()
            logger.info("已点击订阅按钮")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_subscribe_fail")
            logger.error(f"点击订阅按钮失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def is_subscribe_discount_visible(self) -> bool:
        """检查订阅折扣信息是否可见"""
        try:
            element = self.find_element(self._get_locator("subscribe_discount"), timeout=3)
            return element.is_displayed()
        except:
            return False

    # ==================== 功能入口 ====================

    def click_rewards_entry(self):
        """点击 Rewards 入口"""
        try:
            self.wait_element_clickable(self._get_locator("rewards_entry")).click()
            logger.info("已点击 Rewards 入口")
            sleep(1)
            from page.pages.rewards_page import RewardsPage
            return RewardsPage(self.driver)
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_rewards_entry_fail")
            logger.error(f"点击 Rewards 入口失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_inbox_entry(self):
        """点击 Inbox 入口"""
        try:
            self.wait_element_clickable(self._get_locator("inbox_entry")).click()
            logger.info("已点击 Inbox 入口")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_inbox_entry_fail")
            logger.error(f"点击 Inbox 入口失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_become_writer_entry(self):
        """点击成为作者入口"""
        try:
            self.wait_element_clickable(self._get_locator("become_writer_entry")).click()
            logger.info("已点击成为作者入口")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_become_writer_fail")
            logger.error(f"点击成为作者入口失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_settings_entry(self):
        """点击设置入口"""
        try:
            self.wait_element_clickable(self._get_locator("settings_entry")).click()
            logger.info("已点击设置入口")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_settings_fail")
            logger.error(f"点击设置入口失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_feedback_entry(self):
        """点击反馈入口"""
        try:
            self.wait_element_clickable(self._get_locator("feedback_entry")).click()
            logger.info("已点击反馈入口")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_feedback_fail")
            logger.error(f"点击反馈入口失败，截图：{screenshot_path}，异常：{e}")
            raise e

    def click_about_entry(self):
        """点击关于入口"""
        try:
            self.wait_element_clickable(self._get_locator("about_entry")).click()
            logger.info("已点击关于入口")
            sleep(1)
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_about_fail")
            logger.error(f"点击关于入口失败，截图：{screenshot_path}，异常：{e}")
            raise e

    # ==================== 最近阅读 ====================

    def is_recent_read_card_visible(self) -> bool:
        """检查最近阅读卡片是否可见"""
        try:
            element = self.find_element(self._get_locator("recent_read_card"), timeout=3)
            return element.is_displayed()
        except:
            return False

    def close_recent_read_card(self):
        """关闭最近阅读卡片"""
        try:
            self.wait_element_clickable(self._get_locator("recent_read_close_button")).click()
            logger.info("已关闭最近阅读卡片")
            sleep(1)
            return self
        except Exception as e:
            logger.warning(f"关闭最近阅读卡片失败：{e}")
            return self

    def click_continue_read_button(self):
        """点击继续阅读按钮"""
        try:
            self.wait_element_clickable(self._get_locator("continue_read_button")).click()
            logger.info("已点击继续阅读按钮")
            sleep(1)
            from page.pages.reader_page import ReaderPage
            return ReaderPage(self.driver)
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_continue_read_fail")
            logger.error(f"点击继续阅读失败，截图：{screenshot_path}，异常：{e}")
            raise e

    # ==================== 页面验证 ====================

    def is_page_loaded(self) -> bool:
        """验证 Profile 页面是否已加载"""
        try:
            element = self.find_element(self._get_locator("profile_tab"), timeout=5)
            return element.is_displayed()
        except Exception as e:
            logger.error(f"验证 Profile 页面加载失败：{e}")
            return False

    def get_user_id(self) -> str:
        """获取用户ID"""
        try:
            element = self.find_element(self._get_locator("user_id"), timeout=3)
            user_id = element.get_attribute("name") or element.text
            logger.info(f"获取用户ID：{user_id}")
            return user_id
        except Exception as e:
            logger.error(f"获取用户ID失败：{e}")
            return None

    def has_login_button(self) -> bool:
        """检查登录按钮是否存在"""
        try:
            element = self.find_element(self._get_locator("login_button"), timeout=3)
            return element.is_displayed()
        except:
            return False

    def is_element_visible(self, locator_key: str) -> bool:
        """检查元素是否可见"""
        try:
            element = self.find_element(self._get_locator(locator_key), timeout=3)
            return element.is_displayed()
        except:
            return False

    def has_recent_read_card(self) -> bool:
        """检查是否有最近阅读卡片"""
        return self.is_recent_read_card_visible()

    def get_recent_read_book_title(self) -> str:
        """获取最近阅读书籍标题"""
        try:
            element = self.find_element(self._get_locator("recent_read_book_title"), timeout=3)
            title = element.text or element.get_attribute("name")
            logger.info(f"获取最近阅读书籍标题：{title}")
            return title
        except Exception as e:
            logger.error(f"获取最近阅读书籍标题失败：{e}")
            return None