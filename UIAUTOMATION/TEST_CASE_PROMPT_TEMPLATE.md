# 测试用例生成提示词模板

## 模板说明
此模板用于指导AI/Cursor基于Appium Inspector元素信息生成符合项目规范的测试用例。

---

## 📋 执行流程

### 第1步：确认测试场景
根据用户指定的【模块名】和【级别】，询问要测试的具体场景：
- 列出该模块常见场景供用户选择
- 允许用户补充自定义场景

### 第2步：确认Page类
- 检查项目中是否存在对应的Page类文件
  - 主包：`page/main_app/【模块名】_page.py`
  - 马甲包：`page/vest_app/【模块名】_page_vest.py`
  - 共用：`page/common/【模块名】_page.py`
- 如存在，列出已有元素和方法供确认
- 如不存在，提示用户需要先创建Page类

### 第3步：收集元素信息
询问用户是否需要从Appium Inspector获取额外元素：
- 如需要，直接让用户粘贴Appium Inspector的原始输出（无需整理）
- 如现有元素足够，跳过此步

### 第4步：生成测试用例
基于收集的信息，生成完整的测试用例文件

---

## 📝 测试用例生成规范

### 文件路径
```
case/【模块类型】/test_【功能名】.py
```
- 主包：`case/main_app/`
- 马甲包：`case/vest_app/`
- 共用：`case/common/`

### 文件命名规范
- 冒烟测试：`test_【模块名】_smoke.py`
- 回归测试：`test_【模块名】.py`
- 具体功能：`test_【功能名】.py`

### 必需导入
```python
from time import sleep
import pytest
import allure
from utils.report_utils import AllureReportUtils
from utils.screenshot_utils import take_screenshot
from page.【模块路径】.【页面名】 import 【页面类名】
```

### 测试类结构
```python
class Test【模块名】【测试类型】:
    """【模块名】【测试类型】测试类"""

    @pytest.mark.【级别】
    @allure.story("【Allure故事名】")
    @allure.severity(allure.severity_level.【严重级别】)
    @allure.feature("【功能特性】")
    @allure.title("【用例标题】")
    @allure.description("""
    【测试步骤详细描述】
    """)
    @pytest.mark.parametrize("device", [0])
    def test_【功能名】_【场景】(self, app_name, device_index, init_driver):
        """
        测试方法说明

        Args:
            app_name: 应用名称（main/vest1/vest2/vest3）
            device_index: 设备索引
            init_driver: 初始化的WebDriver实例
        """
        # 设置用例基本信息
        AllureReportUtils.set_test_case_info(
            "【用例标题】",
            "【测试描述】"
        )
        AllureReportUtils.add_severity("【严重级别】")
        AllureReportUtils.add_tag("【级别】", "【模块名】", "【应用类型】", app_name)

        # 初始化页面
        page = 【页面类名】(init_driver)

        # 测试步骤（使用allure.step包裹）
        with allure.step("【步骤描述】"):
            # 操作代码
            # 使用page对象的方法
            # page.【方法】(【参数】)
            pass

        # 最终断言
        assert app_name in ["main", "vest1", "vest2", "vest3"]
```

---

## 🔍 Appium Inspector 元素解析规则

### 自动提取以下信息
当用户粘贴Appium Inspector输出时，自动解析：

| 原始信息 | 解析结果 |
|---------|----------|
| `id` 属性值 | `By.ID, "值"` |
| `xpath` 属性值 | `By.XPATH, "值"` |
| `accessibility id` 属性值 | `By.ACCESSIBILITY_ID, "值"` |
| `class` 属性值 | `By.CLASS_NAME, "值"` |
| `text` 属性值 | 用于验证文本内容 |

### 差异化定位格式
如果多包元素不同，自动生成：
```python
element_locator = {
    "main": (By.ID, "主包id"),
    "vest1": (By.ID, "马甲包1id"),
    "vest2": (By.ID, "马甲包2id"),
    "vest3": (By.ID, "马甲包3id"),
}
```

### 单一定位格式
如果所有包元素相同：
```python
element_locator = (By.ID, "通用id")
```

---

## 🎨 Allure 报告规范

### 严重级别选择
| 级别 | 使用场景 |
|------|----------|
| `CRITICAL` | 核心功能、主流程、冒烟测试 |
| `NORMAL` | 常规功能、回归测试 |
| `MINOR` | 次要功能、边界测试 |
| `TRIVIAL` | 界面展示、非核心功能 |
| `BLOCKER` | 阻塞性问题（极少使用） |

### Tag 标记规范
- `smoke` - 冒烟测试
- `regression` - 回归测试
- `integration` - 集成测试
- `【模块名】` - 模块标记
- `【应用类型】` - main_app / vest_app

### Step 步骤命名
- 使用动词开头：点击、验证、切换、获取
- 简洁明确，不超过20字
- 每个step包含截图

---

## ⚙️ 默认值规范

### 自动填写的值（不问用户）
- 作者名：`自动化测试`
- 创建日期：自动获取当前日期
- 设备参数：`[0]`（默认第一个设备）
- 等待时间：`30`秒
- 重试次数：`0`次

### 命令行执行示例
```bash
# 基础执行
pytest case/【模块名】/test_【功能名】.py -v

# 指定应用
pytest --app main -v

# 指定设备
pytest --device 1 -v

# 指定平台
pytest --platform android -v

# 按标记执行
pytest -m smoke -v

# 生成报告
pytest --alluredir=./report/allure
allure serve ./report/allure
```

---

## ✅ 生成检查清单

生成测试用例后，自动检查：

- [ ] 文件路径正确（case/xxx/）
- [ ] 文件命名符合规范（test_开头）
- [ ] 测试类以 `Test` 开头
- [ ] 测试方法以 `test_` 开头
- [ ] 包含 pytest.mark 标记
- [ ] 包含 Allure 注解（story、severity、feature、title、description）
- [ ] 使用 AllureReportUtils 设置用例信息
- [ ] 每个关键步骤有 allure.step
- [ ] 包含截图（take_screenshot + attach_screenshot）
- [ ] 有最终断言
- [ ] 导入语句完整且正确
- [ ] 使用 sleep 控制等待时机
- [ ] 异常处理完善
- [ ] 代码格式符合PEP8

---

## 📞 用户对话规则

1. 用户只需说：「生成XX模块XX级别测试用例」
2. AI主动分步询问，不一次性甩大模板
3. 元素信息用户直接粘贴原始内容，AI自动解析
4. 非必填信息自动填默认值，不问用户
5. 最终只输出完整.py文件内容，确保可执行

---

## 🔧 Page对象方法参考

### 常用操作
```python
# 点击元素
page.click(locator, platform=platform)

# 输入文本
page.send_keys(locator, text, platform=platform)

# 获取文本
text = page.get_text(locator, platform=platform)

# 判断元素存在
is_displayed = page.is_element_displayed(locator, platform=platform)

# 等待元素可见
page.wait_for_element_visible(locator, platform=platform)

# 查找元素
element = page.find_element(locator)

# 滑动
page.swipe(direction="up", duration=500)

# 返回
page.back()

# 截图
page.capture_screenshot("截图名称")
```

---

## 📌 备注

- 所有生成的测试用例必须符合项目 POM 架构
- 优先复用现有 Page 类方法，避免重复造轮子
- 确保 iOS/Android 双平台兼容
- 支持差异化定位
- 代码复制到 Cursor 后可直接通过 `run.py` 执行