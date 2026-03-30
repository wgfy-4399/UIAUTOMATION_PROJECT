"""
定位符生成器
从 XML 元素属性自动生成 optimal locator 表达式
"""
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional, Any
import yaml

from utils.log_utils import global_logger as logger


# 常量定义
MAX_KEY_LENGTH = 30
MAX_DISPLAY_ELEMENTS = 20


class LocatorGenerator:
    """定位符生成器"""

    # 无意义的通用名称（需要忽略）
    GENERIC_NAMES = {
        "", "Button", "Text", "Image", "Cell", "Other", "View",
        "StaticText", "TextField", "TableView", "CollectionView",
    }

    # 有意义的 iOS 元素类型（优先处理）
    IOS_MEANINGFUL_TYPES = {
        "XCUIElementTypeButton",
        "XCUIElementTypeStaticText",
        "XCUIElementTypeTextField",
        "XCUIElementTypeSecureTextField",
        "XCUIElementTypeTabBar",
        "XCUIElementTypeNavigationBar",
        "XCUIElementTypeCell",
        "XCUIElementTypeTable",
        "XCUIElementTypeSwitch",
        "XCUIElementTypeSlider",
        "XCUIElementTypeImage",
    }

    # 无意义的 iOS 元素类型（跳过）
    IOS_SKIP_TYPES = {
        "XCUIElementTypeWindow",
        "XCUIElementTypeApplication",
    }

    # iOS 元素类型映射
    IOS_ELEMENT_TYPES = {
        "XCUIElementTypeButton": "button",
        "XCUIElementTypeStaticText": "text",
        "XCUIElementTypeTextField": "input",
        "XCUIElementTypeSecureTextField": "input",
        "XCUIElementTypeImage": "image",
        "XCUIElementTypeTable": "table",
        "XCUIElementTypeCell": "cell",
        "XCUIElementTypeSwitch": "switch",
        "XCUIElementTypeSlider": "slider",
        "XCUIElementTypeNavigationBar": "navbar",
        "XCUIElementTypeTabBar": "tabbar",
        "XCUIElementTypeOther": "other",
        "XCUIElementTypeWindow": "window",
        "XCUIElementTypeScrollView": "scroll",
    }

    # Android 元素类型映射
    ANDROID_ELEMENT_TYPES = {
        "android.widget.Button": "button",
        "android.widget.TextView": "text",
        "android.widget.EditText": "input",
        "android.widget.ImageView": "image",
        "android.widget.ListView": "list",
        "android.widget.RecyclerView": "recycler",
        "android.widget.CheckBox": "checkbox",
        "android.widget.Switch": "switch",
        "android.widget.LinearLayout": "linear",
        "android.widget.RelativeLayout": "relative",
        "android.widget.FrameLayout": "frame",
    }

    @staticmethod
    def _escape_xpath_string(value: str) -> str:
        """
        转义 XPath 字符串中的特殊字符

        :param value: 原始字符串值
        :return: 转义后的 XPath 字符串表达式
        """
        if "'" not in value:
            return f"'{value}'"
        if '"' not in value:
            return f'"{value}"'
        # 使用 concat() 处理同时包含单引号和双引号的字符串
        parts = value.split("'")
        return "concat('" + "', \"'\", '".join(parts) + "')"

    @staticmethod
    def generate_ios_locator(element_attrs: Dict[str, Any]) -> Tuple[str, str]:
        """
        生成 iOS 定位符 (accessibility_id > xpath)

        :param element_attrs: 元素属性字典
        :return: (定位类型, 定位值)
        """
        name = element_attrs.get("name", "")
        label = element_attrs.get("label", "")
        value = element_attrs.get("value", "")
        element_type = element_attrs.get("type", "")

        # 1. 优先使用 accessibility_id (name 属性)
        if name and name not in LocatorGenerator.GENERIC_NAMES:
            return "accessibility_id", name

        # 2. 使用 label 作为 accessibility_id
        if label and label not in LocatorGenerator.GENERIC_NAMES:
            return "accessibility_id", label

        # 3. 生成 XPath（基于 type 和 name/label/value）- 使用转义
        if name:
            escaped = LocatorGenerator._escape_xpath_string(name)
            return "xpath", f"//{element_type}[@name={escaped}]"
        if label:
            escaped = LocatorGenerator._escape_xpath_string(label)
            return "xpath", f"//{element_type}[@label={escaped}]"
        if value:
            escaped = LocatorGenerator._escape_xpath_string(value)
            return "xpath", f"//{element_type}[@value={escaped}]"

        # 4. 最简单的 XPath（仅类型）
        return "xpath", f"//{element_type}"

    @staticmethod
    def generate_android_locator(element_attrs: Dict[str, Any]) -> Tuple[str, str]:
        """
        生成 Android 定位符 (id > accessibility_id > xpath)

        :param element_attrs: 元素属性字典
        :return: (定位类型, 定位值)
        """
        resource_id = element_attrs.get("resource-id", "")
        content_desc = element_attrs.get("content-desc", "")
        text = element_attrs.get("text", "")
        element_class = element_attrs.get("class", "")

        # 1. 优先使用 resource-id
        if resource_id:
            return "id", resource_id

        # 2. 使用 content-desc 作为 accessibility_id
        if content_desc and content_desc not in LocatorGenerator.GENERIC_NAMES:
            return "accessibility_id", content_desc

        # 3. 生成 XPath（基于 class 和 text/content-desc）- 使用转义
        if text:
            escaped = LocatorGenerator._escape_xpath_string(text)
            return "xpath", f"//{element_class}[@text={escaped}]"

        if content_desc:
            escaped = LocatorGenerator._escape_xpath_string(content_desc)
            return "xpath", f"//{element_class}[@content-desc={escaped}]"

        # 4. 最简单的 XPath（仅 class）
        return "xpath", f"//{element_class}"

    @staticmethod
    def generate_semantic_key(element_attrs: Dict[str, Any], platform: str) -> str:
        """
        生成语义化元素名 (如 login_button, profile_tab)

        :param element_attrs: 元素属性字典
        :param platform: 平台 (android/ios)
        :return: 语义化键名
        """
        name = element_attrs.get("name", "")
        label = element_attrs.get("label", "")
        value = element_attrs.get("value", "")
        text = element_attrs.get("text", "")
        content_desc = element_attrs.get("content-desc", "")
        element_type = element_attrs.get("type", element_attrs.get("class", ""))
        clickable = element_attrs.get("clickable", False)

        # 1. 从 name/label/text/content-desc 提取语义
        semantic_text = name or label or text or content_desc or value

        if semantic_text and semantic_text not in LocatorGenerator.GENERIC_NAMES:
            # 清理并转换为 snake_case
            clean_text = LocatorGenerator._clean_text_for_key(semantic_text)
            suffix = LocatorGenerator._get_type_suffix(element_type, platform, clickable)
            return f"{clean_text}{suffix}"

        # 2. 基于元素类型生成默认名称
        type_suffix = LocatorGenerator._get_type_suffix(element_type, platform, clickable)
        return f"element{type_suffix}"

    @staticmethod
    def _clean_text_for_key(text: str) -> str:
        """
        清理文本用于生成键名

        :param text: 原始文本
        :return: 清理后的 snake_case 键名前缀
        """
        # 移除特殊字符
        clean = re.sub(r'[^\w\s-]', '', text.lower())
        # 转换为 snake_case
        clean = re.sub(r'[\s-]+', '_', clean)
        # 移除前导/后导下划线
        clean = clean.strip('_')
        # 限制长度
        if len(clean) > MAX_KEY_LENGTH:
            clean = clean[:MAX_KEY_LENGTH]
        return clean

    @staticmethod
    def _get_type_suffix(element_type: str, platform: str, clickable: bool) -> str:
        """
        根据元素类型获取后缀

        :param element_type: 元素类型
        :param platform: 平台
        :param clickable: 是否可点击
        :return: 类型后缀
        """
        if platform == "ios":
            type_map = LocatorGenerator.IOS_ELEMENT_TYPES
        else:
            type_map = LocatorGenerator.ANDROID_ELEMENT_TYPES

        type_short = type_map.get(element_type, "")

        # 特殊处理
        if type_short in ("button", "tabbar", "navbar"):
            return "_button" if clickable else "_label"
        if type_short == "text":
            return "_text"
        if type_short == "input":
            return "_input"
        if type_short == "image":
            return "_image"
        if type_short in ("table", "cell", "list", "recycler"):
            return "_item" if clickable else "_container"
        if type_short in ("switch", "checkbox", "slider"):
            return "_control"

        return "_element" if clickable else "_section"

    @staticmethod
    def extract_elements_from_xml(
        xml_content: str,
        platform: str,
        skip_generic: bool = True
    ) -> List[Dict[str, Any]]:
        """
        从 XML 中提取元素并生成定位符

        :param xml_content: XML 内容
        :param platform: 平台 (android/ios)
        :param skip_generic: 是否跳过无意义的通用元素
        :return: 元素列表（包含定位符信息）
        :raises ValueError: 当 XML 内容无效时
        """
        elements = []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"XML 解析失败：{e}")
            raise ValueError(f"Invalid XML content: {e}") from e

        for node in root.iter():
            attrs = dict(node.attrib)

            # 根据平台提取关键属性
            if platform == "ios":
                key_attrs = {
                    "type": attrs.get("type", ""),
                    "name": attrs.get("name", ""),
                    "label": attrs.get("label", ""),
                    "value": attrs.get("value", ""),
                    "visible": attrs.get("visible", "false") == "true",
                    "accessible": attrs.get("accessible", "false") == "true",
                    "enabled": attrs.get("enabled", "false") == "true",
                }
            else:  # android
                key_attrs = {
                    "class": attrs.get("class", ""),
                    "resource-id": attrs.get("resource-id", ""),
                    "text": attrs.get("text", ""),
                    "content-desc": attrs.get("content-desc", ""),
                    "clickable": attrs.get("clickable", "false") == "true",
                    "enabled": attrs.get("enabled", "false") == "true",
                    "bounds": attrs.get("bounds", ""),
                }

            # 过滤无意义元素
            if platform == "ios":
                element_type = key_attrs["type"]
                name = key_attrs["name"]
                label = key_attrs["label"]
                has_value = name or label

                # 跳过无意义类型
                if skip_generic and element_type in LocatorGenerator.IOS_SKIP_TYPES:
                    continue

                # 跳过 XCUIElementTypeOther（除非有有意义的 name）
                if skip_generic and element_type == "XCUIElementTypeOther":
                    if not has_value or has_value in LocatorGenerator.GENERIC_NAMES:
                        continue

                # 跳过无意义的元素
                if not element_type:
                    continue

                # 只保留有意义的元素：有 name/label 或是特定类型
                if not has_value and element_type not in LocatorGenerator.IOS_MEANINGFUL_TYPES:
                    continue

            else:  # android
                has_value = key_attrs["resource-id"] or key_attrs["text"] or key_attrs["content-desc"]
                element_type = key_attrs["class"]
                clickable = key_attrs["clickable"]

                # 跳过无效元素
                if not element_type:
                    continue

                # 跳过非交互且无文本的布局元素
                if skip_generic and not has_value and not clickable:
                    continue

            # 添加原始标签名
            key_attrs["tag"] = node.tag

            # 生成定位符
            if platform == "ios":
                locator_type, locator_value = LocatorGenerator.generate_ios_locator(key_attrs)
            else:
                locator_type, locator_value = LocatorGenerator.generate_android_locator(key_attrs)

            # 生成语义键名
            semantic_key = LocatorGenerator.generate_semantic_key(key_attrs, platform)

            elements.append({
                "attrs": key_attrs,
                "locator_type": locator_type,
                "locator_value": locator_value,
                "semantic_key": semantic_key,
            })

        return elements

    @staticmethod
    def generate_locators_yaml(
        xml_content: str,
        platform: str,
        app_name: str,
        page_name: str,
        deduplicate: bool = True,
    ) -> str:
        """
        从 XML 生成完整 YAML 配置

        :param xml_content: XML 内容
        :param platform: 平台 (android/ios)
        :param app_name: 应用名称 (main/vest1/vest2/vest3)
        :param page_name: 页面名称
        :param deduplicate: 是否去重相同的语义键
        :return: YAML 字符串
        """
        elements = LocatorGenerator.extract_elements_from_xml(xml_content, platform)

        # 构建定位符字典
        locators = {}
        seen_keys: Dict[str, int] = {}  # 用于去重

        for elem in elements:
            key = elem["semantic_key"]
            locator_type = elem["locator_type"]
            locator_value = elem["locator_value"]

            # 去重处理
            if deduplicate:
                if key in seen_keys:
                    # 如果已有相同键，添加序号
                    count = seen_keys[key] + 1
                    seen_keys[key] = count
                    key = f"{key}_{count}"
                else:
                    seen_keys[key] = 1

            # 构建 YAML 结构
            locators[key] = {
                platform: {
                    app_name: {
                        "type": locator_type,
                        "value": locator_value,
                    }
                }
            }

        # 生成 YAML
        header = f"# Generated locators for {page_name} page\n"
        header += f"# Platform: {platform}\n"
        header += f"# App: {app_name}\n\n"
        yaml_content = yaml.dump(
            locators,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )

        return header + yaml_content

    @staticmethod
    def generate_locators_dict(
        xml_content: str,
        platform: str,
        app_name: str,
    ) -> Dict[str, Any]:
        """
        从 XML 生成定位符字典（用于合并到现有配置）

        :param xml_content: XML 内容
        :param platform: 平台
        :param app_name: 应用名称
        :return: 定位符字典
        """
        elements = LocatorGenerator.extract_elements_from_xml(xml_content, platform)

        locators = {}
        seen_keys: Dict[str, int] = {}

        for elem in elements:
            key = elem["semantic_key"]

            if key in seen_keys:
                count = seen_keys[key] + 1
                seen_keys[key] = count
                key = f"{key}_{count}"
            else:
                seen_keys[key] = 1

            locators[key] = {
                platform: {
                    app_name: {
                        "type": elem["locator_type"],
                        "value": elem["locator_value"],
                    }
                }
            }

        return locators

    @staticmethod
    def print_locators_summary(elements: List[Dict[str, Any]], platform: str) -> str:
        """
        打印定位符摘要

        :param elements: 元素列表
        :param platform: 平台
        :return: 摘要字符串
        """
        summary = [f"Generated {len(elements)} locators for {platform}:\n"]

        for i, elem in enumerate(elements[:MAX_DISPLAY_ELEMENTS], 1):
            key = elem["semantic_key"]
            type_ = elem["locator_type"]
            value = elem["locator_value"]

            # 获取元素属性摘要
            attrs = elem["attrs"]
            if platform == "ios":
                attr_summary = attrs.get("name") or attrs.get("label") or attrs.get("type")
            else:
                attr_summary = attrs.get("resource-id") or attrs.get("text") or attrs.get("class")

            summary.append(f"{i}. {key}:")
            summary.append(f"   type: {type_}")
            summary.append(f"   value: {value}")
            summary.append(f"   source: {attr_summary}")
            summary.append("")

        if len(elements) > MAX_DISPLAY_ELEMENTS:
            summary.append(f"... and {len(elements) - MAX_DISPLAY_ELEMENTS} more elements")

        return "\n".join(summary)


# 便捷函数
def generate_locators_from_xml(
    xml_content: str,
    platform: str = "ios",
    app_name: str = "main",
    page_name: str = "unknown",
) -> str:
    """
    从 XML 内容生成定位符 YAML

    :param xml_content: XML 内容
    :param platform: 平台
    :param app_name: 应用名称
    :param page_name: 页面名称
    :return: YAML 配置字符串
    """
    return LocatorGenerator.generate_locators_yaml(
        xml_content, platform, app_name, page_name
    )


def generate_locators_dict_from_xml(
    xml_content: str,
    platform: str = "ios",
    app_name: str = "main",
) -> Dict[str, Any]:
    """
    从 XML 内容生成定位符字典

    :param xml_content: XML 内容
    :param platform: 平台
    :param app_name: 应用名称
    :return: 定位符字典
    """
    return LocatorGenerator.generate_locators_dict(xml_content, platform, app_name)