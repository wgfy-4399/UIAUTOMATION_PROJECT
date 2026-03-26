#!/usr/bin/env python3
"""
XML 采集脚本测试工具
用于验证运行环境和配置是否满足 XML 采集脚本的要求
"""
import argparse
import json
import os
import socket
import subprocess
import sys
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from utils.log_utils import global_logger as logger


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class TestResult:
    """测试结果"""
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []  # (test_name, error_message)
        self.warnings: List[str] = []

    def add_pass(self, test_name: str):
        self.passed.append(test_name)

    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))

    def add_warning(self, message: str):
        self.warnings.append(message)

    def print_summary(self):
        """打印测试摘要"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}测试摘要{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")

        if self.passed:
            print(f"\n{Colors.GREEN}✅ 通过 ({len(self.passed)}):{Colors.RESET}")
            for test in self.passed:
                print(f"   {test}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠️  警告 ({len(self.warnings)}):{Colors.RESET}")
            for warning in self.warnings:
                print(f"   {warning}")

        if self.failed:
            print(f"\n{Colors.RED}❌ 失败 ({len(self.failed)}):{Colors.RESET}")
            for test_name, error in self.failed:
                print(f"   {test_name}")
                print(f"   {Colors.RED}└─ {error}{Colors.RESET}")

        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")

        # 返回是否全部通过
        return len(self.failed) == 0


def run_command(cmd: List[str], timeout: int = 10) -> Tuple[int, str, str]:
    """运行命令并返回 (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


def check_appium_server(result: TestResult) -> bool:
    """检查 Appium Server 是否运行"""
    print(f"\n{Colors.BLUE}[1/6] 检查 Appium Server...{Colors.RESET}")

    # 检查 Appium 是否安装
    code, stdout, stderr = run_command(["appium", "--version"])
    if code != 0:
        result.add_fail("Appium 安装检查", f"Appium 未安装或不在 PATH 中\n   请运行: npm install -g appium")
        return False

    version = stdout.strip()
    print(f"   ✓ Appium 版本: {version}")

    # 检查 Appium Server 是否运行（默认端口 4723）
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect(("localhost", 4723))
        sock.close()
        result.add_pass("Appium Server 运行检查")
        print(f"   {Colors.GREEN}✓ Appium Server 正在运行{Colors.RESET}")
        return True
    except (socket.timeout, ConnectionRefusedError):
        result.add_fail(
            "Appium Server 运行检查",
            "Appium Server 未启动\n   "
            "请在新终端运行: appium"
        )
        print(f"   {Colors.RED}✗ Appium Server 未运行{Colors.RESET}")
        return False


def check_android_device(result: TestResult, device_config: Dict) -> bool:
    """检查 Android 设备连接"""
    print(f"\n{Colors.BLUE}[2/6] 检查 Android 设备连接...{Colors.RESET}")

    code, stdout, stderr = run_command(["adb", "devices"])
    if code != 0:
        result.add_fail("ADB 检查", "ADB 未安装或不在 PATH 中")
        return False

    # 解析 adb devices 输出
    lines = stdout.strip().split('\n')[1:]  # 跳过标题行
    devices = []
    for line in lines:
        if '\tdevice' in line:
            udid = line.split('\t')[0]
            devices.append(udid)

    if not devices:
        result.add_fail(
            "Android 设备检查",
            "未检测到 Android 设备\n   "
            "请连接设备或启动模拟器"
        )
        print(f"   {Colors.RED}✗ 未检测到 Android 设备{Colors.RESET}")
        return False

    print(f"   {Colors.GREEN}✓ 检测到 {len(devices)} 个设备:{Colors.RESET}")
    for udid in devices:
        print(f"      - {udid}")

    # 检查配置中的设备是否存在
    android_devices = [d for d in device_config.get('devices', []) if d.get('platform') == 'android']
    for device in android_devices:
        if device.get('udid') not in devices:
            result.add_warning(
                f"配置中的设备 {device.get('udid')} 未连接"
            )
        else:
            print(f"   ✓ 配置设备 {device.get('udid')} 已连接")

    result.add_pass("Android 设备连接检查")
    return True


def check_ios_device(result: TestResult, device_config: Dict) -> bool:
    """检查 iOS 设备连接（支持真机和模拟器）"""
    print(f"\n{Colors.BLUE}[3/6] 检查 iOS 设备连接...{Colors.RESET}")

    # 检查配置中的 iOS 设备
    ios_devices = [d for d in device_config.get('devices', []) if d.get('platform') == 'ios']
    if not ios_devices:
        result.add_warning("iOS 设备检查: 配置文件中没有 iOS 设备")
        return False

    # 1. 首先检查真机（使用 idevice_id 或 xcrun xctrace）
    print(f"   检查 iOS 真机...")
    real_devices = []

    # 尝试使用 idevice_id（需要安装 libimobiledevice）
    code, stdout, stderr = run_command(["which", "idevice_id"], timeout=3)
    if code == 0:
        code, stdout, stderr = run_command(["idevice_id", "-l"], timeout=5)
        if code == 0 and stdout.strip():
            real_devices = [line.strip() for line in stdout.strip().split('\n') if line.strip()]

    # 如果 idevice_id 不可用，尝试使用 xcrun xctrace
    if not real_devices:
        code, stdout, stderr = run_command(["xcrun", "xctrace", "list", "devices"], timeout=10)
        if code == 0:
            for line in stdout.split('\n'):
                # 跳过标题行和分隔符
                if '==' in line or not line.strip():
                    continue
                # 跳过模拟器
                if 'Simulator' in line:
                    continue
                # 跳过离线设备
                if 'Offline' in line:
                    continue
                # 提取真机 UDID（格式：Device Name (version) (UDID)）
                if '(' in line and line.count('(') >= 2:
                    try:
                        # 获取最后一个括号中的内容（UDID）
                        last_paren_start = line.rfind('(')
                        last_paren_end = line.rfind(')')
                        udid = line[last_paren_start + 1:last_paren_end].strip()
                        if len(udid) == 40:  # UDID 长度验证
                            real_devices.append(udid)
                    except (IndexError, ValueError):
                        continue

    if real_devices:
        print(f"   {Colors.GREEN}✓ 检测到 {len(real_devices)} 个 iOS 真机:{Colors.RESET}")
        for udid in real_devices:
            print(f"      - {udid}")

        # 检查配置中的设备是否在真机列表中
        for device in ios_devices:
            udid = device.get('udid')
            if udid in real_devices:
                print(f"   ✓ 配置设备 {udid} 已连接（真机）")
                result.add_pass("iOS 设备连接检查")
                return True

    # 2. 检查模拟器
    print(f"   检查 iOS 模拟器...")
    code, stdout, stderr = run_command(["xcrun", "simctl", "list", "devices"], timeout=5)
    if code == 0:
        booted_simulators = []
        for line in stdout.split('\n'):
            if 'Booted' in line:
                # 提取 UDID
                try:
                    udid = line.split('(')[1].split(')')[0].strip()
                    booted_simulators.append(udid)
                except (IndexError, ValueError):
                    continue

        if booted_simulators:
            print(f"   {Colors.GREEN}✓ 检测到 {len(booted_simulators)} 个启动的模拟器:{Colors.RESET}")
            for udid in booted_simulators:
                print(f"      - {udid}")

            # 检查配置中的设备是否在模拟器列表中
            for device in ios_devices:
                udid = device.get('udid')
                if udid in booted_simulators:
                    print(f"   ✓ 配置设备 {udid} 已连接（模拟器）")
                    result.add_pass("iOS 设备连接检查")
                    return True

    # 未检测到任何匹配的设备
    result.add_warning(
        "iOS 设备检查: 未检测到匹配的 iOS 设备。"
        "请确保真机已通过 USB 连接且已信任，或启动模拟器: xcrun simctl boot <udid>"
    )
    return False


def check_device_config(result: TestResult) -> Dict:
    """检查设备配置文件"""
    print(f"\n{Colors.BLUE}[4/6] 检查配置文件...{Colors.RESET}")

    config_path = "config/device_config.yaml"
    if not os.path.exists(config_path):
        result.add_fail("设备配置文件", f"文件不存在: {config_path}")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        devices = config.get('devices', [])
        if not devices:
            result.add_fail("设备配置", "配置文件中没有设备定义")
            return {}

        print(f"   ✓ 配置文件格式正确")
        print(f"   ✓ 找到 {len(devices)} 个设备配置:")

        for device in devices:
            platform = device.get('platform', 'unknown')
            udid = device.get('udid', 'N/A')
            print(f"      - {platform.upper()}: {udid}")

            # 验证必需字段
            if platform == 'android':
                required = ['udid', 'platformVersion', 'appium_port']
            else:  # ios
                required = ['udid', 'deviceName', 'platformVersion', 'appium_port']

            missing = [field for field in required if not device.get(field)]
            if missing:
                result.add_warning(
                    f"设备 {udid} 缺少字段: {', '.join(missing)}"
                )

        result.add_pass("设备配置文件检查")
        return config

    except yaml.YAMLError as e:
        result.add_fail("设备配置文件", f"YAML 解析错误: {e}")
        return {}


def check_app_config(result: TestResult, app_name: str) -> Dict:
    """检查应用配置文件"""
    print(f"\n{Colors.BLUE}[5/6] 检查应用配置 [{app_name}]...{Colors.RESET}")

    config_path = "config/app_config.yaml"
    if not os.path.exists(config_path):
        result.add_fail("应用配置文件", f"文件不存在: {config_path}")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if app_name not in config:
            result.add_fail("应用配置", f"应用 '{app_name}' 不在配置文件中")
            return {}

        app_config = config[app_name]
        print(f"   ✓ 找到应用 '{app_name}' 配置")

        # 检查平台配置
        for platform in ['android', 'ios']:
            if platform not in app_config:
                result.add_warning(f"应用 '{app_name}' 缺少 {platform} 配置")
                continue

            platform_config = app_config[platform]
            if platform == 'android':
                required = ['appPackage', 'appActivity']
                pkg = platform_config.get('appPackage', '')
                activity = platform_config.get('appActivity', '')
                print(f"   ✓ Android: {pkg}/{activity}")
            else:
                required = ['bundleId']
                bundle_id = platform_config.get('bundleId', '')
                print(f"   ✓ iOS: {bundle_id}")

        result.add_pass(f"应用配置检查 [{app_name}]")
        return config

    except yaml.YAMLError as e:
        result.add_fail("应用配置文件", f"YAML 解析错误: {e}")
        return {}


def check_python_dependencies(result: TestResult) -> bool:
    """检查 Python 依赖"""
    print(f"\n{Colors.BLUE}[6/6] 检查 Python 依赖...{Colors.RESET}")

    dependencies = [
        ("Appium-Python-Client", "appium"),
        ("pytest", "pytest"),
        ("PyYAML", "yaml"),
        ("Allure", "allure"),
    ]

    all_ok = True
    for package_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"   ✓ {package_name}")
        except ImportError:
            result.add_fail(
                f"依赖检查: {package_name}",
                f"未安装 {package_name}\n   "
                f"请运行: pip install {package_name}"
            )
            print(f"   {Colors.RED}✗ {package_name}{Colors.RESET}")
            all_ok = False

    if all_ok:
        result.add_pass("Python 依赖检查")

    return all_ok


def print_quick_verification(platform: str = "android", app_name: str = "main"):
    """打印快速验证步骤"""
    if platform == "ios":
        device_check = "xcrun xctrace list devices  # 或 idevice_id -l"
    else:
        device_check = "adb devices"

    print(f"""
{Colors.BOLD}{Colors.BLUE}
╔════════════════════════════════════════════════════════════╗
║              快速验证步骤                                   ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. 启动 Appium Server:                                     ║
║     {Colors.YELLOW}appium{Colors.RESET}                                                  ║
║                                                              ║
║  2. 检查设备连接 ({platform.upper()}):                             ║
║     {Colors.YELLOW}{device_check}{Colors.RESET}                                        ║
║                                                              ║
║  3. 运行采集脚本:                                            ║
║     {Colors.YELLOW}python scripts/capture_xml.py --app {app_name} --platform {platform}{Colors.RESET}      ║
║                                                              ║
║  4. 检查输出目录:                                            ║
║     {Colors.YELLOW}ls -la data/page_xml/{platform}/{app_name}/{Colors.RESET}                     ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
{Colors.RESET}
""")


def print_troubleshooting():
    """打印故障排查指南"""
    print(f"""
{Colors.BOLD}{Colors.YELLOW}
╔════════════════════════════════════════════════════════════╗
║              故障排查指南                                   ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  问题: Driver 创建失败                                       ║
║  ─────────────────────────────────────────────────────────  ║
║  可能原因: Appium 未启动                                    ║
║  解决方案: {Colors.WHITE}appium{Colors.RESET}                                           ║
║                                                              ║
║  可能原因: 设备未连接                                        ║
║  解决方案: {Colors.WHITE}adb devices{Colors.RESET} (检查设备列表)                     ║
║                                                              ║
║  可能原因: Appium 端口被占用                                ║
║  解决方案: {Colors.WHITE}lsof -i :4723{Colors.RESET} (检查端口)                       ║
║           {Colors.WHITE}kill -9 <PID>{Colors.RESET} (杀死占用进程)                         ║
║                                                              ║
║  ─────────────────────────────────────────────────────────  ║
║  问题: 应用启动失败                                          ║
║  ─────────────────────────────────────────────────────────  ║
║  可能原因: 应用未安装                                        ║
║  解决方案: 手动安装应用或配置 appPath                        ║
║                                                              ║
║  可能原因: appPackage/bundleId 不匹配                        ║
║  解决方案: {Colors.WHITE}adb shell pm list packages{Colors.RESET} (查看已安装应用)        ║
║                                                              ║
║  ─────────────────────────────────────────────────────────  ║
║  问题: 找不到元素                                            ║
║  ─────────────────────────────────────────────────────────  ║
║  可能原因: 应用版本不同                                      ║
║  解决方案: 检查 appPackage/bundleId 是否正确                 ║
║           确认应用已完全加载                                  ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
{Colors.RESET}
""")


def main():
    parser = argparse.ArgumentParser(
        description="XML 采集脚本测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--app", choices=["main", "vest1", "vest2", "vest3"], default="main",
                        help="应用名称（默认: main）")
    parser.add_argument("--platform", choices=["android", "ios"], default="android",
                        help="平台（默认: android）")
    parser.add_argument("--quick", action="store_true",
                        help="仅显示快速验证步骤")
    parser.add_argument("--troubleshoot", action="store_true",
                        help="仅显示故障排查指南")

    args = parser.parse_args()

    print(f"""
{Colors.BOLD}
╔════════════════════════════════════════════════════════════╗
║          XML 采集脚本测试工具                               ║
╠════════════════════════════════════════════════════════════╣
║  平台: {args.platform.upper():<12}  应用: {args.app:<15}           ║
╚════════════════════════════════════════════════════════════╝
{Colors.RESET}
""")

    if args.quick:
        print_quick_verification(args.platform, args.app)
        return 0

    if args.troubleshoot:
        print_troubleshooting()
        return 0

    result = TestResult()

    # 运行检查
    device_config = check_device_config(result)
    check_app_config(result, args.app)

    if args.platform == "android":
        check_appium_server(result)
        check_android_device(result, device_config)
    else:
        check_ios_device(result, device_config)

    check_python_dependencies(result)

    # 打印摘要
    all_passed = result.print_summary()

    # 如果全部通过，显示快速验证步骤
    if all_passed:
        print_quick_verification(args.platform, args.app)
    else:
        print_troubleshooting()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
