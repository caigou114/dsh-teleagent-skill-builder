---
name: teleagent-skill-builder
description: Build TeleAgent (星辰超级智能体) skills that import cleanly on the first try — frontmatter, trigger-rich description, body style, bundled resources, self-check, .skill packaging and local install. Use when the user asks to create, fix, review, validate, package or install a TeleAgent skill: 技能制作, 技能包, SKILL.md, frontmatter 校验, 导入 TeleAgent, .skill 文件.
---

# TeleAgent 技能制作器

为 TeleAgent 平台产出「结构合法、校验通过、可直接导入」的技能。规范全文见
[references/teleagent-spec.md](references/teleagent-spec.md)，写之前先扫一眼第 3 章（frontmatter 硬约束）。

## 完成定义

一个技能只有同时满足以下三条才算做完：

1. `python scripts/validate_skill.py <技能目录>` 退出码为 0；
2. 目录结构合法，没有多余文件（README/安装说明/变更日志一律不建）；
3. 目录里没有任何 `.pyc` / `__pycache__`（平台按「存在恶意扩展名文件」整包拒收）；
4. 文件真实落在磁盘上（用户要的是能直接导入的文件夹，不是聊天里的代码块）。

## 铁律

| 项 | 规则 |
|---|---|
| 目录名 | 必须与 frontmatter 的 `name` 一字不差 |
| `name` | `^[a-z0-9-]+$`，≤40 字符，不以 `-` 开头/结尾，无 `--` |
| 必填字段 | `name`、`description`、`name_cn`、`description_cn` |
| 键白名单 | 只允许 name/description/name_cn/description_cn/create_source/AIGC/license/allowed-tools/metadata |
| `AIGC` | 平台注入的水印，**绝对不要手写**；同名键重复出现即整包加载失败 |
| 引号 | 中文值、含冒号的值、含特殊字符的值一律写成 `key: "值"`，引号成对且不嵌套同类引号；全角冒号 `：` 在 YAML 里合法，ASCII 冒号 `:` 不加引号会被截断 |
| `description` | ≤1024 字符，**不含 `<>`**，必须同时说明「做什么」+「何时触发」 |
| `name_cn` | 用户给了中文名就一字不差照抄 |
| 正文 | <500 行，祈使句，不写「何时使用」章节 |
| 资源 | 只建 scripts/references/assets/icon，用不到的目录整个不建 |
| 字节码 | 禁止 `.pyc`、`.pyo`、`__pycache__/`：Python 入口脚本加载同目录模块前先 `sys.dont_write_bytecode = True`；打包用 `pack_skill.py`，上传用 `.skill` 文件而不是文件夹 |

## 工作流

1. **收敛需求**。缺信息就一次性问清：要覆盖哪些功能、2–3 句典型触发语、中文名（`name_cn`）、是否需要脚本或参考资料。
2. **规划资源**。反复重写的代码 → `scripts/`；需要查阅的长资料 → `references/`；要复制进产出的模板/字体/图片 → `assets/`。用不上的目录不要建。
3. **生成骨架**。

   ```bash
   python scripts/scaffold_skill.py --name my-skill --name-cn "中文名" \
     --description "What it does. Use when ..." --description-cn "中文简介。" \
     --out ./out --dirs scripts,references
   ```

4. **写 description**（最关键，决定技能会不会被触发）。模板：

   ```yaml
   description: "把 <输入> 转成 <产出>，支持 <能力1> 与 <能力2>。当用户提到 <关键词1>、<关键词2>、<口语说法>，或粘贴 <素材类型> 需要整理成 <产出> 时使用。"
   ```

   把文件类型、任务类型、触发场景全部塞进 description——正文只会在触发之后加载，写在正文里对触发毫无帮助。

5. **写正文**。开头给步骤总览，再逐步展开；脆弱步骤给精确命令，开放决策给启发式原则（自由度分级）。拆到 references 的文件必须在正文里写明「何时读取」。
6. **校验**：`python scripts/validate_skill.py <技能目录> -v`。`[FAIL]` 必须清零；`[warn]` 分两类处理——能改就改（中文值加引号、资源写进正文），确实不适用的（比如因为历史原因必须保留的多余目录）在交付说明里写清原因，不要默默忽略。
7. **交付**。三种出口按用户意图选：

   ```bash
   python scripts/install_skill.py <技能目录>      # 直接装进本机 TeleAgent
   python scripts/pack_skill.py <技能目录>         # 生成 <name>.skill 分发
   ```

   用户没有本机路径（纯对话交付）时，按「目录树 + 每个文件一个带路径标注的代码块」输出。

## description 好坏对照

```yaml
# 差：太笼统，模型无法判断何时启用
description: 一个处理文档的技能

# 好：功能 + 触发词 + 任务类型
description: "Comprehensive document creation, editing and analysis with tracked changes, comments, formatting preservation and text extraction. Use when LLM needs to work with professional documents (.docx) for: (1) creating new documents, (2) modifying or editing content, (3) working with tracked changes, (4) adding comments."
```

## 正文骨架（四种，可混搭）

- **工作流型**：`## 概述 → ## 工作流 → ## 步骤/模板 → ## 资源说明`
- **任务型**：`## 概述 → ## 快速开始 → ## 任务类别 1 → ## 任务类别 2`
- **规范型**：`## 概述 → ## 准则 → ## 规格 → ## 用法`
- **能力型**：`## 概述 → ## 核心能力 → ### 1. 能力 → ### 2. 能力`

## 输出模式

- 强约束产出（API 响应、数据格式）：写明「ALWAYS 使用此精确结构」，给出完整模板。
- 风格敏感产出（文案、纪要）：给 1–2 个输入/输出示例对，比三段描述更有效。

## 安装与生效

- 直接落盘：`$TELEAGENT_CONFIG_DIR/skills/<skill-name>/`，Windows 常见为
  `C:\Users\<用户>\.config\TeleAgent\users\<用户ID>\skills\<skill-name>\`。
- 打包分发：zip 顶层为技能文件夹本身，重命名 `<skill-name>.skill`。
- 生效时机：**从下一条用户消息（新会话）开始生效**，当前会话不可用；启用数达上限时需先关掉部分技能。

## 交付前自检（13 项）

- [ ] 目录名 = `name`
- [ ] `name` 小写字母/数字/连字符，≤40 字符，无首尾 `-`、无 `--`
- [ ] 四个必填字段齐全，无白名单外的键
- [ ] 没有 `AIGC` 键，没有任何键重复
- [ ] 中文值、含冒号值全部成对双引号包裹
- [ ] `description` ≤1024 字符、无尖括号、含「做什么 + 何时触发」
- [ ] `name_cn` 与用户指定名称一字不差
- [ ] 正文 <500 行、祈使句、无「何时使用」章节
- [ ] 正文引用的每个资源都真实存在且说明了使用时机
- [ ] 没有 README/安装指南/变更日志等多余文件
- [ ] 脚本已实际跑通（未测通的要显式标注「需测试」）
- [ ] 目录里没有 `.pyc` / `__pycache__`，入口脚本设了 `sys.dont_write_bytecode = True`
- [ ] `validate_skill.py` 退出码 0

## 工具

- `scripts/scaffold_skill.py`：按上述铁律生成目录与 frontmatter 骨架，写错就改它，别手写 frontmatter。
- `scripts/validate_skill.py`：复刻平台 quick_validate 并加工程检查（正文行数、禁用文件、资源引用、TODO 残留、引号闭合、`.pyc`/`__pycache__` 拒收），支持 `>`/`|` 块标量与跨行引号标量，glob 写法（`references/*.md`）不算真实路径，同类警告超过 8 条只列前 8 条。批量校验传多个目录。
- `scripts/pack_skill.py`：打包 `.skill` 并回读校验顶层目录。
- `scripts/install_skill.py`：先校验再复制到本机 skills 目录，自动探测用户目录，支持 `--dry-run`。
