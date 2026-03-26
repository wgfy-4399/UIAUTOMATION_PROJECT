import allure
import os
import json
import subprocess
import pathlib
import configparser
import platform
from allure_commons.types import Severity
from utils.log_utils import global_logger as logger


class AllureReportUtils:
    """Allure测试报告工具类"""

    # 支持的严重级别（关联Allure枚举，避免非法值）
    SUPPORTED_SEVERITY = {
        "blocker": Severity.BLOCKER,
        "critical": Severity.CRITICAL,
        "normal": Severity.NORMAL,
        "minor": Severity.MINOR,
        "trivial": Severity.TRIVIAL
    }

    @staticmethod
    def set_test_case_info(title, description=""):
        """
        设置测试用例信息
        :param title: 测试用例标题（必填）
        :param description: 测试用例描述
        """
        if not title or not isinstance(title, str):
            raise ValueError("测试用例标题不能为空且必须为字符串！")

        allure.dynamic.title(title.strip())
        if description and isinstance(description, str):
            allure.dynamic.description(description.strip())
        logger.info(f"Allure用例信息已设置 - 标题：{title.strip()}")

    @staticmethod
    def attach_screenshot(screenshot_path, name="Screenshot"):
        """
        附加截图到报告（校验文件有效性）
        :param screenshot_path: 截图文件路径
        :param name: 附件名称
        """
        # 参数校验
        if not screenshot_path or not isinstance(screenshot_path, str):
            logger.error("截图路径不能为空且必须为字符串！")
            raise ValueError("截图路径不能为空且必须为字符串！")

        screenshot_file = pathlib.Path(screenshot_path)
        if not screenshot_file.exists():
            logger.error(f"截图文件不存在：{screenshot_path}")
            raise FileNotFoundError(f"截图文件不存在：{screenshot_path}")

        if screenshot_file.suffix.lower() not in [".png", ".jpg", ".jpeg"]:
            logger.error(f"截图文件格式不支持：{screenshot_file.suffix}（仅支持PNG/JPG/JPEG）")
            raise ValueError(f"截图文件格式不支持：{screenshot_file.suffix}（仅支持PNG/JPG/JPEG）")

        try:
            with open(screenshot_file, 'rb') as image_file:
                allure.attach(
                    image_file.read(),
                    name=name.strip(),
                    attachment_type=allure.attachment_type.PNG if screenshot_file.suffix.lower() == ".png" else allure.attachment_type.JPG
                )
            logger.info(f"✅ 截图已附加到Allure报告: {screenshot_path}")
        except PermissionError as e:
            logger.error(f"❌ 附加截图失败：无文件读取权限 - {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ 附加截图失败: {str(e)}")
            raise

    @staticmethod
    def attach_text(content, name="Text Content"):
        """
        附加文本内容到报告（校验内容非空）
        :param content: 文本内容
        :param name: 附件名称
        """
        if not isinstance(content, str):
            content = str(content)  # 非字符串转字符串

        if not content.strip():
            logger.warning("附加的文本内容为空，跳过附加")
            return

        try:
            allure.attach(
                content.strip(),
                name=name.strip(),
                attachment_type=allure.attachment_type.TEXT
            )
            logger.info(f"✅ 文本内容已附加到Allure报告: {name.strip()}")
        except Exception as e:
            logger.error(f"❌ 附加文本内容失败: {str(e)}")
            raise

    @staticmethod
    def attach_json(data, name="JSON Data"):
        """
        附加格式化的JSON数据到报告（优化格式）
        :param data: JSON数据（字典）
        :param name: 附件名称
        """
        if not isinstance(data, dict):
            raise TypeError("附加的JSON数据必须为字典类型！")

        try:
            # 格式化JSON（缩进2、支持中文）
            json_content = json.dumps(data, ensure_ascii=False, indent=2)
            allure.attach(
                json_content,
                name=name.strip(),
                attachment_type=allure.attachment_type.JSON
            )
            logger.info(f"✅ JSON数据已附加到Allure报告: {name.strip()}")
        except TypeError as e:
            logger.error(f"❌ JSON数据格式错误：无法序列化 - {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ 附加JSON数据失败: {str(e)}")
            raise

    @staticmethod
    def step(step_description):
        """
        生成Allure步骤上下文管理器（支持自定义逻辑）
        :param step_description: 步骤描述
        :return: Allure步骤上下文管理器
        """
        if not step_description.strip():
            step_description = "未命名步骤"

        logger.info(f"📝 Allure步骤: {step_description.strip()}")
        return allure.step(step_description.strip())  # 返回上下文管理器，让用户自定义步骤内逻辑

    @staticmethod
    def add_test_case_link(url, link_type="custom", name="Link"):
        """
        添加链接到测试用例（校验URL合法性）
        :param url: 链接地址（http/https开头）
        :param link_type: 链接类型 (issue/testcase/custom)
        :param name: 链接名称
        """
        # 基础URL校验
        if not url.strip() or not url.startswith(("http://", "https://")):
            raise ValueError(f"链接地址不合法：{url}（必须以http/https开头）")

        link_type = link_type.lower()
        if link_type not in ["issue", "testcase", "custom"]:
            logger.warning(f"链接类型非法：{link_type}，默认使用custom")
            link_type = "custom"

        try:
            if link_type == "issue":
                allure.dynamic.issue(url.strip(), name.strip())
            elif link_type == "testcase":
                allure.dynamic.testcase(url.strip(), name.strip())
            else:
                allure.dynamic.link(url.strip(), name=name.strip())
            logger.info(f"✅ 链接已添加到Allure报告: {url.strip()}")
        except Exception as e:
            logger.error(f"❌ 添加链接失败: {str(e)}")
            raise

    @staticmethod
    def add_environment_info(environment_data, overwrite=True):
        """
        添加环境信息（推荐写入environment.properties文件，符合Allure规范）
        :param environment_data: 环境信息字典
        :param overwrite: 是否覆盖已有文件
        """
        if not isinstance(environment_data, dict) or not environment_data:
            raise ValueError("环境信息必须为非空字典！")

        # 获取Allure结果目录
        allure_results_dir = setup_allure_environment()
        env_file = pathlib.Path(allure_results_dir) / "environment.properties"

        # 处理文件写入逻辑
        write_mode = "w" if overwrite else "a"
        try:
            with open(env_file, write_mode, encoding="utf-8") as f:
                for key, value in environment_data.items():
                    # 过滤空值，避免无效配置
                    if key.strip() and value is not None:
                        f.write(f"{key.strip()}={str(value).strip()}\n")
            logger.info(f"✅ 环境信息已写入文件: {env_file}")
        except PermissionError as e:
            logger.error(f"❌ 写入环境文件失败：无权限 - {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ 添加环境信息失败: {str(e)}")
            raise

    @staticmethod
    def add_severity(severity_level: str = "normal"):
        """
        设置严重级别（校验合法值，关联Allure枚举）
        :param severity_level: 严重级别 (blocker/critical/normal/minor/trivial)
        """
        severity_level = severity_level.lower()
        if severity_level not in AllureReportUtils.SUPPORTED_SEVERITY:
            raise ValueError(f"严重级别非法！支持的级别：{list(AllureReportUtils.SUPPORTED_SEVERITY.keys())}")

        try:
            allure.dynamic.severity(AllureReportUtils.SUPPORTED_SEVERITY[severity_level])
            logger.info(f"✅ 严重级别已设置: {severity_level}")
        except Exception as e:
            logger.error(f"❌ 设置严重级别失败: {str(e)}")
            raise

    @staticmethod
    def add_tag(*tags):
        """
        添加标签（过滤空标签）
        :param tags: 标签列表
        """
        valid_tags = [tag.strip() for tag in tags if tag.strip()]
        if not valid_tags:
            logger.warning("无有效标签，跳过添加")
            return

        try:
            for tag in valid_tags:
                allure.dynamic.tag(tag)
            logger.info(f"✅ 标签已添加: {valid_tags}")
        except Exception as e:
            logger.error(f"❌ 添加标签失败: {str(e)}")
            raise


def setup_allure_environment():
    """
    设置Allure环境配置（创建结果目录，返回绝对路径）
    :return: Allure结果目录绝对路径
    """
    # 改用pathlib处理路径，跨平台友好
    report = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    allure_dir = report / "allure-results"

    # 创建目录（不存在则创建，存在则忽略）
    allure_dir.mkdir(parents=True, exist_ok=True)

    allure_dir_abs = str(allure_dir.absolute())
    logger.info(f"✅ Allure环境已设置，结果目录: {allure_dir_abs}")

    return allure_dir_abs


def get_allure_command_path():
    """
    分层获取Allure Command Line路径（解决硬编码）
    优先级：环境变量(ALLURE_COMMAND_PATH) > 配置文件 > PATH自动查找 > 兜底路径
    :return: Allure可执行文件路径
    """
    # 步骤1：读取系统环境变量（优先级最高，用户可灵活配置）
    env_allure_path = os.environ.get("ALLURE_COMMAND_PATH")
    if env_allure_path and os.path.exists(env_allure_path):
        logger.info(f"✅ 从环境变量获取Allure路径: {env_allure_path}")
        return env_allure_path

    # 步骤2：读取配置文件（兼容配置文件不存在的情况）
    config = configparser.ConfigParser()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config.ini")
    cfg_allure_path = ""
    fallback_path = ""
    if os.path.exists(config_path):
        config.read(config_path, encoding="utf-8")
        # 读取配置文件里的command_path
        cfg_allure_path = config.get("allure", "command_path", fallback="").strip()
        # 读取兜底路径
        fallback_path = config.get("allure", "fallback_path", fallback="").strip()

    # 步骤2.1：配置文件的command_path有效
    if cfg_allure_path and os.path.exists(cfg_allure_path):
        logger.info(f"✅ 从配置文件获取Allure路径: {cfg_allure_path}")
        return cfg_allure_path

    # 步骤3：自动查找系统PATH里的Allure（适配已配置环境变量的场景）
    system_platform = platform.system()
    allure_cmd = "allure.bat" if system_platform == "Windows" else "allure"
    for path in os.environ["PATH"].split(os.pathsep):
        cmd_path = os.path.join(path, allure_cmd)
        if os.path.exists(cmd_path):
            logger.info(f"✅ 从系统PATH自动找到Allure路径: {cmd_path}")
            return cmd_path

    # 步骤4：使用配置文件的兜底路径（替代硬编码）
    if fallback_path and os.path.exists(fallback_path):
        logger.info(f"✅ 使用兜底Allure路径: {fallback_path}")
        return fallback_path

    # 所有方式都失败，抛出异常
    raise FileNotFoundError(
        "❌ 未找到Allure Command Line！请通过以下方式之一配置：\n"
        "1. 设置系统环境变量 ALLURE_COMMAND_PATH=你的allure.bat路径\n"
        "2. 在项目根目录创建config.ini，添加：\n"
        "   [allure]\n"
        "   command_path=你的allure.bat路径\n"
        "   fallback_path=你的allure.bat路径\n"
        "3. 将allure的bin目录添加到系统PATH"
    )


def generate_allure_report(report_dir=None, results_dir=None,
                           open_report=False):
    """
    生成Allure报告（实际执行命令，支持自动打开报告）
    :param report_dir: 报告输出目录
    :param results_dir: 结果输入目录
    :param open_report: 是否生成后自动打开报告
    :return: 报告相关信息（命令、路径等）
    """
    # ========== 关键：获取Allure路径（无硬编码） ==========
    try:
        allure_cmd_path = get_allure_command_path()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # 初始化默认路径
    report = pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not report_dir:
        report_dir = str(report / "allure-report")
    if not results_dir:
        results_dir = str(report / "allure-results")

    # 确保目录存在
    pathlib.Path(report_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(results_dir).mkdir(parents=True, exist_ok=True)

    # 构建命令（使用动态获取的路径，修复变量名错误）
    commands = [
        allure_cmd_path,  # 修复：替换未定义的allure_bat_path
        "generate",
        results_dir,
        "-o", report_dir,
        "--clean"
    ]

    try:
        # 执行生成命令（捕获输出）
        logger.info(f"📢 执行Allure报告生成命令: {' '.join(commands)}")
        result = subprocess.run(
            commands,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"✅ Allure报告生成成功！输出目录: {report_dir}")
        logger.debug(f"命令输出: {result.stdout}")

        # 自动打开报告（可选，单独捕获异常，避免打开失败影响生成结果）
        if open_report:
            open_commands = [allure_cmd_path, "open", report_dir]  # 修复：使用正确的变量名
            try:
                subprocess.Popen(open_commands)
                logger.info(f"🌐 Allure报告已自动打开: {report_dir}")
            except Exception as e:
                logger.warning(f"⚠️ 自动打开报告失败（不影响报告生成）！可手动打开：{report_dir}\\index.html，错误：{str(e)}")

        return {
            "command": ' '.join(commands),
            "report_dir": report_dir,
            "results_dir": results_dir,
            "status": "success"
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 生成报告失败：命令执行错误 - {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"❌ 生成Allure报告失败: {str(e)}")
        raise