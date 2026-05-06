---
name: repo-skill-generator
description: Inspect a code repository and create repo-specific Codex, Claude, or OpenCode skills from its observed development conventions. Use when Claude needs to read README files, docs, manifests, source code, tests, and configuration, then draft a platform-specific skill for future agents.
---

# Repo Skill Generator

## Instructions

1. Confirm the target repository path, target platform, and output skill name.
2. From the repository root, run the canonical scanner from this project:

```bash
python scripts/draft_repo_skill.py --repo /path/to/repo --skill-name repo-name-dev --target claude --knowledge-depth self-contained --output repo-skill-draft.md
```

Use `--target codex`, `--target claude`, `--target opencode`, or `--target all`.

3. Read the generated draft, then inspect the listed README, docs, manifests, config files, representative source files, and tests.
4. Create the target skill in the correct location:
   - Codex: `<skills-dir>/<name>/SKILL.md`
   - Claude: `.claude/skills/<name>/SKILL.md` or `~/.claude/skills/<name>/SKILL.md`
   - OpenCode: `.opencode/skills/<name>/SKILL.md` or `~/.config/opencode/skills/<name>/SKILL.md`
5. Put core workflow in `SKILL.md`; move self-contained repository knowledge into `references/repo-conventions.md`, `references/source-map.md`, and `references/task-playbook.md`.
6. Do not ship a generated skill that depends on the original local checkout used during generation. Future users should use bundled knowledge first and open their checkout only to apply edits, verify drift, or inspect missing details.

## Rules

- Do not invent repository conventions.
- Keep the generated skill concise and evidence-based.
- Use repo-root-relative paths, not absolute generation paths.
- Do not stop at the scanner draft when the user asks for a final skill.
- For out-of-the-box use, ship conventions, source map, and task playbook together.
- Add target-specific frontmatter only when the target platform recognizes it.
