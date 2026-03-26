from time import sleep

from selenium.webdriver.common.by import By

from page.base_page import BasePage
from utils.locator_utils import load_locators, get_locator_from_config
from utils.log_utils import global_logger as logger
from utils.screenshot_utils import take_screenshot


class RechargePage(BasePage):
    """
    充值中心公共页面对象
    - 展示充值档位列表与价格
    - 支付渠道选择
    - 立即支付操作
    - 展示当前余额与充值记录入口
    """

    def __init__(self, driver):
        super().__init__(driver)

        # 这里暂未拆到 YAML，仅保留原有差异化字典结构
        self.package_list_container_locator = {
            "main": (By.ID, "com.kw.literie:id/rv_recharge_package"),
            "vest1": (By.ID, "com.kw.literie.vest1:id/rv_recharge_package"),
            "vest2": (By.ID, "com.kw.literie.vest2:id/rv_recharge_package"),
            "vest3": (By.ID, "com.kw.literie.vest3:id/rv_recharge_package"),
        }
        self.package_price_text_locator = {
            "main": (By.ID, "com.kw.literie:id/tv_package_price"),
            "vest1": (By.ID, "com.kw.literie.vest1:id/tv_package_price"),
            "vest2": (By.ID, "com.kw.literie.vest2:id/tv_package_price"),
            "vest3": (By.ID, "com.kw.literie.vest3:id/tv_package_price"),
        }
        self.payment_channel_list_locator = {
            "main": (By.ID, "com.kw.literie:id/rv_payment_channel"),
            "vest1": (By.ID, "com.kw.literie.vest1:id/rv_payment_channel"),
            "vest2": (By.ID, "com.kw.literie.vest2:id/rv_payment_channel"),
            "vest3": (By.ID, "com.kw.literie.vest3:id/rv_payment_channel"),
        }
        self.pay_now_button_locator = {
            "main": (By.ID, "com.kw.literie:id/btn_pay_now"),
            "vest1": (By.ID, "com.kw.literie.vest1:id/btn_pay_now"),
            "vest2": (By.ID, "com.kw.literie.vest2:id/btn_pay_now"),
            "vest3": (By.ID, "com.kw.literie.vest3:id/btn_pay_now"),
        }
        self.balance_text_locator = {
            "main": (By.ID, "com.kw.literie:id/tv_balance"),
            "vest1": (By.ID, "com.kw.literie.vest1:id/tv_balance"),
            "vest2": (By.ID, "com.kw.literie.vest2:id/tv_balance"),
            "vest3": (By.ID, "com.kw.literie.vest3:id/tv_balance"),
        }
        self.recharge_record_entry_locator = {
            "main": (By.ID, "com.kw.literie:id/tv_recharge_record"),
            "vest1": (By.ID, "com.kw.literie.vest1:id/tv_recharge_record"),
            "vest2": (By.ID, "com.kw.literie.vest2:id/tv_recharge_record"),
            "vest3": (By.ID, "com.kw.literie.vest3:id/tv_recharge_record"),
        }
        self.payment_popup_locator = {
            "main": (By.ID, "com.kw.literie:id/layout_payment_dialog"),
            "vest1": (By.ID, "com.kw.literie.vest1:id/layout_payment_dialog"),
            "vest2": (By.ID, "com.kw.literie.vest2:id/layout_payment_dialog"),
            "vest3": (By.ID, "com.kw.literie.vest3:id/layout_payment_dialog"),
        }

    # ------------------------------ 充值档位选择 ------------------------------

    def select_recharge_package_by_index(self, index: int = 0):
        """
        选择充值档位列表中的某一个档位
        :param index: 档位下标（从0开始）
        """
        try:
            logger.info(f"准备选择第 {index} 个充值档位")
            container = self.find_element(self.package_list_container_locator)
            packages = container.find_elements(By.XPATH, ".//*")
            if not packages:
                raise RuntimeError("充值页面中未找到任何充值档位元素")

            if index < 0 or index >= len(packages):
                raise IndexError(f"充值档位下标越界：index={index}, 总数={len(packages)}")

            packages[index].click()
            logger.info(f"已选择第 {index} 个充值档位（总共 {len(packages)} 个）")
            sleep(1)
            screenshot_path = take_screenshot(self.driver, f"recharge_select_package_{index}")
            logger.info(f"选择充值档位成功，截图路径：{screenshot_path}")
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "recharge_select_package_fail")
            logger.error(f"选择充值档位失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    def get_package_price_by_index(self, index: int = 0) -> str:
        """
        获取指定充值档位的价格文本
        :param index: 档位下标（从0开始）
        :return: 价格文本（原样返回）
        """
        try:
            logger.info(f"开始获取第 {index} 个充值档位的价格")
            container = self.find_element(self.package_list_container_locator)
            packages = container.find_elements(By.XPATH, ".//*")
            if not packages:
                raise RuntimeError("充值页面中未找到任何充值档位元素")

            if index < 0 or index >= len(packages):
                raise IndexError(f"充值档位下标越界：index={index}, 总数={len(packages)}")

            price_elements = packages[index].find_elements(*self.package_price_text_locator["main"])
            if not price_elements:
                raise RuntimeError(f"未在第 {index} 个充值档位下找到价格元素")

            price_text = price_elements[0].text.strip()
            logger.info(f"第 {index} 个充值档位价格文本：{price_text}")
            return price_text
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "recharge_get_package_price_fail")
            logger.error(f"获取充值档位价格失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    # ------------------------------ 支付渠道选择 ------------------------------

    def select_payment_channel(self, channel_identifier=0):
        """
        选择支付渠道：
        - 支持通过下标选择（int，下标从0开始）
        - 也支持通过名称选择（str），常见海外支付方式：
          Google / Google Pay、PayPal、Stripe、Apple、Apple ID 等

        :param channel_identifier: 渠道标识（int下标 或 str名称）
        """
        try:
            container = self.find_element(self.payment_channel_list_locator)
            channels = container.find_elements(By.XPATH, ".//*")
            if not channels:
                raise RuntimeError("充值页面中未找到任何支付渠道元素")

            if isinstance(channel_identifier, str):
                target_name = channel_identifier.strip().lower()
                logger.info(f"准备按名称选择支付渠道：{target_name}")

                keyword_map = {
                    "google": ["google", "google pay", "gpay"],
                    "paypal": ["paypal"],
                    "stripe": ["stripe"],
                    "apple": ["apple", "apple id", "apple pay", "app store"],
                }

                keywords = []
                for key, alias_list in keyword_map.items():
                    if target_name == key or target_name in alias_list:
                        keywords.extend(alias_list)
                        keywords.append(key)
                if not keywords:
                    keywords = [target_name]

                selected_index = None
                for idx, elem in enumerate(channels):
                    text = (elem.text or "").strip().lower()
                    try:
                        content_desc = (elem.get_attribute("contentDescription") or "").strip().lower()
                    except Exception:
                        content_desc = ""

                    for kw in keywords:
                        if kw in text or kw in content_desc:
                            selected_index = idx
                            break
                    if selected_index is not None:
                        break

                if selected_index is None:
                    raise RuntimeError(f"未在支付渠道列表中找到匹配名称：{channel_identifier}")

                channels[selected_index].click()
                logger.info(
                    f"已按名称选择支付渠道：{channel_identifier}（索引={selected_index}，总数={len(channels)}）"
                )
                sleep(1)
                screenshot_path = take_screenshot(self.driver, f"recharge_select_channel_name_{target_name}")
                logger.info(f"按名称选择支付渠道成功，截图路径：{screenshot_path}")
                return self

            if not isinstance(channel_identifier, int):
                raise TypeError(f"支付渠道标识类型错误，应为 int 或 str，当前：{type(channel_identifier)}")

            index = channel_identifier
            logger.info(f"准备按下标选择第 {index} 个支付渠道")
            if index < 0 or index >= len(channels):
                raise IndexError(f"支付渠道下标越界：index={index}, 总数={len(channels)}")

            channels[index].click()
            logger.info(f"已按下标选择第 {index} 个支付渠道（总共 {len(channels)} 个）")
            sleep(1)
            screenshot_path = take_screenshot(self.driver, f"recharge_select_channel_index_{index}")
            logger.info(f"按下标选择支付渠道成功，截图路径：{screenshot_path}")
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "recharge_select_channel_fail")
            logger.error(f"选择支付渠道失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    # ------------------------------ 立即支付 ------------------------------

    def click_pay_now(self):
        """
        点击立即支付按钮
        - 测试环境仅用于唤起支付弹窗，不进行真实支付
        """
        try:
            logger.info("准备点击充值页面【立即支付】按钮")
            self.wait_element_clickable(self.pay_now_button_locator).click()
            logger.info("已点击【立即支付】按钮")
            sleep(2)
            screenshot_path = take_screenshot(self.driver, "recharge_click_pay_now")
            logger.info(f"点击立即支付成功，截图路径：{screenshot_path}")
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "recharge_click_pay_now_fail")
            logger.error(f"点击立即支付失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    def is_payment_popup_displayed(self) -> bool:
        """
        校验支付弹窗是否已唤起
        :return: True/False
        """
        try:
            logger.info("开始校验支付弹窗是否展示")
            elements = self.find_elements(self.payment_popup_locator)
            displayed = any(elem.is_displayed() for elem in elements)
            logger.info(f"支付弹窗展示状态：{displayed}")
            if displayed:
                screenshot_path = take_screenshot(self.driver, "recharge_payment_popup_displayed")
                logger.info(f"支付弹窗已展示，截图路径：{screenshot_path}")
            return displayed
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "recharge_payment_popup_check_fail")
            logger.error(f"校验支付弹窗失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    # ------------------------------ 当前余额 ------------------------------

    def get_current_balance(self) -> int:
        """
        获取当前余额文本，并转换为整数返回
        :return: 当前余额（int）
        """
        try:
            logger.info("开始获取充值页面当前余额")
            text = self.get_element_text(self.balance_text_locator)
            logger.info(f"当前余额文本：{text}")
            digits = "".join(ch for ch in text if ch.isdigit())
            if not digits:
                raise ValueError(f"当前余额文本中未解析到数字：{text}")

            balance = int(digits)
            logger.info(f"解析后的当前余额：{balance}")
            return balance
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "recharge_get_balance_fail")
            logger.error(f"获取当前余额失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    # ------------------------------ 充值记录入口 ------------------------------

    def click_recharge_record_entry(self):
        """点击充值记录入口"""
        try:
            logger.info("准备点击充值记录入口")
            self.wait_element_clickable(self.recharge_record_entry_locator).click()
            logger.info("已点击充值记录入口")
            sleep(2)
            screenshot_path = take_screenshot(self.driver, "recharge_record_entry")
            logger.info(f"点击充值记录入口成功，截图路径：{screenshot_path}")
            return self
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "recharge_record_entry_fail")
            logger.error(f"点击充值记录入口失败，截图路径：{screenshot_path}，异常：{str(e)}")
            raise e

    # ------------------------------ 返回首页 ------------------------------

    def back_to_home(self):
        """
        从充值页面返回首页
        """
        from page.pages.home_page import HomePage

        self.back()
        sleep(2)
        return HomePage(self.driver)
