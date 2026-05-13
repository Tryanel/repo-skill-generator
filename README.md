# Repo Skill Generator

[English](README.md) | [简体中文](README.zh-CN.md)

Create portable, source-invisible capability skills from an existing project.

This skill fully scans a target project once, analyzes its framework and
functional modules, then asks the user which capabilities should become the new
skill's documented abilities and which should become same-language callable
functions under `scripts/`. The final generated skill is source-invisible: it
does not expose source project names, paths, file names, source maps, or
generation evidence.

## What It Generates

`repo-skill-generator` can draft skill formats for:

- Codex
- Claude Code
- OpenCode
- Agent Skills-compatible layouts

For out-of-the-box portability, final capability skills should include:

- `SKILL.md`: trigger and workflow instructions
- `references/capability-map.md`: focused capabilities, inputs, outputs,
  templates, integrations, contracts, and examples
- `references/capability-conventions.md`: source-neutral module explanations,
  usage notes, function style, tests, and pitfalls
- `references/implementation-blueprint.md`: how to recreate same-language functions
  from the approved capability contracts
- `references/task-playbook.md`: task routing and verification guidance
- Optional `references/callable-scripts.md` plus same-language files under
  `scripts/` when the user asks for specific capabilities to become reusable
  callable functions
- Optional draft-only `references/source-map.md` for audit or development use;
  capability skills should not ship it by default

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
  --repo /path/to/project \
  --skill-name capability-tools \
  --target all \
  --knowledge-depth self-contained \
  --skill-purpose capability \
  --output capability-skill-draft.md
```

Generate only one target:

```bash
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target codex --output draft.md
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target claude --output draft.md
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target opencode --output draft.md
```

`--knowledge-depth self-contained` is the default. Use
`--knowledge-depth portable` only when you want a lighter conventions-only
draft.

`--skill-purpose capability` is the default. It creates a skill for recreating
focused repository capabilities as standalone tools. Use
`--skill-purpose development` only when you explicitly want a skill for working
inside the original repository.

Full scan is the default. The scanner reads every known text-like file, also
sniffs unknown extensions that look like text, and ignores `--max-files` while
still respecting skip directories and `--exclude`. Use `--sample-scan
--max-files N` only when full scan is impractical.

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
  preserve it in the generation proposal.

### Callable Function Targets

When the generated skill should include importable functions, tell the scanner
which capabilities should become same-language files under `scripts/`:

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

`--script-focus PATH_OR_LABEL` records a repo-root-relative file, directory, or
operation label whose behavior should be exposed as a generated skill function.
Use `--script-note` for function names, utility names, or extra implementation
intent that does not map cleanly to a path. With `--script-output-dir`, the
scanner writes same-language function files directly into the generated skill's
`scripts/` directory. `references/callable-scripts.md` is only an index and
contract; the usable artifact should be the function file. Before sharing the
final skill, implement and test those functions; do not ship placeholder
functions or imports from the original repository unless the user explicitly
asked for wrappers.

## Workflow

1. Run the scanner against the target project. Full scan is the default.
2. Read the draft and inspect the generation-only evidence files it lists.
3. Analyze the project framework, functional modules, data flow, templates,
   integrations, inputs, outputs, errors, fixtures, and tests.
4. Present the source-neutral approval proposal from the draft to the user.
5. Ask the user what to include, omit, merge, rename, expand, and package as
   functions. Do not create the final skill until they approve.
6. Create the final skill folder for the target agent.
7. Fill and ship the bundled source-invisible references:
   - `capability-map.md`
   - `capability-conventions.md`
   - `implementation-blueprint.md`
   - `task-playbook.md`
   - `callable-scripts.md` and same-language `scripts/` when functions were requested
8. Do not include `source-map.md` in the final capability skill unless the user
   explicitly wants an auditable source map.
9. Validate the generated skill with your agent's validator when available, and
   run any bundled functions with at least one fixture or parity test.

Do not ship a generated skill that tells users to read or provide the source
project. The final skill must behave as if the distilled capabilities are its
own native abilities.

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
- Final generated references must not contain source project paths or file names.
- The generated source map is draft-only evidence. For high-value reusable
  capability skills, internalize behavior into capability docs and functions
  instead of shipping source maps to end users.
- Generated functions should be completed implementations, not scanner placeholders.
