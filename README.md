# Repo Skill Generator

[English](README.md) | [简体中文](README.zh-CN.md)

Create portable, repo-specific agent skills from an existing code repository.

This skill reads a target repository once, extracts focused capabilities,
commands, tooling, source maps, implementation blueprints, tests, and optional
script targets, then packages that knowledge into a self-contained skill. The
generated skill can be shared with other people and can guide agents to recreate
equivalent standalone scripts without depending on the original local checkout
used during generation.

## What It Generates

`repo-skill-generator` can draft skill formats for:

- Codex
- Claude Code
- OpenCode
- Agent Skills-compatible layouts

For out-of-the-box portability, generated skills should include:

- `SKILL.md`: trigger and workflow instructions
- `references/capability-map.md`: focused capabilities, inputs, outputs,
  templates, integrations, and evidence files
- `references/repo-conventions.md`: architecture, commands, tooling, style,
  tests, docs, and pitfalls
- `references/source-map.md`: important modules, public APIs, and test surface
- `references/implementation-blueprint.md`: how to recreate standalone scripts
  from observed repository behavior
- `references/task-playbook.md`: task routing and verification guidance
- Optional `references/callable-scripts.md` and `scripts/` when the user asks
  for specific capabilities to become reusable helper scripts

## Install

Use the layout that matches your agent.

### Codex

Copy this repository as a skill folder:

```text
~/.codex/skills/repo-skill-generator/
```

or place the root files in any Codex skills directory:

```text
repo-skill-generator/
  SKILL.md
  agents/openai.yaml
  scripts/draft_repo_skill.py
```

### Claude Code

Use the bundled Claude-compatible project skill:

```text
.claude/skills/repo-skill-generator/SKILL.md
```

For personal installation, copy it to:

```text
~/.claude/skills/repo-skill-generator/SKILL.md
```

### OpenCode

Use the bundled OpenCode-compatible project skill:

```text
.opencode/skills/repo-skill-generator/SKILL.md
```

For global installation, copy it to:

```text
~/.config/opencode/skills/repo-skill-generator/SKILL.md
```

OpenCode can also discover compatible `.claude/skills/` and `.agents/skills/`
layouts.

### Agent Skills

Use:

```text
.agents/skills/repo-skill-generator/SKILL.md
```

or copy it to:

```text
~/.agents/skills/repo-skill-generator/SKILL.md
```

## CLI Usage

Generate a self-contained draft for all supported targets:

```bash
python scripts/draft_repo_skill.py \
  --repo /path/to/repo \
  --skill-name repo-name-dev \
  --target all \
  --knowledge-depth self-contained \
  --skill-purpose capability \
  --output repo-skill-draft.md
```

Generate only one target:

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target codex --output draft.md
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target claude --output draft.md
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target opencode --output draft.md
```

`--knowledge-depth self-contained` is the default. Use
`--knowledge-depth portable` only when you want a lighter conventions-only
draft.

`--skill-purpose capability` is the default. It creates a skill for recreating
focused repository capabilities as standalone tools. Use
`--skill-purpose development` only when you explicitly want a skill for working
inside the original repository.

### Custom Scan Scope

Some repositories hide the important logic outside common directories like
`src/` or `app/`. For example, a data-mining framework might keep its core
workflows in `dag/` and database templates under `plugin/templates/`.

Use scope flags to tell the scanner what matters:

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

Available scope flags:

- `--focus PATH`: Treat this repo-root-relative file or directory as core.
  Repeat it for multiple paths.
- `--include PATH`: Include a path even if it would normally be skipped.
- `--exclude PATH`: Skip a path for this scan.
- `--scope-note TEXT`: Record the user's explanation of what matters, and
  preserve it in the generated references.

### Callable Script Targets

When the generated skill should include helper scripts, tell the scanner which
capabilities should become scripts:

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

`--script-focus PATH_OR_LABEL` records a repo-root-relative file, directory, or
operation label whose behavior should be exposed as a generated skill script.
Use `--script-note` for function names, utility names, or extra implementation
intent that does not map cleanly to a path. The scanner drafts script contracts
and starter shapes in `references/callable-scripts.md`. Before sharing the
final skill, implement and test the actual files under `scripts/`; do not ship
placeholder scripts or imports from the original repository unless the user
explicitly asked for wrappers.

## Workflow

1. Run the scanner against the target repository.
2. Read the draft and inspect the evidence files it lists.
3. Create the final skill folder for your target agent.
4. Fill and ship the bundled references:
   - `capability-map.md`
   - `repo-conventions.md`
   - `source-map.md`
   - `implementation-blueprint.md`
   - `task-playbook.md`
   - `callable-scripts.md` and `scripts/` when scripts were requested
5. Validate the generated skill with your agent's validator when available, and
   run any bundled scripts with `--help` plus at least one fixture or parity
   test.

Do not ship a generated skill that only says "read the repository." The point
is to package enough knowledge that another person can use the skill without
access to the original local generation checkout.

## Repository Contents

```text
SKILL.md
agents/openai.yaml
scripts/draft_repo_skill.py
.agents/skills/repo-skill-generator/SKILL.md
.claude/skills/repo-skill-generator/SKILL.md
.opencode/skills/repo-skill-generator/SKILL.md
```

## Notes

- The scanner uses only Python standard library modules.
- Paths in generated references should be repo-root-relative.
- The generated source map is a starting point. For high-value reusable skills,
  refine it by hand before sharing.
- Generated scripts should be completed implementation, not scanner placeholders.
