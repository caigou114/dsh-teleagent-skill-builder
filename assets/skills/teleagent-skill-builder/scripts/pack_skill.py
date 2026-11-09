#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把技能目录打包成可分发的 <name>.skill（zip，顶层为技能文件夹本身）。

用法:
    python pack_skill.py <技能目录> [--out 输出目录]

打包后自动回读校验：顶层必须只有一个 <name>/ 目录。
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


SKIP_DIRS = {"__pycache__", ".git", ".idea", ".vscode", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".DS_Store"}


def iter_files(root: Path):
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        if f.suffix in SKIP_SUFFIXES or f.name == ".DS_Store":
            continue
        yield f


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="打包 TeleAgent 技能为 .skill")
    ap.add_argument("path", help="技能目录")
    ap.add_argument("--out", default=None, help="输出目录，默认为技能目录的父目录")
    args = ap.parse_args(argv)

    root = Path(args.path).resolve()
    if not (root / "SKILL.md").is_file():
        print(f"{root} 下没有 SKILL.md", file=sys.stderr)
        return 2

    out_dir = Path(args.out).resolve() if args.out else root.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{root.name}.skill"

    files = list(iter_files(root))
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, Path(root.name) / f.relative_to(root))

    with zipfile.ZipFile(target) as zf:
        names = zf.namelist()
        tops = {n.split("/")[0] for n in names}
        if tops != {root.name}:
            print(f"打包结构异常，顶层应为 {root.name}/，实际 {sorted(tops)}", file=sys.stderr)
            return 1

    size_kb = target.stat().st_size / 1024
    print(f"已生成: {target}（{len(files)} 个文件，{size_kb:.1f} KB）")
    print("导入方式: 技能广场 / 桌面端「导入技能」选择该 .skill 文件")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
