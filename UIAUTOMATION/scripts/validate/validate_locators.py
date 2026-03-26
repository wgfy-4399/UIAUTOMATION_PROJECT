#!/usr/bin/env python3
"""
定位符配置验证脚本

验证 YAML 定位符配置的正确性：
- 检查文件格式是否正确
- 检查必需字段 (type, value)
- 检查平台/应用覆盖完整性

使用方式：
    # 验证所有定位符配置
    python scripts/validate/validate_locators.py

    # 验证指定页面的定位符配置
    python scripts/validate/validate_locators.py --page home

    # 详细输出
    python scripts/validate/validate_locators.py -v
"""
import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOCATORS_DIR = PROJECT_ROOT / "config" / "locators"

# 支持的定位符类型
VALID_LOCATOR_TYPES = {
    "id", "xpath", "css", "accessibility_id",
    "ios_class_chain", "ios_predicate", "android_uiautomator"
}

# 支持的平台
VALID_PLATFORMS = {"android", "ios"}

# 支持的应用
VALID_APPS = {"main", "vest1", "vest2", "vest3"}


class ValidationResult:
    """验证结果"""
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.element_count = 0

    def add_error(self, message: str):
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        status = "✅ 通过" if self.is_valid else "❌ 失败"
        result = f"\n📄 {self.file_name} - {status}\n"
        result += f"   元素数量: {self.element_count}\n"

        if self.errors:
            result += "   ❌ 错误:\n"
            for error in self.errors:
                result += f"      - {error}\n"

        if self.warnings:
            result += "   ⚠️  警告:\n"
            for warning in self.warnings:
                result += f"      - {warning}\n"

        return result


def validate_locator_value(locator_type: str, value: str) -> Optional[str]:
    """
    验证定位符值的有效性

    Args:
        locator_type: 定位符类型
        value: 定位符值

    Returns:
        Optional[str]: 错误信息，None 表示有效
    """
    if not value:
        return "定位符值不能为空"

    # XPath 基本格式检查
    if locator_type == "xpath" and not value.startswith(("/", "(")):
        return f"XPath 应以 '/' 或 '(' 开头: {value[:50]}..."

    # ID 基本格式检查
    if locator_type == "id" and ":" not in value and not value.startswith("@"):
        return f"ID 定位符可能缺少包名前缀: {value}"

    # iOS class chain 格式检查
    if locator_type == "ios_class_chain" and not value.startswith(("*", "/")):
        return f"iOS class chain 应以 '*' 或 '/' 开头: {value[:50]}..."

    return None


def validate_locator_structure(element_key: str, locator_config: Dict, result: ValidationResult):
    """
    验证定位符结构

    Args:
        element_key: 元素键名
        locator_config: 定位符配置
        result: 验证结果
    """
    # 检查是否是旧格式（直接是字符串）
    if isinstance(locator_config, str):
        result.add_warning(f"元素 '{element_key}' 使用旧格式（纯字符串），建议升级为新格式")
        return

    # 检查是否是字典
    if not isinstance(locator_config, dict):
        result.add_error(f"元素 '{element_key}' 配置格式错误，应为字典")
        return

    # 遍历平台
    for platform, platform_config in locator_config.items():
        if platform not in VALID_PLATFORMS:
            result.add_error(f"元素 '{element_key}' 包含无效平台: {platform}")
            continue

        if not isinstance(platform_config, dict):
            result.add_error(f"元素 '{element_key}' 的平台配置应为字典: {platform}")
            continue

        # 遍历应用
        for app, app_config in platform_config.items():
            if app not in VALID_APPS:
                result.add_warning(f"元素 '{element_key}' 包含非标准应用: {app}")
                continue

            # 检查 app_config 格式
            if isinstance(app_config, str):
                # 旧格式兼容
                result.add_warning(f"元素 '{element_key}' ({platform}/{app}) 使用旧格式，建议升级")
                continue

            if not isinstance(app_config, dict):
                result.add_error(f"元素 '{element_key}' ({platform}/{app}) 配置格式错误")
                continue

            # 检查必需字段
            if "type" not in app_config:
                result.add_error(f"元素 '{element_key}' ({platform}/{app}) 缺少 'type' 字段")
                continue

            if "value" not in app_config:
                result.add_error(f"元素 '{element_key}' ({platform}/{app}) 缺少 'value' 字段")
                continue

            locator_type = app_config.get("type")
            locator_value = app_config.get("value", "")

            # 验证定位符类型
            if locator_type not in VALID_LOCATOR_TYPES:
                result.add_error(f"元素 '{element_key}' ({platform}/{app}) 包含无效定位符类型: {locator_type}")

            # 验证定位符值
            value_error = validate_locator_value(locator_type, locator_value)
            if value_error:
                result.add_warning(f"元素 '{element_key}' ({platform}/{app}) - {value_error}")


def validate_platform_coverage(element_key: str, locator_config: Dict, result: ValidationResult):
    """
    验证平台覆盖完整性

    Args:
        element_key: 元素键名
        locator_config: 定位符配置
        result: 验证结果
    """
    if not isinstance(locator_config, dict):
        return

    # 检查 Android 覆盖
    if "android" not in locator_config:
        result.add_warning(f"元素 '{element_key}' 缺少 Android 平台定位符")
    else:
        android_apps = set(locator_config.get("android", {}).keys())
        missing_apps = VALID_APPS - android_apps
        if missing_apps:
            result.add_warning(f"元素 '{element_key}' Android 平台缺少应用: {', '.join(missing_apps)}")

    # 检查 iOS 覆盖
    if "ios" not in locator_config:
        result.add_warning(f"元素 '{element_key}' 缺少 iOS 平台定位符")
    else:
        ios_apps = set(locator_config.get("ios", {}).keys())
        missing_apps = VALID_APPS - ios_apps
        if missing_apps:
            result.add_warning(f"元素 '{element_key}' iOS 平台缺少应用: {', '.join(missing_apps)}")


def validate_locators_file(file_path: Path, verbose: bool = False, check_coverage: bool = True) -> ValidationResult:
    """
    验证单个定位符配置文件

    Args:
        file_path: 文件路径
        verbose: 是否详细输出
        check_coverage: 是否检查平台覆盖

    Returns:
        ValidationResult: 验证结果
    """
    result = ValidationResult(file_path.name)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            locators = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.add_error(f"YAML 解析错误: {e}")
        return result
    except Exception as e:
        result.add_error(f"文件读取错误: {e}")
        return result

    if not locators:
        result.add_warning("文件为空")
        return result

    if not isinstance(locators, dict):
        result.add_error("定位符配置应为字典")
        return result

    # 验证每个元素
    for element_key, locator_config in locators.items():
        result.element_count += 1

        if verbose:
            print(f"   验证元素: {element_key}")

        validate_locator_structure(element_key, locator_config, result)

        if check_coverage:
            validate_platform_coverage(element_key, locator_config, result)

    return result


def validate_all_locators(locators_dir: Path = LOCATORS_DIR, verbose: bool = False,
                          check_coverage: bool = True) -> Tuple[int, int]:
    """
    验证所有定位符配置文件

    Args:
        locators_dir: 定位符目录
        verbose: 是否详细输出
        check_coverage: 是否检查平台覆盖

    Returns:
        Tuple[int, int]: (通过数, 失败数)
    """
    print("""
╔════════════════════════════════════════════════════════════╗
║           定位符配置验证                                    ║
╚════════════════════════════════════════════════════════════╝
""")

    if not locators_dir.exists():
        print(f"❌ 定位符目录不存在: {locators_dir}")
        return 0, 0

    # 获取所有 YAML 文件
    yaml_files = list(locators_dir.glob("*_locators.yaml"))

    if not yaml_files:
        print(f"⚠️  未找到任何定位符配置文件")
        return 0, 0

    print(f"📂 定位符目录: {locators_dir}")
    print(f"📄 发现 {len(yaml_files)} 个配置文件\n")

    passed = 0
    failed = 0

    for yaml_file in sorted(yaml_files):
        result = validate_locators_file(yaml_file, verbose, check_coverage)
        print(result)

        if result.is_valid:
            passed += 1
        else:
            failed += 1

    # 打印摘要
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           验证摘要                                          ║
╠════════════════════════════════════════════════════════════╣
║  ✅ 通过: {passed:<5}  ❌ 失败: {failed:<5}  总计: {len(yaml_files):<5}         ║
╚════════════════════════════════════════════════════════════╝
""")

    return passed, failed


def main():
    parser = argparse.ArgumentParser(
        description="定位符配置验证工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 验证所有定位符配置
  python scripts/validate/validate_locators.py

  # 验证指定页面
  python scripts/validate/validate_locators.py --page home

  # 详细输出
  python scripts/validate/validate_locators.py -v

  # 跳过平台覆盖检查
  python scripts/validate/validate_locators.py --no-coverage
        """
    )

    parser.add_argument("--page", metavar="PAGE",
                        help="验证指定页面的定位符配置")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="详细输出")
    parser.add_argument("--no-coverage", action="store_true",
                        help="跳过平台覆盖检查")

    args = parser.parse_args()

    if args.page:
        # 验证单个页面
        file_path = LOCATORS_DIR / f"{args.page}_locators.yaml"
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            sys.exit(1)

        result = validate_locators_file(file_path, args.verbose, not args.no_coverage)
        print(result)

        sys.exit(0 if result.is_valid else 1)
    else:
        # 验证所有文件
        passed, failed = validate_all_locators(LOCATORS_DIR, args.verbose, not args.no_coverage)

        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()