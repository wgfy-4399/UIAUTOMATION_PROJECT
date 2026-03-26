# 海外网文APP UI自动化测试框架

> 一套代码兼容主包+多马甲包的UI自动化测试框架

## 项目简介

本项目是针对海外网文APP主包+多马甲包的UI自动化测试框架，采用 POM（Page Object Model）分层架构设计，通过差异化定位实现一套测试代码兼容主包和多个马甲包，大幅降低维护成本。

### 核心技术栈

- **移动端自动化**: Appium (支持 Android/iOS)
- **测试框架**: pytest (灵活的测试执行和参数化)
- **测试报告**: Allure (可视化报告，支持步骤记录)
- **配置管理**: YAML (多环境/多应用配置)
- **日志系统**: Python logging (彩色控制台 + 文件记录)

### 项目核心优势

- **一套代码兼容多包**: 通过 YAML 定位符配置实现主包+多马甲包（vest1/vest2/vest3）的元素定位自动适配
- **POM分层高度复用**: Page层统一封装元素操作，Case层专注业务逻辑，代码复用率极高
- **定位符配置外置**: 元素定位符存储在 YAML 文件中，新增马甲包无需修改 Python 代码
- **全流程业务覆盖**: 覆盖首页、书架、阅读器、任务中心、充值中心等核心业务模块
- **开箱即用**: 配置简单，执行入口统一，一键生成Allure测试报告

---

## 核心架构设计

### 整体架构分层逻辑

```
┌─────────────────────────────────────────────────────────────┐
│                     执行入口层 (run.py)                   │
│  - 参数解析、用例筛选、Allure报告生成                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Case层 (case/)                       │
│  - 业务逻辑编排、断言验证、Allure步骤记录                  │
│  - 按包类型+业务模块拆分（main_app/vest_app/common）      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Page层 (page/)                       │
│  - 元素定位封装、页面操作方法、差异化定位适配               │
│  - 分为：common公共层 + main_app主包层 + vest_app马甲包层 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Utils层 (utils/)                      │
│  - 驱动管理、截图、日志、数据库、断言、重试等通用能力     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     配置层 (config/)                     │
│  - app_config.yaml（应用包配置）                         │
│  - device_config.yaml（设备配置）                         │
│  - db_config.yaml（数据库配置）                          │
└─────────────────────────────────────────────────────────────┘
```

**各层核心职责与调用关系**

| 层级 | 核心职责 | 上下游调用关系 |
|------|---------|---------------|
| **执行入口层** | 解析命令行参数、组装pytest命令、清理历史数据、生成测试报告 | 调用pytest框架执行用例；依赖配置层读取环境信息 |
| **Case层** | 编排测试业务流程、验证结果、记录测试步骤 | 调用Page层的方法执行页面操作；依赖Utils层的报告工具记录Allure步骤 |
| **Page层** | 封装元素定位、实现页面操作方法、处理差异化定位 | 调用BasePage基类的通用方法；调用Utils层的截图/日志工具 |
| **Utils层** | 提供通用能力封装 | 被Page层和Case层调用；依赖配置层读取配置信息 |
| **配置层** | 管理多包、多设备、多环境配置 | 被所有层调用，提供配置数据支持 |

---

### Page层核心设计

#### 分层逻辑：统一pages页面层（主包/马甲包统一）

```
page/
├── base_page.py              # 页面基类（所有页面对象的父类）
├── landingpage.py           # 落地页（广告跳转逻辑）
└── pages/                 # 统一页面层（主包+马甲包共用）
    ├── home_page.py        # 首页（统一，使用 YAML 定位符）
    ├── shelf_page.py       # 书架（统一，使用 YAML 定位符）
    ├── reader_page.py      # 阅读器页（使用 YAML 定位符）
    ├── task_center_page.py  # 任务中心页（使用 YAML 定位符）
    ├── recharge_page.py    # 充值中心页（使用 YAML 定位符或差异化字典）
    └── chapter_list_page.py # 章节列表页
```

**设计思路**：
- **统一pages层**：所有页面对象统一放在 `page/pages` 目录下，通过 YAML 定位符配置自动适配不同应用
- **通过YAML区分app**：不再按物理目录区分主包/马甲包，统一使用 YAML 配置进行差异化定位
- **base_page和landingpage独立**：`base_page.py` 是所有页面的父类，`landingpage.py` 是特殊处理的落地页，故放在 `page` 根目录

#### 核心特性：YAML 定位符配置

**问题背景**：主包和马甲包通常使用相同的UI布局，但resource-id不同（如主包是 `com.wangwen.main:id/xxx`，马甲包是 `com.kw.literie:id/xxx`）。

**解决方案**：将定位符配置外置到 YAML 文件，通过双层结构 `{平台: {应用: 定位符值}}` 自动适配。

**定位符配置示例（新格式，包含 `type` + `value`）**（`config/locators/home_locators.yaml`）：

```yaml
# 首页定位符配置
home_tab:
  android:
    main:
      type: css          # 等价于 Selenium By.CSS_SELECTOR
      value: com.wangwen.main:id/tab_home
    vest1:
      type: css
      value: com.kw.literie:id/tab_home
    vest2:
      type: css
      value: com.kw.literie.vest2:id/tab_home
    vest3:
      type: css
      value: com.kw.literie.vest3:id/tab_home
  ios:
    main:
      type: accessibility_id        # 映射为 AppiumBy.ACCESSIBILITY_ID
      value: Discover
    vest1:
      type: accessibility_id
      value: Discover
    vest2:
      type: accessibility_id
      value: Discover
    vest3:
      type: accessibility_id
      value: Discover
```

**使用方式**（在 Page 类中）：

```python
from utils.locator_utils import load_locators, get_locator_from_config

class HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)

        # 加载定位符配置
        self._locators = load_locators("home")

        # 获取当前平台和应用名称
        self._platform = str(self.driver.capabilities.get("platformName", "android")).lower()
        self._app_name = self.driver.capabilities.get("appName", "main")

    def click_home_tab(self):
        """点击底部【首页】Tab"""
        self.wait_element_clickable(
            self._get_locator("home_tab")
        ).click()

    def _get_locator(self, element_key: str):
        """获取定位符"""
        return get_locator_from_config(
            self._locators,
            element_key,
            self._platform,
            self._app_name
        )
```

**业务适配价值**：
- 新增马甲包时，仅需在 YAML 配置文件中添加对应定位符，无需修改 Python 代码
- 同一个测试用例可以同时测试主包和所有马甲包
- 代码复用率极高，减少重复代码
- 维护成本低，定位符修改只需改配置文件

#### 基类设计：BasePage的封装价值

`BasePage` 是所有页面对象的父类，封装了所有页面通用的操作方法，统一了整个框架的元素操作规范。

**核心封装能力**：

| 功能模块 | 方法名 | 说明 |
|---------|--------|------|
| **元素定位** | `find_element()`, `find_elements()` | 智能显式等待 + 差异化定位 + 自动重试 |
| **元素点击** | `click_element()` | 支持重试 + 坐标点击兜底 |
| **文本输入** | `input_text()` | 支持先清空输入框 |
| **文本获取** | `get_element_text()` | 获取元素文本内容 |
| **属性获取** | `get_element_attribute()` | 获取元素属性（如content-desc） |
| **页面滑动** | `swipe_up()`, `swipe_down()` | 支持比例滑动，自动适配不同分辨率 |
| **上下文切换** | `switch_to_webview()`, `switch_to_native()` | WebView与原生上下文切换 |

**智能等待机制**：
- 采用"快速等待 + 兜底等待"两阶段策略，减少不必要的长时间等待
- 默认等待时间30秒，轮询间隔0.5秒
- 支持元素定位自动重试，提升测试稳定性

---

### Case层核心设计

#### 用例分层逻辑：统一扁平化结构

```
case/
├── conftest.py                  # pytest夹具配置（命令行参数、driver管理）
├── test_landing_to_reader.py    # 落地页到阅读器测试
├── test_task_center.py          # 任务中心测试
├── test_recharge.py             # 充值功能测试
├── test_home.py                 # 首页测试
├── test_reader_smoke.py         # 阅读器冒烟测试
└── test_full_flow.py            # 全流程端到端测试
```

#### 用例管理体系：pytest标记（smoke/regression/e2e/vest）的设计与使用规范

**标记定义**：
```python
@pytest.mark.smoke         # 冒烟测试（核心功能验证）
@pytest.mark.regression    # 回归测试（全量功能验证）
@pytest.mark.e2e          # 端到端测试（完整用户旅程）
@pytest.mark.vest          # 马甲包专属测试
```

**使用示例**：
```python
@pytest.mark.smoke
def test_home_basic_flow(app_name, init_driver):
    """主包首页冒烟测试"""
    # 测试逻辑...
```

**执行方式**：
- 执行所有冒烟测试：`pytest -m smoke`
- 执行所有回归测试：`pytest -m regression`
- 执行所有马甲包测试：`pytest -m vest`

#### 核心规范：100%调用Page层对象、用例内无元素定位的POM落地原则

**强制规范**：
1. **测试用例禁止直接使用By.XPATH等定位方式**，所有元素操作必须通过Page层方法完成
2. **测试用例通过Page对象的链式调用完成业务流程**，保证可读性和可维护性

**示例代码（链式调用 + Page 层封装）**：
```python
# ✅ 正确：完全调用Page层方法，配合链式返回
with AllureReportUtils.step("点击首页推荐书籍进入阅读器"):
    reader_page = home_page.click_recommend_book_by_index(0)
    assert isinstance(reader_page, ReaderPage)

with AllureReportUtils.step("从阅读器返回首页（链式调用）"):
    home_page = reader_page.back_to_home()

# ❌ 错误：在Case层直接使用定位或手动 new Page 对象串场景
with AllureReportUtils.step("点击书籍"):
    driver.find_element(By.ID, "com.kw.literie:id/book").click()

with AllureReportUtils.step("进入阅读器"):
    reader_page = ReaderPage(driver)  # 手动 new 而不是通过 ShelfPage 返回
```

**规范价值**：
- 元素定位变更时，只需修改Page层，无需修改Case层
- 提高测试用例的可读性，业务流程一目了然
- 降低维护成本，提升团队协作效率

---

### Utils层核心设计

#### 工具类的封装边界，各工具模块的核心职责

```
utils/
├── driver_utils.py      # Driver管理（单例模式）
├── app_utils.py         # 应用管理工具
├── screenshot_utils.py  # 截图工具
├── report_utils.py      # Allure报告工具
├── log_utils.py        # 日志工具
├── db_utils.py         # 数据库操作工具
├── browser_utils.py    # 浏览器工具
├── assert_utils.py     # 断言工具
├── data_utils.py       # 测试数据生成工具
└── retry_decorator.py  # 重试装饰器
```

| 工具模块 | 核心职责 | 主要方法 |
|---------|---------|---------|
| `driver_utils.py` | Driver单例管理、应用/设备切换 | `get_driver()`, `quit_driver()`, `switch_app()`, `open_browser()` |
| `screenshot_utils.py` | 全屏截图、元素截图 | `take_screenshot()`, `take_screenshot_by_element()` |
| `report_utils.py` | Allure报告生成、环境信息设置 | `set_test_case_info()`, `attach_screenshot()`, `generate_allure_report()` |
| `log_utils.py` | 彩色日志输出、日志文件管理 | `init_logger()` |
| `db_utils.py` | 数据库连接、查询、更新 | `execute_query()`, `execute_update()` |
| `assert_utils.py` | 元素存在断言、文本断言 | `assert_element_exists()`, `assert_text_equals()` |
| `data_utils.py` | 测试数据生成、清理 | `generate_random_user()`, `cleanup_test_data()` |
| `xml_capture_utils.py` | 界面 XML 采集工具 | `capture_page_source()`, `extract_interactive_elements()` |

#### 通用能力：驱动管理、日志、截图、断言、重试、数据生成等能力的复用逻辑

**Driver单例管理**：
- 使用 `DriverSingleton` 类确保全局只有一个Driver实例
- 切换应用/设备时自动销毁旧Driver，创建新实例
- 支持浏览器场景和原生应用场景无缝切换

**日志系统**：
- 彩色控制台输出（不同级别显示不同颜色）
- 日志文件按毫秒级时间戳命名，自动轮转
- 统一日志格式：`时间 - 级别 - 模块:行号 - 消息`

**截图工具**：
- 自动创建截图目录，支持全屏截图和元素截图
- 文件名格式：`时间戳_场景描述.png`
- 异常时自动截图，便于问题排查

**断言工具**：
- 封装常用断言逻辑，简化测试用例编写
- 断言失败时自动截图记录

**重试装饰器**：
- 为不稳定操作提供重试机制
- 可配置重试次数和重试间隔

---

### 执行入口设计：run.py的核心能力

`run.py` 是项目的一站式执行入口，实现了以下核心能力：

**1. 参数化适配不同测试场景**
```bash
# 支持按应用包选择
python run.py --app main       # 主包测试
python run.py --app vest1      # 马甲包1测试
python run.py --app all        # 所有包测试

# 支持按测试级别选择
python run.py --level smoke        # 冒烟测试
python run.py --level regression   # 回归测试
python run.py --level e2e         # 端到端测试

# 支持按业务模块选择
python run.py --module home      # 首页模块测试
python run.py --module reader    # 阅读器模块测试
python run.py --module task      # 任务中心测试
python run.py --module recharge  # 充值模块测试
```

**2. 一键化执行流程**
1. 清理历史数据（allure-results、截图、日志）
2. 组装pytest参数并执行测试
3. 生成Allure测试报告
4. 自动打开报告（可选）

**3. 参数组装逻辑**
- 根据 `--app` 参数决定测试哪个包
- 根据 `--level` 参数决定执行哪个标记的用例（smoke/regression/e2e）
- 根据 `--module` 参数决定执行哪个业务模块的用例

---

## 项目完整文件结构

```
UIAUTOMATION/
├── run.py                              # 执行入口（参数解析、pytest执行、报告生成）
├── pytest.ini                          # pytest配置文件
├── conftest.py                         # pytest夹具配置（命令行参数、driver管理）
│
├── scripts/                            # 工具脚本目录
│   ├── capture_xml.py                  # XML 采集命令行脚本
│   ├── capture_checkin_popup.py       # 签到弹窗采集脚本
│   └── test_xml_capture.py            # XML 采集测试工具
│
├── page/                               # 页面对象层
│   ├── __init__.py
│   ├── base_page.py                     # 页面基类（所有页面对象的父类）
│   ├── landingpage.py                   # 落地页（广告跳转逻辑）
│   └── pages/                         # 统一页面层（主包+马甲包共用）
│       ├── __init__.py
│       ├── home_page.py              # 首页（统一）
│       ├── shelf_page.py             # 书架（统一）
│       ├── reader_page.py            # 阅读器页
│       ├── task_center_page.py       # 任务中心页（支持签到弹窗处理）
│       ├── recharge_page.py         # 充值中心页
│       └── chapter_list_page.py    # 章节列表页
│
├── case/                               # 测试用例层
│   ├── conftest.py                     # pytest夹具配置（命令行参数、driver管理）
│   ├── test_landing_to_reader.py       # 落地页到阅读器测试
│   ├── test_task_center.py             # 任务中心测试
│   ├── test_rewards_smoke.py           # Rewards/任务中心冒烟测试（iOS）
│   ├── test_recharge.py                # 充值功能测试
│   ├── test_home.py                    # 首页测试
│   ├── test_reader_smoke.py            # 阅读器冒烟测试
│   └── test_full_flow.py               # 全流程端到端测试
│
├── utils/                              # 工具类层
│   ├── __init__.py
│   ├── driver_utils.py               # Driver管理（单例模式）
│   ├── app_utils.py                 # 应用管理工具
│   ├── locator_utils.py            # 定位符加载工具（新增）
│   ├── screenshot_utils.py          # 截图工具
│   ├── report_utils.py             # Allure报告工具
│   ├── log_utils.py               # 日志工具
│   ├── db_utils.py                # 数据库操作工具
│   ├── browser_utils.py           # 浏览器工具
│   ├── assert_utils.py            # 断言工具
│   ├── data_utils.py              # 测试数据生成工具
│   └── retry_decorator.py        # 重试装饰器
│
├── config/                            # 配置文件层
│   ├── read_config.py              # 配置文件读取工具
│   ├── app_config.yaml            # 应用包配置（主包/马甲包）
│   ├── device_config.yaml          # 设备列表配置
│   ├── db_config.yaml            # 数据库连接配置
│   ├── log_config.yaml           # 日志配置
│   └── locators/                # 定位符配置目录（新增）
│       ├── home_locators.yaml     # 首页定位符
│       ├── shelf_locators.yaml    # 书架定位符
│       ├── reader_locators.yaml   # 阅读器定位符
│       ├── task_center_locators.yaml # 任务中心定位符（含签到弹窗）
│       └── rewards_locators.yaml  # Rewards 页面定位符（iOS）
│
├── data/                              # 数据目录
│   └── page_xml/                    # XML 采集存储目录
│       ├── android/
│       │   ├── main/
│       │   └── vest1/
│       └── ios/
│
├── report/                            # 测试报告输出目录
│   └── screenshot/                 # 截图存储目录
│
├── log/                               # 日志文件目录
│
├── allure-results/                    # Allure测试结果目录（自动生成）
├── allure-report/                     # Allure报告目录（自动生成）
│
├── README.md                          # 项目文档
└── LOCATOR_REFACTOR_PLAN.md         # 定位符架构优化执行计划（新增）
```

---

## 环境准备与快速开始

### 前置环境要求

| 环境 | 要求 |
|------|------|
| **Python版本** | Python 3.8+ |
| **Appium环境** | Appium 1.x 或 2.x，支持 Android/iOS |
| **移动端测试环境** | Android 模拟器/真机 或 iOS 模拟器/真机 |
| **Allure** | Allure Command Line（用于生成测试报告） |
| **依赖包** | 详见项目 requirements.txt |

### 依赖安装

```bash
# 1. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 2. 安装项目依赖
pip install -r requirements.txt
```

**核心依赖清单**：
- `Appium-Python-Client`: Appium Python客户端
- `pytest`: 测试框架
- `pytest-rerunfailures`: 失败重试插件
- `allure-pytest`: Allure报告插件
- `PyYAML`: YAML配置文件解析
- `selenium`: Selenium WebDriver

### 环境校验

```bash
# 1. 验证Python版本
python --version

# 2. 验证Appium是否正常启动
appium --version

# 3. 验证设备连接
# Android
adb devices

# iOS
xcrun simctl list

# 4. 验证Allure命令
allure --version

# 5. 运行demo测试用例验证环境
pytest case/test_demo.py -v
```

---

## 测试执行指南

### 核心冒烟测试命令（主包+马甲包）

**主包冒烟测试**：
```bash
# 使用run.py执行
python run.py --app main --level smoke --module all

# 或直接使用pytest
pytest -m smoke --app main --alluredir ./allure-results
# 测试结束后会自动生成并打开 Allure 报告（需要 Allure CLI 可用：`allure --version`）
```

**马甲包1冒烟测试**：
```bash
python run.py --app vest1 --level smoke --module all
```

**所有包冒烟测试**：
```bash
python run.py --app all --level smoke --module all
```

### 全量回归测试命令

```bash
# 执行所有回归测试用例
python run.py --app all --level regression --module all

# 或使用pytest标记
pytest -m regression --app all
```

### 单业务模块测试命令（首页/阅读/任务/充值）

**首页模块测试**：
```bash
python run.py --app main --level all --module home
```

**阅读器模块测试**（包含主包+马甲包）：
```bash
python run.py --app all --level all --module reader
```

**任务中心模块测试**：
```bash
python run.py --app all --level all --module task
```

**充值模块测试**：
```bash
python run.py --app all --level all --module recharge
```

### 马甲包专属测试命令

```bash
# 马甲包1全流程测试
python run.py --app vest1 --level e2e --module all

# 马甲包2阅读器测试
pytest case/test_reader_smoke.py --app vest2 -v
```

### Allure测试报告生成与查看命令

**使用run.py自动生成并打开报告**：
```bash
python run.py --app main --level smoke
# 执行完成后会自动打开Allure报告
```

**直接使用 pytest 也会自动生成并打开报告**（并且会在开始前清理 `./allure-results`）：
```bash
pytest case/test_home.py::test_home_basic_flow --app main --platform ios --device 1 -m smoke -v --alluredir ./allure-results
```
如果你没有传 `--alluredir`，将使用项目默认的 `allure-results` 目录；前提是 `allure` 命令行已安装并可在当前环境找到（`allure --version`）。

**手动生成Allure报告**：
```bash
# 生成报告
allure generate allure-results -o allure-report --clean

# 打开报告
allure open allure-report
```

**查看历史报告**：
```bash
# 打开已有报告
allure open allure-report
```

---

## 项目开发规范

### Page层开发规范

**1. 类定义规范**
```python
from utils.locator_utils import load_locators, get_locator_from_config

class MyPage(BasePage):
    """页面对象描述（包含页面功能、核心元素、操作说明）"""

    def __init__(self, driver):
        super().__init__(driver)
        # 加载定位符配置
        self._locators = load_locators("my_page")

        # 获取当前平台和应用名称
        self._platform = str(self.driver.capabilities.get("platformName", "android")).lower()
        self._app_name = self.driver.capabilities.get("appName", "main")

    def _get_locator(self, element_key: str):
        """获取定位符"""
        return get_locator_from_config(
            self._locators,
            element_key,
            self._platform,
            self._app_name,
        )
```

**重要约定（避免定位符类型错误）**：

- Page 层的 `_get_locator` 现在兼容三种入参：
  - **字符串 key**：例如 `"home_tab"`、`"banner.list_container"`，会通过 `get_locator_from_config` 从 YAML 中解析。
  - **定位元组** `(By.XXX, "xxx")`：会直接走 `BasePage._get_locator` 逻辑。
  - **差异化定位字典**：如 `{"android": (By.ID, "xxx"), "ios": (By.XPATH, "xxx")}`，同样交由 `BasePage._get_locator` 解析。
- 推荐在 Page 内部统一只传 **字符串 key** 给 `_get_locator`，由 YAML 管理差异化；如果确实需要直接写元组/差异化字典，则可以把它们直接传给 `find_element` / `wait_element_clickable` 等方法，或传给 `_get_locator`，都会被正确处理。

**2. 元素定位符规范（YAML 配置，新格式优先，兼容旧格式）**

在 `config/locators/` 下创建对应的 YAML 文件（推荐使用包含 `type` 和 `value` 的新格式，旧格式字符串仍然兼容）：

```yaml
# my_page_locators.yaml
my_button:
  android:
    main:
      type: id
      value: "com.wangwen.main:id/btn_my"
    vest1:
      type: id
      value: "com.kw.literie:id/btn_my"
    vest2:
      type: id
      value: "com.kw.literie.vest2:id/btn_my"
    vest3:
      type: id
      value: "com.kw.literie.vest3:id/btn_my"
  ios:
    main:
      type: xpath
      value: "//XCUIElementTypeButton[@name='My']"
    vest1:
      type: xpath
      value: "//XCUIElementTypeButton[@name='My']"
    vest2:
      type: xpath
      value: "//XCUIElementTypeButton[@name='My']"
    vest3:
      type: xpath
      value: "//XCUIElementTypeButton[@name='My']"

title_text:
  android:
    main:
      type: id
      value: "com.wangwen.main:id/tv_title"
    vest1:
      type: id
      value: "com.kw.literie:id/tv_title"
    vest2:
      type: id
      value: "com.kw.literie.vest2:id/tv_title"
    vest3:
      type: id
      value: "com.kw.literie.vest3:id/tv_title"
  ios:
    main:
      type: xpath
      value: "//XCUIElementTypeStaticText[@name='Title']"
    vest1:
      type: xpath
      value: "//XCUIElementTypeStaticText[@name='Title']"
    vest2:
      type: xpath
      value: "//XCUIElementTypeStaticText[@name='Title']"
    vest3:
      type: xpath
      value: "//XCUIElementTypeStaticText[@name='Title']"
```

> 旧格式（仅字符串）仍可使用，系统会自动根据值内容推断定位方式，例如：
> ```yaml
> my_button:
>   android:
>     main: "com.wangwen.main:id/btn_my"
>   ios:
>     main: "//XCUIElementTypeButton[@name='My']"
> ```

**3. 页面操作方法规范**
```python
def click_button(self):
    """方法功能说明"""
    try:
        self.wait_element_clickable(self._get_locator("my_button")).click()
        sleep(1)
        screenshot_path = take_screenshot(self.driver, "button_clicked")
        logger.info(f"按钮点击成功，截图路径：{screenshot_path}")
        return self  # 返回自身，支持链式调用
    except Exception as e:
        screenshot_path = take_screenshot(self.driver, "button_click_fail")
        logger.error(f"按钮点击失败，截图路径：{screenshot_path}，异常：{str(e)}")
        raise e
```

### 测试用例开发规范

**1. 用例文件命名规范**
- 文件名以 `test_` 开头
- 按业务模块命名（如 `test_home.py`、`test_recharge.py`）

**2. 用例函数命名规范**
```python
def test_{业务模块}_{具体场景}(fixture参数):
    """用例描述"""
    pass
```

**3. 用例标记规范**
```python
@pytest.mark.smoke         # 冒烟测试
@pytest.mark.regression    # 回归测试
@pytest.mark.e2e          # 端到端测试
def test_function():
    pass
```

**4. Allure报告注解规范**
```python
def test_function(app_name, init_driver):
    # 1. 设置用例基本信息
    AllureReportUtils.set_test_case_info(
        "用例标题",
        "用例描述"
    )
    AllureReportUtils.add_severity("critical")
    AllureReportUtils.add_tag("smoke", "home", "main_app", app_name)

    # 2. 使用step记录测试步骤
    with AllureReportUtils.step("步骤描述"):
        # 执行操作...
        screenshot_path = take_screenshot(init_driver, "step_screenshot")
        AllureReportUtils.attach_screenshot(screenshot_path, "步骤截图")
```

### 代码风格与异常处理规范

**1. 异常处理规范**
```python
# 所有操作都要进行异常捕获
try:
    # 业务逻辑...
    logger.info("操作成功")
except TimeoutException as e:
    logger.error(f"操作超时：{str(e)}")
    raise e
except Exception as e:
    logger.error(f"操作异常：{str(e)}")
    raise e
```

**2. 日志记录规范**
```python
# 使用全局日志实例
from utils.log_utils import global_logger as logger

logger.info("信息级别日志")
logger.warning("警告级别日志")
logger.error("错误级别日志")
```

**3. 截图规范**
```python
# 异常时自动截图
try:
    # 操作...
except Exception as e:
    screenshot_path = take_screenshot(driver, "场景描述")
    logger.error(f"操作失败，截图路径：{screenshot_path}")
    raise e
```

## Rewards/Task Center 页面与签到弹窗处理

### 页面概述

任务中心页面（iOS 中称为 Rewards，Android 中称为任务中心）用于管理每日签到、任务列表和奖励领取。

### 签到弹窗处理

任务中心页面可能弹出每日签到弹窗，测试用例需要处理这种情况。

**关键定位符**：

| 元素 | iOS accessibility_id | 说明 |
|------|---------------------|------|
| task_center_tab | `Rewards` | 底部导航栏入口 |
| checkin_popup_close_button | `nl boot login close` | 签到弹窗关闭按钮 |
| checkin_popup_checkin_button | `Check in` | 签到按钮 |
| checkin_popup_title_text | `Check in now to earn 20 Vouchers!` | 签到提示文本 |

**使用示例**：

```python
from page.pages.task_center_page import TaskCenterPage

task_center = TaskCenterPage(driver)

# 导航到任务中心
task_center.wait_element_clickable(task_center._get_locator("task_center_tab")).click()

# 关闭签到弹窗（如果存在）
task_center.close_checkin_popup()  # 如果有弹窗则关闭，无弹窗则跳过

# 检查签到弹窗是否可见
has_popup = task_center.is_checkin_popup_visible()

# 点击签到按钮
task_center.click_checkin_popup_checkin()

# 每日签到
task_center.daily_check_in()

# 获取金币余额
balance = task_center.get_gold_balance()
```

**测试用例**：

```bash
# 运行任务中心冒烟测试
pytest case/test_rewards_smoke.py --app main --platform ios -v

# 运行单个测试
pytest case/test_rewards_smoke.py::TestRewardsSmoke::test_rewards_page_basic --app main --platform ios
```

### XML 采集示例

```bash
# 采集签到弹窗的 XML
python scripts/capture_checkin_popup.py
```

采集后的 XML 会自动保存到 `data/page_xml/ios/main/checkin_popup/` 目录。

---

## 工具脚本

### 定位器配置迁移工具

当需要将旧格式的配置文件迁移为新格式时，可以使用迁移脚本：

```bash
python utils/migrate_locators.py
```

该脚本会：
- 自动检测 `config/locators/` 目录下所有 `*_locators.yaml` 文件
- 将旧格式（字符串值）转换为新格式（包含 `type` 和 `value` 字段）
- 根据定位符值内容自动推断定位方式
- 创建 `.backup` 备份文件

如需回滚，可以使用备份文件恢复。

---

### 界面 XML 采集工具

用于采集应用界面的 XML 源码，支持 Android/iOS 双平台。采集后的 XML 可用于：

- AI 驱动的元素定位符自动生成
- 界面元素快速查询
- UI 变更检测
- 测试用例自动生成

**交互式采集**（推荐）：
```bash
python scripts/capture_xml.py --app main --platform android
```

**快速采集**：
```bash
python scripts/capture_xml.py --app main --platform android --page home
```

**查看已采集页面**：
```bash
python scripts/capture_xml.py --list --app main --platform android
python scripts/capture_xml.py --show home --app main --platform android
```

采集后的 XML 存储在 `data/page_xml/{platform}/{app_name}/{page_name}/` 目录下。

### XML 采集测试工具

在运行 XML 采集脚本前，可以使用测试工具验证环境是否准备就绪：

```bash
# 完整环境检查（默认检查 main + android）
python scripts/test_xml_capture.py

# 指定应用和平台
python scripts/test_xml_capture.py --app vest1 --platform ios

# 仅显示快速验证步骤
python scripts/test_xml_capture.py --quick

# 仅显示故障排查指南
python scripts/test_xml_capture.py --troubleshoot
```

**检查项目**：

| 检查项 | 说明 | 验证命令 |
|--------|------|----------|
| **Appium Server** | 确认服务已启动 | 检查 4723 端口 |
| **设备连接** | Android/iOS 设备已连接 | `adb devices` / `xcrun simctl list` |
| **设备配置** | device_config.yaml 格式正确 | YAML 解析 + 必需字段验证 |
| **应用配置** | app_config.yaml 包含目标应用 | appPackage/bundleId 存在 |
| **Python 依赖** | 必需包已安装 | Appium-Python-Client, pytest, PyYAML |

---

### 新增马甲包适配规范

**1. 修改配置文件**
在 `config/app_config.yaml` 中添加新马甲包配置：
```yaml
vest4:
  android:
    appPackage: "com.kw.literie.vest4"
    appActivity: "com.kw.literie.vest4.MainActivity"
    appPath: "/apk/vest4_android_v1.0.0.apk"
  ios:
    bundleId: "com.wangwen.vest4"
    appPath: "/ipa/vest4_ios_v1.0.0.ipa"
```

**2. 修改定位符配置文件**
在对应的 YAML 定位符配置文件中添加新马甲包的定位符：

```yaml
# config/locators/home_locators.yaml
home_tab:
  android:
    # ... 现有配置 ...
    vest4: "com.kw.literie.vest4:id/tab_home"  # 新增
  ios:
    # ... 现有配置 ...
    vest4: "//XCUIElementTypeButton[@name='Home']"  # 新增
```

**3. 修改conftest.py**
在命令行参数choices中添加新马甲包：
```python
parser.addoption(
    "--app",
    choices=["main", "vest1", "vest2", "vest3", "vest4"],  # 新增
    help="指定测试的应用"
)
```

**4. 新增测试用例（统一）**
所有测试用例统一放在 case/ 目录下，通过 pytest 标记（smoke/regression/e2e/vest）和命令行参数（--app）来筛选执行不同类型的测试。

---

## 项目维护与扩展指南

### 新增业务模块的标准流程

**1. 创建定位符配置文件**
```bash
# 在 config/locators/ 下创建新定位符配置文件
touch config/locators/my_new_page_locators.yaml
```

**2. 实现定位符配置**
```yaml
# config/locators/my_new_page_locators.yaml
my_button:
  android:
    main: "com.wangwen.main:id/btn_my"
    vest1: "com.kw.literie:id/btn_my"
    vest2: "com.kw.literie.vest2:id/btn_my"
    vest3: "com.kw.literie.vest3:id/btn_my"
  ios:
    main: "//XCUIElementTypeButton[@name='My']"
    vest1: "//XCUIElementTypeButton[@name='My']"
    vest2: "//XCUIElementTypeButton[@name='My']"
    vest3: "//XCUIElementTypeButton[@name='My']"
```

**3. 创建页面对象**
```bash
# 在 page/pages/ 或 page/common/ 下创建新页面对象
touch page/pages/my_new_page.py
```

**4. 实现页面对象类**
```python
from page.base_page import BasePage
from utils.locator_utils import load_locators, get_locator_from_config
from utils.log_utils import global_logger as logger

class MyNewPage(BasePage):
    """新页面对象描述"""

    def __init__(self, driver):
        super().__init__(driver)
        # 加载定位符配置
        self._locators = load_locators("my_new_page")

        # 获取当前平台和应用名称
        self._platform = str(self.driver.capabilities.get("platformName", "android")).lower()
        self._app_name = self.driver.capabilities.get("appName", "main")

    def _get_locator(self, element_key: str):
        """获取定位符"""
        return get_locator_from_config(
            self._locators,
            element_key,
            self._platform,
            self._app_name
        )

    def click_my_button(self):
        """点击我的按钮"""
        try:
            self.wait_element_clickable(self._get_locator("my_button")).click()
            logger.info("已点击我的按钮")
            return self
        except Exception as e:
            logger.error(f"点击我的按钮失败：{e}")
            raise e
```

**5. 创建测试用例**
```bash
# 在 case/ 下创建新测试文件
touch case/test_my_new_page.py
```

**6. 实现测试用例**
```python
import pytest
from page.pages.my_new_page import MyNewPage
from utils.report_utils import AllureReportUtils

@pytest.mark.smoke
def test_my_new_functionality(init_driver):
    AllureReportUtils.set_test_case_info("新功能测试", "测试新功能...")
    page = MyNewPage(init_driver)
    page.click_my_button()
```

**7. 执行验证**
```bash
# 使用run.py执行新模块测试
python run.py --app main --level smoke --module my_new
```

### 新增马甲包的标准流程

详见上方「新增马甲包适配规范」部分。

### 扩展工具能力的标准流程

**1. 创建新工具类**
```bash
touch utils/my_new_utils.py
```

**2. 实现工具方法**
```python
class MyNewUtils:
    @staticmethod
    def my_util_function():
        # 工具方法逻辑...
        pass
```

**3. 在Page层或Case层引用**
```python
from utils.my_new_utils import MyNewUtils

# 使用工具方法
result = MyNewUtils.my_util_function()
```

### 常见问题排查

**问题1：元素定位失败**
- 检查定位符是否正确（使用Appium Inspector查看）
- 确认是否使用了差异化定位
- 检查是否需要等待页面加载完成

**问题2：Driver创建失败**
- 确认Appium Server是否正常启动
- 检查设备是否连接
- 检查配置文件中的设备参数是否正确

**问题3：测试报告生成失败**
- 确认Allure Command Line是否正确安装
- 检查allure-results目录是否存在
- 检查是否有写入权限

**问题4：用例执行超时**
- 检查网络是否正常
- 增加元素等待时间
- 检查应用是否有弹窗或加载动画

---

## 附录

### pytest标记说明

| 标记 | 含义 | 使用场景 |
|------|------|---------|
| `smoke` | 冒烟测试 | 核心功能快速验证，确保版本基本可用 |
| `regression` | 回归测试 | 全量功能测试，确保新版本无问题 |
| `e2e` | 端到端测试 | 完整用户旅程测试 |
| `vest` | 马甲包专属 | 马甲包独有功能测试 |

### 配置文件说明

**app_config.yaml**：应用包配置
- 主包配置（main）：Android/iOS的包名、Activity、Bundle ID、应用路径
- 马甲包配置（vest1/vest2/vest3）：同上

**device_config.yaml**：设备配置
- 设备列表：UDID、平台、平台版本、Appium端口
- Driver全局配置：noReset、fullReset、unicodeKeyboard等

**db_config.yaml**：数据库配置
- 多环境支持（test/pre/prod）
- 多数据库支持（main_db/order_db）

### 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.1.0 | 2026-03-24 | 新增 XML 采集测试工具、Rewards/Task Center 页面支持、签到弹窗处理 |
| 1.0.0 | 2026-03-12 | 初始版本，完成核心冒烟测试、全量回归测试、优化与扩展 |

---

**本项目遵循自动化测试行业专业规范，代码结构清晰，易于维护和扩展。**
