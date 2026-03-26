import functools
import time
import traceback
from typing import Callable, Iterable, Tuple, Type, TypeVar, Any, Union

from utils.log_utils import global_logger as logger
from utils.screenshot_utils import take_screenshot


F = TypeVar("F", bound=Callable[..., Any])


def _extract_driver_from_args_kwargs(args: Tuple[Any, ...], kwargs: dict) -> Any:
    """
    尝试从装饰器包裹的函数参数中提取 driver 实例：
    1. 用例/页面实例方法：self.driver
    2. 显式传入 driver: func(..., driver=driver)
    """
    # 实例方法：优先从 self.driver 中获取
    if args:
        first = args[0]
        if hasattr(first, "driver"):
            driver = getattr(first, "driver", None)
            if driver is not None:
                return driver

    # 普通函数：从关键字参数中获取
    driver = kwargs.get("driver")
    return driver


def retry(
    tries: int = 3,
    delay: float = 1.0,
    exceptions: Union[Type[BaseException], Iterable[Type[BaseException]]] = Exception,
    backoff: float = 1.0,
) -> Callable[[F], F]:
    """
    通用重试装饰器：
    - 支持自定义重试次数、间隔时间、捕获异常类型
    - 每次重试打印详细日志
    - 所有重试失败后自动截图（若能获取 driver）

    :param tries: 最大重试次数（包含首次执行），最小为1
    :param delay: 初始重试间隔（秒）
    :param exceptions: 触发重试的异常类型或异常元组
    :param backoff: 间隔递增倍数（>1 表示指数退避）
    """
    if tries < 1:
        raise ValueError("参数 tries 必须 >= 1")
    if backoff <= 0:
        raise ValueError("参数 backoff 必须 > 0")

    # 统一异常类型为元组形式，兼容单个类型和可迭代类型
    if isinstance(exceptions, type) and issubclass(exceptions, BaseException):
        retry_exceptions: Tuple[Type[BaseException], ...] = (exceptions,)
    else:
        retry_exceptions = tuple(exceptions)  # type: ignore[arg-type]

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _delay = delay
            attempt = 0
            last_exc: BaseException | None = None

            while attempt < tries:
                try:
                    attempt += 1
                    logger.info(
                        f"执行函数 `{func.__name__}`，第 {attempt}/{tries} 次尝试，"
                        f"delay={_delay:.2f}s"
                    )
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(f"函数 `{func.__name__}` 在第 {attempt} 次重试后执行成功")
                    return result
                except retry_exceptions as e:  # type: ignore[misc]
                    last_exc = e
                    # 最后一次失败，退出循环
                    if attempt >= tries:
                        break

                    # 中间失败：记录日志并等待后重试
                    logger.warning(
                        f"函数 `{func.__name__}` 第 {attempt}/{tries} 次执行抛出异常：{e!r}，"
                        f"{_delay:.2f}s 后重试\n"
                        f"Traceback:\n{traceback.format_exc()}"
                    )
                    time.sleep(_delay)
                    _delay *= backoff
                except Exception as e:
                    # 非重试异常：直接抛出
                    logger.error(
                        f"函数 `{func.__name__}` 执行出现非重试异常：{e!r}\n"
                        f"Traceback:\n{traceback.format_exc()}"
                    )
                    raise

            # 所有尝试失败：尝试截图并抛出最后一次异常
            driver = _extract_driver_from_args_kwargs(args, kwargs)
            if driver is not None:
                try:
                    screenshot_path = take_screenshot(
                        driver, f"retry_fail_{func.__name__}"
                    )
                    logger.error(
                        f"函数 `{func.__name__}` 重试 {tries} 次仍然失败，已自动截图：{screenshot_path}"
                    )
                except Exception as se:  # 截图失败不影响原始异常抛出
                    logger.error(
                        f"函数 `{func.__name__}` 重试失败后自动截图也失败：{se!r}"
                    )
            else:
                logger.error(
                    f"函数 `{func.__name__}` 重试 {tries} 次仍失败，未能获取 driver，跳过截图"
                )

            if last_exc is not None:
                raise last_exc
            # 理论上不会走到这里，仅兜底
            raise RuntimeError(f"函数 `{func.__name__}` 重试机制异常：未捕获到最后一次异常")

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = ["retry"]

