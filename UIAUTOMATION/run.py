import argparse
import os
import shutil
import sys
from typing import List

import pytest

from utils.log_utils import global_logger as logger
from utils.report_utils import generate_allure_report, setup_allure_environment


def _get_project_root() -> str:
    """
    获取项目根目录（基于当前文件位置，避免硬编码）
    run.py 一般位于项目根目录下的 UIAUTOMATION 目录中
    """
    return os.path.dirname(os.path.abspath(__file__))


def _cleanup_history() -> None:
    """
    清理历史 Allure 结果、历史截图、历史日志
    - allure-results
    - allure-report
    - report/screenshot
    - log 目录下旧日志文件
    """
    project_root = _get_project_root()

    # 1. Allure 结果目录（与 utils/report_utils 保持一致）
    allure_results_dir = os.path.join(project_root, "allure-results")
    allure_report_dir = os.path.join(project_root, "allure-report")

    for path in [allure_results_dir, allure_report_dir]:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                logger.info(f"已清理目录：{path}")
            except Exception as e:
                logger.error(f"清理目录失败：{path}，异常：{str(e)}")

    # 2. 截图目录（与 screenshot_utils 中定义保持一致：report/screenshot）
    screenshot_dir = os.path.join(project_root, "report", "screenshot")
    if os.path.exists(screenshot_dir):
        try:
            shutil.rmtree(screenshot_dir)
            logger.info(f"已清理历史截图目录：{screenshot_dir}")
        except Exception as e:
            logger.error(f"清理截图目录失败：{screenshot_dir}，异常：{str(e)}")

    # 3. 日志目录（与 log_utils 中定义保持一致：log）
    log_dir = os.path.join(project_root, "log")
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            file_path = os.path.join(log_dir, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"已删除历史日志文件：{file_path}")
                except Exception as e:
                    logger.error(f"删除日志文件失败：{file_path}，异常：{str(e)}")


def _build_pytest_args(app: str, level: str, module: str, platform: str, device: int) -> List[str]:
    """
    根据命令行参数拼装 pytest 执行参数
    :param app: main/vest1/vest2/vest3/all
    :param level: smoke/regression/e2e/all
    :param module: home/reader/task/recharge
    :param platform: android/ios
    :param device: 设备索引（对应 device_config.yaml 中的 index）
    :return: pytest.main 可接受的参数列表
    """
    args: List[str] = []

    # 0. 平台 & 设备（直接透传给 conftest / driver）
    args.extend(["--platform", platform])
    args.extend(["--device", str(device)])

    # 1. 处理 app 参数
    # - 若为 all，则执行所有包；否则通过 --app 传给 pytest，由 conftest 使用
    if app != "all":
        args.extend(["--app", app])
    else:
        # all 场景下，不传 --app，保留 pytest.ini 默认/命令行覆盖行为
        logger.info("执行所有应用包（不限定 --app 参数，使用外部配置）")

    # 2. 处理 level 参数（pytest 标记）
    #   - smoke/regression/e2e 使用 -m 过滤标记
    if level != "all":
        if level == "smoke":
            args.extend(["-m", "smoke"])
        elif level == "regression":
            args.extend(["-m", "regression"])
        elif level == "e2e":
            args.extend(["-m", "e2e"])

    # 3. 处理 module 参数（对应不同业务模块的用例）
    #    结合 pytest.ini 的 testpaths=case，不需要硬编码绝对路径
    if module == "home":
        args.append(os.path.join("case", "main_app", "test_home.py"))
    elif module == "reader":
        # 包含主包+马甲包阅读器用例
        args.extend([
            os.path.join("case", "main_app", "test_reader_smoke.py"),
            os.path.join("case", "vest_app", "test_vest_reader.py"),
        ])
    elif module == "task":
        args.append(os.path.join("case", "common", "test_task_center.py"))
    elif module == "recharge":
        args.append(os.path.join("case", "common", "test_recharge.py"))
    else:
        # 未指定或为 all 时，按 pytest.ini 中 testpaths=case 执行全部用例
        args.append("case")

    # 4. 输出 Allure 结果目录（与 utils/report_utils 一致）
    project_root = _get_project_root()
    allure_results_dir = os.path.join(project_root, "allure-results")
    args.extend(["--alluredir", allure_results_dir])

    logger.info(f"最终 pytest 执行参数：{args}")
    return args


def _run_pytest(args: List[str]) -> pytest.ExitCode:
    """封装 pytest 执行，返回 ExitCode"""
    try:
        exit_code: pytest.ExitCode = pytest.main(args)
        logger.info(f"pytest 执行完成，ExitCode={exit_code}")
        return exit_code
    except Exception as e:
        logger.error(f"执行 pytest 失败：{str(e)}")
        raise


def _generate_and_open_allure_report() -> None:
    """
    基于 utils.report_utils 中的能力：
    - 确保 Allure 环境目录存在
    - 调用 generate_allure_report 生成报告并自动打开
    """
    try:
        # 初始化/创建 allure-results 目录
        setup_allure_environment()
        # 使用工具类统一生成并打开报告
        generate_allure_report(open_report=True)
    except Exception as e:
        logger.error(f"生成或打开 Allure 报告失败：{str(e)}")


def _print_summary_from_pytest(exit_code: pytest.ExitCode) -> None:
    """
    简单输出测试结果概览。
    说明：pytest.main 返回的 ExitCode 只能供高层判断整体状态，
    更详细的“总数、通过、失败、跳过”通常需要插件或从 Allure/pytest JUnit 结果解析。
    这里为了不引入额外依赖，仅结合 ExitCode 给出简略总结。
    """
    logger.info("============ 测试结果统计（概览） ============")
    if exit_code == pytest.ExitCode.OK:
        logger.info("所有用例执行完毕：整体结果 = 全部通过")
    elif exit_code == pytest.ExitCode.TESTS_FAILED:
        logger.info("所有用例执行完毕：整体结果 = 存在失败用例（具体明细请查看 pytest 输出或 Allure 报告）")
    elif exit_code == pytest.ExitCode.NO_TESTS_COLLECTED:
        logger.info("未收集到任何测试用例，请检查筛选条件（app / level / module）是否过于严格。")
    else:
        logger.info(f"pytest 返回非零状态：{exit_code}，可能存在错误或中断，详情请查看控制台日志。")

    logger.info("详细的用例总数、通过数、失败数、跳过数，请在 Allure 报告中查看统计图表。")


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="UI 自动化测试统一入口（海外网文APP）")

    parser.add_argument(
        "--app",
        choices=["main", "vest1", "vest2", "vest3", "all"],
        default="main",
        help="指定执行的应用包：main/vest1/vest2/vest3/all（默认main）",
    )
    parser.add_argument(
        "--level",
        choices=["smoke", "regression", "e2e", "all"],
        default="all",
        help="指定用例级别：smoke/regression/e2e/all（默认all）",
    )
    parser.add_argument(
        "--module",
        choices=["home", "reader", "task", "recharge", "all"],
        default="all",
        help="指定执行模块：home/reader/task/recharge/all（默认all）",
    )
    parser.add_argument(
        "--platform",
        choices=["android", "ios"],
        default="android",
        help="指定测试设备平台：android/ios（默认android）",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=0,
        help="指定测试设备索引（对应 device_config.yaml 中的 index，默认0）",
    )

    return parser.parse_args()


def main() -> None:
    """run.py 主入口"""
    args = parse_args()
    logger.info(
        f"启动UI自动化测试：app={args.app}, level={args.level}, module={args.module}, "
        f"platform={args.platform}, device={args.device}"
    )

    # 1. 清理历史结果（allure、截图、日志）
    _cleanup_history()

    # 2. 组装 pytest 参数并执行
    pytest_args = _build_pytest_args(
        app=args.app,
        level=args.level,
        module=args.module,
        platform=args.platform,
        device=args.device,
    )
    exit_code = _run_pytest(pytest_args)

    # 3. 生成并打开 Allure 报告
    _generate_and_open_allure_report()

    # 4. 输出测试结果概览
    _print_summary_from_pytest(exit_code)

    # 5. 根据 pytest ExitCode 决定脚本退出状态
    if exit_code == pytest.ExitCode.OK:
        sys.exit(0)
    else:
        # 保留 pytest 的退出码语义
        sys.exit(int(exit_code))


if __name__ == "__main__":
    main()
