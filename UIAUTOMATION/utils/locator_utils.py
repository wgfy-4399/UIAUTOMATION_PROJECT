import os
from typing import Dict, Any, Tuple

import yaml
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

from utils.log_utils import global_logger as logger


LOCATORS_DIR = os.path.join(os.path.dirname(__file__), "../config/locators")


def load_locators(page_name: str) -> Dict[str, Any]:
    """
    加载指定页面的定位符配置
    :param page_name: 页面名称（如 'home', 'shelf', 'reader'）
    :return: 定位符字典
    """
    file_path = os.path.join(LOCATORS_DIR, f"{page_name}_locators.yaml")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"定位符配置文件不存在：{file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _infer_locator_type(locator_value: str) -> str:
    """
    根据定位符值的内容特征自动推断定位方式

    :param locator_value: 定位符值
    :return: 推断的定位方式（id/xpath/css等）
    """
    if not locator_value:
        return "id"  # 默认

    # XPath 特征
    if locator_value.startswith("//") or locator_value.startswith("(//") or locator_value.startswith("(("):
        return "xpath"

    # CSS Selector 特征
    if locator_value.startswith(("#", ".", "[")) or ":" in locator_value:
        return "css"

    # iOS XCUI 元素特征（XPath 格式）
    if "XCUIElementType" in locator_value:
        return "xpath"

    # Android 资源 ID 特征
    if ":" in locator_value and "id/" in locator_value:
        return "id"

    # 默认使用 ID
    return "id"


def _resolve_locator_value(
    value: Any,
    locator_type: str,
) -> Tuple[str, str]:
    """
    解析定位符值（内部辅助函数）
    支持新格式 {type: xxx, value: xxx} 和旧格式字符串

    :param value: 配置中的值
    :param locator_type: 显式指定的定位类型（可选）
    :return: 定位符元组 (By.xxx, value)
    """
    # 新格式：对象格式 {type: "id", value: "xxx"}
    if isinstance(value, dict) and "type" in value and "value" in value:
        locator_type_str = str(value["type"]).strip()
        locator_value = value["value"]

        # 统一大写，便于映射
        type_upper = locator_type_str.upper()

        # Appium 专有定位方式优先走 AppiumBy
        appium_types = {
            "ACCESSIBILITY_ID",
            "IOS_PREDICATE",
            "IOS_CLASS_CHAIN",
            "ANDROID_UIAUTOMATOR",
        }
        if type_upper in appium_types:
            by = getattr(AppiumBy, type_upper)
        else:
            # Selenium By 的别名兼容（如 css -> CSS_SELECTOR）
            selenium_alias = {
                "CSS": "CSS_SELECTOR",
                "CSS_SELECTOR": "CSS_SELECTOR",
                "ID": "ID",
                "XPATH": "XPATH",
                "NAME": "NAME",
                "CLASS_NAME": "CLASS_NAME",
                "TAG_NAME": "TAG_NAME",
                "LINK_TEXT": "LINK_TEXT",
                "PARTIAL_LINK_TEXT": "PARTIAL_LINK_TEXT",
            }
            mapped = selenium_alias.get(type_upper, type_upper)
            by = getattr(By, mapped)

        return by, locator_value

    # 旧格式：字符串值
    if isinstance(value, str):
        # 向后兼容：如果显式指定了 locator_type，使用指定的
        if locator_type:
            logger.debug(f"使用显式指定的定位方式：{locator_type}")
            return getattr(By, locator_type.upper()), value
        # 自动推断
        inferred_type = _infer_locator_type(value)
        logger.debug(f"自动推断定位方式：{inferred_type}")
        return getattr(By, inferred_type.upper()), value

    raise ValueError(f"无法解析定位符值：{value}")


def get_locator_from_config(
    config: Dict[str, Any],
    element_key: str,
    platform: str,
    app_name: str,
    locator_type: str = None,
) -> Tuple[str, str]:
    """
    从配置中获取定位符

    :param config: 定位符配置字典
    :param element_key: 元素键名（如 'home_tab', 'shelf_tab'）
    :param platform: 平台（android/ios）
    :param app_name: 应用名称（main/vest1/vest2/vest3）
    :param locator_type: 定位符类型（可选，None 表示从配置中读取或自动推断）
    :return: 定位符元组 (By.xxx, value)
    """
    # 解析路径（支持嵌套，如 'banner.list_container'）
    keys = element_key.split(".")
    value: Any = config

    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise KeyError(f"无法在配置中找到定位符路径：{element_key}")
        value = value[key]

    # 优先检查是否为新格式（包含 type 和 value 的字典）
    if isinstance(value, dict) and "type" in value and "value" in value:
        return _resolve_locator_value(value, locator_type)

    # 处理平台差异化配置
    if isinstance(value, dict):
        # 1. 精确匹配：platform + app
        if platform in value:
            platform_dict = value[platform]
            if isinstance(platform_dict, dict):
                if app_name in platform_dict:
                    return _resolve_locator_value(platform_dict[app_name], locator_type)

                # 2. 平台兜底：使用 main 的定位符
                if "main" in platform_dict:
                    logger.warning(
                        f"未找到 {platform}平台 {app_name}应用的定位符，使用main定位符兜底"
                    )
                    return _resolve_locator_value(platform_dict["main"], locator_type)

        # 3. 尝试使用 android + main 作为兜底
        if "android" in value and isinstance(value["android"], dict) and "main" in value["android"]:
            logger.warning(f"未找到平台[{platform}]的定位符，使用android+main兜底")
            return _resolve_locator_value(value["android"]["main"], locator_type)

    # 4. 直接返回字符串值（处理顶层字符串配置）
    if isinstance(value, str):
        return _resolve_locator_value(value, locator_type)

    raise ValueError(
        f"无法找到定位符：element_key={element_key}, platform={platform}, app={app_name}"
    )

