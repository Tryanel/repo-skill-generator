---
name: repo-skill-generator
description: Inspect a code repository and create repo-specific Codex, Claude, or OpenCode skills that distill its capabilities into portable knowledge packs. Use when an agent needs to learn what focused directories or functions do, capture workflows, templates, data transformations, integrations, inputs, outputs, and tests, then generate a platform-specific skill that can recreate equivalent same-language callable functions without depending on the original repository checkout.
---

# Repo Skill Generator

## Overview

Create compact, portable, repo-specific skills from observed repository facts. Read the codebase once during generation, package its capabilities and code knowledge into the generated skill, then choose the correct target format for Codex, Claude, OpenCode, or all three. The default output is a capability skill for recreating equivalent same-language callable functions or tools, not a style guide for editing the original repository.

## Workflow

1. Confirm the target repository path, target platform, and intended output skill name. Normalize the skill name to lowercase hyphen-case.
   Ask for or capture the user's scan scope when some directories are more important than the default framework layout, such as `dag/`, `plugin/`, `templates/`, or domain-specific workflow folders.
   Also capture any operations the user wants turned into same-language callable functions under the generated skill's `scripts/` directory.
2. Run `scripts/draft_repo_skill.py` to create a first-pass evidence draft:

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target codex --knowledge-depth self-contained --skill-purpose capability --output repo-skill-draft.md
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target claude --knowledge-depth self-contained --skill-purpose capability --output repo-skill-draft.md
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target opencode --knowledge-depth self-contained --skill-purpose capability --output repo-skill-draft.md
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target all --knowledge-depth self-contained --skill-purpose capability --output repo-skill-draft.md
```

Use `--full-scan` when important capabilities may live outside common source
directories and the project is small enough to scan every known text-like file
plus unknown-extension files that look like text:

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-tools --target all --full-scan --skill-purpose capability --output repo-skill-draft.md
```

Use scope flags when the user identifies core directories:

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name mining-dev --target all --focus dag --focus plugin/templates --scope-note "dag contains the core mining scripts; plugin/templates contains database templates" --output repo-skill-draft.md
```

Use script flags when the user wants specific repository capabilities turned
into same-language callable functions bundled with the generated skill:

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name mining-tools --target opencode --focus dag --focus plugin/templates --script-focus dag --script-focus plugin/templates --script-language auto --script-api function --script-output-dir .opencode/skills/mining-tools/scripts --script-note "turn the DAG runner and database template renderer into portable functions" --output repo-skill-draft.md
```

3. Read the draft, then inspect the most relevant files it lists. Always include README or docs, dependency manifests, build/test configs, representative source files, representative tests, and contribution or developer notes when present.
4. Extract capabilities supported by repository evidence:
   - what each focused directory, DAG, plugin, template, script, or connector does
   - input contracts, output contracts, side effects, external services, and runtime assumptions
   - algorithmic steps, scheduling semantics, SQL/database templates, transforms, validations, and error handling
   - reusable examples, fixtures, tests, and parity checks
   - dependencies that are essential versus incidental framework glue
5. Also extract conventions when they matter for accurate recreation:
   - architecture and major subsystems
   - setup, build, test, lint, format, and run commands
   - naming, style, and module organization patterns
   - testing strategy, fixtures, mocks, and acceptance expectations
   - dependency, migration, generated-code, and asset rules
   - common pitfalls, unsafe operations, or files agents should avoid touching casually
   - user-provided focus paths and why they matter
6. Fill the generated bundled references with self-contained repository facts:
   - `references/capability-map.md`: focused capabilities, inputs, outputs, data flows, templates, integrations, and evidence files.
   - `references/repo-conventions.md`: architecture, commands, tooling, style, tests, docs, and pitfalls.
   - `references/implementation-blueprint.md`: how to recreate equivalent same-language functions without importing the original repository.
   - `references/callable-scripts.md`: index of actual same-language function files under `scripts/`.
   - `references/task-playbook.md`: task categories, source-to-test routing, and verification commands.
   Do not ship `references/source-map.md` by default for capability skills. It may appear in the draft as generation-only evidence, but final users should not need to understand the original repository layout.
   Do not leave instructions such as "read the local repo" or absolute paths to the generation checkout as the source of knowledge.
7. Create the generated skill in the user's requested platform location:
   - Codex: `<skills-dir>/<name>/SKILL.md`, usually `$CODEX_HOME/skills`, `~/.codex/skills`, or this repository's `skills/`.
   - Claude Code: project `.claude/skills/<name>/SKILL.md` or personal `~/.claude/skills/<name>/SKILL.md`.
   - OpenCode: project `.opencode/skills/<name>/SKILL.md` or global `~/.config/opencode/skills/<name>/SKILL.md`.
8. Write the generated skill with progressive disclosure:
   - Put trigger context and core workflow in `SKILL.md`.
   - Put longer repository conventions in `references/repo-conventions.md` when the target supports supporting files.
   - Add same-language function files only for stable, repeatable, user-requested repository capabilities. Generated functions must be implemented and tested before the skill is shared.
   - Add assets only when future agents must copy or reuse concrete files.
9. Validate the generated skill with the target platform's validation rules when available, and test any bundled functions.

## Portability Requirements

- The generated skill must be useful after copying it to another machine or teammate.
- Bundle enough capability, implementation knowledge, examples, and same-language functions that future agents can use the skill without the original local checkout used during generation.
- Future agents should use the bundled capability map, implementation blueprint, function files, and tests first. They may open a checkout only to verify drift or inspect details missing from the bundled knowledge pack.
- If the user asks for callable functions, bundle completed same-language files under `scripts/` and document their contracts in `references/callable-scripts.md`. Do not ship placeholder functions or functions that import the original repository unless the user explicitly asked for wrappers.
- Omit absolute generation paths from bundled references. Use repo-root-relative paths.
- If the generated skill's references still contain placeholders, treat it as incomplete and finish the references before sharing.
- When the user asks to create a skill, do not stop at the scanner draft. Create the final skill folder and complete the bundled reference.

## Target Formats

- **Codex**: Use `name` and `description` frontmatter, optional `agents/openai.yaml`, and optional `scripts/`, `references/`, or `assets/`.
- **Claude Code**: Use `SKILL.md` under `.claude/skills/<name>/` or `~/.claude/skills/<name>/`. Keep `description` specific; optional Claude fields such as `allowed-tools`, `disable-model-invocation`, `argument-hint`, or `paths` should be added only when the repo skill truly needs them.
- **OpenCode**: Use `SKILL.md` under `.opencode/skills/<name>/` or `~/.config/opencode/skills/<name>/`. Only rely on recognized frontmatter fields: `name`, `description`, optional `license`, `compatibility`, and string-to-string `metadata`.

## Output Rules

- Do not invent repository rules. Mark uncertain patterns as "Observed pattern" or "Needs confirmation".
- Prefer concise, actionable instructions over a long repository tour.
- Include exact commands only when they appear in repository files or are directly implied by standard manifests.
- Preserve repository-specific names, paths, commands, and framework terms exactly.
- Package repository-specific conventions into the generated skill, not into a separate local note.
- For "out of the box" portability, ship `capability-map.md`, `repo-conventions.md`, `implementation-blueprint.md`, `task-playbook.md`, and any requested same-language `scripts/` together. Do not ship `source-map.md` for capability skills unless the user explicitly asks for an auditable source map.
- If the user says certain directories are core, pass them through `--focus` and preserve the rationale in bundled references.
- If the user names paths, functions, or operations that should become tools, pass them through `--script-focus` or record them in `--script-note`, then implement final same-language functions from the evidence before distribution.
- Use `--full-scan` when the project may hide core capabilities in uncommon directories and scanning every text-like file is acceptable.
- Do not frame the generated skill only as "modify this repo"; frame it as "recreate this capability independently" unless `--skill-purpose development` is explicitly requested.
- Keep generated `SKILL.md` under 500 lines; move detailed notes into references.
- Do not overwrite an existing skill or draft unless the user explicitly asks for overwrite behavior.

## Resource Map

- `scripts/draft_repo_skill.py`: Scans a repository for text-like docs, manifests, source files, tests, config clues, user-focused capability directories, and optional function targets, then writes a Markdown draft for Codex, Claude, OpenCode, or all target skill formats. With `--script-output-dir`, it also creates same-language function files under the generated skill's `scripts/` directory.
