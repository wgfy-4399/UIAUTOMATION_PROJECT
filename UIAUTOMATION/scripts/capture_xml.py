#!/usr/bin/env python3
"""
界面 XML 采集脚本
使用方式：
    # 交互式采集（手动操作到目标页面后运行）
    python scripts/capture_xml.py --app main --platform android

    # 指定页面名称
    python scripts/capture_xml.py --app main --platform android --page home

    # 查看已采集的页面
    python scripts/capture_xml.py --list

    # 查看某个页面的元素摘要
    python scripts/capture_xml.py --show home --app main --platform android
"""
import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.driver_utils import get_driver, quit_driver
from utils.xml_capture_utils import XMLCaptureUtils
from utils.log_utils import global_logger as logger


def get_device_index_by_platform(platform: str) -> int:
    """根据平台获取设备索引"""
    # 根据 device_config.yaml 中的配置
    # Android: index=0, iOS: index=1
    return 1 if platform.lower() == "ios" else 0


def interactive_capture(platform: str, app_name: str):
    """
    交互式采集：用户手动操作到目标页面后采集
    """
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           界面 XML 交互式采集工具                          ║
╠════════════════════════════════════════════════════════════╣
║  平台: {platform.upper():<12}  应用: {app_name:<15}           ║
╚════════════════════════════════════════════════════════════╝

📱 请按以下步骤操作：
1. 脚本将启动目标应用
2. 请手动操作到需要采集的页面
3. 操作完成后，在此终端输入页面名称（如 home、shelf、reader）
4. 按 Enter 键采集当前界面的 XML
5. 输入 'q' 退出

""")

    # 创建 Driver
    print(f"🚀 正在启动 {app_name} 应用...")
    device_index = get_device_index_by_platform(platform)
    driver = get_driver(platform=platform, app_name=app_name, device_index=device_index)
    print("✅ 应用启动成功！\n")

    try:
        while True:
            page_name = input("📝 请输入当前页面名称（或 'q' 退出）: ").strip()

            if page_name.lower() == 'q':
                print("👋 退出采集工具")
                break

            if not page_name:
                print("❌ 页面名称不能为空！")
                continue

            # 采集 XML
            print(f"📸 正在采集 '{page_name}' 页面的 XML...")
            xml_content = XMLCaptureUtils.capture_page_source(
                driver=driver,
                page_name=page_name,
                app_name=app_name,
                platform=platform
            )

            # 提取并显示元素摘要
            elements = XMLCaptureUtils.extract_interactive_elements(xml_content)
            summary = XMLCaptureUtils.generate_element_summary(elements[:10])  # 只显示前10个
            print(f"\n✅ 采集成功！找到 {len(elements)} 个可交互元素")
            print(f"📄 元素预览（前10个）：\n")
            print(summary)
            print(f"\n💾 XML 已保存到: data/page_xml/{platform}/{app_name}/{page_name}/\n")

    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出采集工具")
    finally:
        quit_driver()


def quick_capture(platform: str, app_name: str, page_name: str, description: str = ""):
    """
    快速采集：直接采集当前界面
    """
    print(f"🚀 正在启动 {app_name} 应用...")
    device_index = get_device_index_by_platform(platform)
    driver = get_driver(platform=platform, app_name=app_name, device_index=device_index)
    print("✅ 应用启动成功！")
    print(f"⏳ 请在 15 秒内手动操作到 '{page_name}' 页面...")
    print(f"📌 Profile 页面入口：点击底部导航栏最右侧的【我的/Me】图标")

    import time
    time.sleep(15)

    print(f"📸 正在采集 '{page_name}' 页面的 XML...")
    xml_content = XMLCaptureUtils.capture_page_source(
        driver=driver,
        page_name=page_name,
        app_name=app_name,
        platform=platform,
        description=description
    )

    elements = XMLCaptureUtils.extract_interactive_elements(xml_content)
    print(f"✅ 采集成功！找到 {len(elements)} 个可交互元素")
    print(f"💾 XML 已保存到: data/page_xml/{platform}/{app_name}/{page_name}/")

    quit_driver()


def list_pages(platform: str, app_name: str):
    """
    列出已采集的页面
    """
    pages = XMLCaptureUtils.list_captured_pages(platform=platform, app_name=app_name)

    print(f"""
╔════════════════════════════════════════════════════════════╗
║           已采集的页面列表                                 ║
╠════════════════════════════════════════════════════════════╣
║  平台: {platform.upper():<12}  应用: {app_name:<15}           ║
╚════════════════════════════════════════════════════════════╝
""")

    if not pages:
        print("📭 还没有采集任何页面")
    else:
        for page in pages:
            print(f"  📄 {page}")


def show_page_elements(platform: str, app_name: str, page_name: str):
    """
    显示某个页面的元素摘要
    """
    base_dir = f"{XMLCaptureUtils.XML_ROOT_DIR}/{platform}/{app_name}/{page_name}"
    if not os.path.exists(base_dir):
        print(f"❌ 未找到页面 '{page_name}' 的采集记录")
        return

    # 获取最新的 XML 文件
    xml_files = [f for f in os.listdir(base_dir) if f.endswith(".xml") and not f.endswith("_meta.json")]
    if not xml_files:
        print(f"❌ 页面 '{page_name}' 没有 XML 文件")
        return

    latest_xml = sorted(xml_files)[-1]
    xml_path = os.path.join(base_dir, latest_xml)

    with open(xml_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    elements = XMLCaptureUtils.extract_interactive_elements(xml_content)
    summary = XMLCaptureUtils.generate_element_summary(elements)

    print(f"""
╔════════════════════════════════════════════════════════════╗
║           页面元素详情                                     ║
╠════════════════════════════════════════════════════════════╣
║  页面: {page_name:<15}  平台: {platform.upper():<12}        ║
║  应用: {app_name:<15}  文件: {latest_xml:<20} ║
╚════════════════════════════════════════════════════════════╝

{summary}
""")


def main():
    parser = argparse.ArgumentParser(
        description="界面 XML 采集工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 交互式采集（推荐）
  python scripts/capture_xml.py --app main --platform android

  # 快速采集指定页面
  python scripts/capture_xml.py --app main --platform android --page home

  # 查看已采集的页面
  python scripts/capture_xml.py --list --app main --platform android

  # 查看某个页面的元素
  python scripts/capture_xml.py --show home --app main --platform android
        """
    )

    parser.add_argument("--app", choices=["main", "vest1", "vest2", "vest3"], default="main",
                        help="应用名称（默认: main）")
    parser.add_argument("--platform", choices=["android", "ios"], default="android",
                        help="平台（默认: android）")
    parser.add_argument("--page", default="",
                        help="页面名称（不指定则进入交互模式）")
    parser.add_argument("--description", default="",
                        help="页面描述（可选）")
    parser.add_argument("--list", action="store_true",
                        help="列出已采集的页面")
    parser.add_argument("--show", default="",
                        help="显示指定页面的元素详情")

    args = parser.parse_args()

    if args.list:
        list_pages(args.platform, args.app)
    elif args.show:
        show_page_elements(args.platform, args.app, args.show)
    elif args.page:
        quick_capture(args.platform, args.app, args.page, args.description)
    else:
        interactive_capture(args.platform, args.app)


if __name__ == "__main__":
    main()
