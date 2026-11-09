# dsh-teleagent-skill-builder

把 [TeleAgent](https://www.teleagent.tech) 技能制作规范做成一个 **DSH 插件**：装一次，之后每个会话都自带 `teleagent-skill-builder` 技能——规范全文、校验器、脚手架、打包器、安装器全在里面，产出的技能第一次导入就能过平台审核（包括那条最容易踩的 `.pyc` 禁令）。

> DeepSeek Harness plugin that ships the TeleAgent skill-authoring standard as a ready-to-use DSH skill. Zero dependencies, no network calls, writes only one directory.

## 它做什么

DSH 启动时，把 `assets/skills/teleagent-skill-builder/` 复制到 `~/.dsh/skills/teleagent-skill-builder/`。复制时过滤 `.pyc` / `.pyo` / `__pycache__`，装完再删一次。

技能里带四件工具：

| 脚本 | 作用 |
|---|---|
| `scripts/scaffold_skill.py` | 按平台硬约束生成目录与 frontmatter 骨架 |
| `scripts/validate_skill.py` | 复刻平台 `quick_validate` 并加工程检查；**字节码直接判失败** |
| `scripts/pack_skill.py` | 打包 `.skill`（zip 顶层唯一技能目录，自动排除字节码） |
| `scripts/install_skill.py` | 校验通过后装进本机 TeleAgent 技能目录 |

`references/teleagent-spec.md` 是规范全文副本，按章节导航。

## 安装

```bash
# A. 从 GitHub 装（不需要 npm 账号）
dsh plugin add github:caigou114/dsh-teleagent-skill-builder

# B. 从 GitHub Release 的预构建包装（免源码安装）
dsh plugin add "https://github.com/caigou114/dsh-teleagent-skill-builder/releases/download/v0.1.0/dsh-teleagent-skill-builder-0.1.0.tgz"

# C. 从本地目录或 tgz 装
dsh plugin add "file:D:/path/to/dsh-teleagent-skill-builder"
dsh plugin add "D:/path/to/dsh-teleagent-skill-builder-0.1.0.tgz"

# D. npm 发布之后
dsh plugin add dsh-teleagent-skill-builder
```

也可以在插件市场里搜 `teleagent`：条目在「技能 / skill」分类下，卡片名 `caigou114/dsh-teleagent-skill-builder`。

装完重启 DSH，插件页「已安装」里会出现，`~/.dsh/skills/teleagent-skill-builder/` 里就是最新标准。

## 为什么必须禁止 .pyc

TeleAgent 审核对包内扩展名做白名单，命中 `.pyc` 会整包拒收，报「存在恶意扩展名文件」。本项目三重拦截：

1. 插件复制时过滤字节码，复制后再删一次；
2. `validate_skill.py` 把 `.pyc` / `__pycache__` 判为 **FAIL** 而不是警告；
3. `npm run check`（也就是 `prepack`）扫描全仓库，发现字节码直接失败；CI 每次 push 也跑一遍。

## 仓库结构

```
lib/index.js                                  # Cordis 入口：apply(ctx, config)
cordis.patch.yml                              # bundle patch：把插件挂进 profile
assets/skills/teleagent-skill-builder/        # 随插件分发的技能标准
  ├── SKILL.md
  ├── references/teleagent-spec.md
  └── scripts/{scaffold,validate,pack,install}_skill.py
tools/check-no-pyc.mjs                        # 字节码自检
.github/workflows/check.yml                   # push 时自动自检
.github/workflows/publish.yml                 # 打 v* 标签时发 npm（可选）
```

## 配置（可选）

`~/.dsh/profiles/<profile>/cordis.patch.yml`：

```yaml
- id: teleagent-skill-builder
  config:
    skillsDir: "D:/my-skills"   # 换落盘目录，默认 ~/.dsh/skills
    install: false              # 只挂插件、不复制文件
```

## 开发与升级

```bash
node tools/check-no-pyc.mjs      # 自检
npm pack                         # 出 tgz（prepack 会再自检一次）
```

升级标准内容时，记得把 `lib/index.js` 顶部的 `STANDARD_VERSION` 加一，否则已安装的用户不会重新复制。

## License

MIT
