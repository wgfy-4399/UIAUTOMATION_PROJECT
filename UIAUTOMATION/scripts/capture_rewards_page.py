#!/usr/bin/env python3
"""
自动采集 Rewards 页面
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from appium import webdriver
from appium.options.ios import XCUITestOptions
from utils.xml_capture_utils import XMLCaptureUtils


def capture_rewards_page():
    """自动导航到 Rewards 页面并采集"""

    # 配置
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
        rewards_tab = driver.find_element("xpath", "//XCUIElementTypeButton[@name='Rewards']")
        rewards_tab.click()
        print("✅ 已点击 Rewards Tab")

        # 等待页面加载
        time.sleep(3)

        # 采集 XML
        print("📸 正在采集 Rewards 页面 XML...")
        xml_content = XMLCaptureUtils.capture_page_source(
            driver=driver,
            page_name="rewards",
            app_name="main",
            platform="ios",
            description="个人中心Rewards页面"
        )

        # 提取并显示元素摘要
        elements = XMLCaptureUtils.extract_interactive_elements(xml_content)

        # iOS 特殊处理：提取可点击元素
        clickable_elements = []
        for elem in elements:
            if elem.get('clickable') or elem.get('name') or elem.get('label'):
                clickable_elements.append(elem)

        print(f"\n✅ 采集成功！")
        print(f"📊 共找到 {len(clickable_elements)} 个可交互元素")

        # 显示前15个元素
        for i, elem in enumerate(clickable_elements[:15], 1):
            tag = elem.get('tag', 'Unknown')
            name = elem.get('name', elem.get('label', ''))
            print(f"   {i}. [{tag}] {name}")

        print(f"\n💾 XML 已保存到: data/page_xml/ios/main/rewards/")

        # 保持会话，方便查看
        input("\n按 Enter 键退出...")

    finally:
        driver.quit()
        print("👋 会话已结束")


if __name__ == "__main__":
    capture_rewards_page()
