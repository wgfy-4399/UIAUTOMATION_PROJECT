#!/usr/bin/env python3
"""
定位符生成脚本
使用方式：
    # 交互式采集并生成
    python scripts/generate_locators.py --page profile --platform ios --app main

    # 从已有 XML 生成
    python scripts/generate_locators.py --from-xml data/page_xml/ios/main/profile/*.xml

    # 输出到文件
    python scripts/generate_locators.py --page profile --platform ios --output config/locators/profile_locators.yaml
"""
import argparse
import glob
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Tuple, List, Dict, Any

from utils.driver_utils import get_driver, quit_driver
from utils.xml_capture_utils import XMLCaptureUtils
from utils.locator_generator import LocatorGenerator, generate_locators_from_xml
from utils.log_utils import global_logger as logger


def get_device_index_by_platform(platform: str) -> int:
    """根据平台获取设备索引"""
    return 1 if platform.lower() == "ios" else 0


def infer_platform_from_path(path: str) -> str:
    """从路径推断平台"""
    if "/ios/" in path:
        return "ios"
    elif "/android/" in path:
        return "android"
    return "ios"


def infer_app_from_path(path: str) -> str:
    """从路径推断应用名"""
    for app in ["main", "vest1", "vest2", "vest3"]:
        if f"/{app}/" in path:
            return app
    return "main"


def interactive_capture_and_generate(
    platform: str,
    app_name: str,
    page_name: str,
    wait_time: int = 15
) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
    """
    交互式采集：用户手动操作到目标页面后采集并生成定位符

    :param platform: 平台 (android/ios)
    :param app_name: 应用名称
    :param page_name: 页面名称
    :param wait_time: 等待用户导航的时间（秒）
    :return: (YAML 内容, 元素列表) 或 (None, None)
    """
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           定位符生成工具 - 交互模式                         ║
╠════════════════════════════════════════════════════════════╣
║  平台: {platform.upper():<12}  应用: {app_name:<15}           ║
║  页面: {page_name:<15}                                    ║
╚════════════════════════════════════════════════════════════╝

📱 请按以下步骤操作：
1. 脚本将启动目标应用
2. 请手动操作到需要采集的页面
3. 操作完成后，脚本将自动采集并生成定位符
4. 按 Ctrl+C 可随时退出

""")

    # 创建 Driver
    print(f"🚀 正在启动 {app_name} 应用...")
    device_index = get_device_index_by_platform(platform)
    try:
        driver = get_driver(platform=platform, app_name=app_name, device_index=device_index)
    except Exception as e:
        logger.error(f"Driver 创建失败：{e}")
        print(f"❌ 启动应用失败：{e}")
        return None, None
    print("✅ 应用启动成功！\n")

    print(f"⏳ 请在 {wait_time} 秒内手动操作到 '{page_name}' 页面...")
    time.sleep(wait_time)

    try:
        # 采集 XML
        print(f"📸 正在采集 '{page_name}' 页面的 XML...")
        try:
            xml_content = XMLCaptureUtils.capture_page_source(
                driver=driver,
                page_name=page_name,
                app_name=app_name,
                platform=platform
            )
        except Exception as e:
            logger.error(f"XML 采集失败：{e}")
            print(f"❌ 采集失败：{e}")
            return None, None

        # 生成定位符
        print(f"🔧 正在生成定位符...")
        try:
            elements = LocatorGenerator.extract_elements_from_xml(xml_content, platform)
        except ValueError as e:
            logger.error(f"定位符生成失败：{e}")
            print(f"❌ 生成失败：{e}")
            return None, None

        # 显示摘要
        summary = LocatorGenerator.print_locators_summary(elements, platform)
        print(summary)

        # 生成 YAML
        yaml_content = generate_locators_from_xml(xml_content, platform, app_name, page_name)

        print(f"\n✅ 生成成功！YAML 配置：\n")
        print("-" * 60)
        print(yaml_content)
        print("-" * 60)

        return yaml_content, elements

    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出采集工具")
        return None, None
    finally:
        try:
            quit_driver()
        except Exception as e:
            logger.error(f"Driver 退出失败：{e}")


def generate_from_xml_file(
    xml_path: str,
    platform: str,
    app_name: str,
    page_name: str
) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
    """
    从已有 XML 文件生成定位符

    :param xml_path: XML 文件路径
    :param platform: 平台
    :param app_name: 应用名称
    :param page_name: 页面名称
    :return: (YAML 内容, 元素列表) 或 (None, None)
    """
    print(f"📂 正在读取 XML 文件：{xml_path}")

    try:
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
    except FileNotFoundError:
        print(f"❌ 文件不存在：{xml_path}")
        return None, None
    except PermissionError:
        print(f"❌ 无权限读取文件：{xml_path}")
        return None, None
    except Exception as e:
        logger.error(f"文件读取失败：{e}")
        print(f"❌ 读取失败：{e}")
        return None, None

    # 推断平台（从文件路径）
    if not platform:
        platform = infer_platform_from_path(xml_path)

    # 推断应用名
    if not app_name:
        app_name = infer_app_from_path(xml_path)

    # 推断页面名
    if not page_name:
        filename = os.path.basename(xml_path)
        page_name = filename.split("_")[0]

    print(f"📋 参数推断：platform={platform}, app={app_name}, page={page_name}")

    # 提取元素
    try:
        elements = LocatorGenerator.extract_elements_from_xml(xml_content, platform)
    except ValueError as e:
        logger.error(f"定位符生成失败：{e}")
        print(f"❌ 生成失败：{e}")
        return None, None

    # 显示摘要
    summary = LocatorGenerator.print_locators_summary(elements, platform)
    print(summary)

    # 生成 YAML
    yaml_content = generate_locators_from_xml(xml_content, platform, app_name, page_name)

    print(f"\n✅ 生成成功！YAML 配置：\n")
    print("-" * 60)
    print(yaml_content)
    print("-" * 60)

    return yaml_content, elements


def save_to_file(yaml_content: str, output_path: str) -> None:
    """
    保存 YAML 到文件

    :param yaml_content: YAML 内容
    :param output_path: 输出路径
    """
    # 确保目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)
        print(f"💾 已保存到：{output_path}")
    except PermissionError:
        print(f"❌ 无权限写入文件：{output_path}")
    except Exception as e:
        logger.error(f"文件保存失败：{e}")
        print(f"❌ 保存失败：{e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="定位符生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 交互式采集并生成
  python scripts/generate_locators.py --page profile --platform ios --app main

  # 从已有 XML 文件生成
  python scripts/generate_locators.py --from-xml data/page_xml/ios/main/profile/*.xml

  # 指定输出文件
  python scripts/generate_locators.py --page profile --platform ios --output config/locators/profile_locators.yaml

  # 批量生成（多个 XML 文件）
  python scripts/generate_locators.py --from-xml data/page_xml/ios/main/*/*.xml --output-dir config/locators/
        """
    )

    parser.add_argument("--page", default="", help="页面名称")
    parser.add_argument("--platform", choices=["android", "ios"], default="", help="平台")
    parser.add_argument("--app", choices=["main", "vest1", "vest2", "vest3"], default="", help="应用名称")
    parser.add_argument("--from-xml", default="", help="从已有 XML 文件生成（支持 glob 模式）")
    parser.add_argument("--output", default="", help="输出文件路径")
    parser.add_argument("--output-dir", default="", help="输出目录（批量模式）")
    parser.add_argument("--interactive", action="store_true", help="交互式模式（等待用户导航）")
    parser.add_argument("--wait-time", type=int, default=15, help="交互模式等待时间（秒）")

    args = parser.parse_args()

    # 确定页面名
    page_name = args.page

    if args.from_xml:
        # 从 XML 文件生成
        xml_files = glob.glob(args.from_xml)

        if not xml_files:
            print(f"❌ 未找到 XML 文件：{args.from_xml}")
            return

        for xml_path in xml_files:
            yaml_content, elements = generate_from_xml_file(
                xml_path, args.platform, args.app, page_name
            )

            if yaml_content and args.output:
                save_to_file(yaml_content, args.output)
            elif yaml_content and args.output_dir:
                # 从 XML 路径推断输出文件名
                inferred_page = os.path.basename(xml_path).split("_")[0]
                output_path = os.path.join(args.output_dir, f"{inferred_page}_locators.yaml")
                save_to_file(yaml_content, output_path)

    elif args.page:
        # 交互式采集
        platform = args.platform or "ios"
        app_name = args.app or "main"
        yaml_content, elements = interactive_capture_and_generate(
            platform, app_name, page_name, args.wait_time
        )

        if yaml_content and args.output:
            save_to_file(yaml_content, args.output)

    else:
        print("❌ 请指定 --page 或 --from-xml 参数")
        parser.print_help()


if __name__ == "__main__":
    main()