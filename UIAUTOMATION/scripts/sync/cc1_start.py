#!/usr/bin/env python3
"""
CC1 工作流启动脚本

CC1 负责页面元素抓取（XML采集 → Locator配置编写）

使用方式：
    # 启动 CC1 工作流（自动创建 worktree 和分支）
    python scripts/sync/cc1_start.py --page reader

    # 检查 CC1 工作流状态
    python scripts/sync/cc1_start.py --status

    # 完成 CC1 工作流（更新状态、提交代码、创建 PR）
    python scripts/sync/cc1_start.py --complete --page reader
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
WORKTREES_DIR = PROJECT_ROOT / ".claude" / "worktrees"

# 导入状态检查模块
sys.path.insert(0, str(SCRIPTS_DIR / "sync"))
from check_status import (
    get_collaboration_status,
    update_collaboration_status,
    mark_cc1_completed,
    CollaborationStatus
)


def run_command(cmd: str, cwd: str = None, check: bool = True) -> subprocess.CompletedProcess:
    """执行 shell 命令"""
    print(f"🔧 执行: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd or str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"命令执行失败: {cmd}")
    return result


def check_git_status() -> bool:
    """检查 git 工作区状态"""
    result = subprocess.run(
        "git status --porcelain",
        shell=True,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )
    if result.stdout.strip():
        print("⚠️  工作区有未提交的更改:")
        print(result.stdout)
        return False
    return True


def create_worktree(page_name: str) -> Path:
    """
    创建 CC1 worktree

    Args:
        page_name: 页面名称

    Returns:
        Path: worktree 路径
    """
    branch_name = f"cc1/element-capture-{page_name}"
    worktree_path = WORKTREES_DIR / "cc1"

    # 确保 worktrees 目录存在
    WORKTREES_DIR.mkdir(parents=True, exist_ok=True)

    # 检查 worktree 是否已存在
    if worktree_path.exists():
        print(f"⚠️  Worktree 已存在: {worktree_path}")
        return worktree_path

    # 检查分支是否已存在
    result = subprocess.run(
        f"git branch --list {branch_name}",
        shell=True,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        # 分支已存在，直接创建 worktree
        print(f"📌 分支已存在，创建 worktree...")
        run_command(f"git worktree add {worktree_path} {branch_name}")
    else:
        # 创建新分支和 worktree
        print(f"📌 创建新分支: {branch_name}")
        run_command(f"git worktree add {worktree_path} -b {branch_name}")

    print(f"✅ Worktree 创建成功: {worktree_path}")
    return worktree_path


def remove_worktree() -> bool:
    """删除 CC1 worktree"""
    worktree_path = WORKTREES_DIR / "cc1"

    if not worktree_path.exists():
        print("⚠️  Worktree 不存在，无需删除")
        return True

    try:
        run_command(f"git worktree remove {worktree_path}")
        print(f"✅ Worktree 已删除: {worktree_path}")
        return True
    except RuntimeError as e:
        print(f"❌ 删除 worktree 失败: {e}")
        return False


def start_cc1_workflow(page_name: str, platform: str = "ios", app_name: str = "main"):
    """
    启动 CC1 工作流

    Args:
        page_name: 页面名称
        platform: 平台 (ios/android)
        app_name: 应用名称
    """
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           CC1 工作流启动                                    ║
╠════════════════════════════════════════════════════════════╣
║  页面: {page_name:<15}  平台: {platform:<10}  应用: {app_name:<10} ║
╚════════════════════════════════════════════════════════════╝
""")

    # 1. 检查 git 状态
    print("\n📋 步骤 1/5: 检查 Git 状态...")
    if not check_git_status():
        print("⚠️  请先提交或暂存工作区的更改")
        return

    # 2. 创建 worktree
    print("\n📋 步骤 2/5: 创建 Worktree...")
    worktree_path = create_worktree(page_name)

    # 3. 更新协作状态
    print("\n📋 步骤 3/5: 更新协作状态...")
    update_collaboration_status(CollaborationStatus.CC1_WORKING, page_name)

    # 4. 提示下一步操作
    print(f"""
✅ CC1 工作流初始化完成！

📂 工作目录: {worktree_path}
🌿 分支: cc1/element-capture-{page_name}

📝 下一步操作:

1️⃣  进入 worktree 目录:
    cd {worktree_path}

2️⃣  运行 XML 抓取脚本:
    python scripts/capture_xml.py --app {app_name} --platform {platform}

    # 交互式采集（推荐）
    python scripts/capture_xml.py --app {app_name} --platform {platform}

    # 或指定页面名称快速采集
    python scripts/capture_xml.py --app {app_name} --platform {platform} --page {page_name}

3️⃣  分析采集的 XML，创建定位符配置:
    # 编辑 config/locators/{page_name}_locators.yaml
    # 参考 config/locators/home_locators.yaml 的格式

4️⃣  完成后运行:
    python scripts/sync/cc1_start.py --complete --page {page_name}

💡 提示:
- 使用交互式采集可以一次性采集多个页面
- 定位符格式参考: config/locators/home_locators.yaml
- 更新 MEMORY.md 记录进度
""")


def complete_cc1_workflow(page_name: str, create_pr: bool = True):
    """
    完成 CC1 工作流

    Args:
        page_name: 页面名称
        create_pr: 是否创建 PR
    """
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           CC1 工作流完成                                    ║
╠════════════════════════════════════════════════════════════╣
║  页面: {page_name:<50} ║
╚════════════════════════════════════════════════════════════╝
""")

    worktree_path = WORKTREES_DIR / "cc1"
    branch_name = f"cc1/element-capture-{page_name}"

    # 1. 检查必需文件
    print("\n📋 步骤 1/5: 检查必需文件...")

    locator_file = worktree_path / "config" / "locators" / f"{page_name}_locators.yaml"
    xml_dir = worktree_path / "data" / "page_xml"

    files_ok = True

    if locator_file.exists():
        print(f"   ✅ 定位符配置: {locator_file}")
    else:
        print(f"   ⚠️  定位符配置不存在: {locator_file}")
        print(f"      请先创建定位符配置文件")
        files_ok = False

    if xml_dir.exists():
        print(f"   ✅ XML 采集目录: {xml_dir}")
    else:
        print(f"   ⚠️  XML 采集目录不存在: {xml_dir}")
        files_ok = False

    if not files_ok:
        print("\n❌ 请先完成元素抓取和定位符配置")
        return

    # 2. 提交代码
    print("\n📋 步骤 2/5: 提交代码...")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 在 worktree 中执行 git 操作
    run_command("git add data/ config/", cwd=str(worktree_path), check=False)
    run_command(f'git commit -m "feat(cc1): add {page_name} page locators ({timestamp})"', cwd=str(worktree_path), check=False)

    # 3. 更新协作状态
    print("\n📋 步骤 3/5: 更新协作状态...")

    # 提交 MEMORY.md 更新
    run_command("git add MEMORY.md", cwd=str(worktree_path), check=False)
    run_command(f'git commit -m "docs: update MEMORY.md - CC1 completed {page_name}"', cwd=str(worktree_path), check=False)

    # 更新状态为 CC1_COMPLETED
    update_collaboration_status(CollaborationStatus.CC1_COMPLETED, page_name)
    mark_cc1_completed(page_name)

    # 4. 推送分支
    print("\n📋 步骤 4/5: 推送分支...")
    run_command(f"git push -u origin {branch_name}", cwd=str(worktree_path), check=False)

    # 5. 创建 PR
    if create_pr:
        print("\n📋 步骤 5/5: 创建 Pull Request...")

        pr_title = f"feat: add {page_name} page locators"
        pr_body = f"""## Summary
- 采集 {page_name} 页面 XML 源码
- 添加 {page_name} 页面元素定位符配置

## Test plan
- [ ] 验证 XML 文件已正确保存
- [ ] 验证定位符配置格式正确
- [ ] 使用定位符配置编写测试用例

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""

        run_command(f'gh pr create --title "{pr_title}" --body "{pr_body}"', cwd=str(worktree_path), check=False)

    print(f"""
✅ CC1 工作流完成！

📊 协作状态已更新为: CC1_COMPLETED
🔔 CC2 现在可以开始编写测试用例

📂 已生成文件:
   - 定位符配置: config/locators/{page_name}_locators.yaml
   - XML 文件: data/page_xml/*/main/{page_name}/

📝 下一步:
   - 等待 CC2 完成测试用例编写
   - 或继续抓取其他页面: python scripts/sync/cc1_start.py --page <next_page>
""")


def print_status():
    """打印 CC1 工作流状态"""
    status_info = get_collaboration_status()

    print(f"""
╔════════════════════════════════════════════════════════════╗
║           CC1 工作流状态                                    ║
╚════════════════════════════════════════════════════════════╝

📊 当前协作状态: {status_info['status'] or '未初始化'}
📝 活跃页面: {status_info['active_page'] or '无'}
⏰ 最后更新: {status_info['last_update'] or '无'}

📋 CC1 进度:
   ✅ 已完成: {', '.join(status_info['cc1_completed']) or '无'}
   ⏳ 待抓取: {', '.join(status_info['cc1_pending']) or '无'}
""")

    worktree_path = WORKTREES_DIR / "cc1"
    if worktree_path.exists():
        print(f"📂 Worktree: {worktree_path} (存在)")

        # 显示当前分支
        result = subprocess.run(
            "git branch --show-current",
            shell=True,
            cwd=str(worktree_path),
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(f"🌿 当前分支: {result.stdout.strip()}")
    else:
        print("📂 Worktree: 未创建")


def main():
    parser = argparse.ArgumentParser(
        description="CC1 工作流启动脚本（元素抓取）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动 CC1 工作流
  python scripts/sync/cc1_start.py --page reader

  # 检查状态
  python scripts/sync/cc1_start.py --status

  # 完成工作流
  python scripts/sync/cc1_start.py --complete --page reader

  # 完成工作流（不创建 PR）
  python scripts/sync/cc1_start.py --complete --page reader --no-pr
        """
    )

    parser.add_argument("--page", metavar="PAGE",
                        help="页面名称")
    parser.add_argument("--platform", choices=["ios", "android"], default="ios",
                        help="平台 (默认: ios)")
    parser.add_argument("--app", choices=["main", "vest1", "vest2", "vest3"], default="main",
                        help="应用名称 (默认: main)")
    parser.add_argument("--status", action="store_true",
                        help="查看 CC1 工作流状态")
    parser.add_argument("--complete", action="store_true",
                        help="完成 CC1 工作流")
    parser.add_argument("--no-pr", action="store_true",
                        help="完成时不创建 PR")
    parser.add_argument("--cleanup", action="store_true",
                        help="删除 CC1 worktree")

    args = parser.parse_args()

    if args.status:
        print_status()
    elif args.complete:
        if not args.page:
            print("❌ 完成工作流时必须指定 --page 参数")
            sys.exit(1)
        complete_cc1_workflow(args.page, create_pr=not args.no_pr)
    elif args.cleanup:
        remove_worktree()
    elif args.page:
        start_cc1_workflow(args.page, args.platform, args.app)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()