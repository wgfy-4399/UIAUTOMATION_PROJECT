import yaml
import os
from utils.log_utils import global_logger as logger
# 配置文件路径
APP_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.yaml")
DEVICE_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "device_config.yaml")
# 数据库配置路径
DB_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_config.yaml")


def load_device_config(device_index):
    """
        读取设备配置，返回指定索引的设备信息
        :param device_index: 设备索引（默认第1个设备）
        :return: ({'index': 0, 'platform': 'android', 'udid': 'DUM0219703006996', 'appium_port': 4723}, 'android')
        """
    try:
        with open(DEVICE_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        devices = config.get("devices", [])
        if not devices:
            raise ValueError("设备配置为空！请检查device_config.yaml")
        if device_index >= len(devices):
            logger.warning(f"设备索引{device_index}超出范围，使用第1个设备")

            return devices[0]
        for device in devices:
            if device_index == device["index"]:
                return device
        return devices[0]


    except Exception as e:
        logger.error(f"读取设备配置失败！异常信息：{str(e)}")
        raise e


def load_app_config(app_name, platform):
    """
    修复版：读取多包配置，返回指定应用的配置（主包/马甲包）
    :param app_name: 应用名称（main/vest1/vest2/vest3）
    :param platform: 平台（android/ios）
    :return: 应用配置字典（appPackage/appActivity等）
    """
    try:
        with open(APP_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 步骤1：获取指定app_name的配置（优先）
        app_level_config = config.get(app_name)
        # 步骤2：如果app_name不存在，或指定platform的配置不存在 → 用main的对应platform配置兜底
        if not app_level_config or platform not in app_level_config:
            logger.warning(f"应用{app_name}的{platform}配置缺失，返回主包{platform}配置")
            return config.get("main", {}).get(platform, {})

        # 步骤3：返回指定app_name+platform的配置（确保返回字典，避免None）
        return app_level_config.get(platform, {})

    except FileNotFoundError:
        logger.error(f"配置文件不存在：{APP_CONFIG_PATH}")
        raise
    except KeyError as e:
        logger.error(f"配置键缺失：{e}")
        raise
    except Exception as e:
        logger.error(f"读取应用配置失败！异常信息：{str(e)}")


def load_driver_global_config() :
    """读取Driver全局配置（noReset/newCommandTimeout等）"""
    try:
        with open(DEVICE_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("driver_config", {})
    except Exception as e:
        # logger.error(f"读取Driver全局配置失败！异常信息：{str(e)}")
        raise e

def load_db_config(env="test", db_type = "main_db") :
    """
    读取数据库配置（支持指定环境/数据库类型）
    :param env: 环境（test/pre/prod），默认使用配置中的default
    :param db_type: 数据库类型（main_db/order_db）
    :return: 数据库连接配置字典
    """
    try:
        with open(DB_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 确定使用的环境
        use_env = env or config["env"]["default"]
        if use_env not in config["env"]:
            # logger.warning(f"环境{use_env}未配置，使用默认test环境")
            use_env = "test"

        # 读取指定类型的数据库配置
        db_config = config["env"][use_env].get(db_type)
        if not db_config:
            raise ValueError(f"{use_env}环境下未配置{db_type}数据库！")

        # logger.info(f"加载数据库配置：环境={use_env}，类型={db_type}，主机={db_config['host']}")
        return db_config
    except Exception as e:
        # logger.error(f"读取数据库配置失败！异常：{str(e)}")
        raise e

if __name__ == '__main__':
    print(load_db_config(env="test", db_type = "main_db"))
