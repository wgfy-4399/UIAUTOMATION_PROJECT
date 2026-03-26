from time import sleep
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)

from utils.driver_utils import get_driver, quit_driver
from utils.log_utils import global_logger as logger
from utils.screenshot_utils import take_screenshot


class BasePage:
    """页面基类：封装所有页面的通用操作"""

    def __init__(self, driver):
        """
        构造方法：初始化Driver、等待时间等
        :param driver: Appium Driver实例（从conftest.py夹具传入）
        """
        self.driver = driver
        # 全局显式等待时间（可通过配置文件读取，此处默认30秒）
        self.wait_time = 30
        # 轮询间隔（秒）
        self.poll_frequency = 0.5
        # 元素定位等待对象（复用 WebDriverWait，作为兜底等待）
        self.wait = WebDriverWait(
            driver=self.driver,
            timeout=self.wait_time,
            poll_frequency=self.poll_frequency,
            ignored_exceptions=[NoSuchElementException, StaleElementReferenceException],
        )

        # ------------------------------ 元素定位方法（核心）------------------------------

    def _get_locator(self, locator):
        """
        统一处理定位符：
        - 支持普通定位元组：(By.xxx, value)
        - 支持按应用差异化：{"main": (By.ID, "xxx"), "vest1": (By.XPATH, "xxx"), ...}
        - 支持按平台差异化：{"android": (...), "ios": (...)}
          （优先按平台匹配，其次按 appName 匹配，最后兜底 main/android）

        :param locator: 定位符（普通元组或差异化字典）
        :return: 最终定位符元组 (By.xxx, value)
        """
        # 当前应用（主包/马甲包）和平台
        current_app = self.driver.capabilities.get("appName", "main")
        platform = str(self.driver.capabilities.get("platformName", "android")).lower()

        if isinstance(locator, dict):
            # 1. 优先按平台键查找（android / ios）
            if platform in locator:
                value = locator[platform]
                if not isinstance(value, tuple) or len(value) != 2:
                    raise ValueError(
                        f"平台差异化定位符中 {platform} 对应的值必须是长度为2的元组，当前类型：{type(value)}"
                    )
                return value

            # 2. 其次按应用名称查找（main / vest1 / vest2 / vest3 / ...）
            if current_app in locator:
                value = locator[current_app]
                if not isinstance(value, tuple) or len(value) != 2:
                    raise ValueError(
                        f"差异化定位符中 {current_app} 对应的值必须是长度为2的元组，当前类型：{type(value)}"
                    )
                return value

            # 3. 兜底：尝试 main / android
            main_locator = locator.get("main") or locator.get("android")
            if not main_locator:
                raise ValueError(
                    f"未找到适配当前平台[{platform}]或应用[{current_app}]的定位符，"
                    f"且 main/android 兜底定位符缺失！当前定位符：{locator}"
                )
            if not isinstance(main_locator, tuple) or len(main_locator) != 2:
                raise ValueError(
                    f"兜底定位符（main/android）格式错误！必须是长度为2的元组，当前：{main_locator}"
                    f"（类型：{type(main_locator)}）"
                )
            logger.warning(
                f"未为平台[{platform}]或应用[{current_app}]配置专用定位符，"
                f"使用兜底定位符：{main_locator}"
            )
            return main_locator

        elif isinstance(locator, tuple) and len(locator) == 2:
            # 普通定位符（直接返回）
            return locator
        else:
            raise ValueError(
                "定位符格式错误！支持：\n"
                "- 元组: (By.xxx, value)\n"
                "- 字典: {appName/platform: (By.xxx, value)}"
            )

    # ------------------------------ 智能等待与重试封装 ------------------------------

    def _smart_wait_single(
        self,
        real_locator,
        total_timeout: Optional[float] = None,
        fast_first_phase: float = 5.0,
    ):
        """
        智能等待单个元素：
        - 先用较短时间快速等待，满足大部分“页面已加载好”的场景，减少长时间白等
        - 若快速等待失败，再用剩余时间做兜底等待
        """
        timeout = total_timeout or self.wait_time
        fast_phase = min(fast_first_phase, timeout)
        remain = max(timeout - fast_phase, 0)

        # 第一阶段：快速等待
        try:
            wait_fast = WebDriverWait(
                driver=self.driver,
                timeout=fast_phase,
                poll_frequency=self.poll_frequency,
                ignored_exceptions=[NoSuchElementException, StaleElementReferenceException],
            )
            return wait_fast.until(
                EC.visibility_of_element_located(real_locator),
                message=f"元素快速等待超时，进入兜底等待阶段：{real_locator}",
            )
        except TimeoutException:
            logger.info(f"元素快速等待阶段未找到，进入兜底等待：locator={real_locator}, remain={remain}s")

        # 第二阶段：兜底等待（只有在仍有剩余时间时才执行）
        if remain > 0:
            wait_remain = WebDriverWait(
                driver=self.driver,
                timeout=remain,
                poll_frequency=self.poll_frequency,
                ignored_exceptions=[NoSuchElementException, StaleElementReferenceException],
            )
            return wait_remain.until(
                EC.visibility_of_element_located(real_locator),
                message=f"元素定位超时！定位符：{real_locator}",
            )
        # 如果没有剩余时间，直接抛出 TimeoutException
        raise TimeoutException(f"元素定位超时（智能等待已耗尽）！定位符：{real_locator}")

    def _retry_locate_single(self, real_locator, max_retry: int = 2, timeout: Optional[float] = None):
        """
        元素定位重试封装：
        - 对于 NoSuchElement / StaleElement，最多做多次重试
        - 每次失败之间加入微小等待，提升稳定性
        """
        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= max_retry:
            try:
                attempt += 1
                logger.info(f"开始定位元素：{real_locator}，第 {attempt}/{max_retry + 1} 次尝试")
                return self._smart_wait_single(real_locator, total_timeout=timeout)
            except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e:
                last_exc = e
                if attempt > max_retry:
                    break
                logger.warning(
                    f"元素定位失败（第 {attempt}/{max_retry + 1} 次）：{e!r}，"
                    f"稍后重试，locator={real_locator}"
                )
                sleep(0.5)
        # 所有重试失败
        assert last_exc is not None
        raise last_exc

    def find_element(self, locator, timeout: Optional[float] = None):
        """
        查找单个元素（智能显式等待 + 差异化定位 + 重试）
        :param locator: 定位符（普通/差异化）
        :param timeout: 自定义超时时间（秒），None 使用全局默认
        :return: WebElement 元素对象
        """
        try:
            # 处理定位符（适配多包）
            real_locator = self._get_locator(locator)
            logger.info(f"查找元素：定位方式={real_locator[0]}, 定位值={real_locator[1]}")

            element = self._retry_locate_single(real_locator, timeout=timeout)
            return element  # type: ignore
        except TimeoutException as e:
            # 定位超时：截图+日志+抛异常
            screenshot_path = take_screenshot(self.driver, "element_locator_fail")
            logger.error(f"元素定位失败！截图路径：{screenshot_path}\n异常信息：{str(e)}")
            raise e
        except Exception as e:
            logger.error(f"元素定位异常！异常信息：{str(e)}")
            raise e

    def find_elements(self, locator, timeout: Optional[float] = None):
        """
        查找多个元素（智能等待）
        :param locator: 定位符（普通/差异化）
        :param timeout: 自定义超时时间（秒），None 使用全局默认
        :return: 元素列表（空列表表示未找到）
        """
        total_timeout = timeout or self.wait_time
        try:
            real_locator = self._get_locator(locator)
            logger.info(f"查找多个元素：定位方式={real_locator[0]}, 定位值={real_locator[1]}")

            fast_phase = min(3.0, total_timeout)
            remain = max(total_timeout - fast_phase, 0)

            # 第一阶段：快速尝试获取所有元素
            try:
                wait_fast = WebDriverWait(
                    driver=self.driver,
                    timeout=fast_phase,
                    poll_frequency=self.poll_frequency,
                    ignored_exceptions=[NoSuchElementException, StaleElementReferenceException],
                )
                elements = wait_fast.until(
                    EC.presence_of_all_elements_located(real_locator),
                    message=f"多个元素快速定位超时，进入兜底等待：{real_locator}",
                )
            except TimeoutException:
                logger.info(
                    f"多个元素快速等待阶段未找到，进入兜底等待：locator={real_locator}, remain={remain}s"
                )
                if remain <= 0:
                    raise
                wait_remain = WebDriverWait(
                    driver=self.driver,
                    timeout=remain,
                    poll_frequency=self.poll_frequency,
                    ignored_exceptions=[NoSuchElementException, StaleElementReferenceException],
                )
                elements = wait_remain.until(
                    EC.presence_of_all_elements_located(real_locator),
                    message=f"多个元素定位超时！定位符：{real_locator}",
                )

            logger.info(f"找到 {len(elements)} 个匹配元素")
            return elements  # 直接返回 WebDriverWait 返回的 List[WebElement]
        except TimeoutException:
            # 未找到元素时返回空列表（不抛异常，由业务层处理）
            logger.warning(f"未找到匹配元素：{real_locator}")
            return []
        except Exception as e:
            logger.error(f"多个元素定位异常！异常信息：{str(e)}")
            raise e

    def wait_element_clickable(self, locator, timeout: Optional[float] = None):
        """仅等待元素「可点击」（内置元素定位的核心：比仅可见更精准）"""
        try:
            real_locator = self._get_locator(locator)
            total_timeout = timeout or self.wait_time
            wait_clickable = WebDriverWait(
                driver=self.driver,
                timeout=total_timeout,
                poll_frequency=self.poll_frequency,
                ignored_exceptions=[
                    NoSuchElementException,
                    StaleElementReferenceException,
                ],
            )
            return wait_clickable.until(
                EC.element_to_be_clickable(real_locator),  # 使用处理后的定位符
                message=f"元素{real_locator}等待可点击超时",
            )
        except TimeoutException as e:
            raise RuntimeError(f"元素不可点击：{str(e)}")

    def click_element(self, locator, timeout: Optional[float] = None):
        """
        点击元素（支持自定义超时时间 + 重试 + 兜底坐标点击）
        :param locator: 定位符
        :param timeout: 自定义超时时间（None 则使用全局默认）
        """
        total_timeout = timeout or self.wait_time

        # 先等待元素可点击
        elem = self.wait_element_clickable(locator, timeout=total_timeout)

        # 1. 校验元素状态
        if not elem.is_displayed():
            raise RuntimeError(f"元素{locator}不可见！")
        if not elem.is_enabled():
            raise RuntimeError(f"元素{locator}被禁用！")

        # 2. 原生点击 + 小次数重试
        max_retry = 2
        for attempt in range(1, max_retry + 2):
            try:
                logger.info(f"尝试原生点击元素：{locator}，第 {attempt}/{max_retry + 1} 次")
                elem.click()
                sleep(1)  # 等待点击响应
                return "原生点击成功"
            except (ElementClickInterceptedException, StaleElementReferenceException) as e:
                if attempt > max_retry:
                    logger.warning(
                        f"原生点击多次失败（第 {attempt} 次），进入坐标点击兜底。异常：{e!r}"
                    )
                    break
                logger.warning(
                    f"原生点击失败（第 {attempt}/{max_retry + 1} 次）：{e!r}，"
                    f"短暂等待后重试点击"
                )
                sleep(0.5)
                # 再次确保元素处于可点击状态
                elem = self.wait_element_clickable(locator, timeout=2)
            except Exception as e:
                logger.error(f"点击元素出现未知异常：{e!r}")
                break

        # 3. 原生点击失败 → 坐标点击兜底（适配不同分辨率）
        try:
            logger.info(f"原生点击失败，尝试坐标点击兜底：{locator}")
            center_x = elem.location["x"] + elem.size["width"] / 2
            center_y = elem.location["y"] + elem.size["height"] / 2

            # 优先使用 Appium 的 tap 接口（如存在）
            if hasattr(self.driver, "tap"):
                # type: ignore[attr-defined]
                self.driver.tap([(center_x, center_y)], 100)  # 轻点 100ms
            else:
                # 兜底使用 swipe 模拟轻点（起止坐标一致，duration 很短）
                self.driver.swipe(
                    start_x=center_x,
                    start_y=center_y,
                    end_x=center_x,
                    end_y=center_y,
                    duration=100,
                )
            sleep(1)
            return "坐标点击成功"
        finally:
            # 保持 BasePage 兼容性：不修改外部等待配置
            if timeout:
                self.wait.timeout = self.wait_time

    def input_text(self, locator, text, clear_first=True):
        """
        输入文本（支持先清空输入框）
        :param locator: 定位符
        :param text: 输入文本
        :param clear_first: 是否先清空（默认True）
        """
        try:
            element = self.find_element(locator)
            if clear_first:
                element.clear()
                logger.info(f"清空元素输入框：{locator}")

            element.send_keys(text)
            logger.info(f"输入文本：{text}，元素：{locator}")
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "element_input_fail")
            logger.error(f"输入文本失败！截图路径：{screenshot_path}\n异常信息：{str(e)}")
            raise e

    def get_element_text(self, locator):
        """
        获取元素文本
        :return: 元素文本内容
        """
        try:
            element = self.find_element(locator)
            text = element.text.strip()
            logger.info(f"获取元素文本：{text}，元素：{locator}")
            return text
        except Exception as e:
            logger.error(f"获取元素文本失败！异常信息：{str(e)}")
            raise e

    def get_element_attribute(self, locator, attribute):
        """
        获取元素属性（如content-desc、resource-id）
        :param attribute: 属性名（如"contentDescription"、"resourceId"）
        :return: 属性值
        """
        try:
            element = self.find_element(locator)
            value = element.get_attribute(attribute)
            logger.info(f"获取元素属性：{attribute}={value}，元素：{locator}")
            return value
        except Exception as e:
            logger.error(f"获取元素属性失败！异常信息：{str(e)}")
            raise e

    def swipe_up(self, duration=300, scale=0.8, anchor_locator=None):
        """
        向上滑动（从下到上）
        :param duration: 滑动时长（建议200-500ms）
        :param scale: 滑动比例（建议0.7-0.8，避免0.9极端值）
        :param anchor_locator: 锚点元素定位符
        """
        if anchor_locator:
            print(f"等待目标页面锚点元素：{anchor_locator}")
            self.wait_element_clickable(anchor_locator)
            sleep(0.5)

        screen_size = self.driver.get_window_size()
        width = screen_size["width"]
        height = screen_size["height"]

        # 不同分辨率下使用百分比计算，自动适配全面屏/刘海屏等机型
        start_x = width * 0.5
        # 避开底部导航栏和顶部状态栏，使用相对安全区
        start_y = height * min(max(scale, 0.5), 0.9)
        end_y = height * max(0.1, 1 - scale)

        print(f"滑动坐标：start({start_x},{start_y}) → end({start_x},{end_y})")

        # 使用 swipe，内部会根据分辨率做适配
        self.driver.swipe(
            start_x=start_x,
            start_y=start_y,
            end_x=start_x,
            end_y=end_y,
            duration=duration,
        )
        sleep(0.5)
        print(f"向上滑动完成：时长{duration}ms，比例{scale}")

    def swipe_down(self, duration=300, scale=0.8, anchor_locator=None):
        """
        向上滑动（从上到下）
        :param duration: 滑动时长（建议200-500ms）
        :param scale: 滑动比例（建议0.7-0.8，避免0.9极端值）
        :param anchor_locator: 锚点元素定位符
        """
        if anchor_locator:
            print(f"等待目标页面锚点元素：{anchor_locator}")
            self.wait_element_clickable(anchor_locator)
            sleep(0.5)

        screen_size = self.driver.get_window_size()
        width = screen_size["width"]
        height = screen_size["height"]

        start_x = width * 0.5
        start_y = height * max(0.1, 1 - scale)
        end_y = height * min(max(scale, 0.5), 0.9)

        print(f"滑动坐标：start({start_x},{start_y}) → end({start_x},{end_y})")

        self.driver.swipe(
            start_x=start_x,
            start_y=start_y,
            end_x=start_x,
            end_y=end_y,
            duration=duration,
        )
        sleep(0.5)
        print(f"向下滑动完成：时长{duration}ms，比例{scale}")

    def back(self):
        """返回上一页"""
        self.driver.back()
        logger.info("执行返回操作")


    def get_page_source(self):
        """获取页面源码（用于调试）"""
        source = self.driver.page_source
        logger.info("获取页面源码成功")
        return source

    def switch_to_webview(self):
        """切换到Chrome的WebView上下文（适配所有Chrome上下文名称变体）"""
        import time
        max_retry = 3  # 重试3次
        retry_count = 0
        webview_ctx = None

        while retry_count < max_retry:
            try:
                # 1. 等待15秒（给Chrome足够时间初始化WebView）
                self.wait.until(
                    lambda d: len([ctx for ctx in d.contexts if "WEBVIEW" in ctx]) > 0,
                    message=f"超时15秒：未找到任何WEBVIEW上下文（重试{retry_count + 1}/{max_retry}）"
                )

                # 2. 适配Chrome的所有上下文变体（不硬编码完整包名）
                # 匹配包含"chrome"的WEBVIEW上下文（不区分大小写）
                webview_ctx_list = [
                    ctx for ctx in self.driver.contexts
                    if "WEBVIEW" in ctx and "chrome" in ctx.lower()
                ]

                if webview_ctx_list:
                    webview_ctx = webview_ctx_list[0]
                    break  # 找到则退出重试

                # 若没找到Chrome专属的，就用第一个WEBVIEW上下文（兜底）
                all_webview = [ctx for ctx in self.driver.contexts if "WEBVIEW" in ctx]
                if all_webview:
                    webview_ctx = all_webview[0]
                    print(f"⚠️ 未找到Chrome专属WebView，使用兜底上下文：{webview_ctx}")
                    break

                # 没找到则重试
                retry_count += 1
                time.sleep(2)
                print(f"🔄 未找到Chrome WebView上下文，重试第{retry_count}次...")

            except Exception as e:
                retry_count += 1
                time.sleep(2)
                print(f"🔄 切换上下文失败，重试第{retry_count}次：{e}")

        # 最终判断并切换
        if not webview_ctx:
            raise RuntimeError(
                f"重试{max_retry}次后仍未找到WebView上下文！\n"
                f"当前所有上下文：{self.driver.contexts}"
            )

        self.driver.switch_to.context(webview_ctx)
        print(f"✅ 成功切换到Chrome WebView上下文：{webview_ctx}")
        print(f"📌 Chrome所有上下文列表：{self.driver.contexts}")

    def switch_to_native(self):
        """切换到原生上下文（处理APP）"""
        self.driver.switch_to.context("NATIVE_APP")
        print("✅ 切换到原生上下文")



if __name__ == '__main__':

    driver = get_driver("android", "vest1")
    page = BasePage(driver)
    page.find_element((By.XPATH, "//*[@id='content']")).click()







