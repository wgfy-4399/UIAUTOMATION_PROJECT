import os
import random
import string
from typing import Any, Dict

import yaml

from utils.log_utils import global_logger as logger


# ------------------------------ 随机测试数据生成 ------------------------------

def generate_oversea_phone(country_code: str = "+1") -> str:
    """
    生成随机海外手机号（仅用于测试，无真实短信能力）
    :param country_code: 国家区号（默认美国+1，可传入+44/+61等）
    :return: 形如：+1-5551234567 的测试手机号
    """
    # 为避免生成真实运营商号段，这里使用 555 开头的测试号段
    local_part = f"555{random.randint(1000000, 9999999)}"
    phone = f"{country_code}-{local_part}"
    logger.info(f"生成随机海外测试手机号：{phone}")
    return phone


def generate_username(prefix: str = "test_user") -> str:
    """
    生成随机用户名：前缀+短随机串
    :param prefix: 用户名前缀
    :return: 例如：test_user_ab12CD
    """
    suffix = "".join(random.choices(string.ascii_letters + string.digits, k=6))
    username = f"{prefix}_{suffix}"
    logger.info(f"生成随机测试用户名：{username}")
    return username


def generate_recharge_amount(min_amount: int = 1, max_amount: int = 100) -> int:
    """
    生成随机充值金额（单位：元/币种，可根据业务映射）
    :param min_amount: 最小金额（含）
    :param max_amount: 最大金额（含）
    :return: 随机整数金额
    """
    if min_amount <= 0 or max_amount < min_amount:
        raise ValueError(f"随机充值金额区间非法：min={min_amount}, max={max_amount}")
    amount = random.randint(min_amount, max_amount)
    logger.info(f"生成随机充值金额：{amount}")
    return amount


def generate_book_id(prefix: str = "book_", length: int = 8) -> str:
    """
    生成随机书籍ID（仅用于测试数据，与真实后台ID解耦）
    :param prefix: ID前缀
    :param length: 随机部分长度
    :return: 例如：book_a1B2c3D4
    """
    rand_part = "".join(random.choices(string.ascii_letters + string.digits, k=length))
    book_id = f"{prefix}{rand_part}"
    logger.info(f"生成随机书籍ID：{book_id}")
    return book_id


# ------------------------------ YAML 测试数据读写 ------------------------------

def read_yaml_data(file_path: str) -> Dict[str, Any]:
    """
    从指定YAML文件读取测试数据
    :param file_path: YAML文件路径
    :return: 数据字典
    """
    if not file_path:
        raise ValueError("YAML文件路径不能为空！")

    if not os.path.exists(file_path):
        logger.error(f"YAML测试数据文件不存在：{file_path}")
        raise FileNotFoundError(f"YAML测试数据文件不存在：{file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            logger.warning(f"YAML文件{file_path}内容不是字典，将返回空字典")
            return {}
        logger.info(f"成功读取YAML测试数据文件：{file_path}")
        return data
    except yaml.YAMLError as e:
        logger.error(f"解析YAML测试数据文件失败：{file_path}，异常：{str(e)}")
        raise
    except Exception as e:
        logger.error(f"读取YAML测试数据文件失败：{file_path}，异常：{str(e)}")
        raise


def write_yaml_data(file_path: str, data: Dict[str, Any]) -> None:
    """
    将测试数据写入指定YAML文件（覆盖写入）
    :param file_path: YAML文件路径
    :param data: 要写入的字典数据
    """
    if not file_path:
        raise ValueError("YAML文件路径不能为空！")
    if not isinstance(data, dict):
        raise TypeError("写入YAML的数据必须为字典类型！")

    dir_name = os.path.dirname(os.path.abspath(file_path))
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        logger.info(f"成功写入YAML测试数据文件：{file_path}")
    except Exception as e:
        logger.error(f"写入YAML测试数据文件失败：{file_path}，异常：{str(e)}")
        raise


# ------------------------------ 测试数据清理 ------------------------------

def cleanup_yaml_data(file_path: str) -> None:
    """
    清空指定YAML测试数据文件内容（保留文件，只清空数据）
    :param file_path: YAML文件路径
    """
    if not file_path:
        raise ValueError("YAML文件路径不能为空！")

    if not os.path.exists(file_path):
        logger.warning(f"要清理的YAML测试数据文件不存在：{file_path}，忽略清理操作")
        return

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("")  # 写入空内容
        logger.info(f"已清空YAML测试数据文件内容：{file_path}")
    except Exception as e:
        logger.error(f"清理YAML测试数据文件失败：{file_path}，异常：{str(e)}")
        raise


def remove_test_data_files(*file_paths: str) -> None:
    """
    删除指定的测试数据文件（如用于tearDown阶段清理临时数据）
    :param file_paths: 一个或多个文件路径
    """
    for path in file_paths:
        if not path:
            continue
        if not os.path.exists(path):
            logger.warning(f"测试数据文件不存在，无需删除：{path}")
            continue
        try:
            os.remove(path)
            logger.info(f"已删除测试数据文件：{path}")
        except Exception as e:
            logger.error(f"删除测试数据文件失败：{path}，异常：{str(e)}")
            raise


def prepare_test_data_file(base_dir: str, filename: str = "test_data.yaml") -> str:
    """
    在指定目录下准备一个可读写的测试数据YAML文件路径
    :param base_dir: 基础目录（如项目根目录下的某个data目录）
    :param filename: 文件名（默认test_data.yaml）
    :return: 绝对路径
    """
    if not base_dir:
        raise ValueError("测试数据基础目录不能为空！")
    abs_dir = os.path.abspath(base_dir)
    os.makedirs(abs_dir, exist_ok=True)
    file_path = os.path.join(abs_dir, filename)
    logger.info(f"测试数据文件准备完成：{file_path}")
    return file_path


if __name__ == "__main__":
    # 简单自测示例（实际使用中可删除或替换为单元测试）
    phone = generate_oversea_phone("+61")
    username = generate_username("qa_user")
    amount = generate_recharge_amount(5, 50)
    book_id = generate_book_id()
    logger.info(f"[自测] phone={phone}, username={username}, amount={amount}, book_id={book_id}")

