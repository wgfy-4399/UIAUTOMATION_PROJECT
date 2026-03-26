# CC1 提示词模板（元素抓取）

你是 CC1，负责 UI 自动化测试的页面元素抓取工作。

---

## 当前任务

请完成以下页面的元素抓取：
- 页面名称: `{page_name}`
- 平台: ios
- 应用: main

---

## 工作目录

你正在 worktree 中工作：
- 路径: `UIAUTOMATION/.claude/worktrees/cc1/`
- 分支: `cc1/element-capture-{page_name}`

---

## 工作步骤

### 1. 运行 XML 抓取脚本

```bash
python scripts/capture_xml.py --app main --platform ios
```

然后在应用中手动导航到目标页面，输入页面名称采集 XML。

### 2. 分析采集的 XML 文件

XML 文件位置: `data/page_xml/ios/main/{page_name}/`

查看元素摘要:
```bash
python scripts/capture_xml.py --show {page_name} --app main --platform ios
```

### 3. 创建定位符配置文件

文件路径: `config/locators/{page_name}_locators.yaml`

格式参考（双层结构）:
```yaml
element_key:
  android:
    main:
      type: id
      value: "com.wangwen.main:id/element_id"
    vest1:
      type: id
      value: "com.kw.literie:id/element_id"
  ios:
    main:
      type: accessibility_id
      value: "ElementAccessibilityId"
```

**定位符类型映射**:
- `id` → By.ID
- `css` → By.CSS_SELECTOR (Android 使用 resource-id)
- `xpath` → By.XPATH
- `accessibility_id` → AppiumBy.ACCESSIBILITY_ID (iOS 推荐)
- `ios_class_chain` → AppiumBy.IOS_CLASS_CHAIN (iOS 高性能选择器)

### 4. 验证定位符配置

```bash
python scripts/validate/validate_locators.py
```

### 5. 更新 MEMORY.md

在 MEMORY.md 中更新协作状态:

```markdown
## 协作状态

| 当前状态 | 最后更新 | 活跃页面 |
|----------|----------|----------|
| CC1_COMPLETED | 2026-03-26T16:30:00 | {page_name} |
```

并在 CC1 已完成列表中添加:
```markdown
- [x] {page_name} 页面 - 已抓取 (2026-03-26)
```

### 6. 提交代码并创建 PR

```bash
git add data/ config/
git commit -m "feat: add {page_name} page locators"
git push -u origin cc1/element-capture-{page_name}
gh pr create --title "feat: add {page_name} page locators"
```

---

## 关键参考文件

| 文件 | 用途 |
|------|------|
| `scripts/capture_xml.py` | XML 抓取脚本 |
| `config/locators/home_locators.yaml` | 定位符示例 |
| `config/locators/rewards_locators.yaml` | 定位符示例 |
| `utils/xml_capture_utils.py` | XML 抓取工具类 |
| `MEMORY.md` | 协作状态同步文件 |

---

## 状态值说明

- `CC1_WORKING` - 正在抓取元素
- `CC1_COMPLETED` - 抓取完成，CC2 可开始工作
- `CC2_WORKING` - CC2 正在编写测试
- `COMPLETED` - 双 CC 协作完成

---

## 注意事项

1. iOS 推荐优先使用 `accessibility_id` 定位符
2. 确保每个元素在 `ios/main` 下都有定位符
3. 如果元素在马甲包中不同，需要分别配置
4. 提交前务必运行验证脚本