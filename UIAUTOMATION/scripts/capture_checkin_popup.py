#!/usr/bin/env python3
"""
采集签到弹窗的 XML
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from appium import webdriver
from appium.options.ios import XCUITestOptions
from utils.xml_capture_utils import XMLCaptureUtils
from utils.screenshot_utils import take_screenshot


def capture_checkin_popup():
    """导航到 Rewards 页面并采集签到弹窗"""

    desired_caps = {
        "platformName": "ios",
        "platformVersion": "15.6.1",
        "deviceName": "Novellair",
        "udid": "43320ae5864ab870fc7489a147f528d827da68d6",
        "noReset": True,
        "automationName": "XCUITest",
        "xcodeOrgId": "92787V7C7H",
        "xcodeSigningId": "Apple Development",
        "bundleId": "com.qvon.novellair",
        "wdaLaunchTimeout": 120000,
        "appName": "main"
    }

    options = XCUITestOptions().load_capabilities(desired_caps)

    print("🚀 正在连接设备...")
    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
    print("✅ 设备连接成功！")

    try:
        # 等待应用加载
        time.sleep(3)

        # 点击底部 Rewards Tab
        print("📍 正在点击 Rewards Tab...")
        from appium.webdriver.common.appiumby import AppiumBy
        rewards_tab = driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Rewards")
        rewards_tab.click()
        print("✅ 已点击 Rewards Tab")

        # 等待页面和弹窗加载
        time.sleep(5)

        # 采集 XML（无论是否有弹窗）
        print("📸 正在采集当前页面 XML...")
        xml_content = XMLCaptureUtils.capture_page_source(
            driver=driver,
            page_name="checkin_popup",
            app_name="main",
            platform="ios",
            description="签到弹窗页面"
        )

        # 截图
        screenshot_path = take_screenshot(driver, "checkin_popup_page")
        print(f"📸 截图已保存：{screenshot_path}")

        # 分析元素
        elements = []
        root = ET.fromstring(xml_content)
        for node in root.iter():
            name = node.attrib.get('name', '')
            label = node.attrib.get('label', '')
            visible = node.attrib.get('visible', 'false') == 'true'
            if visible and (name or label):
                elements.append({
                    'tag': node.tag,
                    'name': name,
                    'label': label
                })

        print(f"\n✅ 采集成功！")
        print(f"📊 共找到 {len(elements)} 个可见元素")

        # 显示包含 'close', 'check', 'sign' 的元素
        print(f"\n🔍 签到/关闭相关元素：")
        for elem in elements:
            text = elem['name'] or elem['label']
            if any(keyword in text.lower() for keyword in ['close', 'check', 'sign', 'popup', 'alert', 'cancel']):
                print(f"   [{elem['tag']}] {text}")

        print(f"\n💾 XML 已保存到: data/page_xml/ios/main/checkin_popup/")

        # 保持会话
        input("\n按 Enter 键退出...")

    finally:
        driver.quit()
        print("👋 会话已结束")


if __name__ == "__main__":
    import xml.etree.ElementTree as ET
    capture_checkin_popup()
