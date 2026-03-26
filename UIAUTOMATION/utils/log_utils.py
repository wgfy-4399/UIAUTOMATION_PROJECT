import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# 日志存储路径
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 定义日志颜色（ANSI 转义码）
LOG_COLORS = {
    logging.DEBUG: '\033[0;36m',  # 青色
    logging.INFO: '\033[0;32m',   # 绿色（替换掉红色）
    logging.WARNING: '\033[0;33m',# 黄色
    logging.ERROR: '\033[0;31m',  # 红色（仅ERROR/CRITICAL用）
    logging.CRITICAL: '\033[0;35m'# 紫色
}
RESET_COLOR = '\033[0m'  # 重置颜色（避免后续输出变色）

class ColoredStreamHandler(logging.StreamHandler):
    """自定义带颜色的控制台日志处理器"""
    def emit(self, record):
        try:
            # 给日志添加对应级别的颜色
            color = LOG_COLORS.get(record.levelno, RESET_COLOR)
            # 拼接颜色码和日志内容
            record.msg = f"{color}{record.msg}{RESET_COLOR}"
            super().emit(record)
        except Exception:
            self.handleError(record)

def get_log_file_path():
    """动态生成毫秒级日志文件路径"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    log_filename = f"{timestamp[:-3]}.log"
    return os.path.join(LOG_DIR, log_filename)

def init_logger(name = "app_auto_test", level = logging.INFO) :
    """初始化日志配置（带颜色控制）"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. 带颜色的控制台处理器（跟随全局级别）
    console_handler = ColoredStreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 文件处理器（无颜色，保留原始内容）
    file_handler = RotatingFileHandler(
        filename=get_log_file_path(),
        maxBytes=50 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# 全局日志实例
global_logger = init_logger()

