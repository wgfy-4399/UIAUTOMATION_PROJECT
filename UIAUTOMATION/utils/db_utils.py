import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB
from utils.log_utils import global_logger as logger
from config.read_config import load_db_config

class DBUtils:
    """数据库操作工具类：封装连接池、查询、执行等能力"""
    # 连接池缓存（key：环境+数据库类型，value：连接池实例）
    _pool_cache = {}

    def __init__(self, env = None, db_type = "main_db"):
        """
        初始化：加载配置并创建连接池
        :param env: 数据库环境（test/pre/prod）
        :param db_type: 数据库类型（main_db/order_db）
        """
        self.env = env or "test"
        self.db_type = db_type
        self.pool_key = f"{self.env}_{self.db_type}"
        # 初始化连接池（单例，避免重复创建）
        self.pool = self._get_or_create_pool()

    def _get_or_create_pool(self) :
        """获取/创建连接池（单例模式）"""
        if self.pool_key in DBUtils._pool_cache:
            return DBUtils._pool_cache[self.pool_key]

        # 加载数据库配置
        db_config = load_db_config(self.env, self.db_type)
        # 创建连接池（参数说明：最小空闲连接/最大连接数/连接参数）
        pool = PooledDB(
            creator=pymysql,
            mincached=1,
            maxcached=5,
            maxconnections=10,
            blocking=True,
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
            charset=db_config["charset"],
            connect_timeout=db_config["timeout"],
            cursorclass=DictCursor  # 游标返回字典格式（字段名:值）
        )
        DBUtils._pool_cache[self.pool_key] = pool
        logger.info(f"创建数据库连接池：{self.pool_key}，主机={db_config['host']}")
        return pool

    def get_connection(self):
        """从连接池获取连接（自动归还，无需手动关闭）"""
        return self.pool.connection()

    def query_one(self, sql: str, params = None) :
        """
        执行查询：返回单条结果（字典格式）
        :param sql: 查询SQL（支持参数化，如 "SELECT * FROM user WHERE phone=%s"）
        :param params: SQL参数（元组，如 ("13800138000",)）
        :return: 单条结果字典，无结果返回None
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            logger.info(f"执行查询SQL：{sql}，参数：{params}")
            cursor.execute(sql, params or ())
            result = cursor.fetchone()
            logger.info(f"查询结果（单条）：{result}")
            return result
        except Exception as e:
            logger.error(f"查询SQL执行失败！SQL：{sql}，参数：{params}，异常：{str(e)}")
            raise e
        finally:
            # 关闭游标（连接自动归还连接池）
            if cursor:
                cursor.close()

    def query_all(self, sql: str, params = None) :
        """
        执行查询：返回多条结果（列表+字典格式）
        :return: 结果列表，无结果返回空列表
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            logger.info(f"执行查询SQL：{sql}，参数：{params}")
            cursor.execute(sql, params or ())
            results = cursor.fetchall()
            logger.info(f"查询结果（多条）：共{len(results)}条")
            return results
        except Exception as e:
            logger.error(f"查询SQL执行失败！SQL：{sql}，参数：{params}，异常：{str(e)}")
            raise e
        finally:
            if cursor:
                cursor.close()

    def execute(self, sql: str, params = None) -> int:
        """
        执行增/删/改操作（支持事务）
        :return: 受影响的行数
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            logger.info(f"执行SQL：{sql}，参数：{params}")
            affected_rows = cursor.execute(sql, params or ())
            conn.commit()  # 提交事务
            return affected_rows
        except Exception as e:
            if conn:
                conn.rollback()  # 回滚事务
            logger.error(f"SQL执行失败！已回滚，SQL：{sql}，参数：{params}，异常：{str(e)}")
            raise e
        finally:
            if cursor:
                cursor.close()

    def batch_execute(self, sql: str, params_list) -> int:
        """
        批量执行SQL（如批量插入）
        :param params_list: 参数列表（如 [(1, 'a'), (2, 'b')]）
        :return: 受影响的总行数
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            logger.info(f"批量执行SQL：{sql}，参数组数：{len(params_list)}")
            affected_rows = cursor.executemany(sql, params_list)
            conn.commit()
            logger.info(f"批量SQL执行成功，受影响行数：{affected_rows}")
            return affected_rows
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"批量SQL执行失败！已回滚，SQL：{sql}，异常：{str(e)}")
            raise e
        finally:
            if cursor:
                cursor.close()

    def close_pool(self):
        """关闭连接池（测试结束后调用）"""
        if self.pool_key in DBUtils._pool_cache:
            self.pool.close()
            del DBUtils._pool_cache[self.pool_key]
            logger.info(f"关闭数据库连接池：{self.pool_key}")

    # 上下文管理器：自动管理连接（推荐用with语句）
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"数据库操作异常：{exc_val}")
        # 无需手动关闭连接，连接池自动管理


# ------------------------------ 全局快捷函数 ------------------------------
def get_db_utils(env: str = None, db_type = "main_db") -> DBUtils:
    """快捷获取数据库工具类实例"""
    return DBUtils(env, db_type)

# ------------------------------ 查询 ------------------------------

def query_user_by_id(user_id: str, env: str = None) :
    """
    业务快捷函数：根据手机号查询用户信息（封装常用SQL，避免case层写原生SQL）
    """
    sql = "SELECT * FROM fq_users WHERE id=%s"
    return get_db_utils(env).query_one(sql, (user_id,))

def query_order_by_user_id(user_id: str, env: str = None) :
    """业务快捷函数：查询用户所有订单"""
    return get_db_utils(env).query_all(
        "SELECT * FROM `fq_orders` WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,)
    )



# ------------------------------ 修改 ------------------------------

def update_user_balance(user_id: str, balance: int, env: str = None) -> int:
    """业务快捷函数：更新用户余额"""
    sql = "UPDATE fq_user_assets SET balance=%s WHERE user_id=%s"
    return get_db_utils(env).execute(sql, (balance, user_id))

def update_behavior_records_by_user_id(user_id: str, last_created_or_event_time: str, env: str = None) -> int:
    """业务快捷函数：更新用户余额"""
    sql = "UPDATE fq_user_behavior_records SET last_created_or_event_time=%s WHERE user_id=%s"
    return get_db_utils(env).execute(sql, (last_created_or_event_time, user_id))


# ------------------------------ 新增 ------------------------------
# def insert_fq_chapter_unlock_record_details_by_user_id(user_id: str, balance: int, freeze_balance: int = 0, env: str = None) -> int:
#     """
#     业务快捷函数：新增用户解锁记录（插入fq_chapter_unlock_record_details表）
#     :param user_id: 用户ID
#     :param balance: 可用余额
#     :param freeze_balance: 冻结余额（默认0）
#     :param env: 数据库环境
#     :return: 受影响的行数（新增成功返回1）
#     """
#     # 插入SQL：字段和占位符一一对应，支持默认值
#     sql = """
#         INSERT INTO fq_user_assets (user_id, balance, freeze_balance, created_at, updated_at)
#         VALUES (%s, %s, %s, NOW(), NOW())
#     """
#     # 参数元组顺序必须和SQL中的%s完全一致
#     return get_db_utils(env).execute(sql, (user_id, balance, freeze_balance))

# ------------------------------ 批量新增 ------------------------------
def batch_insert_chapter_unlock_details(params_list: list, env: str = None) -> int:
    """
    业务快捷函数：批量新增章节解锁记录详情（核心使用batch_execute）
    :param params_list: 批量参数列表，每个元组对应一条记录（顺序严格对应字段）：
                        元组顺序：user_id, channel_id, user_type, type, book_id, chapter_id,
                                 sort_id, coin, red_envelope, task_red_envelope, recharge_red_envelope,
                                 compensation_red_envelope, initial_price, end_chapter_id, diff_price,
                                 nums, discount_before_price
    :param env: 数据库环境（test/dev/prod）
    :return: 受影响的总行数（成功插入的记录数）
    """
    # 校验空列表：避免无意义的SQL执行
    if not params_list:
        logger.warning("批量新增章节解锁记录：参数列表为空，无需执行")
        return 0

    # SQL字段顺序严格对应表结构（排除自增id、自动生成的时间字段）
    sql = """
          INSERT INTO fq_chapter_unlock_record_details_1 (user_id, channel_id, user_type, type, book_id, chapter_id, \
                                                          sort_id, coin, red_envelope, task_red_envelope, \
                                                          recharge_red_envelope, \
                                                          compensation_red_envelope, initial_price, end_chapter_id, \
                                                          diff_price, \
                                                          nums, discount_before_price) \
          VALUES (%s, %s, %s, %s, %s, %s, \
                  %s, %s, %s, %s, %s, \
                  %s, %s, %s, %s, \
                  %s, %s) \
          """
    # 核心调用batch_execute实现批量插入
    return get_db_utils(env).batch_execute(sql, params_list)

# ------------------------------ 删除 ------------------------------
def delete_user_welfare_by_user_id(user_id: str, env: str = None) -> int:
    """
    业务快捷函数：删除指定用户的所有福利记录
    :param user_id: 用户ID
    :param env: 数据库环境
    :return: 受影响的行数
    """
    # 按user_id删除：删除该用户的所有福利记录
    sql = "DELETE FROM fq_user_welfares WHERE user_id=%s"
    return get_db_utils(env).execute(sql, (user_id,))

