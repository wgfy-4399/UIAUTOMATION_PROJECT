#!/usr/bin/env python3
"""
CC2 工作流启动脚本

CC2 负责测试脚本编写（Page Object → 测试用例）

使用方式：
    # 启动 CC2 工作流（自动检查 CC1 是否完成）
    python scripts/sync/cc2_start.py --page reader

    # 检查 CC2 工作流状态
    python scripts/sync/cc2_start.py --status

    # 完成 CC2 工作流（更新状态、提交代码、创建 PR）
    python scripts/sync/cc2_start.py --complete --page reader
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
    mark_cc2_completed,
    wait_for_cc1_completion,
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
    创建 CC2 worktree

    Args:
        page_name: 页面名称

    Returns:
        Path: worktree 路径
    """
    branch_name = f"cc2/test-development-{page_name}"
    worktree_path = WORKTREES_DIR / "cc2"

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
    """删除 CC2 worktree"""
    worktree_path = WORKTREES_DIR / "cc2"

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


def validate_locators(page_name: str) -> bool:
    """
    验证定位符配置

    Args:
        page_name: 页面名称

    Returns:
        bool: 验证是否通过
    """
    locator_file = PROJECT_ROOT / "config" / "locators" / f"{page_name}_locators.yaml"

    if not locator_file.exists():
        print(f"❌ 定位符配置不存在: {locator_file}")
        return False

    # 运行验证脚本
    validate_script = PROJECT_ROOT / "scripts" / "validate" / "validate_locators.py"
    if validate_script.exists():
        result = subprocess.run(
            f"python {validate_script} --page {page_name}",
            shell=True,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"❌ 定位符验证失败:")
            print(result.stdout)
            print(result.stderr)
            return False
        print(f"✅ 定位符验证通过")
    else:
        print(f"⚠️  验证脚本不存在，跳过验证")

    return True


def start_cc2_workflow(page_name: str, platform: str = "ios", app_name: str = "main",
                       wait_for_cc1: bool = True, timeout: int = 3600):
    """
    启动 CC2 工作流

    Args:
        page_name: 页面名称
        platform: 平台 (ios/android)
        app_name: 应用名称
        wait_for_cc1: 是否等待 CC1 完成
        timeout: 等待超时时间
    """
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           CC2 工作流启动                                    ║
╠════════════════════════════════════════════════════════════╣
║  页面: {page_name:<15}  平台: {platform:<10}  应用: {app_name:<10} ║
╚════════════════════════════════════════════════════════════╝
""")

    # 1. 检查 CC1 状态
    print("\n📋 步骤 1/6: 检查 CC1 状态...")
    status_info = get_collaboration_status()

    cc1_ready = (
        status_info["status"] == CollaborationStatus.CC1_COMPLETED or
        page_name in status_info["cc1_completed"]
    )

    if not cc1_ready:
        if wait_for_cc1:
            print(f"⏳ CC1 尚未完成 '{page_name}' 页面的元素抓取，等待中...")
            if not wait_for_cc1_completion(page_name, timeout=timeout):
                print("❌ 等待 CC1 超时，无法启动 CC2 工作流")
                return
        else:
            print(f"❌ CC1 尚未完成 '{page_name}' 页面的元素抓取")
            print("   请先运行 CC1 完成元素抓取，或使用 --wait 参数等待")
            return
    else:
        print(f"✅ CC1 已完成 '{page_name}' 页面的元素抓取")

    # 2. 验证定位符配置
    print("\n📋 步骤 2/6: 验证定位符配置...")
    if not validate_locators(page_name):
        print("❌ 定位符验证失败，请先确保定位符配置正确")
        return

    # 3. 检查 git 状态
    print("\n📋 步骤 3/6: 检查 Git 状态...")
    if not check_git_status():
        print("⚠️  请先提交或暂存工作区的更改")
        return

    # 4. 创建 worktree 并 rebase main
    print("\n📋 步骤 4/6: 创建 Worktree 并同步最新代码...")
    worktree_path = create_worktree(page_name)

    # Rebase main 分支获取 CC1 的更新
    print("📥 同步 main 分支最新代码...")
    run_command("git fetch origin", cwd=str(worktree_path), check=False)
    run_command("git rebase origin/main", cwd=str(worktree_path), check=False)

    # 5. 更新协作状态
    print("\n📋 步骤 5/6: 更新协作状态...")
    update_collaboration_status(CollaborationStatus.CC2_WORKING, page_name)

    # 6. 提示下一步操作
    print(f"""
✅ CC2 工作流初始化完成！

📂 工作目录: {worktree_path}
🌿 分支: cc2/test-development-{page_name}

📝 下一步操作:

1️⃣  进入 worktree 目录:
    cd {worktree_path}

2️⃣  创建 Page Object:
    # 编辑 page/pages/{page_name}_page.py
    # 参考 page/pages/home_page.py 的格式
    #
    # 基本结构:
    # from page.base_page import BasePage
    # from utils.locator_utils import load_locators, get_locator_from_config
    #
    # class {page_name.capitalize()}Page(BasePage):
    #     def __init__(self, driver):
    #         super().__init__(driver)
    #         self._locators = load_locators("{page_name}")
    #         ...

3️⃣  创建测试用例:
    # 编辑 case/test_{page_name}.py
    # 参考 case/test_rewards_smoke.py 的格式
    #
    # 基本结构:
    # import pytest
    # from page.pages.{page_name}_page import {page_name.capitalize()}Page
    # from utils.report_utils import AllureReportUtils
    #
    # @pytest.mark.smoke
    # def test_{page_name}_basic(init_driver, app_name):
    #     ...

4️⃣  运行测试验证:
    pytest case/test_{page_name}.py --app {app_name} --platform {platform} -v

5️⃣  完成后运行:
    python scripts/sync/cc2_start.py --complete --page {page_name}

💡 提示:
- Page Object 必须继承 BasePage
- 使用 load_locators("{page_name}") 加载定位符
- 测试用例使用 init_driver 和 app_name fixture
- 使用 AllureReportUtils 记录测试步骤
""")


def complete_cc2_workflow(page_name: str, create_pr: bool = True, run_tests: bool = True):
    """
    完成 CC2 工作流

    Args:
        page_name: 页面名称
        create_pr: 是否创建 PR
        run_tests: 是否运行测试
    """
    print(f"""
╔════════════════════════════════════════════════════════════╗
║           CC2 工作流完成                                    ║
╠════════════════════════════════════════════════════════════╣
║  页面: {page_name:<50} ║
╚════════════════════════════════════════════════════════════╝
""")

    worktree_path = WORKTREES_DIR / "cc2"
    branch_name = f"cc2/test-development-{page_name}"

    # 1. 检查必需文件
    print("\n📋 步骤 1/6: 检查必需文件...")

    page_object_file = worktree_path / "page" / "pages" / f"{page_name}_page.py"
    test_file = worktree_path / "case" / f"test_{page_name}.py"

    files_ok = True

    if page_object_file.exists():
        print(f"   ✅ Page Object: {page_object_file}")
    else:
        print(f"   ⚠️  Page Object 不存在: {page_object_file}")
        files_ok = False

    if test_file.exists():
        print(f"   ✅ 测试用例: {test_file}")
    else:
        print(f"   ⚠️  测试用例不存在: {test_file}")
        files_ok = False

    if not files_ok:
        print("\n❌ 请先完成 Page Object 和测试用例的编写")
        return

    # 2. 运行测试
    if run_tests:
        print("\n📋 步骤 2/6: 运行测试验证...")
        result = subprocess.run(
            f"pytest case/test_{page_name}.py --app main --platform ios -v",
            shell=True,
            cwd=str(worktree_path),
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print("❌ 测试未通过，请先修复测试用例")
            print(result.stderr)
            return
        print("✅ 测试通过")

    # 3. 提交代码
    print("\n📋 步骤 3/6: 提交代码...")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    run_command("git add page/ case/", cwd=str(worktree_path), check=False)
    run_command(f'git commit -m "feat(cc2): add {page_name} test cases ({timestamp})"', cwd=str(worktree_path), check=False)

    # 4. 更新协作状态
    print("\n📋 步骤 4/6: 更新协作状态...")

    # 提交 MEMORY.md 更新
    run_command("git add MEMORY.md", cwd=str(worktree_path), check=False)
    run_command(f'git commit -m "docs: update MEMORY.md - CC2 completed {page_name}"', cwd=str(worktree_path), check=False)

    # 更新状态为 COMPLETED
    update_collaboration_status(CollaborationStatus.COMPLETED, page_name)
    mark_cc2_completed(page_name)

    # 5. 推送分支
    print("\n📋 步骤 5/6: 推送分支...")
    run_command(f"git push -u origin {branch_name}", cwd=str(worktree_path), check=False)

    # 6. 创建 PR
    if create_pr:
        print("\n📋 步骤 6/6: 创建 Pull Request...")

        pr_title = f"feat: add {page_name} test cases"
        pr_body = f"""## Summary
- 创建 {page_name} 页面 Page Object
- 编写 {page_name} 页面测试用例

## Test plan
- [x] 测试用例运行通过
- [ ] Code Review 通过
- [ ] 合并到 main 分支

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""

        run_command(f'gh pr create --title "{pr_title}" --body "{pr_body}"', cwd=str(worktree_path), check=False)

    print(f"""
✅ CC2 工作流完成！

📊 协作状态已更新为: COMPLETED
🎉 双 CC 协作成功完成！

📂 已生成文件:
   - Page Object: page/pages/{page_name}_page.py
   - 测试用例: case/test_{page_name}.py

📝 下一步:
   - 等待 PR 合并
   - 或继续开发其他页面: python scripts/sync/cc2_start.py --page <next_page>
""")


def print_status():
    """打印 CC2 工作流状态"""
    status_info = get_collaboration_status()

    print(f"""
╔════════════════════════════════════════════════════════════╗
║           CC2 工作流状态                                    ║
╚════════════════════════════════════════════════════════════╝

📊 当前协作状态: {status_info['status'] or '未初始化'}
📝 活跃页面: {status_info['active_page'] or '无'}
⏰ 最后更新: {status_info['last_update'] or '无'}

📋 CC2 进度:
   ✅ 已完成: {', '.join(status_info['cc2_completed']) or '无'}
   ⏳ 等待中: {', '.join(status_info['cc2_pending']) or '无'}
""")

    worktree_path = WORKTREES_DIR / "cc2"
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
        description="CC2 工作流启动脚本（测试开发）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动 CC2 工作流（等待 CC1 完成）
  python scripts/sync/cc2_start.py --page reader

  # 启动 CC2 工作流（不等待 CC1）
  python scripts/sync/cc2_start.py --page reader --no-wait

  # 检查状态
  python scripts/sync/cc2_start.py --status

  # 完成工作流
  python scripts/sync/cc2_start.py --complete --page reader

  # 完成工作流（不运行测试）
  python scripts/sync/cc2_start.py --complete --page reader --no-test
        """
    )

    parser.add_argument("--page", metavar="PAGE",
                        help="页面名称")
    parser.add_argument("--platform", choices=["ios", "android"], default="ios",
                        help="平台 (默认: ios)")
    parser.add_argument("--app", choices=["main", "vest1", "vest2", "vest3"], default="main",
                        help="应用名称 (默认: main)")
    parser.add_argument("--status", action="store_true",
                        help="查看 CC2 工作流状态")
    parser.add_argument("--complete", action="store_true",
                        help="完成 CC2 工作流")
    parser.add_argument("--no-wait", action="store_true",
                        help="不等待 CC1 完成")
    parser.add_argument("--no-pr", action="store_true",
                        help="完成时不创建 PR")
    parser.add_argument("--no-test", action="store_true",
                        help="完成时不运行测试")
    parser.add_argument("--timeout", type=int, default=3600,
                        help="等待 CC1 的超时时间（秒）")
    parser.add_argument("--cleanup", action="store_true",
                        help="删除 CC2 worktree")

    args = parser.parse_args()

    if args.status:
        print_status()
    elif args.complete:
        if not args.page:
            print("❌ 完成工作流时必须指定 --page 参数")
            sys.exit(1)
        complete_cc2_workflow(args.page, create_pr=not args.no_pr, run_tests=not args.no_test)
    elif args.cleanup:
        remove_worktree()
    elif args.page:
        start_cc2_workflow(
            args.page,
            args.platform,
            args.app,
            wait_for_cc1=not args.no_wait,
            timeout=args.timeout
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()