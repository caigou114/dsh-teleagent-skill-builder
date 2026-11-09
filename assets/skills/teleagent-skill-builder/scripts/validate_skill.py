#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TeleAgent 技能包校验器。

复刻平台 quick_validate 的核心规则（frontmatter 键白名单、name 规则、description 规则），
并补充工程性检查（正文行数、禁用文件、资源引用、TODO 残留等）。

用法:
    python validate_skill.py <技能目录> [更多目录 ...] [-v]

退出码: 0 = 通过（可能带警告），1 = 存在错误。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")


REQUIRED_KEYS = ("name", "description", "name_cn", "description_cn")
ALLOWED_KEYS = {
    "name", "description", "name_cn", "description_cn",
    "create_source", "AIGC", "license", "allowed-tools", "metadata",
}
FORBIDDEN_FILES = {"readme.md", "installation_guide.md", "quick_reference.md", "changelog.md"}
ALLOWED_TOP_DIRS = {"scripts", "references", "assets", "icon"}
RESOURCE_DIRS = ("scripts", "references", "assets")
NAME_RE = re.compile(r"^[a-z0-9-]+$")
KEY_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$")
RES_REF_RE = re.compile(
    r"(?:^|[\s(\[`'\"：:])((?:scripts|references|assets|icon)/[^\s`'\"<>|，。；：、（）\[\]]+)"
)
WHEN_TO_USE_RE = re.compile(r"^#{1,6}\s*(?:when to use|何时使用|什么时候使用|适用场景)", re.I | re.M)
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]")
ASCII_COLON_RE = re.compile(r":(?=\s|$)")
BLOCK_SCALAR_RE = re.compile(r"[>|][+-]?\d?")
TRIGGER_RE = re.compile(r"(use when|use for|use this|何时|当用户|时使用|触发|适用于)", re.I)


class Report:
    def __init__(self, path: Path):
        self.path = path
        self.errors: list[str] = []
        self.warns: list[str] = []
        self.oks: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warns.append(msg)

    def ok(self, msg: str) -> None:
        self.oks.append(msg)

    @property
    def passed(self) -> bool:
        return not self.errors


def split_frontmatter(text: str):
    """返回 (frontmatter_raw, body, error)。"""
    clean = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = clean.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, clean, "文件第一行必须是 ---（frontmatter 前不能有空行、BOM 或注释）"
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, clean, "frontmatter 未用单独一行 --- 结束"
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1:]), None


def parse_keys(fm_text: str, rep: Report):
    """解析 frontmatter 顶层键，返回 [(key, value_raw, lineno, multiline)]。

    支持块标量（`>` / `|`）与跨行引号标量：缩进续行并入上一个键，multi=True。
    """
    entries: list[tuple[str, str, int, bool]] = []
    seen: dict[str, int] = {}
    cur: dict | None = None

    def flush() -> None:
        if cur is not None:
            entries.append((cur["key"], "\n".join(cur["parts"]), cur["lineno"], cur["multi"]))

    for lineno, line in enumerate(fm_text.split("\n"), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[:1] in (" ", "\t"):
            if cur is None:
                rep.err(f"frontmatter 第 {lineno} 行是缩进内容，但上方没有对应的键 —— {line!r}")
                continue
            cur["parts"].append(line)
            cur["multi"] = True
            continue
        m = KEY_LINE_RE.match(line)
        if not m:
            rep.err(f"frontmatter 第 {lineno} 行无法解析为 key: value —— {line!r}")
            continue
        flush()
        key, raw = m.group(1), (m.group(2) or "")
        if key in seen:
            rep.err(f"键 {key!r} 重复出现（第 {seen[key]} 行与第 {lineno} 行），YAML 会解析失败")
        seen[key] = lineno
        cur = {"key": key, "lineno": lineno, "parts": [raw], "multi": False}
    flush()
    return entries


def strip_quotes(raw: str):
    v = raw.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1], True
    return v, False


def check_quote_hygiene(entries, rep: Report) -> None:
    for key, raw, lineno, multi in entries:
        if not raw.strip():
            continue
        first = raw.split("\n", 1)[0]
        head = first.strip()[:1]
        if multi or BLOCK_SCALAR_RE.fullmatch(first.strip()):  # 块标量 / 跨行标量交给 YAML 解析器判断
            continue
        raw = raw.strip()
        if head in "\"'" and not (len(raw) > 1 and raw[-1] == head):
            rep.err(f"第 {lineno} 行 {key!r} 的引号未闭合")
            continue
        val, quoted = strip_quotes(raw)
        if quoted:
            inner = raw[1:-1]
            if head == '"' and '"' in inner:
                rep.err(f"第 {lineno} 行 {key!r} 的双引号内又嵌套了双引号，请改用单引号或「」")
            if head == "'" and "'" in inner:
                rep.err(f"第 {lineno} 行 {key!r} 的单引号内又嵌套了单引号")
            continue
        if ASCII_COLON_RE.search(raw):
            rep.err(f"第 {lineno} 行 {key!r} 的值含 ASCII 冒号，YAML 会截断，必须整体用双引号包裹 —— {raw[:40]!r}")
        elif head in "#&*!|>{[@`%":
            rep.err(f"第 {lineno} 行 {key!r} 以 YAML 特殊字符 {head!r} 开头，必须加引号")
        elif " #" in raw:
            rep.err(f"第 {lineno} 行 {key!r} 的值含「空格+#」，会被当成注释截断，必须加引号")
        elif CJK_RE.search(raw):
            rep.warn(f"第 {lineno} 行 {key!r} 的中文值未加引号（YAML 合法但不稳），建议整体加双引号 —— {raw[:30]!r}")


def validate(skill_dir: Path, verbose: bool = False) -> Report:
    rep = Report(skill_dir)

    if not skill_dir.is_dir():
        rep.err(f"目录不存在: {skill_dir}")
        return rep

    md = skill_dir / "SKILL.md"
    if not md.is_file():
        rep.err("缺少 SKILL.md（必须位于技能目录根部）")
        return rep

    stray = [x for x in skill_dir.rglob("SKILL.md") if x.resolve() != md.resolve()]
    if stray:
        rep.err("存在多余的 SKILL.md: " + ", ".join(str(x.relative_to(skill_dir)) for x in stray))
    else:
        rep.ok("SKILL.md 唯一")

    raw_bytes = md.read_bytes()
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        rep.err("SKILL.md 带 BOM；frontmatter 必须以 --- 开头")
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        rep.err(f"SKILL.md 不是 UTF-8 编码: {exc}")
        return rep

    fm_text, body, perr = split_frontmatter(text)
    if perr:
        rep.err(perr)
        return rep
    if "\t" in fm_text:
        rep.err("frontmatter 中出现制表符（Tab），缩进只能用空格")
    else:
        rep.ok("frontmatter 无制表符")

    entries = parse_keys(fm_text, rep)
    keys = [k for k, _, _, _ in entries]

    unknown = sorted({k for k in keys if k not in ALLOWED_KEYS})
    if unknown:
        rep.err("frontmatter 出现非白名单键: " + ", ".join(unknown))
    else:
        rep.ok("frontmatter 键全部在白名单内")

    if "AIGC" in keys:
        rep.err("禁止手写 AIGC 键（平台自动注入的水印，手写会重复叠加导致整批技能加载失败）")
    else:
        rep.ok("未手写 AIGC 键")

    missing = [k for k in REQUIRED_KEYS if k not in keys]
    if missing:
        rep.err("缺少必填字段: " + ", ".join(missing))
        return rep
    rep.ok("四个必填字段齐全")

    check_quote_hygiene(entries, rep)

    loaded = None
    try:
        import yaml  # 可选：装了 pyyaml 就做一次权威解析
    except ImportError:
        rep.warn("未安装 pyyaml，跳过 YAML 结构解析（pip install pyyaml 可获得更强校验）")
    else:
        try:
            parsed = yaml.safe_load(fm_text)
            if not isinstance(parsed, dict):
                rep.err("frontmatter 不是 YAML 字典")
            else:
                loaded = parsed
                rep.ok("YAML 结构可被安全解析")
        except Exception as exc:  # noqa: BLE001
            rep.err(f"YAML 解析失败: {exc}")

    values: dict[str, str] = {}
    for key, raw, _lineno, multi in entries:
        if key in values:
            continue
        if loaded is not None and key in loaded:
            v = loaded[key]
            values[key] = v.strip() if isinstance(v, str) else ("" if v is None else str(v))
        elif multi:  # 没有 pyyaml 时的兜底：块标量取续行，跨行引号拼接
            rest = "\n".join(raw.split("\n")[1:])
            values[key] = " ".join(rest.split())
        else:
            values[key] = strip_quotes(raw)[0].strip()

    name = values.get("name", "").strip()
    if not NAME_RE.match(name):
        rep.err(f"name {name!r} 只允许小写字母、数字、连字符")
    elif name.startswith("-") or name.endswith("-") or "--" in name:
        rep.err(f"name {name!r} 不能以连字符开头/结尾，也不能含连续连字符")
    elif len(name) > 64:
        rep.err(f"name 过长（{len(name)} > 64）")
    elif name != skill_dir.name:
        rep.err(f"name {name!r} 与目录名 {skill_dir.name!r} 不一致")
    else:
        if len(name) > 40:
            rep.warn(f"name 长度 {len(name)} 超过建议上限 40，建议缩短")
        rep.ok(f"name 合法: {name}")

    desc = values.get("description", "").strip()
    if len(desc) > 1024:
        rep.err(f"description 过长（{len(desc)} > 1024）")
    if "<" in desc or ">" in desc:
        rep.err("description 含尖括号（HTML 标签会让平台校验失败）")
    if not TRIGGER_RE.search(desc):
        rep.warn("description 未见触发场景说明（应包含「做什么 + 何时触发」）")
    if len(desc) < 40:
        rep.warn(f"description 仅 {len(desc)} 字符，缺少触发关键词")
    if len(desc) <= 1024 and "<" not in desc and ">" not in desc:
        rep.ok("description 长度与字符集合法")

    cs = values.get("create_source")
    if cs is not None and cs != "super-agent-skill-creator":
        rep.err(f"create_source 若存在必须是 super-agent-skill-creator，当前为 {cs!r}")

    for key in ("name_cn", "description_cn"):
        val = values.get(key, "").strip()
        if not val:
            rep.err(f"{key} 为空")
        elif val.startswith(("<", ">")):
            rep.warn(f"{key} 以尖括号开头，前端展示可能异常")

    body_lines = body.splitlines()
    n_lines = len(body_lines)
    if n_lines >= 500:
        rep.err(f"正文 {n_lines} 行，超过 500 行上限，请拆分到 references/")
    elif n_lines > 450:
        rep.warn(f"正文 {n_lines} 行，接近 500 行上限")
    else:
        rep.ok(f"正文行数 {n_lines} < 500")

    if WHEN_TO_USE_RE.search(body):
        rep.err("正文出现「何时使用」章节（触发信息属于 description，正文不要重复）")
    if "TODO" in body:
        rep.err("正文仍残留 TODO 占位内容（骨架没写完，不能交付）")
    words = len(body.split())
    if words > 5000:
        rep.warn(f"正文约 {words} 词，超过建议的 5000 词")

    for child in sorted(skill_dir.iterdir()):
        if child.is_dir() and child.name not in ALLOWED_TOP_DIRS:
            rep.warn(f"非常规顶层目录: {child.name}/（平台只约定 scripts/references/assets/icon，能放进 references/ 就放进去）")

    for f in sorted(skill_dir.rglob("*")):
        if f.is_file() and f.name.lower() in FORBIDDEN_FILES:
            rep.err(f"出现禁用文件: {f.relative_to(skill_dir)}（技能包不放写给人类的文档）")

    # 平台审核会直接拒绝 .pyc / __pycache__（「存在恶意扩展名文件」），这里当硬错误
    BYTECODE_SUFFIX = (".pyc", ".pyo")
    for f in skill_dir.rglob("*"):
        if f.is_dir() and f.name == "__pycache__":
            rep.err(f"发现 __pycache__ 目录（{f.relative_to(skill_dir).as_posix()}）：平台审核会因为 .pyc 拒绝导入，打包前必须删掉")
        elif f.is_file() and f.suffix.lower() in BYTECODE_SUFFIX:
            rep.err(f"发现字节码文件 {f.relative_to(skill_dir).as_posix()}：平台审核会拒绝含 .pyc 的技能包，删掉再打包")

    for d in RESOURCE_DIRS:
        p = skill_dir / d
        if p.is_dir() and not any(x.is_file() for x in p.rglob("*")):
            rep.err(f"{d}/ 是空目录，不需要就整目录删掉")

    referenced = set()
    skipped = 0
    for m in RES_REF_RE.finditer(body):
        raw_rel = m.group(1)
        nxt = body[m.end():m.end() + 1]
        if nxt in ("*", "?", "{", "<", "$") or any(ch in raw_rel for ch in "*?{}<>$"):
            skipped += 1  # glob 或占位写法（如 references/*.md），不当作真实路径
            continue
        rel = raw_rel.rstrip(".,;:)`'\"。，、）")
        referenced.add(rel)
        if not (skill_dir / rel).exists():
            rep.err(f"正文引用了并不存在的资源: {rel}")
    if referenced:
        rep.ok(f"正文引用资源 {len(referenced)} 个，均已存在")
    if skipped:
        rep.ok(f"跳过 {skipped} 个 glob/占位写法（如 references/*.md）")

    for d in RESOURCE_DIRS:
        p = skill_dir / d
        if not p.is_dir():
            continue
        missing_refs = []
        for f in p.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() in (".pyc", ".pyo") or "__pycache__" in f.parts:
                continue  # 字节码已单独报错，别再补一条「未引用」的噪音
            rel = f.relative_to(skill_dir).as_posix()
            if rel not in referenced:
                missing_refs.append(rel)
        for rel in missing_refs[:8]:
            rep.warn(f"{rel} 未在 SKILL.md 正文中出现（模型不会知道它存在）")
        if len(missing_refs) > 8:
            rep.warn(f"……另有 {len(missing_refs) - 8} 个资源文件未被正文引用（同类问题，不再逐条列出）")

    return rep


def print_report(rep: Report, verbose: bool) -> None:
    print(f"\n=== {rep.path}")
    if verbose:
        for msg in rep.oks:
            print(f"  [ok]   {msg}")
    for msg in rep.warns:
        print(f"  [warn] {msg}")
    for msg in rep.errors:
        print(f"  [FAIL] {msg}")
    if rep.passed:
        print(f"  => 通过（警告 {len(rep.warns)} 条）")
    else:
        print(f"  => 失败（{len(rep.errors)} 个错误，{len(rep.warns)} 条警告）")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="TeleAgent 技能包校验器")
    ap.add_argument("paths", nargs="+", help="技能目录（可多个）")
    ap.add_argument("-v", "--verbose", action="store_true", help="打印通过的检查项")
    args = ap.parse_args(argv)

    failed = 0
    for raw in args.paths:
        rep = validate(Path(raw).resolve(), verbose=args.verbose)
        print_report(rep, args.verbose)
        if not rep.passed:
            failed += 1
    print()
    if failed:
        print(f"结论: {failed} 个技能包未通过校验，修复后重试。")
        return 1
    print("Skill is valid!")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
