from typing import Any

from appium.webdriver.webdriver import WebDriver
from appium.webdriver.webelement import WebElement

from utils.log_utils import global_logger as logger
from utils.screenshot_utils import take_screenshot


def _validate_driver(driver: WebDriver) -> None:
    """简单校验 Driver 实例是否有效（适配Android/iOS双端）"""
    if driver is None:
        raise ValueError("Appium Driver 实例不能为空！")
    required_methods = ["save_screenshot", "find_element"]
    for method in required_methods:
        if not hasattr(driver, method):
            raise AttributeError(f"Driver 实例缺少核心方法：{method}")


def _validate_element(element: WebElement) -> None:
    """简单校验元素实例是否有效（兼容Android/iOS）"""
    if element is None:
        raise ValueError("传入的元素对象不能为空！")
    if not isinstance(element, WebElement):
        raise TypeError(f"传入的对象不是有效的 WebElement 类型：{type(element)}")


def assert_element_exist(driver: WebDriver, element: WebElement, scene: str = "assert_element_exist") -> None:
    """
    断言元素存在且可见
    :param driver: Appium Driver 实例
    :param element: Appium WebElement 实例
    :param scene: 断言场景描述（用于截图命名）
    """
    _validate_driver(driver)
    try:
        _validate_element(element)
        displayed = element.is_displayed()
        logger.info(f"断言元素是否存在且可见：结果={displayed}，场景={scene}")
        if not displayed:
            screenshot_path = take_screenshot(driver, f"{scene}_not_displayed")
            logger.error(f"元素不可见！场景：{scene}，已自动截图：{screenshot_path}")
            raise AssertionError(f"元素不可见！场景：{scene}")
    except Exception as e:
        # 兜底截图
        try:
            screenshot_path = take_screenshot(driver, f"{scene}_assert_element_exist_exception")
            logger.error(f"断言元素存在失败，已自动截图：{screenshot_path}，异常：{str(e)}")
        except Exception as ss_e:
            logger.error(f"断言元素存在失败，且截图失败：{str(ss_e)}；原始异常：{str(e)}")
        raise


def assert_text_equal(driver: WebDriver, actual: Any, expected: Any, scene: str = "assert_text_equal") -> None:
    """
    断言文本完全相等
    :param driver: Appium Driver 实例
    :param actual: 实际文本（将转换为字符串）
    :param expected: 期望文本（将转换为字符串）
    :param scene: 断言场景描述
    """
    _validate_driver(driver)
    try:
        actual_str = "" if actual is None else str(actual).strip()
        expected_str = "" if expected is None else str(expected).strip()
        logger.info(f"断言文本相等：actual='{actual_str}', expected='{expected_str}'，场景={scene}")

        if actual_str != expected_str:
            screenshot_path = take_screenshot(driver, f"{scene}_text_not_equal")
            logger.error(
                f"文本断言失败！actual='{actual_str}', expected='{expected_str}'，"
                f"场景：{scene}，截图：{screenshot_path}"
            )
            raise AssertionError(f"文本不相等！actual='{actual_str}', expected='{expected_str}'")
    except Exception as e:
        try:
            screenshot_path = take_screenshot(driver, f"{scene}_assert_text_equal_exception")
            logger.error(f"断言文本相等异常，已自动截图：{screenshot_path}，异常：{str(e)}")
        except Exception as ss_e:
            logger.error(f"断言文本相等异常，且截图失败：{str(ss_e)}；原始异常：{str(e)}")
        raise


def assert_text_contains(driver: WebDriver, actual: Any, expected_substring: Any,
                         scene: str = "assert_text_contains") -> None:
    """
    断言实际文本包含期望子串
    :param driver: Appium Driver 实例
    :param actual: 实际文本（将转换为字符串）
    :param expected_substring: 期望包含的子串（将转换为字符串）
    :param scene: 断言场景描述
    """
    _validate_driver(driver)
    try:
        actual_str = "" if actual is None else str(actual)
        expected_str = "" if expected_substring is None else str(expected_substring)
        logger.info(f"断言文本包含：actual='{actual_str}', expected_substring='{expected_str}'，场景={scene}")

        if expected_str not in actual_str:
            screenshot_path = take_screenshot(driver, f"{scene}_text_not_contains")
            logger.error(
                f"文本包含断言失败！actual='{actual_str}', expected_substring='{expected_str}'，"
                f"场景：{scene}，截图：{screenshot_path}"
            )
            raise AssertionError(f"文本未包含期望子串！actual='{actual_str}', expected_substring='{expected_str}'")
    except Exception as e:
        try:
            screenshot_path = take_screenshot(driver, f"{scene}_assert_text_contains_exception")
            logger.error(f"断言文本包含异常，已自动截图：{screenshot_path}，异常：{str(e)}")
        except Exception as ss_e:
            logger.error(f"断言文本包含异常，且截图失败：{str(ss_e)}；原始异常：{str(e)}")
        raise


def assert_number_greater_than(
        driver: WebDriver,
        actual: Any,
        threshold: Any,
        scene: str = "assert_number_greater_than"
) -> None:
    """
    断言数值大于指定阈值（支持字符串数字）
    :param driver: Appium Driver 实例
    :param actual: 实际数值
    :param threshold: 阈值
    :param scene: 断言场景描述
    """
    _validate_driver(driver)
    try:
        actual_num = float(actual)
        threshold_num = float(threshold)
        logger.info(f"断言数值大于阈值：actual={actual_num}, threshold={threshold_num}，场景={scene}")

        if actual_num <= threshold_num:
            screenshot_path = take_screenshot(driver, f"{scene}_number_not_greater")
            logger.error(
                f"数值断言失败！actual={actual_num} 不大于 threshold={threshold_num}，"
                f"场景：{scene}，截图：{screenshot_path}"
            )
            raise AssertionError(f"数值未大于阈值！actual={actual_num}, threshold={threshold_num}")
    except ValueError as ve:
        # 数值转换失败也视为断言失败
        screenshot_path = take_screenshot(driver, f"{scene}_number_cast_fail")
        logger.error(
            f"数值转换失败！actual={actual}，threshold={threshold}，"
            f"场景：{scene}，截图：{screenshot_path}，异常：{str(ve)}"
        )
        raise
    except Exception as e:
        try:
            screenshot_path = take_screenshot(driver, f"{scene}_assert_number_greater_exception")
            logger.error(f"断言数值大于阈值异常，已自动截图：{screenshot_path}，异常：{str(e)}")
        except Exception as ss_e:
            logger.error(f"断言数值大于阈值异常，且截图失败：{str(ss_e)}；原始异常：{str(e)}")
        raise

