#!/usr/bin/env python3
"""
双 CC 协作状态检查脚本

用于解析和更新 MEMORY.md 中的协作状态信息。

使用方式：
    # 获取当前协作状态
    python scripts/sync/check_status.py

    # 更新协作状态
    python scripts/sync/check_status.py --update CC1_COMPLETED --page rewards

    # 等待 CC1 完成（阻塞直到状态变为 CC1_COMPLETED）
    python scripts/sync/check_status.py --wait-cc1 --page rewards
"""
import re
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
MEMORY_FILE = PROJECT_ROOT / "MEMORY.md"


class CollaborationStatus:
    """协作状态枚举"""
    CC1_WORKING = "CC1_WORKING"
    CC1_COMPLETED = "CC1_COMPLETED"
    CC2_WORKING = "CC2_WORKING"
    COMPLETED = "COMPLETED"

    @classmethod
    def all_statuses(cls) -> List[str]:
        return [cls.CC1_WORKING, cls.CC1_COMPLETED, cls.CC2_WORKING, cls.COMPLETED]

    @classmethod
    def is_valid(cls, status: str) -> bool:
        return status in cls.all_statuses()

    @classmethod
    def description(cls, status: str) -> str:
        descriptions = {
            cls.CC1_WORKING: "CC1 正在抓取元素",
            cls.CC1_COMPLETED: "CC1 已完成，CC2 可开始",
            cls.CC2_WORKING: "CC2 正在编写测试",
            cls.COMPLETED: "双 CC 协作完成"
        }
        return descriptions.get(status, "未知状态")


def parse_memory_file() -> Dict:
    """
    解析 MEMORY.md 文件，提取协作状态信息

    Returns:
        dict: 包含 status, last_update, active_page, cc1_progress, cc2_progress 等字段
    """
    if not MEMORY_FILE.exists():
        return {
            "status": None,
            "last_update": None,
            "active_page": None,
            "cc1_completed": [],
            "cc1_pending": [],
            "cc2_completed": [],
            "cc2_pending": []
        }

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    result = {
        "status": None,
        "last_update": None,
        "active_page": None,
        "cc1_completed": [],
        "cc1_pending": [],
        "cc2_completed": [],
        "cc2_pending": []
    }

    # 解析协作状态表格
    # 格式: | 当前状态 | 最后更新 | 活跃页面 |
    #       | CC1_WORKING | 2026-03-26T16:00:00 | rewards |
    status_pattern = r'\|\s*当前状态\s*\|\s*最后更新\s*\|\s*活跃页面\s*\|\s*\n\|\s*(\w+)\s*\|\s*([\dT:.-]+)\s*\|\s*(\w+)\s*\|'
    status_match = re.search(status_pattern, content)
    if status_match:
        result["status"] = status_match.group(1)
        result["last_update"] = status_match.group(2)
        result["active_page"] = status_match.group(3)

    # 解析 CC1 已完成列表
    cc1_completed_pattern = r'## CC1（元素抓取）进度.*?### 已完成\s*\n((?:- \[x\].*?\n)*)'
    cc1_completed_match = re.search(cc1_completed_pattern, content, re.DOTALL)
    if cc1_completed_match:
        completed_section = cc1_completed_match.group(1)
        result["cc1_completed"] = re.findall(r'- \[x\]\s*(\w+)', completed_section)

    # 解析 CC1 待抓取列表
    cc1_pending_pattern = r'### 待抓取\s*\n((?:- \[ \].*?\n)*)'
    cc1_pending_match = re.search(cc1_pending_pattern, content)
    if cc1_pending_match:
        pending_section = cc1_pending_match.group(1)
        result["cc1_pending"] = re.findall(r'- \[ \]\s*(\w+)', pending_section)

    # 解析 CC2 已完成列表
    cc2_completed_pattern = r'## CC2（用例编写）进度.*?### 已完成\s*\n((?:- \[x\].*?\n)*)'
    cc2_completed_match = re.search(cc2_completed_pattern, content, re.DOTALL)
    if cc2_completed_match:
        completed_section = cc2_completed_match.group(1)
        result["cc2_completed"] = re.findall(r'- \[x\]\s*(\w+)', completed_section)

    # 解析 CC2 等待列表
    cc2_pending_pattern = r'### 等待 CC1 完成抓取\s*\n((?:- \[ \].*?\n)*)'
    cc2_pending_match = re.search(cc2_pending_pattern, content)
    if cc2_pending_match:
        pending_section = cc2_pending_match.group(1)
        result["cc2_pending"] = re.findall(r'- \[ \]\s*(\w+)', pending_section)

    return result


def get_collaboration_status() -> Dict:
    """
    获取当前协作状态

    Returns:
        dict: 协作状态信息
    """
    return parse_memory_file()


def update_collaboration_status(status: str, page_name: str) -> bool:
    """
    更新 MEMORY.md 中的协作状态

    Args:
        status: 新状态 (CC1_WORKING, CC1_COMPLETED, CC2_WORKING, COMPLETED)
        page_name: 当前活跃的页面名称

    Returns:
        bool: 更新是否成功
    """
    if not CollaborationStatus.is_valid(status):
        print(f"❌ 无效的状态: {status}")
        print(f"   有效状态: {', '.join(CollaborationStatus.all_statuses())}")
        return False

    if not MEMORY_FILE.exists():
        print(f"❌ MEMORY.md 文件不存在: {MEMORY_FILE}")
        return False

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # 检查是否已存在协作状态表格
    status_table_pattern = r'\|\s*当前状态\s*\|\s*最后更新\s*\|\s*活跃页面\s*\|\s*\n\|[^|]+\|[^|]+\|[^|]+\|'

    if re.search(status_table_pattern, content):
        # 更新现有表格
        new_row = f"| {status} | {timestamp} | {page_name} |"
        content = re.sub(status_table_pattern, f"| 当前状态 | 最后更新 | 活跃页面 |\n{new_row}", content)
    else:
        # 创建新的状态表格（在文件开头添加）
        status_table = f"""# 双 CC 协作进度同步

## 协作状态

| 当前状态 | 最后更新 | 活跃页面 |
|----------|----------|----------|
| {status} | {timestamp} | {page_name} |

**状态值说明:**
- `CC1_WORKING` - CC1 正在抓取元素
- `CC1_COMPLETED` - CC1 已完成，CC2 可开始
- `CC2_WORKING` - CC2 正在编写测试
- `COMPLETED` - 双 CC 协作完成

---
"""
        # 在第一个标题后插入状态表格
        if content.startswith("#"):
            lines = content.split("\n")
            # 找到第一个二级标题的位置
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    insert_pos = i
                    break
            # 替换开头的标题
            lines = lines[1:]  # 移除原标题
            content = "\n".join(lines)
            content = status_table + content
        else:
            content = status_table + content

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 协作状态已更新:")
    print(f"   状态: {status} ({CollaborationStatus.description(status)})")
    print(f"   页面: {page_name}")
    print(f"   时间: {timestamp}")

    return True


def mark_cc1_completed(page_name: str) -> bool:
    """
    标记 CC1 已完成某个页面的元素抓取

    Args:
        page_name: 页面名称

    Returns:
        bool: 更新是否成功
    """
    if not MEMORY_FILE.exists():
        return False

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 更新 CC1 已完成列表（将待抓取改为已完成）
    # 查找待抓取列表中的页面
    pending_pattern = rf'(- \[ \]\s*){page_name}\s*页面'
    if re.search(pending_pattern, content):
        content = re.sub(pending_pattern, f"- [x] {page_name} 页面", content)

    # 如果不存在，添加到已完成列表
    if f"- [x] {page_name} 页面" not in content:
        # 在 CC1 已完成部分添加
        cc1_completed_pattern = r'(## CC1（元素抓取）进度\s*\n\s*### 已完成\s*\n)'
        if re.search(cc1_completed_pattern, content):
            timestamp = datetime.now().strftime("%Y-%m-%d")
            new_entry = f"- [x] {page_name} 页面 - 已抓取 ({timestamp})\n"
            content = re.sub(cc1_completed_pattern, r'\1' + new_entry, content)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    return True


def mark_cc2_completed(page_name: str) -> bool:
    """
    标记 CC2 已完成某个页面的测试开发

    Args:
        page_name: 页面名称

    Returns:
        bool: 更新是否成功
    """
    if not MEMORY_FILE.exists():
        return False

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 更新 CC2 等待列表（将等待改为已完成）
    pending_pattern = rf'(- \[ \]\s*){page_name}\s*页面'
    if re.search(pending_pattern, content):
        content = re.sub(pending_pattern, f"- [x] {page_name} 页面", content)

    # 如果不存在，添加到已完成列表
    if f"- [x] {page_name} 页面" not in content:
        cc2_completed_pattern = r'(## CC2（用例编写）进度\s*\n\s*### 已完成\s*\n)'
        if re.search(cc2_completed_pattern, content):
            timestamp = datetime.now().strftime("%Y-%m-%d")
            new_entry = f"- [x] {page_name} 页面 - 测试用例已完成 ({timestamp})\n"
            content = re.sub(cc2_completed_pattern, r'\1' + new_entry, content)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    return True


def wait_for_cc1_completion(page_name: str, timeout: int = 3600, interval: int = 10) -> bool:
    """
    等待 CC1 完成元素抓取

    Args:
        page_name: 等待的页面名称
        timeout: 超时时间（秒），默认1小时
        interval: 检查间隔（秒），默认10秒

    Returns:
        bool: 是否成功等到 CC1 完成
    """
    print(f"⏳ 等待 CC1 完成 '{page_name}' 页面的元素抓取...")
    print(f"   超时: {timeout}秒, 检查间隔: {interval}秒")

    start_time = time.time()

    while time.time() - start_time < timeout:
        status_info = get_collaboration_status()

        # 检查状态是否为 CC1_COMPLETED 且活跃页面匹配
        if status_info["status"] == CollaborationStatus.CC1_COMPLETED:
            if status_info["active_page"] == page_name or page_name in status_info["cc1_completed"]:
                print(f"✅ CC1 已完成 '{page_name}' 页面的元素抓取！")
                return True

        # 检查页面是否已在 CC1 已完成列表中
        if page_name in status_info["cc1_completed"]:
            print(f"✅ '{page_name}' 页面已在 CC1 已完成列表中！")
            return True

        elapsed = int(time.time() - start_time)
        print(f"   等待中... 已等待 {elapsed}秒 (状态: {status_info['status']})")
        time.sleep(interval)

    print(f"❌ 等待超时！CC1 在 {timeout}秒内未完成 '{page_name}' 页面的元素抓取")
    return False


def print_status():
    """打印当前协作状态"""
    status_info = get_collaboration_status()

    print("""
╔════════════════════════════════════════════════════════════╗
║           双 CC 协作状态                                    ║
╚════════════════════════════════════════════════════════════╝
""")

    if status_info["status"]:
        print(f"📊 当前状态: {status_info['status']}")
        print(f"   描述: {CollaborationStatus.description(status_info['status'])}")
        print(f"   活跃页面: {status_info['active_page']}")
        print(f"   最后更新: {status_info['last_update']}")
    else:
        print("📊 当前状态: 未初始化")
        print("   请使用 --update 参数初始化协作状态")

    print(f"""
📋 CC1（元素抓取）进度:
   ✅ 已完成: {', '.join(status_info['cc1_completed']) or '无'}
   ⏳ 待抓取: {', '.join(status_info['cc1_pending']) or '无'}

📋 CC2（用例编写）进度:
   ✅ 已完成: {', '.join(status_info['cc2_completed']) or '无'}
   ⏳ 等待中: {', '.join(status_info['cc2_pending']) or '无'}
""")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="双 CC 协作状态检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 查看当前状态
  python scripts/sync/check_status.py

  # 更新协作状态
  python scripts/sync/check_status.py --update CC1_WORKING --page home

  # 等待 CC1 完成
  python scripts/sync/check_status.py --wait-cc1 --page home

状态说明:
  CC1_WORKING    - CC1 正在抓取元素
  CC1_COMPLETED  - CC1 已完成，CC2 可开始
  CC2_WORKING    - CC2 正在编写测试
  COMPLETED      - 双 CC 协作完成
        """
    )

    parser.add_argument("--update", metavar="STATUS",
                        help="更新协作状态")
    parser.add_argument("--page", metavar="PAGE",
                        help="页面名称")
    parser.add_argument("--wait-cc1", action="store_true",
                        help="等待 CC1 完成")
    parser.add_argument("--timeout", type=int, default=3600,
                        help="等待超时时间（秒）")
    parser.add_argument("--interval", type=int, default=10,
                        help="检查间隔（秒）")
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 格式输出")

    args = parser.parse_args()

    if args.update:
        if not args.page:
            print("❌ 更新状态时必须指定 --page 参数")
            sys.exit(1)
        success = update_collaboration_status(args.update, args.page)
        sys.exit(0 if success else 1)

    if args.wait_cc1:
        if not args.page:
            print("❌ 等待时必须指定 --page 参数")
            sys.exit(1)
        success = wait_for_cc1_completion(args.page, args.timeout, args.interval)
        sys.exit(0 if success else 1)

    if args.json:
        status_info = get_collaboration_status()
        print(json.dumps(status_info, ensure_ascii=False, indent=2))
    else:
        print_status()


if __name__ == "__main__":
    main()