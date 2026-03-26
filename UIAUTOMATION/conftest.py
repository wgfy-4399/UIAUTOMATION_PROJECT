# 定义命令行参数：支持执行时指定应用和设备（如 pytest --app=vest1 --device=0）
import time
import os
import pathlib
import shutil

import pytest
from utils.driver_utils import get_driver,quit_driver
from utils.report_utils import generate_allure_report, setup_allure_environment

def pytest_addoption(parser):
    """添加Pytest命令行参数"""
    parser.addoption(
        "--app",
        action="store",
        default="main",
        choices=["main", "vest1", "vest2", "vest3","browser"],
        help="指定测试的应用：main（主包）/vest1/vest2/vest3（马甲包）/browser"
    )
    parser.addoption(
        "--device",
        action="store",
        default=0,
        type=int,
        help="指定测试的设备索引（对应device_config.yaml中的设备列表）"
    )

    parser.addoption(
        "--platform",
        action="store",
        default="android",
        choices=["android", "ios"],
        help="指定测试设备平台（'android', 'ios'）"
    )


@pytest.fixture(scope="session")  # 作用域：整个测试会话（所有用例共用一个Driver）
def app_name(request):
    """获取命令行指定的应用名称"""
    app = request.config.getoption("--app")
    # logger.info(f"测试应用：{app}")
    return app

@pytest.fixture(scope="session")  # 作用域：整个测试会话
def device_index(request):
    """获取命令行指定的设备索引（根据平台自动选择）"""
    device = request.config.getoption("--device")
    platform = request.config.getoption("--platform")

    # 如果用户没有明确指定 device，根据平台自动选择
    # device_config.yaml 中：Android index=0, iOS index=1
    if device == 0:  # 使用默认值时
        if platform.lower() == "ios":
            device = 1  # iOS 设备索引
        else:
            device = 0  # Android 设备索引

    print(f"📱 平台: {platform.upper()}, 设备索引: {device}")
    return device


@pytest.fixture(scope="session")  # 作用域：整个测试会话
def device_platform(request):
    """获取命令行指定的设备索引"""
    platform = request.config.getoption("--platform")
    # logger.info(f"测试设备索引：{device}")
    return platform

@pytest.fixture(scope="session")  # 全局唯一Driver（所有用例复用）
def init_driver(device_platform,app_name, device_index):
    """
    全局Driver夹具：测试会话开始时创建，结束时销毁
    :return: Driver实例（供用例直接使用）
    """
    # 1. 创建Driver
    driver = get_driver(platform=device_platform,app_name=app_name, device_index=device_index)

    yield driver  # 用例执行期间复用Driver
    # 2. 测试会话结束后，销毁Driver
    quit_driver()


import time


@pytest.fixture(scope="function")
def reset_app(init_driver):
    """重置App（兼容Android/iOS+Appium 5.2.4）"""
    yield

    try:
        # 1. 获取当前测试平台（Android/iOS）
        platform = init_driver.capabilities.get("platformName", "android")
        # 2. 定义App标识（包名/Bundle ID）
        app_identifier = {
            "android": "com.kw.literie",
            "iOS": "com.kw.literie.ios"
        }[platform]
        # 3. 选择参数名（Android=appId，iOS=bundleId）
        param_name = "appId" if platform == "android" else "bundleId"

        # 4. 关闭+重启App
        init_driver.execute_script("mobile: terminateApp", {param_name: app_identifier})
        time.sleep(1)
        init_driver.execute_script("mobile: activateApp", {param_name: app_identifier})

        print(f"\n===== 用例执行完毕，已适配{platform}重置App =====")

    except Exception as e:
        print(f"\n===== 重置App失败：{str(e)} =====")
        raise e


def pytest_sessionfinish(session, exitstatus):
    """
    让“直接运行 pytest”也能自动生成 Allure HTML 报告。

    复用项目内现成的 Allure 工具方法：
    - `setup_allure_environment()`：创建默认 allure-results 目录
    - `generate_allure_report()`：执行 `allure generate` 并（可选）打开报告
    """
    # 1) 优先使用本次 pytest 的 --alluredir
    alluredir = getattr(session.config.option, "alluredir", None)
    if alluredir:
        # pytest 允许传相对路径，这里基于 rootpath 转成绝对路径，提高健壮性
        results_dir = (
            alluredir
            if os.path.isabs(alluredir)
            else os.path.abspath(os.path.join(str(session.config.rootpath), alluredir))
        )
    else:
        # 未指定时，按项目约定的默认 allure-results 目录
        results_dir = setup_allure_environment()

    results_path = pathlib.Path(results_dir)
    # 2) 若结果目录为空（没有 json），避免生成空报告
    if not results_path.exists() or not any(results_path.glob("*.json")):
        return

    # 3) 生成报告并打开（与 run.py 行为保持一致）
    try:
        generate_allure_report(open_report=True, results_dir=str(results_path))
    except Exception as e:
        # fail-fast：如果生成报告失败，需要让用户明确知道
        pytest.exit(f"生成Allure报告失败：{e}", returncode=1)


def pytest_sessionstart(session):
    """
    每次直接运行 pytest 时，清理上一次的 `allure-results`，避免旧 json/附件混入本次报告。

    复用项目的默认目录约定：
    - 如果用户传了 `--alluredir`：以该目录为准
    - 否则使用 `utils.report_utils.setup_allure_environment()` 的默认 `allure-results`
    """
    alluredir = getattr(session.config.option, "alluredir", None)
    if alluredir:
        results_dir = (
            alluredir
            if os.path.isabs(alluredir)
            else os.path.abspath(os.path.join(str(session.config.rootpath), alluredir))
        )
    else:
        results_dir = setup_allure_environment()

    results_path = pathlib.Path(results_dir)
    try:
        if results_path.exists():
            shutil.rmtree(results_path)
        results_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        pytest.exit(f"清理Allure结果目录失败：{results_path}，异常：{e}", returncode=1)