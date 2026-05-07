---
name: repo-skill-generator
description: Inspect a code repository and create repo-specific Codex, Claude, OpenCode, or Agent Skills-compatible instructions from its observed development conventions. Use when an agent needs to read README files, docs, manifests, source code, tests, and configuration, then draft a platform-specific skill for future agents.
---

# Repo Skill Generator

## Instructions

1. Confirm the target repository path, target platform, output skill name, and any user-defined focus paths.
2. From the repository root, run the canonical scanner from this project:

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target all --knowledge-depth self-contained --output repo-skill-draft.md
```

Use `--target codex`, `--target claude`, `--target opencode`, or `--target all`.
Use `--focus`, `--include`, `--exclude`, and `--scope-note` when the user says certain folders are core, for example `--focus dag --focus plugin/templates`.

3. Read the generated draft, then inspect the listed README, docs, manifests, config files, representative source files, and tests.
4. Create the target skill in the correct location:
   - Codex: `<skills-dir>/<name>/SKILL.md`
   - Claude: `.claude/skills/<name>/SKILL.md` or `~/.claude/skills/<name>/SKILL.md`
   - OpenCode: `.opencode/skills/<name>/SKILL.md` or `~/.config/opencode/skills/<name>/SKILL.md`
   - Agent-compatible: `.agents/skills/<name>/SKILL.md` or `~/.agents/skills/<name>/SKILL.md`
5. Put core workflow in `SKILL.md`; move self-contained repository knowledge into:
   - `references/repo-conventions.md`
   - `references/source-map.md`
   - `references/task-playbook.md`
6. Do not ship a generated skill that depends on the original local checkout used during generation. Future users should use bundled knowledge first and open their checkout only to apply edits, verify drift, or inspect missing details.

## Rules

- Do not invent repository conventions.
- Keep the generated skill concise and evidence-based.
- Use repo-root-relative paths, not absolute generation paths.
- Do not stop at the scanner draft when the user asks for a final skill.
- For out-of-the-box use, ship conventions, source map, and task playbook together.
- Preserve user-provided focus paths and rationale in the final references.
- Add target-specific frontmatter only when the target platform recognizes it.
