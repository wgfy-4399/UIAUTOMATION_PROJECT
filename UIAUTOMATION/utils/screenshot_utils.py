from datetime import datetime
import os
import pathlib
import time
from utils.log_utils import global_logger as logger

# 项目根目录 & 截图目录（纯 pathlib 实现，跨平台友好）
PROJECT_ROOT = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCREENSHOT_DIR = PROJECT_ROOT / "report" / "screenshot"

# 合法字符过滤（保留：字母、数字、下划线、横线、中文）
# 移除：\/:*?"<>|（这些是系统禁止的文件名字符）
INVALID_CHARS = set(r'\/:*?"<>|')


def _ensure_screenshot_dir() -> None:
    """确保截图目录存在（pathlib 简洁实现）"""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def _get_timestamp() -> str:
    """统一生成毫秒级时间戳（避免重复逻辑）"""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def _sanitize_scene_name(scene) :
    """清洗场景名：过滤系统禁止的字符，保留中文/字母/数字"""
    # 非字符串转字符串，空值默认 unknown
    if not isinstance(scene, str):
        scene = str(scene) if scene is not None else "unknown"
    # 过滤系统禁止的字符，替换为下划线
    sanitized = "".join([c if c not in INVALID_CHARS else "_" for c in scene])
    # 空字符串默认 unknown
    return sanitized.strip() if sanitized.strip() else "unknown"


def _generate_screenshot_name(scene, suffix = "") -> str:
    """生成规范的截图文件名（修复：给 suffix 加默认值）"""
    timestamp = _get_timestamp()
    scene_sanitized = _sanitize_scene_name(scene)
    parts = [timestamp, scene_sanitized]
    # 只有 suffix 非空时才添加
    if suffix.strip():
        parts.append(_sanitize_scene_name(suffix))
    return "_".join(parts) + ".png"


def _validate_driver(driver) -> None:
    """校验 Driver 实例是否有效"""
    if driver is None:
        raise ValueError("Appium Driver 实例不能为空！")
    # 简单校验 Driver 核心方法是否存在
    required_methods = ["save_screenshot", "find_element"]
    for method in required_methods:
        if not hasattr(driver, method):
            raise AttributeError(f"传入的 Driver 实例无效，缺少核心方法：{method}")


def take_screenshot(driver, scene = "unknown") -> str:
    """
    截取当前屏幕并保存到指定目录
    :param driver: 有效 Appium Driver 实例
    :param scene: 截图场景描述（如：登录失败、首页加载完成）
    :return: 截图文件的绝对路径
    """
    # 前置参数校验
    _validate_driver(driver)
    _ensure_screenshot_dir()

    # 生成截图路径（纯 pathlib 实现）
    screenshot_name = _generate_screenshot_name(scene)
    screenshot_path = SCREENSHOT_DIR / screenshot_name
    abs_path = str(screenshot_path.absolute())

    try:
        # 执行全屏截图
        driver.save_screenshot(abs_path)
        # 轻微延迟，避免文件未完全写入就判断
        time.sleep(0.1)

        # 校验文件是否真的生成
        screenshot_file = pathlib.Path(abs_path)
        if screenshot_file.exists() and screenshot_file.stat().st_size > 0:
            logger.info(
                f"✅ 全屏截图成功！场景：{scene}，保存路径：{abs_path}，文件大小：{screenshot_file.stat().st_size} 字节"
            )
            return abs_path
        else:
            raise IOError("截图文件生成失败（文件为空或不存在）")
    except IOError as e:
        logger.error(f"❌ 全屏截图IO错误！场景：{scene}，路径：{abs_path}，异常：{str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ 全屏截图失败！场景：{scene}，异常信息：{str(e)}")
        raise


def take_screenshot_by_element(
        driver, locator, scene = "element_screenshot"
) -> str:
    """
    截取指定元素的局部截图
    :param driver: Appium Driver 实例
    :param locator: 元素定位符（如：(By.ID, "com.app:id/btn_login")）
    :param scene: 截图场景描述
    :return: 元素截图的绝对路径
    """
    # 前置参数校验
    _validate_driver(driver)
    if not isinstance(locator, (list, tuple)) or len(locator) != 2:
        raise ValueError(f"元素定位符格式错误！需为 (定位方式, 定位值)，当前：{locator}")
    _ensure_screenshot_dir()

    # 生成截图路径
    screenshot_name = _generate_screenshot_name(scene, "element")
    screenshot_path = SCREENSHOT_DIR / screenshot_name
    abs_path = str(screenshot_path.absolute())

    try:
        from page.base_page import BasePage
        # 定位目标元素
        base_page = BasePage(driver)
        element = base_page.find_element(locator)
        if not element:
            raise ValueError(f"未找到目标元素！定位符：{locator}")

        # 执行元素截图
        element.screenshot(abs_path)
        # 轻微延迟，避免文件未完全写入
        time.sleep(0.1)

        # 校验文件有效性（pathlib 实现）
        screenshot_file = pathlib.Path(abs_path)
        if screenshot_file.exists() and screenshot_file.stat().st_size > 0:
            logger.info(
                f"✅ 元素截图成功！场景：{scene}，定位符：{locator}，保存路径：{abs_path}"
            )
            return abs_path
        else:
            raise IOError("元素截图文件生成失败（文件为空或不存在）")
    except ValueError as e:
        logger.error(f"❌ 元素定位失败！场景：{scene}，定位符：{locator}，异常：{str(e)}")
        raise
    except IOError as e:
        logger.error(f"❌ 元素截图IO错误！场景：{scene}，路径：{abs_path}，异常：{str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ 元素截图失败！场景：{scene}，定位符：{locator}，异常信息：{str(e)}")
        raise