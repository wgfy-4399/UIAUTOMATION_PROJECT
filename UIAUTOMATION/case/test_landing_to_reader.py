import os
from time import sleep

import pytest

from data.sql.landing_sql import query_chapters_by_id_sql
from page.landingpage import LandingPage
from selenium.webdriver.common.by import By

from utils.app_utils import get_app_utils
from utils.db_utils import get_db_utils

sql = query_chapters_by_id_sql
landing_url = "https://fqwebsite.lin47.com/share/middle/ofgublg3mpues0glbq4qoirx?campaign_id={{campaign.id}}&adset_id={{adset.id}}&ad_id={{ad.id}}&campaign={{campaign.name}}&adgroup={{adset.name}}"
target_app_package = "com.kw.literie"
chapter_id_locator = (By.ID, "com.kw.literie:id/titleTv")

current_file = os.path.abspath(__file__)
case_common_dir = os.path.dirname(current_file)
case_dir = os.path.dirname(case_common_dir)
project_root = os.path.dirname(case_dir)

# 拼接app_packages/android
ANDROID_APP_PACKAGE_DIR = os.path.join(project_root, "app_packages", "android")
ANDROID_APP_PACKAGE_DIR = os.path.normpath(ANDROID_APP_PACKAGE_DIR)
# 自动创建目录
if not os.path.exists(ANDROID_APP_PACKAGE_DIR):
    os.makedirs(ANDROID_APP_PACKAGE_DIR)


# @pytest.mark.flaky(reruns=3, reruns_delay=5)
# def test_landing_to_reader(init_driver):
#     try:
#         # 初始化落地页对象
#         landing_page = LandingPage(init_driver)
#         # 一站式完成：加载落地页→点击按钮→跳转APP（返回章节ID）
#         landing_chapter_id, reader_page = landing_page.jump_to_app(
#             url=landing_url,
#             app_package=target_app_package
#         )
#
#         db_chapter_info = get_db_utils(env="test").query_one(sql, (landing_chapter_id,))
#         # 切换到原生上下文后，操作阅读器
#         sleep(10)
#         chapter_id = reader_page.get_element_text(chapter_id_locator)
#         assert db_chapter_info["chapter_name"] == chapter_id
#
#         print("🎉 测试完成！")
#     except Exception as e:
#         raise


def test_landing_local_app_install_and_jump(init_driver):
    """
    最终稳定版：修复EC导入错误 + APP启动成功 + 基础元素定位
    """
    # 1. 初始化APP工具
    app_utils = get_app_utils(platform="android", app_name="vest1", device_index=0)
    assert app_utils.bundle_id == target_app_package, \
        f"包名配置不一致！配置：{app_utils.bundle_id}，目标：{target_app_package}"

    try:
        # 2. 前置：卸载旧APP
        app_utils.stop_app()
        uninstall_success = app_utils.uninstall_app()
        assert uninstall_success, "❌ 卸载旧APP失败"
        print("✅ 卸载旧APP完成")

        # 3. 启动浏览器+打开落地页
        landing_page = LandingPage(init_driver)
        landing_page._load_landing_page(url=landing_url)
        sleep(5)
        print("✅ 浏览器打开落地页完成")

        # 4. 提取章节ID
        landing_chapter_id = landing_page.extract_chapter_id()
        print(f"✅ 提取落地页章节ID：{landing_chapter_id}")

        # 5. JS触发按钮点击（已验证成功）
        js_code = """
            var btn = document.querySelector('div.jump-btn.theme-color-1[onclick="jumpLink()"]');
            if (btn) {
                btn.click();
                return "success";
            } else {
                return "fail";
            }
        """
        js_result = init_driver.execute_script(js_code)
        if js_result != "success":
            raise Exception("❌ JS未找到跳转按钮")
        print("✅ JS触发按钮点击成功，已跳转到谷歌商店")

        # 6. 本地安装APP（已验证成功）
        install_success = app_utils.install_app_from_dir(
            scan_dir=ANDROID_APP_PACKAGE_DIR,
            reinstall=True
        )
        assert install_success, "❌ 本地安装APP失败"
        print("✅ 本地安装APP完成")

        # ========== APP启动逻辑（已验证成功，保留） ==========
        print("✅ 强制激活已安装的APP")
        app_utils.start_app()
        sleep(20)  # 延长到20秒，确保APP完全加载到阅读器页面

        # 切回NATIVE_APP（已验证成功）
        init_driver.switch_to.context("NATIVE_APP")
        print(f"✅ 确认APP状态：包名={init_driver.current_package}，Activity={init_driver.current_activity}")

        # ========== 核心修复：简化元素定位，避开EC导入问题 ==========
        print(f"✅ 开始定位元素：{chapter_id_locator}")
        # 多次重试定位（容错APP页面加载延迟）
        max_retry = 5
        retry_count = 0
        chapter_title = None

        while retry_count < max_retry:
            try:
                # 用基础的find_element定位，不用EC
                element = init_driver.find_element(*chapter_id_locator)
                chapter_title = element.text
                print(f"✅ 元素定位成功！章节标题：{chapter_title}")
                break
            except Exception as e:
                retry_count += 1
                print(f"⚠️ 第{retry_count}次定位失败（可重试）：{e}")
                sleep(3)  # 每次重试间隔3秒

        if not chapter_title:
            raise Exception(f"❌ 重试{max_retry}次仍未定位到元素：{chapter_id_locator}")

        # 8. 数据库校验
        db_chapter_info = get_db_utils(env="test").query_one(
            query_chapters_by_id_sql,
            (landing_chapter_id,)
        )
        assert db_chapter_info is not None, f"❌ 数据库未查询到章节ID：{landing_chapter_id}"
        assert db_chapter_info["chapter_name"] == chapter_title, \
            f"❌ 章节标题校验失败！数据库：{db_chapter_info['chapter_name']}，APP：{chapter_title}"

        print("🎉 测试全通过！")

    except Exception as e:
        print(f"\n❌ 调试信息 - 当前包名：{init_driver.current_package}")
        print(f"❌ 调试信息 - 当前Activity：{init_driver.current_activity}")
        print(f"❌ 用例执行失败：{str(e)}")
        raise
    finally:
        app_utils.stop_app()
        print("ℹ️ 测试结束，已停止目标APP")