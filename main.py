import os
import random
import shutil
import argparse
from pathlib import Path
from typing import Tuple, Optional
import sys

try:
    from rich.console import Console
    from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TextColumn
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("[警告] 未安装 'rich' 库，将使用简化输出（无彩色进度条）。建议运行: pip install rich", file=sys.stderr)


# ======================
# 工具函数
# ======================

def format_size(size_bytes: int) -> str:
    """将字节大小格式化为带单位的字符串，基于1024"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def generate_random_byte_not_equal_to(original: bytes) -> bytes:
    """生成一个随机字节，且不等于原始字节"""
    original_int = original[0] if len(original) > 0 else 0
    while True:
        b = bytes([random.randint(0, 255)])
        if b != original:
            return b

def parse_size_str(s: str) -> int:
    """将如 '1KB' 的字符串解析为字节数，仅支持 KB（基于1024）"""
    s = s.strip().upper()
    num = ''
    unit = 'KB'
    for c in s:
        if c.isdigit() or c == '.':
            num += c
        else:
            unit = s[s.index(c):].upper()
            break
    if not num:
        num = '1'
    num_f = float(num)
    if unit == 'KB':
        return int(num_f * 1024)
    elif unit == 'B':
        return int(num_f)
    else:
        raise ValueError(f"不支持的step单位: {unit}，目前只支持 KB (如 1KB 或 1)")

def ask_yes_no(prompt: str, default: Optional[bool] = None) -> bool:
    """询问用户 yes/no，返回布尔值"""
    if default is True:
        prompt += " [Y/n]: "
    elif default is False:
        prompt += " [y/N]: "
    else:
        prompt += " [y/n]: "

    while True:
        resp = input(prompt).strip().lower()
        if not resp:
            if default is True:
                return True
            elif default is False:
                return False
            else:
                print("请输入 y 或 n")
                continue
        if resp in ('y', 'yes'):
            return True
        elif resp in ('n', 'no'):
            return False
        else:
            print("请输入 y 或 n")

def confirm_action(description: str) -> bool:
    print(f"\n🔍 操作详情：")
    print(description)
    return ask_yes_no("❓ 是否继续执行？", default=True)

def protect_region_check(file_size: int, pos: int, destroy_count: int) -> Tuple[int, int]:
    """返回可安全破坏的起始位置和实际能破坏的字节数（考虑首尾1024B保护）"""
    safe_start = 1024
    safe_end = file_size - 1024
    if safe_end <= safe_start:
        raise ValueError("文件太小（<2048B），无法进行破坏（首尾各有1024B保护区域）")

    if pos < safe_start or pos >= safe_end:
        return (0, 0)  # 当前step区间不在可破坏范围内

    start = pos
    end = min(pos + 1024, safe_end)  # 每个step区间为1KB，但实际可能不到（结尾部分）
    available_range = end - start
    if available_range <= 0:
        return (0, 0)

    destroy_here = min(destroy_count, available_range)
    actual_start = start + random.randint(0, available_range - destroy_here) if destroy_here > 0 else start
    return (actual_start, destroy_here)

# ======================
# 文件损坏核心函数
# ======================

def corrupt_file(
    file_path: Path,
    step_kb: int,
    destroy_bytes: int,
    make_backup: bool,
    console: Optional[Console] = None
) -> None:
    file_path = Path(file_path)
    file_size = file_path.stat().st_size
    file_name = file_path.name

    step_bytes = step_kb * 1024
    total_steps = (file_size - 2048) // step_bytes  # 去掉首尾各1024，然后按step划分
    if (file_size - 2048) % step_bytes != 0:
        total_steps += 1  # 最后一部分不足也处理

    # 备份逻辑
    backup_path = None
    if make_backup:
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        try:
            console and console.print(f"📦 正在生成备份文件: {backup_path}")
            shutil.copy2(file_path, backup_path)
            console and console.print("[✓] 备份成功")
        except Exception as e:
            console and console.print(f"[!] 备份失败: {e}")
            if ask_yes_no("备份失败，是否继续直接破坏原文件？（不推荐）", default=False):
                make_backup = False
                backup_path = None
            else:
                console and console.print("❌ 用户取消操作")
                return

    try:
        with open(file_path, 'r+b') as f:
            if RICH_AVAILABLE and console:
                # 使用 rich 的进度条，带速度显示
                with Progress(
                    TextColumn(f"[bold blue]{file_name}[/]"),
                    BarColumn(),
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    "•",
                    TransferSpeedColumn(),
                    "•",
                    DownloadColumn(),
                    console=console,
                    refresh_per_second=10
                ) as progress:
                    task = progress.add_task("", total=total_steps)

                    for step_idx in range(total_steps):
                        current_pos = 1024 + step_idx * step_bytes  # 从第1024字节后开始，每step_bytes处理一次

                        actual_pos, num_to_corrupt = protect_region_check(file_size, current_pos, destroy_bytes)

                        if num_to_corrupt <= 0:
                            progress.update(task, advance=1)
                            continue

                        # 定位并破坏
                        f.seek(actual_pos)
                        original_bytes = f.read(num_to_corrupt)
                        new_bytes = b''.join([generate_random_byte_not_equal_to(bytes([b])) for b in original_bytes])

                        f.seek(actual_pos)
                        f.write(new_bytes)

                        progress.update(task, advance=1)

            else:
                # 简化版无 rich 进度条
                for step_idx in range(total_steps):
                    current_pos = 1024 + step_idx * step_bytes

                    actual_pos, num_to_corrupt = protect_region_check(file_size, current_pos, destroy_bytes)

                    if num_to_corrupt <= 0:
                        continue

                    f.seek(actual_pos)
                    original_bytes = f.read(num_to_corrupt)
                    new_bytes = b''.join([generate_random_byte_not_equal_to(bytes([b])) for b in original_bytes])

                    f.seek(actual_pos)
                    f.write(new_bytes)

                    if console:
                        console.print(f"Step {step_idx + 1}/{total_steps}: 已破坏 {actual_pos} 处 {num_to_corrupt} 字节", end='\r')

        if console:
            console.print(f"\n✅ 文件已成功破坏: {file_path}")
    except Exception as e:
        console and console.print(f"[!] 操作失败: {e}")
        raise

# ======================
# 交互模式主函数
# ======================

def interactive_mode():
    console = Console() if RICH_AVAILABLE else None

    try:
        file_path = file_path = input("📁 请输入要破坏的文件路径: ").strip('\'" ')  # 去除首尾的单引号、双引号以及空格
        if not file_path:
            raise ValueError("文件路径不能为空")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")

        file_size = file_path.stat().st_size
        console and console.print(f"📄 文件大小: {format_size(file_size)}")

        # 询问 step
        step_input = input("⏱ 请输入 step (每隔多少KB破坏一次，留空默认1KB): ").strip()
        step_kb = 1  # 默认 1KB
        if step_input:
            try:
                step_kb = int(step_input)
                if step_kb <= 0:
                    raise ValueError
            except ValueError:
                try:
                    step_kb = parse_size_str(step_input) // 1024
                except Exception:
                    raise ValueError("step 必须为正整数或如 '1KB' 格式")
        step_bytes = step_kb * 1024
        console and console.print(f"✅ 使用 step: {step_kb}KB ({step_bytes} 字节)")

        # 询问 destroy
        destroy_input = input("💥 请输入每次破坏的字节数 (留空默认4B): ").strip()
        destroy_bytes = 4
        if destroy_input:
            try:
                destroy_bytes = int(destroy_input)
                if destroy_bytes <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError("destroy 必须为正整数")
        console and console.print(f"✅ 每次破坏: {destroy_bytes} 字节")

        # 询问备份
        disable_backup_input = input("📦 是否禁用备份？[y/N] （留空或 n/N 表示生成备份，y/Y 表示禁用备份）: ").strip().lower()
        make_backup = True  # 默认生成备份
        if disable_backup_input in ('y', 'yes'):
            make_backup = False

        if not make_backup:
            console and console.print("[⚠️] 警告：您选择了不生成备份，原文件可能永久损坏！")

        # 复述并确认
        desc = (
            f"文件: {file_path.name}\n"
            f"大小: {format_size(file_size)}\n"
            f"Step: 每隔 {step_kb}KB ({step_bytes}B)\n"
            f"每次破坏: {destroy_bytes} 字节\n"
            f"保护区域: 文件首尾各 1024B 不受影响\n"
            f"备份: {'是' if make_backup else '否'}"
        )
        if not confirm_action(desc):
            console and console.print("❌ 用户取消操作")
            return

        corrupt_file(file_path, step_kb, destroy_bytes, make_backup, console)

    except Exception as e:
        console and console.print(f"[错误] {e}")
        sys.exit(1)

# ======================
# CLI 参数解析 & 入口
# ======================

def cli_main():
    parser = argparse.ArgumentParser(description="文件破坏工具（保留首尾1024B）")
    parser.add_argument('-f', '--file', required=True, help='目标文件路径')
    parser.add_argument('-s', '--step', type=str, default='1KB', help='每隔多少KB破坏一次（如 1KB，默认1KB）')
    parser.add_argument('-d', '--destroy', type=int, default=4, help='每次破坏多少字节（默认4）')
    parser.add_argument('--no-backup', action='store_true', help='禁用备份（默认生成 .bak 备份）')

    args = parser.parse_args()

    file_path = Path(args.file.strip('\'" '))  # 去除首尾的单/双引号和空格
    if not file_path.exists():
        print(f"[错误] 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)
    if not file_path.is_file():
        print(f"[错误] 不是文件: {file_path}", file=sys.stderr)
        sys.exit(1)

    step_kb = 1
    try:
        step_kb = int(args.step)
        if step_kb <= 0:
            raise ValueError
    except ValueError:
        try:
            step_kb = parse_size_str(args.step) // 1024
        except Exception as e:
            print(f"[错误] step 参数无效: {args.step}，应为如 1KB 或 正整数。错误: {e}", file=sys.stderr)
            sys.exit(1)

    destroy_bytes = args.destroy
    if destroy_bytes <= 0:
        print("[错误] destroy 必须 > 0", file=sys.stderr)
        sys.exit(1)

    make_backup = not args.no_backup
    if args.no_backup:
        print("[⚠️] 警告：您使用了 --no-backup，将不生成备份！原文件可能永久损坏！")
        if not ask_yes_no("是否继续？", default=False):
            print("❌ 用户取消")
            sys.exit(0)

    file_size = file_path.stat().st_size
    console = Console() if RICH_AVAILABLE else None
    desc = (
        f"文件: {file_path.name}\n"
        f"大小: {format_size(file_size)}\n"
        f"Step: 每隔 {step_kb}KB\n"
        f"每次破坏: {destroy_bytes} 字节\n"
        f"保护区域: 文件首尾各 1024B\n"
        f"备份: {'是' if make_backup else '否'}"
    )
    if not confirm_action(desc):
        print("❌ 用户取消")
        sys.exit(0)

    corrupt_file(file_path, step_kb, destroy_bytes, make_backup, console)

# ======================
# 程序入口
# ======================

if __name__ == '__main__':
    try:
        if len(sys.argv) > 1 and sys.argv[1] in ['-f', '--file', '-s', '--step', '-d', '--destroy', '--no-backup']:
            # 命令行参数模式
            cli_main()
        else:
            # 交互模式
            interactive_mode()
    except KeyboardInterrupt:
        print("\n[取消] 用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)
