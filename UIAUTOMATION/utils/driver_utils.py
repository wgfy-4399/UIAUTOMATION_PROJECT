from appium import webdriver
import os
import time
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from appium.webdriver.webdriver import WebDriver

from config.read_config import (
    load_app_config,
    load_device_config,
    load_driver_global_config
)


# 单例模式：确保全局只有一个Driver实例
class DriverSingleton:
    _instance = None  # Driver实例
    _current_app = "main"  # 当前激活的应用（主包/马甲包/browser）
    _device_index = 0  # 当前使用的设备索引
    _platform = None

    @classmethod
    def get_driver(cls, platform, app_name="main", device_index=0):
        """
        获取Driver实例（单例）：不存在则创建，已存在则复用（支持切换应用/设备）
        :param platform: android/ios
        :param app_name: 应用名称（main/vest1/vest2/vest3/browser）
        :param device_index: 设备索引
        :return: Appium Driver实例
        """
        # 如果切换了应用或设备，销毁旧Driver，创建新实例
        if (cls._instance is not None) and (
                app_name != cls._current_app or device_index != cls._device_index or platform != cls._platform):
            cls.quit_driver()

        if cls._instance is None:
            cls._current_app = app_name
            cls._device_index = device_index
            cls._platform = platform
            cls._instance = cls._create_driver()
        return cls._instance

    @classmethod
    def _create_driver(cls):
        """创建Driver实例（内部方法，兼容浏览器场景）"""
        # 1. 加载配置
        app_config = None
        if cls._current_app != "browser":  # 浏览器场景不加载App配置
            app_config = load_app_config(cls._current_app, cls._platform)
        device_config = load_device_config(cls._device_index)
        driver_global_config = load_driver_global_config()

        platform_lower = cls._platform.lower()

        if platform_lower == "android":
            desired_caps = {
                # 设备信息
                "platformName": device_config.get("platform", "android"),
                "deviceName": device_config.get("deviceName", "Android Device"),
                "udid": device_config.get("udid"),
                "platformVersion": device_config.get("platformVersion"),
                # 全局配置（去掉App相关配置，避免绑定）
                "noReset": driver_global_config.get("noReset", True),
                "fullReset": driver_global_config.get("fullReset", False),
                "unicodeKeyboard": driver_global_config.get("unicodeKeyboard", True),
                "resetKeyboard": driver_global_config.get("resetKeyboard", True),
                "newCommandTimeout": driver_global_config.get("newCommandTimeout", 300),
                "appName": cls._current_app,
            }
            # 非浏览器场景，补充App配置
            if cls._current_app != "browser" and app_config:
                desired_caps["appPackage"] = app_config.get("appPackage")
                desired_caps["appActivity"] = app_config.get("appActivity")
            options = UiAutomator2Options().load_capabilities(desired_caps)
        elif platform_lower == "ios":
            desired_caps = {
                "platformName": "ios",
                "platformVersion": device_config.get("platformVersion"),
                "deviceName": device_config.get("deviceName", "iPhone"),
                "udid": device_config.get("udid"),
                "noReset": driver_global_config.get("noReset", True),
                "automationName": "XCUITest",
                "xcodeOrgId": device_config.get("xcodeOrgId"),
                "xcodeSigningId": device_config.get("xcodeSigningId"),
                "wdaLaunchTimeout": 120000,
                "wdaConnectionTimeout": 60000,
                "wdaStartupRetries": 4,
                "showXcodeLog": True,
                "usePrebuiltWDA": False,
                "shouldUseSingletonTestManager": True,
                "maxTypingFrequency": 60,
                "simpleIsVisibleCheck": True,
                "useNewWDA": True,
                "wdaLocalPort": 8100,
                "webkitDebugProxyPort": 27753,
                "appName": cls._current_app
            }
            # 非浏览器场景，补充App配置
            if cls._current_app != "browser" and app_config:
                bundle_id = app_config.get("bundleId")
                if not bundle_id:
                    raise ValueError(f"未找到{cls._current_app}应用的 bundleId 配置！")
                desired_caps["bundleId"] = bundle_id
            options = XCUITestOptions().load_capabilities(desired_caps)
        else:
            raise ValueError(f"不支持的平台：{cls._platform}")

        # 处理App路径（非浏览器场景）
        if cls._current_app != "browser" and app_config:
            app_path = app_config.get("appPath")
            if app_path and os.path.exists(app_path):
                # Android / iOS 统一：仅在本地文件真实存在时才设置 app，表示需要自动安装
                desired_caps["app"] = app_path
                print(f"自动安装应用：{app_path}")
            else:
                # 若路径未配或文件不存在，则不向 capabilities 注入 app，表示仅依赖已安装应用（appPackage/bundleId）
                if "app" in desired_caps:
                    # 防御性删除可能残留的 app 字段（主要针对 iOS 逻辑调整前的兼容）
                    desired_caps.pop("app", None)
                print(f"未配置APK/IPA路径或文件不存在，按已安装应用方式启动，跳过自动安装")

        # 3. 连接Appium Server，创建Driver
        appium_server = device_config.get("appiumServer", "http://127.0.0.1:4723")
        try:
            driver = webdriver.Remote(appium_server, options=options)

            # 非浏览器场景，才激活目标App
            if cls._current_app != "browser" and app_config:
                app_package = app_config.get("appPackage") or app_config.get("bundleId")
                if app_package:
                    driver.activate_app(app_package)
                    time.sleep(3)
                else:
                    raise ValueError(f"未找到{cls._current_app}应用的包名配置！")
            return driver
        except Exception as e:
            print(f"Driver创建失败！异常信息：{str(e)}")
            raise e

    @classmethod
    def open_browser(cls):
        """仅打开默认浏览器（无URL访问，保留原有功能）"""
        if cls._instance is None:
            raise RuntimeError("请先调用get_driver创建Driver实例！")

        driver: WebDriver = cls._instance
        platform = cls._platform.lower()

        if platform == "android":
            driver.activate_app("com.android.chrome")
        elif platform == "ios":
            driver.execute_script('mobile: launchApp', {'bundleId': 'com.apple.mobilesafari'})
        else:
            raise ValueError(f"不支持的平台：{platform}")

        time.sleep(4)
        driver.implicitly_wait(10)
        print(f"✅ 成功打开{platform}默认浏览器")
        return driver

    # 新增：打开浏览器并访问URL（核心适配你的需求）
    @classmethod
    def open_browser_and_visit_url(cls, url):
        """
        打开浏览器并访问指定落地页URL（解决上下文/Intent解析问题）
        :param url: 落地页完整URL（需替换{{}}模板变量为实际值）
        """
        # 1. 先调用原有方法打开浏览器
        cls.open_browser()
        driver: WebDriver = cls._instance
        platform = cls._platform.lower()

        if platform == "android":
            # 用deepLink指令（最简单，无需切换上下文）
            driver.execute_script(
                'mobile: deepLink',
                {
                    'url': url,
                    'package': 'com.android.chrome'  # 强制Chrome打开URL
                }
            )
        elif platform == "ios":
            driver.execute_script(
                'mobile: deepLink',
                {'url': url, 'bundleId': 'com.apple.mobilesafari'}
            )

        time.sleep(5)  # 等待页面加载，触发唤起APP逻辑
        print(f"✅ 成功在{platform}浏览器中打开URL：{url}")
        return driver

    @classmethod
    def switch_back_to_target_app(cls, app_package=None):
        """从浏览器切回原目标App（兼容手动传包名）"""
        if cls._instance is None:
            raise RuntimeError("无可用Driver！")

        driver: WebDriver = cls._instance
        platform = cls._platform.lower()

        # 优先用传的包名，没有则用配置的
        if not app_package and cls._current_app != "browser":
            app_config = load_app_config(cls._current_app, cls._platform)
            app_package = app_config.get("appPackage") or app_config.get("bundleId")

        if not app_package:
            raise ValueError("请传入目标APP的包名，或先绑定有效app_name")

        if platform == "android":
            driver.activate_app(app_package)
        elif platform == "ios":
            driver.execute_script('mobile: launchApp', {'bundleId': app_package})

        time.sleep(3)
        print(f"✅ 切回应用：{app_package}")
        return driver

    @classmethod
    def quit_driver(cls):
        """销毁Driver实例，释放设备资源"""
        if cls._instance is not None:
            try:
                cls._instance.quit()
                print(f"Driver销毁成功：应用={cls._current_app}，设备索引={cls._device_index}")
            except Exception as e:
                print(f"Driver销毁失败！异常信息：{str(e)}")
            finally:
                cls._instance = None
                cls._current_app = "main"
                cls._device_index = 0


# 对外暴露的简化接口
def get_driver(platform, app_name="main", device_index=0):
    return DriverSingleton.get_driver(platform, app_name, device_index)


def quit_driver():
    DriverSingleton.quit_driver()


def switch_app(platform, app_name="main", device_index=0):
    return DriverSingleton.get_driver(platform, app_name, device_index)


def open_browser():
    """简化：打开浏览器（需先调用get_driver）"""
    return DriverSingleton.open_browser()


def switch_back_to_target_app(app_package=None):
    """简化：切回原目标App"""
    return DriverSingleton.switch_back_to_target_app(app_package)


def open_browser_and_visit_url(url):
    """简化： 打开浏览器并访问指定落地页URL"""
    return DriverSingleton.open_browser_and_visit_url(url)


if __name__ == '__main__':
    driver = get_driver(platform="android", app_name="browser", device_index=0)
    try:

        target_url = "https://fqwebsite.lin47.com/share/middle/ofgublg3mpues0glbq4qoirx?campaign_id={{campaign.id}}&adset_id={{adset.id}}&ad_id={{ad.id}}&campaign={{campaign.name}}&adgroup={{adset.name}}"
        # 调用新增方法：打开浏览器+访问URL
        DriverSingleton.open_browser_and_visit_url(target_url)
    finally:
        quit_driver()
