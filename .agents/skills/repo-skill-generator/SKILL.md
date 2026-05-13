---
name: repo-skill-generator
description: Fully scan a project as one-time training material, negotiate the desired capability set with the user, and create source-invisible Codex, Claude, OpenCode, or Agent Skills-compatible capability skills with optional same-language functions.
---

# Repo Skill Generator

## Instructions

1. Confirm the target project path, target platform, output skill name, known important areas, and whether any capabilities should become same-language functions.
2. Run the canonical scanner from this project. Full scan is the default; use `--sample-scan --max-files N` only when full scan is impractical.

```bash
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target all --knowledge-depth self-contained --skill-purpose capability --output capability-skill-draft.md
```

Use `--target codex`, `--target claude`, `--target opencode`, or `--target all`.
Use `--focus`, `--include`, `--exclude`, and `--scope-note` when the user identifies important areas.
Use `--script-focus PATH_OR_LABEL`, `--script-output-dir <skill>/scripts`, `--script-language auto`, and `--script-note TEXT` when the user wants functions.

3. Read the draft and inspect the full-scan evidence. Analyze framework, runtime, functional modules, data flow, templates, integrations, inputs, outputs, errors, fixtures, and tests.
4. Present a source-neutral proposal before creating the final skill:
   - capability modules to include
   - module details for `references/capability-conventions.md`
   - functions to implement under `scripts/`
   - items to omit, merge, rename, or expand
   - whether to include an auditable source map; default is no
5. Continue only after the user approves or edits the proposal.
6. Build the final skill as source-invisible:
   - no source project names, paths, file names, source maps, source-to-test maps, or evidence lists
   - no "learned from", "original repository", or "source project" phrasing
   - capabilities are written as this new skill's native abilities
7. Ship `SKILL.md`, `references/capability-map.md`, `references/capability-conventions.md`, `references/implementation-blueprint.md`, `references/task-playbook.md`, optional `references/callable-scripts.md`, and implemented same-language `scripts/` files.

## Rules

- Do not invent capability behavior.
- Do not stop at the scanner draft when the user asks for a final skill.
- Do not silently choose final scope; negotiate with the user first.
- Do not ship placeholder functions.
- Add target-specific frontmatter only when the target platform recognizes it.
