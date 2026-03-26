import glob
import os
import subprocess
import re
import requests
import tempfile
from typing import Optional, Tuple, Dict, List
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from config.read_config import load_device_config, load_app_config
from utils.log_utils import global_logger as logger


# ======================== 蒲公英下载函数（无修改）========================
def get_pgyer_shortlink_info(shortlink: str) -> Optional[Dict]:
    """解析蒲公英分享短链接，提取应用信息和下载链接"""
    base_url = "https://www.pgyer.com/"
    if shortlink.startswith(base_url):
        full_url = shortlink
    elif shortlink.startswith("http"):
        full_url = shortlink
    else:
        full_url = f"{base_url}{shortlink}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(full_url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        download_btn = soup.find("a", attrs={"class": "download-btn"})
        if not download_btn or not download_btn.get("href"):
            logger.error("未找到蒲公英下载按钮")
            return None
        download_path = download_btn["href"]
        download_url = f"https://www.pgyer.com{download_path}" if not download_path.startswith(
            "http") else download_path

        version_elem = soup.find("div", attrs={"class": "version"})
        app_name_elem = soup.find("div", attrs={"class": "app-name"})
        if not version_elem or not app_name_elem:
            logger.error("未找到应用版本/名称信息")
            return None

        version_name = version_elem.text.strip()
        app_name = app_name_elem.text.strip()

        return {
            "download_url": download_url,
            "version_name": version_name,
            "app_name": app_name,
            "shortlink": full_url
        }
    except Exception as e:
        logger.error(f"解析蒲公英短链接失败：{str(e)}")
        return None


def download_pgyer_shortlink(shortlink: str, save_path: str = None) -> Optional[str]:
    """从蒲公英短链接下载最新版本安装包"""
    link_info = get_pgyer_shortlink_info(shortlink)
    if not link_info or not link_info.get("download_url"):
        return None
    download_url = link_info["download_url"]
    version_name = link_info["version_name"]

    try:
        logger.info(f"开始下载蒲公英最新版本：{download_url}")
        response = requests.get(download_url, stream=True, timeout=60)
        response.raise_for_status()

        # 自动生成文件名
        filename = None
        if "Content-Disposition" in response.headers:
            cd = response.headers["Content-Disposition"]
            filename_match = re.findall(r"filename=\"?([^\";]+)\"?", cd)
            if filename_match:
                filename = filename_match[0]

        if not filename:
            if "application/vnd.android.package-archive" in response.headers.get("Content-Type", ""):
                filename = f"app_v{version_name}.apk"
            elif "application/ipa" in response.headers.get("Content-Type",
                                                           "") or "application/octet-stream" in response.headers.get(
                    "Content-Type", ""):
                filename = f"app_v{version_name}.ipa"
            else:
                logger.warning("无法识别文件类型，默认保存为apk")
                filename = f"app_v{version_name}.apk"

        # 确定保存路径
        if not save_path:
            temp_dir = tempfile.gettempdir()
            save_path = os.path.join(temp_dir, filename)
        else:
            if os.path.isdir(save_path):
                os.makedirs(save_path, exist_ok=True)
                save_path = os.path.join(save_path, filename)

        # 分块下载
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        # 校验文件是否下载成功
        if os.path.getsize(save_path) == 0:
            logger.error("下载的文件为空，删除无效文件")
            os.remove(save_path)
            return None

        logger.info(f"下载成功，保存路径：{save_path}")
        return save_path
    except Exception as e:
        logger.error(f"下载失败：{str(e)}")
        return None


# ======================== 抽象基类（无修改）========================
class BaseAppUtils(ABC):
    def __init__(self, app_name: str = "main", device_index: int = 0):
        self.app_name = app_name
        self.device_index = device_index
        self.device_config = load_device_config(device_index)
        self.platform = self.device_config.get("platform")

        if self.platform not in ["android", "ios"]:
            raise ValueError(f"不支持的平台类型：{self.platform}，仅支持android/ios")

        self.udid = self.device_config.get("udid")
        if not self.udid:
            logger.warning("设备UDID未配置，可能导致部分命令执行失败")

        # 读取应用配置
        self.app_config = load_app_config(app_name, self.platform)
        self.bundle_id = self.app_config.get("bundleId") or self.app_config.get("appPackage")
        self.app_path = self.app_config.get("appPath")
        self.pgyer_shortlink = self.app_config.get("pgyer_shortlink")
        self.pgyer_save_dir = self.app_config.get("pgyer_save_dir", tempfile.gettempdir())

        if not self.bundle_id:
            raise ValueError(f"应用{app_name}的{self.platform}平台未配置bundleId/appPackage")

    @abstractmethod
    def find_latest_app_package(self, scan_dir: str) -> Optional[str]:
        pass

    def install_app_from_dir(self, scan_dir: str, reinstall: bool = False) -> bool:
        latest_pkg_path = self.find_latest_app_package(scan_dir)
        if not latest_pkg_path:
            logger.error(f"扫描目录{scan_dir}未找到可用的安装包（APK/IPA）")
            return False

        self.app_path = latest_pkg_path
        logger.info(f"找到最新安装包：{latest_pkg_path}")
        return self.install_app(reinstall=reinstall, use_pgyer=False)

    @abstractmethod
    def _exec_platform_cmd(self, cmd: str) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def install_app(self, reinstall: bool = False, use_pgyer: bool = False) -> bool:
        pass

    @abstractmethod
    def uninstall_app(self) -> bool:
        pass

    @abstractmethod
    def start_app(self) -> bool:
        pass

    @abstractmethod
    def activate_app(self) -> bool:
        """强制激活APP到前台（即使已启动）"""
        pass

    @abstractmethod
    def is_app_installed(self) -> bool:
        pass

    @abstractmethod
    def is_app_running(self) -> bool:
        pass

    def stop_app(self) -> bool:
        """停止运行中的APP"""
        if not self.is_app_running():
            logger.warning(f"APP未运行：{self.bundle_id}")
            return True
        return self._stop_app_impl()

    @abstractmethod
    def _stop_app_impl(self) -> bool:
        pass


# ======================== Android实现类（仅修改核心问题点）========================
class AndroidAppUtils(BaseAppUtils):
    def _exec_platform_cmd(self, cmd: str) -> Tuple[bool, str]:
        full_cmd = f"adb -s {self.udid} {cmd}" if self.udid else f"adb {cmd}"
        try:
            result = subprocess.run(
                full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                encoding="gbk",  # 适配Windows中文编码
                errors="ignore",  # 忽略无法解码的字节
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def find_latest_app_package(self, scan_dir: str) -> Optional[str]:
        if not os.path.exists(scan_dir):
            logger.error(f"扫描目录不存在：{scan_dir}")
            return None

        apk_files = glob.glob(os.path.join(scan_dir, "*.apk"))
        if not apk_files:
            logger.warning(f"目录{scan_dir}中无APK文件")
            return None

        # 过滤不可读文件
        apk_files = [f for f in apk_files if os.access(f, os.R_OK)]
        if not apk_files:
            logger.error("扫描到的APK文件无读取权限")
            return None

        apk_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        latest_apk = apk_files[0]
        logger.info(f"找到最新APK：{latest_apk}（修改时间：{os.path.getmtime(latest_apk)}）")
        return latest_apk

    def install_app(self, reinstall: bool = False, use_pgyer: bool = False) -> bool:
        apk_path = self.app_path
        if use_pgyer:
            if not self.pgyer_shortlink:
                logger.error("未配置蒲公英短链接，无法使用蒲公英下载")
                return False
            apk_path = download_pgyer_shortlink(self.pgyer_shortlink, save_path=self.pgyer_save_dir)
            if not apk_path or not apk_path.endswith(".apk"):
                logger.error("蒲公英包下载失败或不是APK文件")
                return False

        if not os.path.exists(apk_path):
            logger.error(f"APK包不存在：{apk_path}")
            return False

        if reinstall and self.is_app_installed():
            if not self.uninstall_app():
                logger.error("覆盖安装失败：卸载旧版本失败")
                return False

        install_cmd = f"install {'-r' if reinstall else ''} -g {apk_path}"
        success, output = self._exec_platform_cmd(install_cmd)
        if success:
            logger.info(f"Android App安装成功：{self.bundle_id}")
            return True
        else:
            logger.error(f"Android App安装失败：{output}")
            return False

    def uninstall_app(self) -> bool:
        if not self.is_app_installed():
            logger.warning(f"App未安装：{self.bundle_id}")
            return True
        uninstall_cmd = f"uninstall {self.bundle_id}"
        success, _ = self._exec_platform_cmd(uninstall_cmd)
        return success

    def start_app(self) -> bool:
        if not self.is_app_installed():
            logger.error("App未安装，启动失败")
            return False
        app_activity = self.app_config.get("appActivity")
        if not app_activity:
            logger.error("未配置appActivity，无法启动应用")
            return False
        # 修复1：给am命令加shell（Android系统命令需要shell）
        start_cmd = f"shell am start -n {self.bundle_id}/{app_activity}"
        success, output = self._exec_platform_cmd(start_cmd)
        # 启动后自动激活前台
        if success:
            self.activate_app()
        # 修复2：去掉"Starting: Intent"的严格判定，仅以命令返回码为准
        return success

    def activate_app(self) -> bool:
        """Android 强制激活APP到前台"""
        if not self.is_app_installed():
            logger.error("App未安装，无法激活")
            return False
        app_activity = self.app_config.get("appActivity")
        if not app_activity:
            logger.error("未配置appActivity，无法激活应用")
            return False

        # 修复1：给am命令加shell
        activate_cmd = f"shell am start -n {self.bundle_id}/{app_activity}"
        success, output = self._exec_platform_cmd(activate_cmd)

        # 兜底：激活失败则先停止再启动
        if not success:
            logger.warning(f"激活前台失败，尝试重启APP：{output}")
            self.stop_app()
            success, output = self._exec_platform_cmd(activate_cmd)

        if success:
            logger.info(f"Android APP激活到前台成功：{self.bundle_id}")
        else:
            logger.error(f"Android APP激活到前台失败：{output}")
        return success

    def is_app_installed(self) -> bool:
        # 修复1：给pm命令加shell
        list_cmd = f"shell pm list packages {self.bundle_id}"
        success, output = self._exec_platform_cmd(list_cmd)
        return success and f"package:{self.bundle_id}" in output

    def is_app_running(self) -> bool:
        """检查Android APP是否正在运行"""
        # 修复1：给ps命令加shell
        ps_cmd = f"shell ps | grep {self.bundle_id}"
        success, output = self._exec_platform_cmd(ps_cmd)
        return success and len(
            [line for line in output.splitlines() if self.bundle_id in line and "grep" not in line]) > 0

    def _stop_app_impl(self) -> bool:
        # 修复1：给am force-stop加shell
        stop_cmd = f"shell am force-stop {self.bundle_id}"
        success, output = self._exec_platform_cmd(stop_cmd)
        if success:
            logger.info(f"停止Android APP成功：{self.bundle_id}")
        else:
            logger.error(f"停止Android APP失败：{output}")
        return success


# ======================== iOS实现类（无修改）========================
class IOSAppUtils(BaseAppUtils):
    def _exec_platform_cmd(self, cmd: str) -> Tuple[bool, str]:
        full_cmd = f"{cmd} -u {self.udid}" if self.udid else cmd
        try:
            result = subprocess.run(
                full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                encoding="gbk",  # 适配Windows中文编码
                errors="ignore",  # 忽略无法解码的字节
                timeout=60
            )
            return result.returncode == 0, result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def find_latest_app_package(self, scan_dir: str) -> Optional[str]:
        if not os.path.exists(scan_dir):
            logger.error(f"扫描目录不存在：{scan_dir}")
            return None

        ipa_files = glob.glob(os.path.join(scan_dir, "*.ipa"))
        if not ipa_files:
            logger.warning(f"目录{scan_dir}中无IPA文件")
            return None

        # 过滤不可读文件
        ipa_files = [f for f in ipa_files if os.access(f, os.R_OK)]
        if not ipa_files:
            logger.error("扫描到的IPA文件无读取权限")
            return None

        ipa_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        latest_ipa = ipa_files[0]
        logger.info(f"找到最新IPA：{latest_ipa}（修改时间：{os.path.getmtime(latest_ipa)}）")
        return latest_ipa

    def install_app(self, reinstall: bool = False, use_pgyer: bool = False) -> bool:
        ipa_path = self.app_path
        if use_pgyer:
            if not self.pgyer_shortlink:
                logger.error("未配置蒲公英短链接，无法使用蒲公英下载")
                return False
            ipa_path = download_pgyer_shortlink(self.pgyer_shortlink, save_path=self.pgyer_save_dir)
            if not ipa_path or not ipa_path.endswith(".ipa"):
                logger.error("蒲公英包下载失败或不是IPA文件")
                return False

        if not os.path.exists(ipa_path):
            logger.error(f"IPA包不存在：{ipa_path}")
            return False

        if reinstall and self.is_app_installed():
            if not self.uninstall_app():
                logger.error("覆盖安装失败：卸载旧版本失败")
                return False

        install_cmd = f"ideviceinstaller -i {ipa_path}"
        success, output = self._exec_platform_cmd(install_cmd)
        if success:
            logger.info(f"iOS App安装成功：{self.bundle_id}")
            return True
        else:
            logger.error(f"iOS App安装失败：{output}")
            return False

    def uninstall_app(self) -> bool:
        if not self.is_app_installed():
            logger.warning(f"App未安装：{self.bundle_id}")
            return True
        uninstall_cmd = f"ideviceinstaller -U {self.bundle_id}"
        success, _ = self._exec_platform_cmd(uninstall_cmd)
        return success

    def start_app(self) -> bool:
        if not self.is_app_installed():
            logger.error("App未安装，启动失败")
            return False
        start_cmd = f"ios-deploy --bundle_id {self.bundle_id} --launch"
        success, output = self._exec_platform_cmd(start_cmd)
        # 启动后自动激活前台
        if success:
            self.activate_app()
        if success:
            logger.info(f"iOS App启动成功：{self.bundle_id}")
        else:
            logger.error(f"iOS App启动失败：{output}")
        return success

    def activate_app(self) -> bool:
        """iOS 强制激活APP到前台"""
        if not self.is_app_installed():
            logger.error("App未安装，无法激活")
            return False

        # iOS 用 ios-deploy --launch 激活前台
        activate_cmd = f"ios-deploy --bundle_id {self.bundle_id} --launch"
        success, output = self._exec_platform_cmd(activate_cmd)

        if success:
            logger.info(f"iOS APP激活到前台成功：{self.bundle_id}")
        else:
            logger.error(f"iOS APP激活到前台失败：{output}")
        return success

    def is_app_installed(self) -> bool:
        list_cmd = f"ideviceinstaller -l"
        success, output = self._exec_platform_cmd(list_cmd)
        return success and self.bundle_id in output

    def is_app_running(self) -> bool:
        """检查iOS APP是否正在运行（修复重复代码+编码）"""
        # 方式1：真机检查
        ios_deploy_cmd = f"ios-deploy --bundle_id {self.bundle_id} --exists"
        success, _ = self._exec_platform_cmd(ios_deploy_cmd)
        if success:
            return True

        # 方式2：模拟器检查（仅保留一份，修复编码）
        if not self.udid or "simulator" in self.udid.lower():
            sim_ps_cmd = f"xcrun simctl spawn booted ps aux | grep {self.bundle_id}"
            try:
                result = subprocess.run(
                    sim_ps_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    encoding="gbk",  # 修复：改为GBK编码
                    errors="ignore",  # 修复：添加错误忽略
                    timeout=10
                )
                output = [line for line in result.stdout.splitlines() if self.bundle_id in line and "grep" not in line]
                return len(output) > 0
            except Exception as e:
                logger.warning(f"模拟器进程检查失败：{str(e)}")
                return False

        return False

    def _stop_app_impl(self) -> bool:
        stop_cmd = f"ios-deploy --bundle_id {self.bundle_id} --terminate"
        success, output = self._exec_platform_cmd(stop_cmd)
        if success:
            logger.info(f"停止iOS APP成功：{self.bundle_id}")
        else:
            logger.error(f"停止iOS APP失败：{output}")
        return success


# ======================== 工厂函数（无修改）========================
def get_app_utils(platform: str, app_name: str = "main", device_index: int = 0) -> BaseAppUtils:
    if platform.lower() == "android":
        return AndroidAppUtils(app_name, device_index)
    elif platform.lower() == "ios":
        return IOSAppUtils(app_name, device_index)
    else:
        raise ValueError(f"不支持的平台：{platform}")