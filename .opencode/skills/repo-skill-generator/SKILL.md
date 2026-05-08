---
name: repo-skill-generator
description: Inspect a code repository and create repo-specific Codex, Claude, or OpenCode skills that distill focused capabilities into portable knowledge packs and optional same-language callable functions.
metadata:
  kind: repo-skill-generator
  source: skill-learn
---

# Repo Skill Generator

## Instructions

1. Confirm the target repository path, target platform, output skill name, user-defined focus paths, whether to use `--full-scan`, and any capabilities the user wants turned into same-language callable functions.
2. From the repository root, run the canonical scanner from this project:

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target opencode --knowledge-depth self-contained --skill-purpose capability --output repo-skill-draft.md
```

Use `--target codex`, `--target claude`, `--target opencode`, or `--target all`.
Use `--focus`, `--include`, `--exclude`, and `--scope-note` when the user says certain folders are core, for example `--focus dag --focus plugin/templates`.
Use `--full-scan` when capabilities may live outside common source directories.
Use `--script-focus PATH_OR_LABEL`, `--script-output-dir <skill>/scripts`, `--script-language auto`, and `--script-note TEXT` when the user wants specific paths, functions, or operations turned into bundled same-language functions.

3. Read the generated draft, then inspect the listed README, docs, manifests, config files, representative source files, tests, and user-focused capability paths.
4. Create the target skill in the correct location:
   - Codex: `<skills-dir>/<name>/SKILL.md`
   - Claude: `.claude/skills/<name>/SKILL.md` or `~/.claude/skills/<name>/SKILL.md`
   - OpenCode: `.opencode/skills/<name>/SKILL.md` or `~/.config/opencode/skills/<name>/SKILL.md`
5. Put core workflow in `SKILL.md`; move self-contained capability knowledge into `references/capability-map.md`, `references/repo-conventions.md`, `references/implementation-blueprint.md`, and `references/task-playbook.md`. Do not ship `source-map.md` by default for capability skills.
6. When functions are requested, implement tested same-language files under `scripts/` and document contracts in `references/callable-scripts.md`. Do not ship placeholder functions.
7. Do not ship a generated skill that depends on the original local checkout used during generation. Future users should use bundled knowledge first and open a checkout only to verify drift or inspect missing details.

## Rules

- Do not invent repository capabilities or conventions.
- Keep the generated skill concise and evidence-based.
- Use repo-root-relative paths, not absolute generation paths.
- Do not stop at the scanner draft when the user asks for a final skill.
- For out-of-the-box use, ship capability map, conventions, implementation blueprint, task playbook, and any requested same-language functions together.
- Preserve user-provided focus paths, script targets, and rationale in the final references.
- Add target-specific frontmatter only when the target platform recognizes it.
