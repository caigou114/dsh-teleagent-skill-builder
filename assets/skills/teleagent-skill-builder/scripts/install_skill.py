#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把技能目录直接安装到本机 TeleAgent 的 skills 目录（先校验再复制）。

用法:
    python install_skill.py <技能目录>                 # 自动探测用户目录
    python install_skill.py <技能目录> --user 2082075  # 指定用户 ID 片段
    python install_skill.py <技能目录> --root "D:/x/skills"
    python install_skill.py <技能目录> --dry-run

定位顺序: --root > $TELEAGENT_CONFIG_DIR/skills > ~/.config/TeleAgent/users/<用户>/skills
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_skill import validate, print_report  # noqa: E402


def candidate_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("TELEAGENT_CONFIG_DIR")
    if env:
        roots.append(Path(env) / "skills")
    users = Path.home() / ".config" / "TeleAgent" / "users"
    if users.is_dir():
        for u in sorted(users.iterdir()):
            s = u / "skills"
            if s.is_dir():
                roots.append(s)
    return roots


def score(root: Path) -> tuple[int, float]:
    count = len([d for d in root.iterdir() if d.is_dir()]) if root.is_dir() else 0
    newest = 0.0
    for f in root.glob("*/SKILL.md"):
        newest = max(newest, f.stat().st_mtime)
    return count, newest


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="安装技能到本机 TeleAgent")
    ap.add_argument("path")
    ap.add_argument("--root", help="skills 目录")
    ap.add_argument("--user", help="用户 ID 片段，用于在多个用户目录中筛选")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    src = Path(args.path).resolve()
    rep = validate(src)
    print_report(rep, verbose=False)
    if not rep.passed:
        print("校验未通过，已中止安装。", file=sys.stderr)
        return 1

    if args.root:
        roots = [Path(args.root).resolve()]
    else:
        roots = candidate_roots()
        if args.user:
            roots = [r for r in roots if args.user in str(r)]
    if not roots:
        print("未找到 TeleAgent skills 目录，请用 --root 指定。", file=sys.stderr)
        return 2

    roots.sort(key=score, reverse=True)
    target_root = roots[0]
    if len(roots) > 1:
        print("\n候选目录（按技能数量与新鲜度排序）:")
        for r in roots:
            print(f"  - {r}")
        print(f"使用: {target_root}（如不对，用 --user 或 --root 指定）")

    dst = target_root / src.name
    if dst.exists() and args.dry_run:
        print(f"\n[dry-run] 将覆盖: {dst}")
        return 0
    if args.dry_run:
        print(f"\n[dry-run] 将安装到: {dst}")
        return 0

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))

    after = validate(dst)
    print(f"\n已安装: {dst}")
    if not after.passed:
        print_report(after, verbose=False)
        print("复制后校验失败，请检查目标目录权限或文件占用。", file=sys.stderr)
        return 1

    print(
        "\n生效提醒:\n"
        "  1. 新技能从下一条用户消息（新会话）开始生效，当前会话不可用\n"
        "  2. 若本机已启用技能数达到上限，需先在技能面板关闭部分技能\n"
        "  3. 平台若未自动发现，重启 TeleAgent 后在技能面板确认已启用"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
