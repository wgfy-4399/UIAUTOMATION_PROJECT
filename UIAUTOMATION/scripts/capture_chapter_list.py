#!/usr/bin/env python3
"""
章节列表页面XML采集脚本
直接连接已启动的Appium session，采集当前页面XML
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.driver_utils import get_driver, quit_driver
from utils.xml_capture_utils import XMLCaptureUtils
from utils.locator_generator import LocatorGenerator, generate_locators_from_xml
from utils.log_utils import global_logger as logger


def capture_chapter_list():
    """采集章节列表页面XML并生成定位符"""
    print("=" * 60)
    print("章节列表页面 XML 采集工具")
    print("=" * 60)

    platform = "ios"
    app_name = "main"
    page_name = "chapter_list"
    device_index = 1  # iOS设备索引

    print(f"\n📱 平台: {platform.upper()}")
    print(f"📱 应用: {app_name}")
    print(f"📱 页面: {page_name}")
    print(f"📱 设备索引: {device_index}")

    # 1. 连接 Appium Driver
    print("\n🚀 正在连接 Appium Server...")
    try:
        driver = get_driver(platform=platform, app_name=app_name, device_index=device_index)
        print("✅ Driver 连接成功！")
    except Exception as e:
        logger.error(f"Driver 创建失败：{e}")
        print(f"❌ 连接失败：{e}")
        return None

    # 2. 等待2秒确保页面稳定
    import time
    print("\n⏳ 等待页面稳定...")
    time.sleep(2)

    # 3. 采集当前页面 XML
    print(f"\n📸 正在采集 '{page_name}' 页面的 XML...")
    try:
        xml_content = XMLCaptureUtils.capture_page_source(
            driver=driver,
            page_name=page_name,
            app_name=app_name,
            platform=platform,
            description="阅读器章节列表弹窗/页面"
        )
        print("✅ XML 采集成功！")
    except Exception as e:
        logger.error(f"XML 采集失败：{e}")
        print(f"❌ 采集失败：{e}")
        quit_driver()
        return None

    # 4. 提取元素并生成定位符
    print(f"\n🔧 正在分析元素并生成定位符...")
    try:
        elements = LocatorGenerator.extract_elements_from_xml(xml_content, platform)
        summary = LocatorGenerator.print_locators_summary(elements, platform)
        print(summary)
    except ValueError as e:
        logger.error(f"定位符生成失败：{e}")
        print(f"❌ 生成失败：{e}")
        quit_driver()
        return None

    # 5. 生成 YAML 配置
    yaml_content = generate_locators_from_xml(xml_content, platform, app_name, page_name)

    print(f"\n✅ 定位符配置生成成功！\n")
    print("-" * 60)
    print("YAML 配置内容：")
    print("-" * 60)
    print(yaml_content)
    print("-" * 60)

    # 6. 保存到文件
    output_path = "config/locators/chapter_list_locators.yaml"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"\n💾 定位符配置已保存到：{output_path}")

    # 7. 退出 Driver
    print("\n🔚 正在关闭 Driver...")
    try:
        quit_driver()
        print("✅ Driver 已关闭")
    except Exception as e:
        logger.error(f"Driver 退出失败：{e}")

    print("\n" + "=" * 60)
    print("采集完成！")
    print("=" * 60)

    return yaml_content


if __name__ == "__main__":
    capture_chapter_list()