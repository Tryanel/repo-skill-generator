---
name: repo-skill-generator
description: Inspect a code repository and create repo-specific Codex, Claude, or OpenCode skills that capture its development conventions. Use when an agent needs to read README files, docs, manifests, source code, tests, and configuration in a target repository, then generate a new platform-specific skill for future agents to follow that repository's architecture, commands, coding style, testing habits, dependency rules, and common pitfalls.
---

# Repo Skill Generator

## Overview

Create compact, portable, repo-specific skills from observed repository facts. Read the codebase once during generation, package the conventions and code knowledge into the generated skill, then choose the correct target format for Codex, Claude, OpenCode, or all three.

## Workflow

1. Confirm the target repository path, target platform, and intended output skill name. Normalize the skill name to lowercase hyphen-case.
   Ask for or capture the user's scan scope when some directories are more important than the default framework layout, such as `dag/`, `plugin/`, `templates/`, or domain-specific workflow folders.
2. Run `scripts/draft_repo_skill.py` to create a first-pass evidence draft:

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target codex --knowledge-depth self-contained --output repo-skill-draft.md
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target claude --knowledge-depth self-contained --output repo-skill-draft.md
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target opencode --knowledge-depth self-contained --output repo-skill-draft.md
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target all --knowledge-depth self-contained --output repo-skill-draft.md
```

Use scope flags when the user identifies core directories:

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name mining-dev --target all --focus dag --focus plugin/templates --scope-note "dag contains the core mining scripts; plugin/templates contains database templates" --output repo-skill-draft.md
```

3. Read the draft, then inspect the most relevant files it lists. Always include README or docs, dependency manifests, build/test configs, representative source files, representative tests, and contribution or developer notes when present.
4. Extract only conventions supported by repository evidence:
   - architecture and major subsystems
   - setup, build, test, lint, format, and run commands
   - naming, style, and module organization patterns
   - testing strategy, fixtures, mocks, and acceptance expectations
   - dependency, migration, generated-code, and asset rules
   - common pitfalls, unsafe operations, or files agents should avoid touching casually
   - user-provided focus paths and why they matter
5. Fill the generated bundled references with self-contained repository facts:
   - `references/repo-conventions.md`: architecture, commands, tooling, style, tests, docs, and pitfalls.
   - `references/source-map.md`: module responsibilities, important symbols, public exports, and test modules.
   - `references/task-playbook.md`: task categories, source-to-test routing, and verification commands.
   Do not leave instructions such as "read the local repo" or absolute paths to the generation checkout as the source of knowledge.
6. Create the generated skill in the user's requested platform location:
   - Codex: `<skills-dir>/<name>/SKILL.md`, usually `$CODEX_HOME/skills`, `~/.codex/skills`, or this repository's `skills/`.
   - Claude Code: project `.claude/skills/<name>/SKILL.md` or personal `~/.claude/skills/<name>/SKILL.md`.
   - OpenCode: project `.opencode/skills/<name>/SKILL.md` or global `~/.config/opencode/skills/<name>/SKILL.md`.
7. Write the generated skill with progressive disclosure:
   - Put trigger context and core workflow in `SKILL.md`.
   - Put longer repository conventions in `references/repo-conventions.md` when the target supports supporting files.
   - Add scripts only for stable, repeatable, error-prone repository operations.
   - Add assets only when future agents must copy or reuse concrete files.
8. Validate the generated skill with the target platform's validation rules when available, and test any bundled scripts.

## Portability Requirements

- The generated skill must be useful after copying it to another machine or teammate.
- Bundle enough repo facts and source-map knowledge that future agents do not need the original local checkout used during generation to learn conventions or locate task-relevant code.
- Future agents should use the bundled source map and task playbook first. They may open the user's current checkout only to apply edits, verify code drift, or inspect details missing from the bundled knowledge pack.
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
- For "out of the box" portability, ship `repo-conventions.md`, `source-map.md`, and `task-playbook.md` together.
- If the user says certain directories are core, pass them through `--focus` and preserve the rationale in bundled references.
- Keep generated `SKILL.md` under 500 lines; move detailed notes into references.
- Do not overwrite an existing skill or draft unless the user explicitly asks for overwrite behavior.

## Resource Map

- `scripts/draft_repo_skill.py`: Scans a repository for text-like docs, manifests, source files, tests, and config clues, then writes a Markdown draft for Codex, Claude, OpenCode, or all target skill formats.
