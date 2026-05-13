---
name: repo-skill-generator
description: Inspect a code repository as one-time training material and create source-invisible Codex, Claude, or OpenCode capability skills. Use when an agent needs to fully scan a project, identify its framework and functional modules, negotiate which capabilities and functions the user wants, then generate a new skill that treats the distilled capabilities as its own native behavior without exposing source project names, paths, source maps, or generation evidence.
---

# Repo Skill Generator

## Overview

Create compact, portable, source-invisible capability skills from a project used
as one-time training material. Fully scan the project during generation, analyze
its framework and functional modules, negotiate the target capability set with
the user, then build a new skill that presents the distilled capabilities as its
own native abilities.

## Workflow

1. Confirm the target project path, target platform, intended output skill name,
   and whether the user already knows any critical directories or operations.
   Normalize the skill name to lowercase hyphen-case.
2. Run `scripts/draft_repo_skill.py` to create a first-pass evidence draft:

```bash
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target codex --knowledge-depth self-contained --skill-purpose capability --output capability-skill-draft.md
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target claude --knowledge-depth self-contained --skill-purpose capability --output capability-skill-draft.md
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target opencode --knowledge-depth self-contained --skill-purpose capability --output capability-skill-draft.md
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name capability-tools --target all --knowledge-depth self-contained --skill-purpose capability --output capability-skill-draft.md
```

The scanner uses full scan by default: every known text-like file plus
unknown-extension files that look like text are scanned unless excluded. Use
`--sample-scan --max-files N` only when the project is too large.

Use scope flags when the user identifies core directories:

```bash
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name mining-tools --target all --focus dag --focus plugin/templates --scope-note "dag contains the core mining scripts; plugin/templates contains database templates" --output capability-skill-draft.md
```

Use script flags when the user wants specific repository capabilities turned
into same-language callable functions bundled with the generated skill:

```bash
python scripts/draft_repo_skill.py --repo /path/to/project --skill-name mining-tools --target opencode --focus dag --focus plugin/templates --script-focus dag --script-focus plugin/templates --script-language auto --script-api function --script-output-dir .opencode/skills/mining-tools/scripts --script-note "turn the DAG runner and database template renderer into portable functions" --output capability-skill-draft.md
```

3. Read the draft, then inspect all relevant files listed by the full scan:
   README/docs, dependency manifests, build/test configs, representative source,
   tests, templates, DSL files, examples, fixtures, and developer notes.
4. Analyze the project framework and functional modules:
   - runtime, language, framework, plugin architecture, schedulers, adapters, templates, data flow
   - module responsibilities and how users experience those capabilities
   - inputs, outputs, schemas, side effects, external services, and runtime assumptions
   - algorithmic steps, scheduling semantics, SQL/database templates, transforms, validations, and error handling
   - reusable examples, fixtures, tests, and parity checks
5. Present a source-neutral proposal to the user before creating the final skill:
   - candidate capability modules with plain-language names
   - recommended `references/capability-map.md` entries
   - recommended detailed module docs for `references/capability-conventions.md`
   - candidate same-language function files under `scripts/`
   - what should be omitted, merged, renamed, or expanded
   - whether the user wants an auditable source map; default is no
   Do not continue to final skill generation until the user approves or edits this proposal.
6. After approval, write the final generated skill as source-invisible:
   - `SKILL.md`: trigger and native workflow for the new skill
   - `references/capability-map.md`: approved capabilities, inputs, outputs, contracts, examples
   - `references/capability-conventions.md`: approved module explanations and detailed usage notes
   - `references/implementation-blueprint.md`: source-neutral implementation and verification rules
   - `references/task-playbook.md`: how to use the new skill's own functions and docs
   - `references/callable-scripts.md`: index of same-language functions when scripts are included
   - `scripts/`: implemented, tested same-language function files requested by the user
7. Keep generation evidence out of the final skill:
   - no source project name
   - no absolute paths or repo-root-relative paths
   - no source file names, source map, or source-to-test map
   - no "learned from", "original repository", "source project", or evidence-list phrasing
   - no imports from the source project unless the user explicitly asks for a wrapper skill

## Analysis Checklist

Extract capabilities supported by project evidence:
   - what each focused directory, DAG, plugin, template, script, or connector does
   - input contracts, output contracts, side effects, external services, and runtime assumptions
   - algorithmic steps, scheduling semantics, SQL/database templates, transforms, validations, and error handling
   - reusable examples, fixtures, tests, and parity checks
   - dependencies that are essential versus incidental framework glue
Also extract conventions when they matter for accurate recreation:
   - architecture and major subsystems
   - setup, build, test, lint, format, and run commands
   - naming, style, and module organization patterns
   - testing strategy, fixtures, mocks, and acceptance expectations
   - dependency, migration, generated-code, and asset rules
   - common pitfalls, unsafe operations, or files agents should avoid touching casually
   - user-provided focus paths and why they matter
## Target Locations

Create the generated skill in the user's requested platform location:
   - Codex: `<skills-dir>/<name>/SKILL.md`, usually `$CODEX_HOME/skills`, `~/.codex/skills`, or this repository's `skills/`.
   - Claude Code: project `.claude/skills/<name>/SKILL.md` or personal `~/.claude/skills/<name>/SKILL.md`.
   - OpenCode: project `.opencode/skills/<name>/SKILL.md` or global `~/.config/opencode/skills/<name>/SKILL.md`.

## Portability Requirements

- The generated skill must be useful after copying it to another machine or teammate.
- Bundle enough capability, implementation knowledge, examples, and same-language functions that future agents can use the skill without any source project.
- Future agents should use the bundled capability map, implementation blueprint, function files, and tests first. They should never need the source project.
- If the user asks for callable functions, bundle completed same-language files under `scripts/` and document their contracts in `references/callable-scripts.md`. Do not ship placeholder functions or functions that import the original repository unless the user explicitly asked for wrappers.
- Omit all source names, source paths, file names, generation evidence, and source maps from bundled references.
- If the generated skill's references still contain placeholders, treat it as incomplete and finish the references before sharing.
- When the user asks to create a skill, do not stop at the scanner draft. Create the final skill folder and complete the bundled reference.

## Target Formats

- **Codex**: Use `name` and `description` frontmatter, optional `agents/openai.yaml`, and optional `scripts/`, `references/`, or `assets/`.
- **Claude Code**: Use `SKILL.md` under `.claude/skills/<name>/` or `~/.claude/skills/<name>/`. Keep `description` specific; optional Claude fields such as `allowed-tools`, `disable-model-invocation`, `argument-hint`, or `paths` should be added only when the repo skill truly needs them.
- **OpenCode**: Use `SKILL.md` under `.opencode/skills/<name>/` or `~/.config/opencode/skills/<name>/`. Only rely on recognized frontmatter fields: `name`, `description`, optional `license`, `compatibility`, and string-to-string `metadata`.

## Output Rules

- Do not invent capability behavior. Mark uncertain behavior as "Needs user confirmation" during the proposal stage.
- Prefer concise, actionable instructions over a long repository tour.
- Include user-facing commands only when they are part of the new skill's own API.
- Package capability-specific conventions into the generated skill, not into a separate local note.
- For "out of the box" portability, ship `capability-map.md`, `capability-conventions.md`, `implementation-blueprint.md`, `task-playbook.md`, and any requested same-language `scripts/` together. Do not ship `source-map.md` unless the user explicitly asks for an auditable source map.
- If the user says certain directories are core, pass them through `--focus` and preserve the rationale in bundled references.
- If the user names paths, functions, or operations that should become tools, pass them through `--script-focus` or record them in `--script-note`, then implement final same-language functions from the evidence before distribution.
- Use full scan by default. Use `--sample-scan` only when full scan is impractical.
- Do not frame the generated skill only as "modify this repo"; frame it as "recreate this capability independently" unless `--skill-purpose development` is explicitly requested.
- Keep generated `SKILL.md` under 500 lines; move detailed notes into references.
- Do not overwrite an existing skill or draft unless the user explicitly asks for overwrite behavior.

## Resource Map

- `scripts/draft_repo_skill.py`: Scans a repository for text-like docs, manifests, source files, tests, config clues, user-focused capability directories, and optional function targets, then writes a Markdown draft for Codex, Claude, OpenCode, or all target skill formats. With `--script-output-dir`, it also creates same-language function files under the generated skill's `scripts/` directory.
