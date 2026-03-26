"""
定位符配置文件迁移脚本
将旧格式（字符串值）转换为新格式（包含 type 和 value 字段）
"""
import os
from typing import Dict, Any

import yaml


# 支持的定位类型（预留，当前未强制使用）
LOCATOR_TYPES = [
    "id",
    "xpath",
    "css",
    "class_name",
    "tag_name",
    "accessibility_id",
    "name",
    "link_text",
    "partial_link_text",
]


def _infer_locator_type(locator_value: str) -> str:
    """
    根据定位符值的内容特征自动推断定位方式
    """
    if not locator_value:
        return "id"

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


def _migrate_value(value: Any) -> Any:
    """
    迁移单个配置值
    """
    if isinstance(value, str):
        # 字符串值转换为对象格式
        return {
            "type": _infer_locator_type(value),
            "value": value,
        }
    elif isinstance(value, dict):
        # 嵌套字典递归处理
        return {k: _migrate_value(v) for k, v in value.items()}
    else:
        return value


def migrate_config_dict(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    迁移配置字典
    """
    return {k: _migrate_value(v) for k, v in config.items()}


def migrate_config_file(file_path: str, backup: bool = True) -> bool:
    """
    迁移单个配置文件

    :param file_path: 配置文件路径
    :param backup: 是否创建备份文件
    :return: 迁移是否成功
    """
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在：{file_path}")
        return False

    try:
        # 读取原配置
        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config:
            print(f"⚠️  文件为空：{file_path}")
            return False

        # 迁移配置
        migrated_config = migrate_config_dict(config)

        # 备份原文件
        if backup:
            backup_path = f"{file_path}.backup"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(file_path, backup_path)
            print(f"📦 已备份：{backup_path}")

        # 写入新文件
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(
                migrated_config,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
                width=120,
            )

        print(f"✅ 已迁移：{file_path}")
        return True

    except Exception as e:
        print(f"❌ 迁移失败：{file_path} - {e}")
        return False


def migrate_all_configs(locators_dir: str = None, backup: bool = True):
    """
    批量迁移所有配置文件

    :param locators_dir: 定位符配置目录路径
    :param backup: 是否创建备份文件
    """
    if locators_dir is None:
        # 默认使用相对路径
        locators_dir = os.path.join(os.path.dirname(__file__), "../config/locators")

    # 规范化路径
    locators_dir = os.path.abspath(locators_dir)

    print(f"📁 配置目录：{locators_dir}")
    print("🔧 开始迁移...\n")

    if not os.path.exists(locators_dir):
        print(f"❌ 目录不存在：{locators_dir}")
        return

    # 获取所有 _locators.yaml 文件
    config_files = [
        f
        for f in os.listdir(locators_dir)
        if f.endswith("_locators.yaml")
    ]

    if not config_files:
        print("⚠️  未找到配置文件（*_locators.yaml）")
        return

    # 迁移每个文件
    success_count = 0
    for filename in config_files:
        file_path = os.path.join(locators_dir, filename)
        if migrate_config_file(file_path, backup):
            success_count += 1

    print(f"\n📊 迁移完成：成功 {success_count}/{len(config_files)} 个文件")


if __name__ == "__main__":
    # 运行迁移
    migrate_all_configs(backup=True)

