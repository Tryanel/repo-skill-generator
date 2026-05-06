# Repo Skill Generator

[English](README.md) | [简体中文](README.zh-CN.md)

从现有代码仓库生成可移植的、仓库专属的 agent skill。

这个 skill 会读取目标仓库一次，提取它的架构、命令、工具链、代码风格、
测试体系、源码地图和任务 playbook，然后把这些知识打包进一个
self-contained skill。生成后的 skill 可以分享给其他人使用，不依赖生成时
那台机器上的本地仓库路径。

## 能生成什么

`repo-skill-generator` 可以为这些目标格式生成草稿：

- Codex
- Claude Code
- OpenCode
- Agent Skills 兼容布局

为了开箱即用，最终生成的 skill 应该包含：

- `SKILL.md`：触发条件和工作流程
- `references/repo-conventions.md`：架构、命令、工具链、风格、测试、
  文档和坑点
- `references/source-map.md`：重要模块、公共 API 和测试覆盖面
- `references/task-playbook.md`：任务路由和验证建议

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

## 工作流程

1. 对目标仓库运行扫描器。
2. 阅读生成的草稿，并检查草稿列出的证据文件。
3. 为目标 agent 创建最终 skill 文件夹。
4. 填充并一起分发这些 bundled references：
   - `repo-conventions.md`
   - `source-map.md`
   - `task-playbook.md`
5. 如果目标 agent 有 validator，运行对应校验。

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
