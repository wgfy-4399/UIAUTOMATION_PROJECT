import time
from appium.webdriver.webdriver import WebDriver



def open_browser(driver: WebDriver, platform_type: str = "android"):
    """
    打开手机默认浏览器（适配Android Chrome / iOS Safari）
    :param driver: Appium驱动实例
    :param platform_type: 平台类型（android/ios）
    """
    if platform_type == "android":
        # 启动Android Chrome浏览器
        driver.start_activity(
            app_package="com.android.chrome",
            app_activity="com.google.android.apps.chrome.Main"
        )
        # 等待Chrome加载完成
        time.sleep(3)
    elif platform_type == "ios":
        # 启动iOS Safari浏览器（使用mobile: launchApp指令）
        driver.execute_script(
            'mobile: launchApp',
            {'bundleId': 'com.apple.mobilesafari'}
        )
        time.sleep(3)
    else:
        raise ValueError(f"不支持的平台类型：{platform_type}，仅支持android/ios")

    # 设置隐式等待
    driver.implicitly_wait(10)
    print(f"✅ 成功打开{platform_type}默认浏览器")


def close_browser(driver: WebDriver, platform_type: str = "android"):
    """关闭手机默认浏览器（可选，用于用例清理）"""
    if platform_type == "android":
        driver.terminate_app("com.android.chrome")
    elif platform_type == "ios":
        driver.execute_script('mobile: terminateApp', {'bundleId': 'com.apple.mobilesafari'})
    print(f"✅ 成功关闭{platform_type}默认浏览器")


if __name__ == '__main__':
    open_browser(driver=WebDriver, platform_type="android")