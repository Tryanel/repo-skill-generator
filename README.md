# Repo Skill Generator

Create portable, repo-specific agent skills from an existing code repository.

This skill reads a target repository once, extracts its architecture,
commands, tooling, code style, tests, source map, and task playbook, then
packages that knowledge into a self-contained skill. The generated skill can be
shared with other people without depending on the original local checkout used
during generation.

## What It Generates

`repo-skill-generator` can draft skill formats for:

- Codex
- Claude Code
- OpenCode
- Agent Skills-compatible layouts

For out-of-the-box portability, generated skills should include:

- `SKILL.md`: trigger and workflow instructions
- `references/repo-conventions.md`: architecture, commands, tooling, style,
  tests, docs, and pitfalls
- `references/source-map.md`: important modules, public APIs, and test surface
- `references/task-playbook.md`: task routing and verification guidance

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

## Workflow

1. Run the scanner against the target repository.
2. Read the draft and inspect the evidence files it lists.
3. Create the final skill folder for your target agent.
4. Fill and ship the bundled references:
   - `repo-conventions.md`
   - `source-map.md`
   - `task-playbook.md`
5. Validate the generated skill with your agent's validator when available.

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
