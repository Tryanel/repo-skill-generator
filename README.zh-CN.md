# Repo Skill Generator

[English](README.md) | [简体中文](README.zh-CN.md)

从现有代码仓库生成可移植的、仓库专属的 agent skill。

这个 skill 会读取目标仓库一次，提取它的核心能力、命令、工具链、源码地图、
实现蓝图、测试体系，以及可选的脚本化目标，然后把这些知识打包进一个
self-contained skill。生成后的 skill 可以分享给其他人使用，并能指导 agent
在不依赖原始本地 checkout 的情况下，写出功能等价的独立脚本。

## 能生成什么

`repo-skill-generator` 可以为这些目标格式生成草稿：

- Codex
- Claude Code
- OpenCode
- Agent Skills 兼容布局

为了开箱即用，最终生成的 skill 应该包含：

- `SKILL.md`：触发条件和工作流程
- `references/capability-map.md`：核心能力、输入输出、模板、集成和证据文件
- `references/repo-conventions.md`：架构、命令、工具链、风格、测试、
  文档和坑点
- `references/source-map.md`：重要模块、公共 API 和测试覆盖面
- `references/implementation-blueprint.md`：如何根据仓库行为复刻独立脚本
- `references/task-playbook.md`：任务路由和验证建议
- 可选 `references/callable-scripts.md` 和 `scripts/`：当用户指定某些能力要
  变成可复用脚本时一起分发

## 安装

根据你使用的 agent 选择对应布局。

### Codex

把这个仓库作为一个 skill 文件夹复制到：

```text
~/.codex/skills/repo-skill-generator/
```

或者把根目录文件放到任意 Codex skills 目录：

```text
repo-skill-generator/
  SKILL.md
  agents/openai.yaml
  scripts/draft_repo_skill.py
```

### Claude Code

使用仓库内置的 Claude 兼容项目 skill：

```text
.claude/skills/repo-skill-generator/SKILL.md
```

如果要作为个人 skill 安装，复制到：

```text
~/.claude/skills/repo-skill-generator/SKILL.md
```

### OpenCode

使用仓库内置的 OpenCode 兼容项目 skill：

```text
.opencode/skills/repo-skill-generator/SKILL.md
```

如果要全局安装，复制到：

```text
~/.config/opencode/skills/repo-skill-generator/SKILL.md
```

OpenCode 也可以发现兼容的 `.claude/skills/` 和 `.agents/skills/` 布局。

### Agent Skills

使用：

```text
.agents/skills/repo-skill-generator/SKILL.md
```

或者复制到：

```text
~/.agents/skills/repo-skill-generator/SKILL.md
```

## CLI 用法

为所有支持的目标生成 self-contained 草稿：

```bash
python scripts/draft_repo_skill.py \
  --repo /path/to/repo \
  --skill-name repo-name-dev \
  --target all \
  --knowledge-depth self-contained \
  --skill-purpose capability \
  --output repo-skill-draft.md
```

只生成某一种目标格式：

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target codex --output draft.md
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target claude --output draft.md
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target opencode --output draft.md
```

`--knowledge-depth self-contained` 是默认值。如果只想要更轻量的
conventions-only 草稿，可以使用 `--knowledge-depth portable`。

`--skill-purpose capability` 是默认值，用于生成“复刻仓库能力”的 skill。
只有当你明确想在原仓库里继续开发、修改、测试时，才使用
`--skill-purpose development`。

### 自定义扫描范围

有些仓库的核心逻辑不在常见的 `src/` 或 `app/` 目录里。比如一个数据挖掘
框架，最核心的流程可能在 `dag/`，数据库模板可能在 `plugin/templates/`。

这时可以用 scope 参数告诉扫描器哪些目录最重要：

```bash
python scripts/draft_repo_skill.py \
  --repo /path/to/mining-framework \
  --skill-name mining-framework-dev \
  --target all \
  --focus dag \
  --focus plugin/templates \
  --scope-note "dag contains the core mining scripts; plugin/templates contains database templates" \
  --output mining-framework-skill-draft.md
```

可用参数：

- `--focus PATH`：把某个相对仓库根目录的文件或目录视为核心区域。可以重复
  传多个。
- `--include PATH`：即使某个路径通常会被跳过，也强制纳入扫描。
- `--exclude PATH`：本次扫描跳过某个路径。
- `--scope-note TEXT`：记录用户对扫描重点的说明，并保存在生成的 references
  里。

### 可调用脚本目标

当生成的 skill 需要自带 helper scripts 时，可以明确告诉扫描器哪些能力要
写成脚本：

```bash
python scripts/draft_repo_skill.py \
  --repo /path/to/mining-framework \
  --skill-name mining-framework-tools \
  --target all \
  --focus dag \
  --focus plugin/templates \
  --script-focus dag \
  --script-focus plugin/templates \
  --script-note "turn the DAG runner and database template renderer into portable scripts" \
  --output mining-framework-skill-draft.md
```

`--script-focus PATH_OR_LABEL` 用来记录某个相对仓库根目录的文件、目录，
或者一个能力标签，其行为应该被暴露为最终 skill 的脚本。对于函数名、
通用工具名、无法直接映射到路径的实现意图，可以写进 `--script-note`。
扫描器会在 `references/callable-scripts.md` 中生成脚本契约和 starter 形状；
最终分享 skill 之前，需要把实际脚本放进 `scripts/` 并完成实现和测试。
不要发布仍是占位模板的脚本，也不要让脚本依赖原始仓库，除非用户明确要求
生成 wrapper。

## 工作流程

1. 对目标仓库运行扫描器。
2. 阅读生成的草稿，并检查草稿列出的证据文件。
3. 为目标 agent 创建最终 skill 文件夹。
4. 填充并一起分发这些 bundled references：
   - `capability-map.md`
   - `repo-conventions.md`
   - `source-map.md`
   - `implementation-blueprint.md`
   - `task-playbook.md`
   - 如果请求了脚本，还要包含 `callable-scripts.md` 和 `scripts/`
5. 如果目标 agent 有 validator，运行对应校验；如果包含脚本，还要运行
   `--help` 和至少一个 fixture 或 parity test。

不要发布一个只写着“去读这个仓库”的 skill。这个项目的目标是打包足够多
的仓库知识，让别人拿到 skill 后不需要访问你生成 skill 时的本地 checkout。

## 仓库内容

```text
SKILL.md
agents/openai.yaml
scripts/draft_repo_skill.py
.agents/skills/repo-skill-generator/SKILL.md
.claude/skills/repo-skill-generator/SKILL.md
.opencode/skills/repo-skill-generator/SKILL.md
```

## 说明

- 扫描器只使用 Python 标准库。
- 生成的 reference 里应该使用相对仓库根目录的路径。
- 生成的 source map 是一个起点。对于高价值、可复用的 skill，建议在分享
  前手动打磨。
- 生成的脚本必须是完成实现并验证过的脚本，不能只是扫描器模板。
