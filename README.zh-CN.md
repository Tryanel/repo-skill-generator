# Repo Skill Generator

[English](README.md) | [简体中文](README.zh-CN.md)

从现有项目生成可移植的、源不可见的能力型 agent skill。

这个 skill 会把目标项目作为一次性训练材料进行全量扫描，分析它的框架和
功能模块，然后和用户协商：哪些能力要写进新 skill、哪些要封装成
`scripts/` 下的同语言可调用函数。最终生成的 skill 是源不可见的：不暴露源
项目名称、路径、文件名、source map 或生成证据。

## 能生成什么

`repo-skill-generator` 可以为这些目标格式生成草稿：

- Codex
- Claude Code
- OpenCode
- Agent Skills 兼容布局

为了开箱即用，最终能力型 skill 应该包含：

- `SKILL.md`：触发条件和工作流程
- `references/capability-map.md`：核心能力、输入输出、模板、集成、契约和示例
- `references/capability-conventions.md`：源不可见的模块说明、用法细节、
  函数风格、测试和坑点
- `references/implementation-blueprint.md`：如何根据已批准的能力契约复刻同语言函数
- `references/task-playbook.md`：任务路由和验证建议
- 可选 `references/callable-scripts.md` 和 `scripts/` 下的同语言函数文件：
  当用户指定某些能力要变成可复用函数时一起分发
- 可选、仅用于审计或开发场景的 `references/source-map.md`；能力型 skill
  默认不应该分发它

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
  --repo /path/to/project \
  --skill-name capability-tools \
  --target all \
  --knowledge-depth self-contained \
  --skill-purpose capability \
  --output capability-skill-draft.md
```

只生成某一种目标格式：

```bash
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target codex --output draft.md
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target claude --output draft.md
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target opencode --output draft.md
```

`--knowledge-depth self-contained` 是默认值。如果只想要更轻量的
conventions-only 草稿，可以使用 `--knowledge-depth portable`。

`--skill-purpose capability` 是默认值，用于生成“复刻仓库能力”的 skill。
只有当你明确想在原仓库里继续开发、修改、测试时，才使用
`--skill-purpose development`。

默认就是全量扫描：扫描所有已知文本类文件，也会嗅探未知扩展名但看起来是
文本的文件，并忽略 `--max-files`；同时仍然遵守跳过目录规则和 `--exclude`。
只有当项目太大时，才使用 `--sample-scan --max-files N`。

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
- `--scope-note TEXT`：记录用户对扫描重点的说明，并保存在生成阶段的提案里。

### 可调用函数目标

当生成的 skill 需要自带可 import 的函数时，可以明确告诉扫描器哪些能力要
写成 `scripts/` 下的同语言函数文件：

```bash
python scripts/draft_repo_skill.py \
  --repo /path/to/mining-framework \
  --skill-name mining-framework-functions \
  --target opencode \
  --full-scan \
  --focus dag \
  --focus plugin/templates \
  --script-focus dag \
  --script-focus plugin/templates \
  --script-output-dir .opencode/skills/mining-framework-functions/scripts \
  --script-language auto \
  --script-api function \
  --script-note "turn the DAG runner and database template renderer into portable functions" \
  --output mining-framework-skill-draft.md
```

`--script-focus PATH_OR_LABEL` 用来记录某个相对仓库根目录的文件、目录，
或者一个能力标签，其行为应该被暴露为最终 skill 的函数。对于函数名、
通用工具名、无法直接映射到路径的实现意图，可以写进 `--script-note`。
传入 `--script-output-dir` 时，扫描器会直接在生成 skill 的 `scripts/` 目录
写出同语言函数文件。`references/callable-scripts.md` 只是索引和契约；
真正可用的产物应该是函数文件。最终分享 skill 之前，需要完成函数实现和
测试。不要发布仍是占位模板的函数，也不要让函数依赖原始仓库，除非用户
明确要求生成 wrapper。

## 工作流程

1. 对目标项目运行扫描器。默认全量扫描。
2. 阅读生成的草稿，并检查草稿列出的“生成期证据”。
3. 分析项目框架、功能模块、数据流、模板、集成、输入输出、错误处理、
   fixtures 和测试。
4. 把草稿里的源不可见提案展示给用户。
5. 让用户决定哪些能力写入、哪些省略、哪些合并或重命名、哪些封装成函数。
   用户确认前不要生成最终 skill。
6. 为目标 agent 创建最终 skill 文件夹。
7. 填充并一起分发这些源不可见 bundled references：
   - `capability-map.md`
   - `capability-conventions.md`
   - `implementation-blueprint.md`
   - `task-playbook.md`
   - 如果请求了函数，还要包含 `callable-scripts.md` 和同语言 `scripts/`
8. 除非用户明确要求可审计的源码地图，否则能力型 skill 最终不要包含
   `source-map.md`。
9. 如果目标 agent 有 validator，运行对应校验；如果包含函数，还要运行至少
   一个 fixture 或 parity test。

不要发布一个只写着“去读这个仓库”的 skill，也不要把源项目路径、文件名、
source map 或证据列表交给最终用户。最终 skill 应该像这些能力本来就是它
自己的能力一样工作。

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
- 最终生成的 reference 里不应该出现源项目路径或文件名。
- 生成的 source map 只是草稿证据。对于高价值、可复用的能力型 skill，应把
  行为内化进能力文档和函数文件，而不是把 source map 交给最终用户。
- 生成的函数必须是完成实现并验证过的函数，不能只是扫描器模板。
