from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy

from page.base_page import BasePage
from utils.locator_utils import load_locators, get_locator_from_config
from utils.log_utils import global_logger as logger


class HomePage(BasePage):
    """
    首页页面对象（统一，不再区分主包/马甲包）
    - 底部Tab切换
    - Banner点击
    - 推荐书籍点击
    - 搜索入口点击
    """

    def __init__(self, driver):
        super().__init__(driver)

        # 加载定位符配置
        self._locators = load_locators("home")

        # 获取当前平台和应用名称
        self._platform = str(self.driver.capabilities.get("platformName", "android")).lower()
        self._app_name = self.driver.capabilities.get("appName", "main")

    def _get_locator(self, locator, locator_type: str = None):
        """
        获取定位符（兼容 BasePage 差异化定位逻辑）
        :param locator: 元素键名字符串，或已解析好的定位符（元组/差异化字典）
        :param locator_type: 定位符类型（可选，None 表示从配置中读取或自动推断）
        :return: 定位符元组
        """
        # 已经是 BasePage 支持的定位格式（元组或差异化字典）时，直接交给父类处理
        if isinstance(locator, (tuple, dict)):
            return super()._get_locator(locator)

        # 否则按 element_key 从 YAML 配置中解析
        element_key = locator
        return get_locator_from_config(
            self._locators,
            element_key,
            self._platform,
            self._app_name,
            locator_type,
        )

    # ------------------------------ 底部 Tab 切换 ------------------------------

    def click_home_tab(self):
        """点击底部【首页】Tab"""
        try:
            self.wait_element_clickable(self._get_locator("home_tab")).click()
            logger.info("已点击底部【首页】Tab")
            sleep(1)
            return self
        except Exception as e:
            logger.error(f"点击底部【首页】Tab 失败：{e}")
            raise e

    def click_shelf_tab(self):
        """点击底部【书架】Tab"""
        try:
            self.wait_element_clickable(self._get_locator("shelf_tab")).click()
            logger.info("已点击底部【书架】Tab")
            sleep(1)
            # 延迟导入，避免循环依赖
            from page.pages.shelf_page import ShelfPage

            return ShelfPage(self.driver)
        except Exception as e:
            logger.error(f"点击底部【书架】Tab 失败：{e}")
            raise e

    def click_task_tab(self):
        """点击底部【任务】Tab"""
        try:
            self.wait_element_clickable(self._get_locator("task_tab")).click()
            logger.info("已点击底部【任务】Tab")
            sleep(1)
            # 任务中心属于共用页面，固定返回 TaskCenterPage，异常时抛出由上层处理
            from page.pages.task_center_page import TaskCenterPage

            return TaskCenterPage(self.driver)
        except Exception as e:
            logger.error(f"点击底部【任务】Tab 失败：{e}")
            raise e

    def click_mine_tab(self):
        """点击底部【我的】Tab"""
        try:
            self.wait_element_clickable(self._get_locator("mine_tab")).click()
            logger.info("已点击底部【我的】Tab")
            sleep(1)
            return self
        except Exception as e:
            logger.error(f"点击底部【我的】Tab 失败：{e}")
            raise e

    def click_genre_tab(self):
        """点击底部【分类】Tab"""
        try:
            self.wait_element_clickable(self._get_locator("genre_tab")).click()
            logger.info("已点击底部【分类】Tab")
            sleep(1)
            return self
        except Exception as e:
            logger.error(f"点击底部【分类】Tab 失败：{e}")
            raise e


    # ------------------------------ 顶部tab 点击 ------------------------------
    def click_top_tab_by_index(self, index: int = 0):
        """
        点击顶部tab中的某一个tab
        :param index: tab下标（从0开始）
        """
        try:
            top_tab_container = self.find_element(self._get_locator("top_tab_list"))
            top_tabs = top_tab_container.find_elements(By.XPATH, ".//*")
            if not top_tabs:
                raise RuntimeError("未找到任何顶部tab元素")
            if index < 0 or index >= len(top_tabs):
                raise IndexError(f"顶部tab下标越界：index={index}, 总数={len(top_tabs)}")
            top_tabs[index].click()
            logger.info(f"已点击顶部tab中第 {index} 个tab（总共 {len(top_tabs)} 个）")
            sleep(1)
            return self
        except Exception as e:
            logger.error(f"点击顶部tab失败：{e}")
            raise e

    def click_top_first_tab(self):
        """点击顶部第一个tab"""
        try:
            self.wait_element_clickable(self._get_locator("top_first_tab")).click()
            logger.info("已点击顶部第一个tab")
            sleep(1)
            return self
        except Exception as e:
            logger.error(f"点击顶部第一个tab失败：{e}")
            raise e


    # ------------------------------ 推荐书籍点击 ------------------------------

    def click_recommend_book_by_index(self, index: int = 0):
        """
        点击首页推荐书籍列表中的某一本书
        - Android：按推荐列表下标点击
        - iOS：按 3*N 榜单区块下的元素索引点击
        :param index: 书籍下标/榜单元素下标（从0开始）
        """
        try:
            if self._platform == "android":
                # Android：使用推荐书籍列表容器 + 下标点击
                book_list_container = self.find_element(self._get_locator("recommend_book_list"))
                books = book_list_container.find_elements(By.XPATH, ".//*")
                if not books:
                    raise RuntimeError("未找到任何推荐书籍元素")

                if index < 0 or index >= len(books):
                    raise IndexError(f"推荐书籍下标越界：index={index}, 总数={len(books)}")

                books[index].click()
                logger.info(f"已点击首页推荐书籍列表中第 {index} 本书（总共 {len(books)} 本）")
            else:
                # iOS：按照 3*N 榜单标题定位区块，再在榜单容器内按索引点击
                # 1. 等待并找到 3*N 榜单标题
                section_title = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (AppiumBy.ACCESSIBILITY_ID, "3*N榜单页卡-新-测试-1")
                    )
                )

                # 2. 找到标题下方的书籍列表父容器（使用 YAML 中的 recommend_book_list 定位器）
                #    YAML 中本身就是通过该标题的 following-sibling::XCUIElementTypeCell[1] 来定位容器
                book_list_container = self.find_element(self._get_locator("recommend_book_list"))

                # 3. 在父容器内获取所有可点击的目标元素列表，这里统一抓取 StaticText
                elements = book_list_container.find_elements(
                    AppiumBy.CLASS_NAME,
                    "XCUIElementTypeStaticText",
                )

                # 过滤可见元素（可选增强稳定性）
                visible_elements = [el for el in elements if el.is_displayed()]
                if not visible_elements:
                    raise RuntimeError("在 3*N 榜单容器内未找到任何可见元素")

                if index < 0 or index >= len(visible_elements):
                    raise IndexError(
                        f"3*N 榜单元素下标越界：index={index}, 总数={len(visible_elements)}"
                    )

                # 简单版本：直接点击该索引位置的元素
                target_element = visible_elements[index]
                target_element.click()

                logger.info(
                    f"已点击 iOS 3*N 榜单中索引为 {index} 的元素（可见元素总数={len(visible_elements)}）"
                )

            sleep(1)
            # 打开书籍后，通常会进入阅读器页面
            try:
                from page.pages.reader_page import ReaderPage

                return ReaderPage(self.driver)
            except Exception:
                return self
        except Exception as e:
            logger.error(f"点击推荐书籍失败：{e}")
            raise e

    # ------------------------------ 搜索入口 ------------------------------

    def click_search_entry(self):
        """点击首页搜索入口（搜索框/搜索图标）"""
        try:
            self.wait_element_clickable(self._get_locator("search_entry")).click()
            logger.info("已点击首页搜索入口")
            sleep(1)
            return self
        except Exception as e:
            logger.error(f"点击首页搜索入口失败：{e}")
            raise e

     # ------------------------------ 任务中心气泡 ------------------------------
    def click_task_center_bubble(self):
        """点击任务中心气泡"""
        try:
            self.wait_element_clickable(self._get_locator("task_center_bubble")).click()
            logger.info("已点击任务中心气泡")
            sleep(1)
            from page.pages.task_center_page import TaskCenterPage
            return TaskCenterPage(self.driver)
        except Exception as e:
            logger.error(f"点击任务中心气泡失败：{e}")
            raise e
