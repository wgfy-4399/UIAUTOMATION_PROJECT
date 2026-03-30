#!/usr/bin/env python3
"""
章节列表直接测试脚本
直接连接当前设备状态进行测试，不通过导航流程
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from time import sleep

from utils.driver_utils import get_driver, quit_driver
from utils.log_utils import global_logger as logger
from utils.screenshot_utils import take_screenshot
from page.pages.chapter_list_page import ChapterList


def test_chapter_list_direct():
    """直接测试章节列表功能（设备已在章节列表页面）"""
    print("=" * 60)
    print("章节列表直接测试")
    print("=" * 60)

    platform = "ios"
    app_name = "main"
    device_index = 1

    # 1. 连接 Driver
    print("\n🚀 正在连接设备...")
    try:
        driver = get_driver(platform=platform, app_name=app_name, device_index=device_index)
        print("✅ Driver 连接成功！")
    except Exception as e:
        logger.error(f"Driver 创建失败：{e}")
        print(f"❌ 连接失败：{e}")
        return False

    # 2. 创建 ChapterList 页面对象
    print("\n📋 创建章节列表页面对象...")
    chapter_list = ChapterList(driver)

    # 3. 测试页面加载验证
    print("\n🔍 测试1: 页面加载验证")
    try:
        is_loaded = chapter_list.is_page_loaded()
        print(f"   页面加载状态: {'已加载' if is_loaded else '未加载'}")
        if is_loaded:
            print("   ✅ 测试通过：章节列表页面已加载")
        else:
            print("   ❌ 测试失败：章节列表页面未加载")
    except Exception as e:
        print(f"   ❌ 测试失败：{e}")
        screenshot_path = take_screenshot(driver, "page_load_test_fail")
        print(f"   截图保存: {screenshot_path}")

    # 4. 测试获取章节数量
    print("\n🔍 测试2: 获取章节数量")
    try:
        chapter_count = chapter_list.get_chapter_count()
        print(f"   章节总数: {chapter_count}")
        if chapter_count > 0:
            print("   ✅ 测试通过：成功获取章节数量")
        else:
            print("   ❌ 测试失败：章节数量为0")
    except Exception as e:
        print(f"   ❌ 测试失败：{e}")

    # 5. 测试获取可见章节标题
    print("\n🔍 测试3: 获取可见章节标题")
    try:
        titles = chapter_list.get_visible_chapter_titles()
        print(f"   可见章节数量: {len(titles)}")
        if titles:
            print(f"   前5个章节: {', '.join(titles[:5])}")
            print("   ✅ 测试通过：成功获取章节标题")
        else:
            print("   ❌ 测试失败：未获取到章节标题")
    except Exception as e:
        print(f"   ❌ 测试失败：{e}")

    # 6. 测试获取当前章节
    print("\n🔍 测试4: 获取当前章节")
    try:
        current_title = chapter_list.get_current_chapter_title()
        print(f"   当前章节: {current_title}")
        if current_title:
            print("   ✅ 测试通过：成功获取当前章节")
        else:
            print("   ⚠️ 无法获取当前章节（可能是正常情况）")
    except Exception as e:
        print(f"   ❌ 测试失败：{e}")

    # 7. 测试滚动
    print("\n🔍 测试5: 滚动测试")
    try:
        chapter_list.scroll_to_bottom()
        sleep(1)
        screenshot_path = take_screenshot(driver, "after_scroll")
        print(f"   截图保存: {screenshot_path}")
        print("   ✅ 测试通过：滚动成功")
    except Exception as e:
        print(f"   ❌ 测试失败：{e}")

    # 8. 测试关闭章节列表
    print("\n🔍 测试6: 关闭章节列表")
    try:
        from page.pages.reader_page import ReaderPage
        reader_page = chapter_list.close_chapter_list()
        sleep(1)
        if isinstance(reader_page, ReaderPage):
            print("   ✅ 测试通过：成功关闭章节列表并返回阅读器")
        else:
            print("   ❌ 测试失败：返回类型不正确")
        screenshot_path = take_screenshot(driver, "after_close")
        print(f"   截图保存: {screenshot_path}")
    except Exception as e:
        print(f"   ❌ 测试失败：{e}")
        screenshot_path = take_screenshot(driver, "close_fail")
        print(f"   截图保存: {screenshot_path}")

    # 9. 清理
    print("\n🔚 正在关闭 Driver...")
    try:
        quit_driver()
        print("✅ Driver 已关闭")
    except Exception as e:
        logger.error(f"Driver 退出失败：{e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

    return True


if __name__ == "__main__":
    test_chapter_list_direct()