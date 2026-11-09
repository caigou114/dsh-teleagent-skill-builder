#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成符合 TeleAgent 规范的技能骨架。

用法:
    python scaffold_skill.py --name meeting-minutes-organizer \
        --name-cn "会议纪要整理器" \
        --description "Convert raw transcripts into structured minutes... Use when ..." \
        --description-cn "把速记整理成结构化纪要。" \
        --out ./out --dirs scripts,references

只创建真正用得上的资源目录；不需要的目录不要传。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


NAME_RE = re.compile(r"^[a-z0-9-]+$")

SKELETON = """---
name: "{name}"
description: "{description}"
name_cn: "{name_cn}"
description_cn: "{description_cn}"
---

# {title}

## 概述

{description_cn}

## 工作流

1. TODO: 判断输入类型 → 走对应分支
2. TODO: 关键动作（需要确定性结果时调 scripts/ 下的脚本）
3. TODO: 按下方模板产出

## 输出格式

TODO: 固定模板（ALWAYS 使用此结构）或给出 1-2 个输入/输出示例

## 资源说明

{resources}
"""


def build_resources(dirs: list[str]) -> str:
    lines = []
    if "scripts" in dirs:
        lines.append("- **脚本**：scripts/ 目录下的脚本，正文需写明文件名、运行命令与触发条件")
    if "references" in dirs:
        lines.append("- **参考文档**：references/ 目录下的资料，正文需写明在什么场景下读取")
    if "assets" in dirs:
        lines.append("- **资产**：assets/ 目录下的模板/字体/图片，产出时直接复制使用")
    return "\n".join(lines) if lines else "（本技能无捆绑资源）"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="生成 TeleAgent 技能骨架")
    ap.add_argument("--name", required=True)
    ap.add_argument("--name-cn", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--description-cn", required=True)
    ap.add_argument("--title")
    ap.add_argument("--out", default=".", help="父目录，默认当前目录")
    ap.add_argument("--dirs", default="", help="逗号分隔: scripts,references,assets")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    name = args.name.strip()
    if not NAME_RE.match(name):
        print(f"name {name!r} 只允许小写字母、数字、连字符", file=sys.stderr)
        return 2
    if name.startswith("-") or name.endswith("-") or "--" in name or len(name) > 40:
        print(f"name {name!r} 违反命名规则（不能以 - 开头/结尾、不能含 --、建议 ≤40 字符）", file=sys.stderr)
        return 2
    if "<" in args.description or ">" in args.description:
        print("description 不能含尖括号", file=sys.stderr)
        return 2
    if len(args.description) > 1024:
        print("description 超过 1024 字符", file=sys.stderr)
        return 2

    root = Path(args.out).resolve() / name
    if root.exists() and not args.force:
        print(f"目录已存在: {root}（加 --force 覆盖）", file=sys.stderr)
        return 2

    dirs = [d.strip() for d in args.dirs.split(",") if d.strip()]
    bad = [d for d in dirs if d not in {"scripts", "references", "assets"}]
    if bad:
        print(f"未知资源目录: {bad}", file=sys.stderr)
        return 2

    root.mkdir(parents=True, exist_ok=True)
    for d in dirs:
        (root / d).mkdir(exist_ok=True)

    title = args.title or args.name_cn
    md = SKELETON.format(
        name=name,
        description=args.description.replace('"', "'"),
        name_cn=args.name_cn.replace('"', "'"),
        description_cn=args.description_cn.replace('"', "'"),
        title=title,
        resources=build_resources(dirs),
    )
    (root / "SKILL.md").write_text(md, encoding="utf-8", newline="\n")

    print(f"已创建: {root}")
    print(f"  SKILL.md")
    for d in dirs:
        print(f"  {d}/")
    print("\n下一步: 填正文 → python validate_skill.py " + str(root))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
