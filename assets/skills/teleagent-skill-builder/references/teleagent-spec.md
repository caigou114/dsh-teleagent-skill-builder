> **导航**：本文件是 TeleAgent 技能规范的权威副本，由 	eleagent-skill-builder 技能随包携带。
> 章节：1 技能是什么 · 2 目录结构 · 3 SKILL.md 格式硬约束（3.3 校验规则 / 3.4 YAML 雷区 / 3.5 description 写法）· 4 正文规范 · 5 捆绑资源 · 6 设计模式库 · 7 黄金模板 · 8 输出协议 · 9 自检清单 · 10 导入方式 · 11 平台管线 · 附录 A 本地校验脚本
> 原始出处：`C:\Users\yhyc\.local\share\TeleAgent\TeleAgent的工作空间\TeleAgent技能制作规范_喂给DeepSeek.md`（版本基准 2026-11）
# TeleAgent（星辰超级智能体）技能制作完整规范

> **本文档用途**：这是一份自包含的规范文档。把它完整投喂给任何 AI 助手（如 DeepSeek）后，该助手即可为 TeleAgent 平台产出「结构合法、校验通过、可直接导入」的技能（Skill）。
>
> **阅读顺序建议**：先通读第 1–3 章（格式硬约束），再读第 4–6 章（内容质量规范），最后按第 7–9 章的模板和输出协议交付。
>
> 版本基准：TeleAgent skill-creator 技能规范（2026-11 提取），校验规则与平台内置校验器逐条对应。

---

## 1. 什么是 TeleAgent 技能（Skill）

技能是**模块化、自包含的扩展包**，用来增强 LLM 的能力。可以把技能理解为「某个特定领域的入职培训手册」——它把通用大模型变成一个具备「程序性知识」的专用助手。

技能能提供四类价值：

1. **专业工作流**——特定领域的多步骤操作程序（如：PDF 表单填充的 5 步流程）
2. **工具集成**——操作特定文件格式或 API 的指令（如：docx/PPT 的读写方法）
3. **领域知识**——公司特有的知识、数据模式、业务逻辑（如：内部数据库表结构）
4. **捆绑资源**——脚本、参考文档、模板资产（如：可执行的处理脚本、品牌模板）

**核心理念（贯穿全文）**：技能是写给「另一个 LLM 实例」看的说明书，不是写给人看的文档。默认 LLM 已经很聪明，只写它不知道的信息。

---

## 2. 技能的标准目录结构

```
<skill-name>/                 ← 目录名必须与 frontmatter 的 name 完全一致
├── SKILL.md                  ← 【必需】唯一的必需文件
├── scripts/                  ← 【可选】可执行代码（Python/Bash 等）
│   └── xxx.py
├── references/               ← 【可选】按需加载进上下文的参考文档
│   └── xxx.md
├── assets/                   ← 【可选】用于最终产出的文件（模板/图片/字体等）
│   └── xxx.pptx
└── icon/                     ← 【可选】技能图标（如 avatar.png）
```

三条硬规则：

- **必须且只能有一个 `SKILL.md`**，位于技能目录根部。
- **三个资源目录（scripts/references/assets）按需存在**，不需要的整目录删除，不要留空目录或占位文件。
- **目录名 = frontmatter 的 `name` 字段**，一字不差。

---

## 3. SKILL.md 完全规范（格式硬约束）

### 3.1 文件构成

SKILL.md = **YAML frontmatter（元数据）** + **Markdown 正文（指令）**，格式如下：

```markdown
---
name: my-skill-name
description: 一句话说明技能做什么、什么时候触发使用
name_cn: "技能中文名"
description_cn: "技能中文简介"
---

# 技能标题

（Markdown 正文：使用该技能的完整指令）
```

### 3.2 frontmatter 字段一览

| 字段 | 必填 | 谁看到 | 作用 |
|---|---|---|---|
| `name` | ✅ | LLM | 触发逻辑读取；**必须与目录名一致** |
| `description` | ✅ | LLM | **技能的主触发机制**，LLM 靠它判断何时启用技能 |
| `name_cn` | ✅ | 用户前端 | 产品界面显示的中文名 |
| `description_cn` | ✅ | 用户前端 | 产品界面显示的中文简介 |
| `license` | ⬜ | — | 许可说明，一般写 `Complete terms in LICENSE.txt` |
| `allowed-tools` | ⬜ | — | 工具白名单（极少用） |
| `metadata` | ⬜ | — | 自定义元数据（极少用） |
| `create_source` | ⬜ | — | 来源标记；存在时值必须为 `super-agent-skill-creator`。**手工制作的技能直接省略此字段** |
| `AIGC` | ❌禁止手写 | 系统 | 平台自动注入的水印元数据。**绝对不要自己写** |

**字段命名规则（与平台校验器逐条对应）：**

- 允许出现的键**只有**：`name`、`description`、`name_cn`、`description_cn`、`create_source`、`AIGC`、`license`、`allowed-tools`、`metadata`。
- 出现任何其他键 → 校验直接失败。
- **同一种键出现两次（如两个 `AIGC:` 或两个 `name:`）→ YAML 解析直接失败，技能无法加载。**

### 3.3 各字段的硬性校验规则

**`name` 字段：**

- 只允许 **小写字母、数字、连字符（-）**，即匹配 `^[a-z0-9-]+$`
- 不能以连字符开头或结尾；不能出现连续连字符 `--`
- 长度 ≤ 64 字符（安全线：**≤ 40 字符**，初始化脚本的建议上限）
- 必须与技能目录名**完全一致**
- 起名风格：英文连字符命名，如 `meeting-minutes-organizer`、`pdf-form-filler`

**`description` 字段：**

- 长度 ≤ 1024 字符
- **不能包含尖括号 `<` 或 `>`**（含 HTML 标签的描述会校验失败）
- 内容必须包含两部分：**① 技能做什么；② 什么场景/关键词触发它**
- 描述里包含「文件类型、任务类型、触发场景」等所有「何时使用」的信息——**这些信息不要写到正文里**，因为正文只有在技能被触发之后才会加载，写在那里对触发毫无帮助

**`name_cn` / `description_cn` 字段：**

- 必须是字符串（YAML 中表现为带引号的文本）
- **如果用户给出了想要的技能名称（任何语言），`name_cn` 必须一字不差地用用户提供的字符串**，即使原文是英文

### 3.4 YAML 避坑铁律（真实故障总结，违反即技能报废）

以下每一条都来自技能包批量导入时的真实故障案例，**任何一条违反都会导致 frontmatter 解析失败、技能整包无法加载**：

1. **中文值和含特殊字符的值必须用双引号包裹**。`name_cn` 和 `description_cn` 永远写成 `name_cn: "中文名"`。
2. **值内含冒号必须整体加引号**。裸写 `description: Use when: needed` 会把 YAML 结构劈碎。规则：值里只要出现「冒号+空格」，整个值必须加引号。
3. **引号必须成对闭合**。`description_cn: "未闭合的引号` 是最常见的废包原因。
4. **引号内不要嵌套同种引号**。双引号包裹的值里如果还要用引号，内层改用单引号，或改用中文引号「」。
5. **禁止手写 `AIGC` 键**。它是平台注入的水印。新技能写了会被注入流程重复叠加（历史上真实出现过 AIGC 键重复导致 181 个技能集体加载失败的事故）。
6. **frontmatter 只写一个块**。文件必须以 `---\n` 开头，frontmatter 以单独一行 `---` 结束，之后才是 `# 标题`。
7. **不要在 YAML 值里使用制表符（Tab）**，缩进一律用空格。
8. **frontmatter 顶部必须从文件第一行开始**，`---` 之前不能有空行、BOM 或注释。

### 3.5 description 黄金写法（对照示例）

**❌ 差的写法（太笼统，无触发信息）：**

```yaml
description: 一个处理文档的技能
```

**✅ 好的写法（功能 + 触发场景 + 任务类型）：**

```yaml
description: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when LLM needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks"
```

中文技能同理（注意引号）：

```yaml
description: "微信群管理技能：读取群聊天记录、按时段总结群消息、进行敏感词检测并向指定群发送简报。当用户提到『群聊天总结』『群消息总结』『微信群敏感词』或要求管理/监控微信群时使用。"
```

---

## 4. 正文（Body）编写规范

### 4.1 三级渐进式加载机制（技能的底层运行逻辑）

理解这个机制才能写出好技能。技能内容按三级加载，目的是**省上下文窗口**：

| 级别 | 内容 | 加载时机 | 体量约束 |
|---|---|---|---|
| 第 1 级 | `name` + `description` | **始终在上下文中**（所有技能的元数据常驻） | 合计约 100 词 |
| 第 2 级 | SKILL.md 正文 | **技能被触发后才加载** | < 5000 词 |
| 第 3 级 | scripts/references/assets | LLM 按需读取；脚本可以不读入上下文直接执行 | 不限（脚本不占上下文） |

上下文窗口是「公共资源」，要和系统提示词、对话历史、其他技能元数据、用户请求共享。**每一句话都要自问：这值得花这个 token 吗？**

### 4.2 简洁原则

- **默认读者已经很聪明**。只写 LLM 不可能已知的信息（公司内部流程、特定工具用法、专有数据模式）。
- **用简短示例代替冗长解释**。一个代码片段胜过三段描述。

### 4.3 自由度分级（按任务脆弱性设定约束强度）

写指令时，根据任务的「容错度」选择约束粒度，像修桥一样：窄桥加护栏，旷野任通行。

| 自由度 | 形式 | 适用场景 |
|---|---|---|
| **高自由度** | 文本化指令 | 多种做法都成立、决策依赖上下文、靠启发式判断 |
| **中自由度** | 伪代码 / 带参数的脚本 | 有首选模式、允许少量变化、配置影响行为 |
| **低自由度** | 精确脚本、固定参数 | 操作脆弱易错、一致性关键、必须按固定顺序执行 |

### 4.4 硬性限制与结构要求

- 正文 **< 500 行**。接近上限时必须拆分内容到 `references/` 文件。
- 拆分时**必须在 SKILL.md 里明确引用**这些文件并说明「何时读取它们」，否则 LLM 不知道它们存在。
- 引用文件**保持一层深度**：所有 reference 文件都从 SKILL.md 直接链接，不要嵌套引用。
- 超过 100 行的 reference 文件，**开头要有目录**，让 LLM 预览时看到全貌。
- **语言风格：一律用祈使句/动词原形开头**（"Extract the text…"/「提取文本…」），不要用「你应该…」的对话体。

### 4.5 禁止出现的正文内容

- 不要写「When to Use This Skill」章节（触发信息属于 description，正文加载时触发已经发生）
- 不要写开发过程记录、安装说明、变更日志、测试步骤

---

## 5. 捆绑资源规范

### 5.1 `scripts/` —— 可执行代码

- **何时放**：同一段代码被反复重写时；需要确定性可靠性时
- **示例**：`scripts/rotate_pdf.py`（PDF 旋转）、`scripts/fill_form.py`（表单填充）
- **优点**：省 token、结果确定、可以不读入上下文直接执行
- **注意**：脚本必须实际测试通过后才能放进技能包；LLM 仍可能读它来打补丁，所以代码要写得可读

### 5.2 `references/` —— 按需加载的参考文档

- **何时放**：LLM 工作中需要查阅的详细资料
- **示例**：`references/schema.md`（数据库表结构）、`references/api_docs.md`（API 规格）、`references/policies.md`（公司制度）
- **大文件**：> 10000 词的文件，要在 SKILL.md 中附上 grep 搜索模式（如「搜索关键词：账期、结算」），方便 LLM 定位
- **去重原则**：同一信息只存在一个地方——要么在 SKILL.md，要么在 reference，不要两边都写

### 5.3 `assets/` —— 产出用的资产文件

- **何时放**：需要出现在最终产出里的文件
- **示例**：`assets/logo.png`、`assets/slides.pptx`（PPT 模板）、`assets/frontend-template/`（前端脚手架）、`assets/font.ttf`
- **特点**：**不进入上下文**，直接被复制/引用到输出中
- 与 references 的本质区别：references 是「读给 LLM 看的」，assets 是「拿去用的」

### 5.4 技能包里禁止出现的文件

技能目录里**只放**支撑功能的核心文件。以下文件一律禁止创建：

- `README.md`
- `INSTALLATION_GUIDE.md`
- `QUICK_REFERENCE.md`
- `CHANGELOG.md`
- 任何「写给人类的辅助文档」

技能是给 AI 用的，多余文件只会造成混乱和加载噪音。

---

## 6. 设计模式库（可直接套用）

### 6.1 正文骨架——四种结构模式（可混搭）

**模式 1：工作流型**（适合有明确步骤顺序的流程）
```
## Overview → ## Workflow Decision Tree → ## Step 1 → ## Step 2 → …
```

**模式 2：任务型**（适合工具集合）
```
## Overview → ## Quick Start → ## Task Category 1 → ## Task Category 2 → …
```

**模式 3：参考/规范型**（适合标准、准则类）
```
## Overview → ## Guidelines → ## Specifications → ## Usage
```

**模式 4：能力型**（适合多功能集成系统）
```
## Overview → ## Core Capabilities → ### 1. Feature → ### 2. Feature → …
```

### 6.2 渐进披露——三种拆分模式

**模式 A：高层指南 + 引用文件**（正文只留工作流，细节外移）

```markdown
# PDF 处理

## 快速开始
用 pdfplumber 提取文本：
[核心代码示例]

## 高级功能
- **表单填充**：见 [FORMS.md](references/FORMS.md) 完整指南
- **API 参考**：见 [REFERENCE.md](references/REFERENCE.md) 全部方法
```

**模式 B：领域分域组织**（多领域技能，问哪个领域读哪个文件）

```
bigquery-skill/
├── SKILL.md（总览 + 导航）
└── references/
    ├── finance.md   ← 问财务指标时只读这个
    ├── sales.md
    └── product.md
```

**模式 C：条件性细节**（基础内联，高级外链）

```markdown
## 创建文档
新文档用 docx-js。详见 [DOCX-JS.md](references/DOCX-JS.md)。

## 编辑文档
简单编辑直接改 XML。
**修订追踪**：见 [REDLINING.md](references/REDLINING.md)
```

### 6.3 工作流模式（正文内部的流程写法）

**顺序工作流**——开头给步骤总览：

```markdown
填充 PDF 表单包含以下步骤：
1. 分析表单（运行 analyze_form.py）
2. 创建字段映射（编辑 fields.json）
3. 校验映射（运行 validate_fields.py）
4. 填充表单（运行 fill_form.py）
5. 验证输出（运行 verify_output.py）
```

**条件工作流**——决策点用分支引导：

```markdown
1. 判断修改类型：
   **新建内容？** → 走下方「创建工作流」
   **修改已有内容？** → 走下方「编辑工作流」
2. 创建工作流：[步骤]
3. 编辑工作流：[步骤]
```

### 6.4 输出模式（保证产出质量一致性）

**严格模板模式**（用于 API 响应、数据格式等强约束场景）——写明「ALWAYS 使用此精确模板结构」。

**灵活模板模式**（允许临场调整的场景）——写明「这是合理默认格式，按最佳判断调整」。

**示例对模式**（输出质量依赖风格时）——给输入/输出对：

```markdown
**示例 1：**
输入：Added user authentication with JWT tokens
输出：
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

示例比描述更能让 LLM 领会风格和详略程度。

---

## 7. 黄金模板（完整可复制的 SKILL.md 样例）

以下是一个填写完整的真实样例（虚构技能「会议纪要整理器」），可直接模仿：

````markdown
---
name: meeting-minutes-organizer
description: "Convert raw meeting transcripts or voice notes into structured meeting minutes with attendees, decisions, action items and deadlines. Use when the user mentions 会议纪要, meeting minutes, meeting summary, 会上说的整理一下, or pastes raw transcript/voice memo text that needs to be organized into a formal minutes document."
name_cn: "会议纪要整理器"
description_cn: "把会议速记、录音转写整理成结构化纪要：自动提取参会人、决议事项、行动项与截止日期。"
---

# 会议纪要整理器

## 概述

把非结构化的会议转写文本转换为标准格式纪要，重点是行动项的可追踪性。

## 工作流

1. 判断输入类型：**已分段转写文本** → 走「直接整理」；**原始语音转写（无分段）** → 先走「预处理」
2. 预处理：运行 `scripts/split_speakers.py` 按说话人切分
3. 提取要素：参会人、议题、决议、行动项（负责人+截止日期）
4. 按模板生成纪要（见下）
5. 行动项汇总表放在纪要末尾

## 纪要模板（ALWAYS 使用此结构）

# [会议标题]
## 会议信息
[日期 / 时间 / 参会人 / 缺席人]
## 决议事项
- [决议内容]
## 行动项
| 事项 | 负责人 | 截止日期 |
|---|---|---|

## 输出格式细则

多语言会议（中英混杂）按主要语言输出纪要。行动项截止日期一律写成 YYYY-MM-DD。

## 资源说明

- **按说话人切分脚本**：`scripts/split_speakers.py`，用法见文件头注释；仅当输入无分段时运行
- **公司专有名词对照表**：内部项目代号/人名映射见 [references/glossary.md](references/glossary.md)，遇到未识别代号时用 grep 搜索该文件
````

配套目录：

```
meeting-minutes-organizer/
├── SKILL.md
├── scripts/
│   └── split_speakers.py
└── references/
    └── glossary.md
```

注意样例体现的要点：frontmatter 全部值加引号；description 里塞满触发词；正文用祈使句；资源引用说明了「何时读取」；没有多余文件。

---

## 8. DeepSeek 的输出格式协议

当用户请你制作一个 TeleAgent 技能时，按以下协议输出：

**第 1 步：确认需求**（若用户没说清楚）

- 技能要支持哪些具体功能？
- 举 2–3 个典型使用示例（用户会怎么说什么话来触发它）？
- 期望的技能中文名（`name_cn` 必须一字不差采用用户给的名称）？

**第 2 步：产出技能**

用如下格式输出所有文件——先给目录树，再逐个文件，每个文件用带路径标注的代码块：

````
技能目录结构：
<skill-name>/
├── SKILL.md
└── …

文件 1：SKILL.md
（在此代码块内给出完整 SKILL.md 内容）

文件 2：scripts/xxx.py
（在此代码块内给出完整脚本内容）
````

**第 3 步：自检**

输出后附上第 9 章的自检清单，逐项打勾确认。

**绝对禁止**：输出 README.md、安装说明、变更日志等任何额外文件；frontmatter 手写 AIGC 键；description 含尖括号。

---

## 9. 交付前自检清单（12 项）

产出技能前逐项核对：

- [ ] 目录名与 `name` 字段**完全一致**
- [ ] `name` 为小写字母+数字+连字符，≤40 字符，不以 `-` 开头/结尾，无 `--`
- [ ] `name`、`description`、`name_cn`、`description_cn` 四个必填字段齐全
- [ ] frontmatter 没有出现允许清单之外的键（只允许 name/description/name_cn/description_cn/license/allowed-tools/metadata）
- [ ] 没有手写 `AIGC` 键，没有任何键重复出现
- [ ] 所有含中文/冒号/特殊字符的值都用**成对双引号**包裹
- [ ] `description` ≤1024 字符，**不含尖括号**，同时包含「做什么」+「何时触发」
- [ ] `name_cn` 与用户指定名称一字不差
- [ ] 正文 <500 行，用祈使句，没有「何时使用」章节
- [ ] 正文里引用的每个 scripts/references/assets 文件都真实存在，且说明了使用时机
- [ ] 没有多余文件（README、安装指南等）
- [ ] 脚本经过实际运行测试（或明确标注「需测试」）

---

## 10. 导入 TeleAgent（用户侧操作，AI 助手只需了解）

DeepSeek 产出技能后，用户有三种导入方式：

1. **直接落盘**：把技能文件夹复制到本机技能目录
   - 目录位置由环境变量 `TELEAGENT_CONFIG_DIR` 决定：`$TELEAGENT_CONFIG_DIR/skills/<skill-name>/`
   - Windows 本机实际路径示例：`C:\Users\<用户名>\.config\TeleAgent\users\<用户ID>\skills\<skill-name>\`
2. **粘贴回 TeleAgent 代写**：把 DeepSeek 的输出整段粘贴给 TeleAgent，说「把这个技能写入 skills 目录」，由 TeleAgent 落盘并注册
3. **打包 .skill 分发**：把技能文件夹打包为 zip（顶层为技能文件夹本身），重命名为 `<skill-name>.skill`，可通过技能广场/桌面端导入

**生效条件**：新注册的技能**从下一条用户消息（新会话）开始生效**，当前会话中不可用。

**启用机制**：注册后技能默认自动启用；若本机「已启用技能数」达到上限，需先手动关闭部分技能再启用新的。

---

## 11. 底层处理管线（了解即可，AI 助手无需执行）

TeleAgent 官方 skill-creator 技能的完整制作管线共 11 步，供理解平台机制：

1. 解析技能存储目录（读环境变量 `TELEAGENT_CONFIG_DIR`，拼接 `/skills`）
2. 用具体示例理解技能用途（向用户收集用例和触发语）
3. 规划可复用内容（分析每个示例需要哪些 scripts/references/assets）
4. 运行 `init_skill.py` 生成模板目录（含 TODO 占位的 SKILL.md + 三个示例资源目录）
5. 编辑技能（实现资源 + 撰写 SKILL.md）
6. 运行 `quick_validate.py` 校验（本文档第 3.3/3.4 节规则即来自此校验器），**直接交付文件夹**，不打 .skill 包
7. 实际使用中迭代
8. 用 `teleai_claw_scan` 做安全扫描（最多 3 轮修复；连续 3 轮失败则整体回滚——新技能删目录，改技能还原文件）
9. 通过 `add_skill_remote.py` 向内核注册（POST 技能绝对路径到服务端）
10. 轮询 `list_installed_skills` 确认注册成功（按 `name` 精确匹配，最多 15 轮）
11. 启用技能并汇报（`desiredEnabled` 为 false 时调用启用接口）

**给 DeepSeek 的定位说明**：DeepSeek 负责第 2–5 步的内容生产（本文档的核心），第 1、6–11 步由用户本机的 TeleAgent 完成。只要产出严格符合本规范，后续管线即可无缝衔接。

---

## 附录 A：本地自校验脚本（可选，供用户在 Python 3 环境运行）

把以下脚本存为 `check_skill.py`，运行 `python check_skill.py <技能目录路径>` 即可复现平台核心校验：

```python
#!/usr/bin/env python3
"""TeleAgent 技能 frontmatter 自校验（与平台 quick_validate 核心规则一致）"""
import re, sys
from pathlib import Path
import yaml

ALLOWED = {"name", "description", "name_cn", "description_cn",
           "create_source", "AIGC", "license", "allowed-tools", "metadata"}

def validate(skill_path: str):
    p = Path(skill_path)
    md = p / "SKILL.md"
    if not md.exists():
        return False, "SKILL.md not found"
    content = md.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        return False, "No YAML frontmatter found"
    m = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not m:
        return False, "Invalid frontmatter format"
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {e}"
    if not isinstance(fm, dict):
        return False, "Frontmatter must be a YAML dict"
    bad = set(fm) - ALLOWED
    if bad:
        return False, f"Unexpected keys: {sorted(bad)}"
    for k in ("name", "description", "name_cn", "description_cn"):
        if k not in fm:
            return False, f"Missing '{k}'"
    name = str(fm["name"]).strip()
    if not re.match(r"^[a-z0-9-]+$", name):
        return False, f"Name '{name}' must be hyphen-case"
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return False, "Name cannot start/end with hyphen or contain '--'"
    if len(name) > 64:
        return False, f"Name too long ({len(name)} > 64)"
    if name != p.name:
        return False, f"Name '{name}' != directory '{p.name}'"
    desc = str(fm["description"]).strip()
    if len(desc) > 1024:
        return False, "Description too long (>1024)"
    if "<" in desc or ">" in desc:
        return False, "Description contains angle brackets"
    cs = fm.get("create_source")
    if cs is not None and cs != "super-agent-skill-creator":
        return False, "create_source must be 'super-agent-skill-creator'"
    return True, "Skill is valid!"

if __name__ == "__main__":
    ok, msg = validate(sys.argv[1])
    print(msg)
    sys.exit(0 if ok else 1)
```

依赖：`pip install pyyaml`。

---

*本文档由 TeleAgent skill-creator 技能规范提炼生成，覆盖格式约束、设计原则、设计模式、输出协议与导入流程五大部分。投喂给 DeepSeek 后，请配合第 8 章协议使用。*

> AI生成
