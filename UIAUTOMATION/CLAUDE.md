# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在此代码库中工作的指导。

## 项目概述

这是一个面向海外网文APP（主包+多马甲包）的UI自动化测试框架。采用 POM（Page Object Model）分层架构，通过 YAML 定位符配置实现一套代码兼容主包和多个马甲包（vest1/vest2/vest3），大幅降低维护成本。

**技术栈**: Appium (Android/iOS)、pytest、Allure报告、YAML配置

## 测试执行命令

### 直接使用 pytest
```bash
# 主包Android冒烟测试（会自动生成并打开Allure报告）
pytest -m smoke --app main --platform android --device 0

# 马甲包1阅读器测试
pytest case/test_reader_smoke.py --app vest1 -v

# 指定allure目录
pytest case/ --app main --alluredir ./allure-results
```

### 使用 run.py（便捷入口）
```bash
# 主包冒烟测试
python run.py --app main --level smoke

# 所有包冒烟测试
python run.py --app all --level smoke --module all

# 指定模块测试
python run.py --app vest1 --module reader --platform ios --device 1
```

**注意**: 直接运行 pytest 会自动清理旧的 `allure-results` 并在测试结束后生成/打开报告（需安装 Allure CLI）。

### Pytest 标记
- `smoke`: 冒烟测试（核心功能验证）
- `regression`: 回归测试（全量功能）
- `e2e`: 端到端测试（完整用户旅程）
- `vest`: 马甲包专属测试

## 核心架构

### 分层结构
```
run.py           -> 执行入口层（参数解析、pytest执行、报告生成）
case/            -> 测试用例层（业务逻辑编排、断言验证、Allure步骤记录）
page/pages/      -> 页面对象层（元素定位封装、页面操作方法、差异化定位适配）
utils/           -> 工具层（驱动管理、截图、日志、数据库、断言、重试等通用能力）
config/          -> 配置层（app_config.yaml、device_config.yaml、locators/*.yaml）
```

### YAML 定位符配置（核心设计）

框架使用双层结构 `{平台: {应用: 定位符值}}` 自动适配不同应用包的元素定位，实现一套代码测试多包。

**新格式示例** (`config/locators/home_locators.yaml`):
```yaml
home_tab:
  android:
    main:
      type: id
      value: "com.wangwen.main:id/tab_home"
    vest1:
      type: id
      value: "com.kw.literie:id/tab_home"
  ios:
    main:
      type: accessibility_id
      value: "Discover"
```

**定位符类型映射**: `id` → By.ID, `xpath` → By.XPATH, `css` → By.CSS_SELECTOR, `accessibility_id` → AppiumBy.ACCESSIBILITY_ID

旧格式（纯字符串）仍然兼容，系统会自动推断定位方式。

### Page Object 开发规范

所有页面类继承 `BasePage`，使用以下标准模式：

```python
from page.base_page import BasePage
from utils.locator_utils import load_locators, get_locator_from_config
from utils.log_utils import global_logger as logger

class HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self._locators = load_locators("home")
        self._platform = str(self.driver.capabilities.get("platformName", "android")).lower()
        self._app_name = self.driver.capabilities.get("appName", "main")

    def _get_locator(self, element_key: str):
        """获取定位符（兼容三种格式：字符串key/元组/差异化字典）"""
        if isinstance(element_key, (tuple, dict)):
            return super()._get_locator(element_key)
        return get_locator_from_config(
            self._locators, element_key, self._platform, self._app_name
        )

    def click_home_tab(self):
        """点击底部【首页】Tab"""
        try:
            self.wait_element_clickable(self._get_locator("home_tab")).click()
            logger.info("已点击底部【首页】Tab")
            sleep(1)
            return self  # 支持链式调用
        except Exception as e:
            screenshot_path = take_screenshot(self.driver, "click_home_tab_fail")
            logger.error(f"点击失败，截图：{screenshot_path}，异常：{e}")
            raise e
```

**重要规范**:
- 页面方法应返回 `self` 或下一个页面对象以支持链式调用
- 所有操作必须包含 try-except 异常处理
- 异常时自动截图记录

### 测试用例开发规范

```python
import pytest
from page.pages.home_page import HomePage
from utils.report_utils import AllureReportUtils
from utils.screenshot_utils import take_screenshot

@pytest.mark.smoke
def test_home_basic_flow(app_name, init_driver):
    """首页核心冒烟流程"""
    # 1. 设置用例基本信息
    AllureReportUtils.set_test_case_info("首页核心冒烟", "验证首页加载和Tab切换")
    AllureReportUtils.add_severity("critical")
    AllureReportUtils.add_tag("smoke", "home", app_name)

    home_page = HomePage(init_driver)

    # 2. 使用step记录测试步骤
    with AllureReportUtils.step("点击首页Tab"):
        home_page.click_home_tab()
        screenshot_path = take_screenshot(init_driver, "home_tab_clicked")
        AllureReportUtils.attach_screenshot(screenshot_path, "点击后截图")

    # 3. 断言验证
    assert app_name in ["main", "vest1", "vest2", "vest3"]
```

**强制规范**: 测试用例禁止直接使用 By.XPATH 等定位方式，所有元素操作必须通过 Page 层方法完成。

### 驱动管理

`utils/driver_utils.py` 中的 `DriverSingleton` 实现单例模式：
- 全局唯一 Driver 实例
- 切换应用/设备时自动销毁旧 Driver，创建新实例
- 支持浏览器场景和原生应用场景无缝切换

驱动通过 `conftest.py` 的 pytest 夹具创建：
- `init_driver`: 会话级驱动（所有用例共用）
- `app_name`, `device_index`, `device_platform`: 命令行参数夹具

### 配置文件说明

- `config/app_config.yaml`: 应用包配置（主包/马甲包的 appPackage、appActivity、bundleId、appPath、蒲公英短链接）
- `config/device_config.yaml`: 设备列表配置（UDID、平台、平台版本、Appium端口）+ 全局Driver配置
- `config/locators/*.yaml`: 按页面组织的元素定位符（home_locators.yaml、shelf_locators.yaml等）

## 新增马甲包流程

1. **修改应用配置**: 在 `config/app_config.yaml` 中添加新马甲包配置
2. **添加定位符**: 在所有 `config/locators/*_locators.yaml` 中添加新马甲包的定位符
3. **更新参数选项**: 修改 `conftest.py` 和 `run.py` 中的 `--app` choices
4. **无需修改代码**: 现有测试用例无需任何修改即可运行

## 新增业务模块流程

1. 创建定位符配置: `config/locators/my_new_page_locators.yaml`
2. 创建页面对象: `page/pages/my_new_page.py`（继承 BasePage）
3. 创建测试用例: `case/test_my_new_page.py`（使用 Page 对象）
4. 执行验证: `pytest case/test_my_new_page.py --app main`

## 常用工具方法

| 工具模块 | 方法 | 说明 |
|---------|------|------|
| `screenshot_utils.py` | `take_screenshot(driver, name)` | 全屏截图到 `report/screenshot/` |
| `report_utils.py` | `AllureReportUtils.set_test_case_info()` | 设置用例标题/描述 |
| `report_utils.py` | `AllureReportUtils.step()` | 记录测试步骤（上下文管理器） |
| `report_utils.py` | `AllureReportUtils.attach_screenshot()` | 附加截图到报告 |
| `log_utils.py` | `global_logger` | 彩色日志（INFO/WARNING/ERROR） |
| `driver_utils.py` | `get_driver(platform, app_name, device_index)` | 获取Driver实例 |
| `driver_utils.py` | `open_browser_and_visit_url(url)` | 打开浏览器访问URL |
| `xml_capture_utils.py` | `XMLCaptureUtils.capture_page_source()` | 采集界面XML并保存到文件 |
| `xml_capture_utils.py` | `XMLCaptureUtils.extract_interactive_elements()` | 从XML中提取可交互元素 |
| `xml_capture_utils.py` | `XMLCaptureUtils.list_captured_pages()` | 列出已采集的页面 |

## Rewards/Task Center 页面

任务中心页面（iOS 中称为 Rewards，Android 中称为任务中心）用于管理每日签到、任务列表和奖励领取。

### 页面对象

```python
from page.pages.task_center_page import TaskCenterPage

task_center = TaskCenterPage(driver)

# 导航到任务中心
task_center.wait_element_clickable(task_center._get_locator("task_center_tab")).click()

# 关闭签到弹窗（如果存在）
task_center.close_checkin_popup()

# 检查签到弹窗是否可见
has_popup = task_center.is_checkin_popup_visible()

# 点击签到按钮
task_center.click_checkin_popup_checkin()

# 每日签到
task_center.daily_check_in()

# 获取金币余额
balance = task_center.get_gold_balance()

# 点击任务规则入口
task_center.click_task_rule_entry()
```

### 签到弹窗处理

任务中心页面可能弹出每日签到弹窗，测试用例需要处理这种情况：

```python
# 导航后自动关闭弹窗
task_center.wait_element_clickable(task_center._get_locator("task_center_tab")).click()
task_center.close_checkin_popup()  # 如果有弹窗则关闭，无弹窗则跳过

# 或者先检查再处理
if task_center.is_checkin_popup_visible():
    task_center.click_checkin_popup_checkin()  # 点击签到
    # 或
    task_center.close_checkin_popup()  # 关闭弹窗
```

### 关键定位符

| 元素 | iOS accessibility_id | 说明 |
|------|---------------------|------|
| task_center_tab | `Rewards` | 底部导航栏入口 |
| checkin_popup_close_button | `nl boot login close` | 签到弹窗关闭按钮 |
| checkin_popup_checkin_button | `Check in` | 签到按钮 |
| task_list_container | `//XCUIElementTypeTable` | 任务列表容器 |
| reward_button | `//XCUIElementTypeButton[@name='领取']` | 领取奖励按钮 |

### 测试用例

```bash
# 运行任务中心冒烟测试
pytest case/test_rewards_smoke.py --app main --platform ios -v

# 运行单个测试
pytest case/test_rewards_smoke.py::TestRewardsSmoke::test_rewards_page_basic --app main --platform ios
```

## 界面 XML 采集工具

### 采集命令

```bash
# 交互式采集（推荐）
python scripts/capture_xml.py --app main --platform android

# 快速采集指定页面
python scripts/capture_xml.py --app main --platform android --page home

# 查看已采集的页面
python scripts/capture_xml.py --list --app main --platform android

# 查看某个页面的元素详情
python scripts/capture_xml.py --show home --app main --platform android
```

### 代码中使用

```python
from utils.xml_capture_utils import XMLCaptureUtils

# 采集当前页面 XML
xml_content = XMLCaptureUtils.capture_page_source(
    driver=init_driver,
    page_name="home",
    app_name="main",
    platform="android"
)

# 提取可交互元素
elements = XMLCaptureUtils.extract_interactive_elements(xml_content)

# 生成元素摘要
summary = XMLCaptureUtils.generate_element_summary(elements)
```

### XML 存储结构

```
data/page_xml/
├── android/
│   ├── main/
│   │   ├── home/
│   │   │   ├── home_20260324_143022.xml
│   │   │   └── home_20260324_143022_meta.json
│   │   └── shelf/
│   └── vest1/
└── ios/
```

## XML 采集脚本测试工具

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

### 检查项目

测试工具会自动检查以下项目：

| 检查项 | 说明 | 验证命令 |
|--------|------|----------|
| **Appium Server** | 确认服务已启动 | 检查 4723 端口 |
| **设备连接** | Android/iOS 设备已连接 | `adb devices` / `xcrun simctl list` |
| **设备配置** | device_config.yaml 格式正确 | YAML 解析 + 必需字段验证 |
| **应用配置** | app_config.yaml 包含目标应用 | appPackage/bundleId 存在 |
| **Python 依赖** | 必需包已安装 | Appium-Python-Client, pytest, PyYAML |

### 快速验证步骤

```bash
# 1. 启动 Appium Server
appium

# 2. 检查设备连接 (Android)
adb devices

# 3. 运行环境测试
python scripts/test_xml_capture.py --app main --platform android

# 4. 运行采集脚本
python scripts/capture_xml.py --app main --platform android

# 5. 检查输出
ls -la data/page_xml/android/main/
```

### 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| Driver 创建失败 | Appium 未启动 | `appium` |
| Driver 创建失败 | 设备未连接 | `adb devices` 检查 |
| Driver 创建失败 | Appium 端口被占用 | `lsof -i :4723` + `kill -9 <PID>` |
| 应用启动失败 | 应用未安装 | 手动安装或配置 appPath |
| 找不到元素 | appPackage 不匹配 | `adb shell pm list packages` 检查 |

## Pytest 配置

`pytest.ini` 中的关键配置：
- `reruns = 2`: 失败重跑2次
- `reruns_delay = 3`: 重跑间隔3秒
- `testpaths = case`: 测试用例目录
- `markers`: 定义 smoke/regression/e2e/vest 标记

## 定位符迁移工具

当需要将旧格式配置迁移为新格式时：
```bash
python utils/migrate_locators.py
```
该脚本会自动转换 `config/locators/` 下所有 YAML 文件，并创建 `.backup` 备份。

## 双 CC 协作工作流程

双 CC 模式是一种并行工作流程，CC1 负责页面元素抓取，CC2 负责测试用例编写，通过 MEMORY.md 文件同步进度。

### 协作状态值

| 状态 | 说明 |
|------|------|
| `IDLE` | 空闲状态，无活跃任务 |
| `CC1_WORKING` | CC1 正在抓取元素 |
| `CC1_COMPLETED` | CC1 已完成，CC2 可开始 |
| `CC2_WORKING` | CC2 正在编写测试 |
| `COMPLETED` | 双 CC 协作完成 |

### 终端 1：CC1 工作流（元素抓取）

```bash
# 1. 进入项目目录
cd /Users/zhuanzmima0000/UIautomation_project/UIAUTOMATION

# 2. 启动 CC1 工作流（自动创建 worktree 和分支）
python scripts/sync/cc1_start.py --page profile

# 3. 进入 worktree
cd .claude/worktrees/cc1

# 4. 启动 Claude Code
claude

# 5. 参考 scripts/sync/CC1_PROMPT.md 中的提示词执行任务
```

### 终端 2：CC2 工作流（测试开发）

```bash
# 1. 检查 CC1 状态
python scripts/sync/check_status.py

# 2. 当状态变为 CC1_COMPLETED 后，启动 CC2
python scripts/sync/cc2_start.py --page profile

# 3. 进入 worktree
cd .claude/worktrees/cc2

# 4. 启动 Claude Code
claude

# 5. 参考 scripts/sync/CC2_PROMPT.md 中的提示词执行任务
```

### 辅助脚本

| 脚本 | 功能 |
|------|------|
| `scripts/sync/check_status.py` | 解析 MEMORY.md 协作状态 |
| `scripts/sync/cc1_start.py` | CC1 工作流入口脚本 |
| `scripts/sync/cc2_start.py` | CC2 工作流入口脚本 |
| `scripts/validate/validate_locators.py` | YAML 定位符验证 |
| `scripts/sync/CC1_PROMPT.md` | CC1 提示词模板 |
| `scripts/sync/CC2_PROMPT.md` | CC2 提示词模板 |

### CC1 工作流程

1. **启动工作流**: `python scripts/sync/cc1_start.py --page <page_name>`
2. **采集 XML**: `python scripts/capture_xml.py --app main --platform ios`
3. **创建定位符配置**: 编辑 `config/locators/<page_name>_locators.yaml`
4. **验证配置**: `python scripts/validate/validate_locators.py`
5. **完成工作流**: `python scripts/sync/cc1_start.py --complete --page <page_name>`

### CC2 工作流程

1. **等待 CC1 完成**: 使用 `check_status.py` 检查状态
2. **启动工作流**: `python scripts/sync/cc2_start.py --page <page_name>`
3. **创建 Page Object**: 编辑 `page/pages/<page_name>_page.py`
4. **创建测试用例**: 编辑 `case/test_<page_name>.py`
5. **运行测试**: `pytest case/test_<page_name>.py --app main`
6. **完成工作流**: `python scripts/sync/cc2_start.py --complete --page <page_name>`

### 协作时序图

```
时间轴 →

终端1 (CC1): [启动脚本] → [创建worktree] → [抓取元素] → [编写Locator] → [完成]
                                                           ↓
                                                     MEMORY.md 更新
                                                           ↓
终端2 (CC2):                                          [检测CC1完成] → [创建worktree] → [编写测试]
```

### 关键文件路径

| 组件 | 路径 | 用途 |
|------|------|------|
| XMLCaptureUtils | `utils/xml_capture_utils.py` | XML 抓取 |
| load_locators | `utils/locator_utils.py` | 加载定位符 |
| BasePage | `page/base_page.py` | Page Object 基类 |
| init_driver | `conftest.py` | pytest fixture |
| MEMORY.md | `MEMORY.md` | 协作状态同步文件 |
