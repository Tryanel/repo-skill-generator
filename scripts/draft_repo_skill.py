#!/usr/bin/env python3
"""Draft a repo-specific agent skill from observable repository files."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".cache",
    ".deps",
    ".git",
    ".hg",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "external",
    "node_modules",
    "out",
    "target",
    "third_party",
    "vendor",
}

DOC_NAMES = {
    "readme",
    "contributing",
    "architecture",
    "development",
    "developer",
    "docs",
    "guide",
    "manual",
}

MANIFEST_NAMES = {
    "Cargo.toml",
    "composer.json",
    "go.mod",
    "Makefile",
    "package.json",
    "pnpm-workspace.yaml",
    "poetry.lock",
    "pyproject.toml",
    "requirements.txt",
    "setup.cfg",
    "setup.py",
    "yarn.lock",
}

CONFIG_NAMES = {
    ".editorconfig",
    ".eslintrc",
    ".eslintrc.cjs",
    ".eslintrc.js",
    ".prettierrc",
    ".prettierrc.json",
    "eslint.config.js",
    "jest.config.js",
    "pytest.ini",
    "ruff.toml",
    "tsconfig.json",
    "vite.config.js",
    "vitest.config.js",
}

TEXT_EXTS = {
    ".c",
    ".cc",
    ".cfg",
    ".cjs",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".lock",
    ".md",
    ".mjs",
    ".php",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".svelte",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}

SOURCE_EXTS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".ts",
    ".tsx",
}

TEST_MARKERS = ("test", "tests", "spec", "__tests__")
TARGETS = ("codex", "claude", "opencode")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a repository and draft evidence for a repo-specific agent skill."
    )
    parser.add_argument("--repo", required=True, help="Path to the target repository root.")
    parser.add_argument("--skill-name", required=True, help="Name for the generated repo-specific skill.")
    parser.add_argument(
        "--target",
        choices=(*TARGETS, "all"),
        default="codex",
        help="Skill format to draft. Defaults to codex.",
    )
    parser.add_argument(
        "--knowledge-depth",
        choices=("portable", "self-contained"),
        default="self-contained",
        help=(
            "portable bundles conventions only; self-contained also drafts source-map "
            "and task-playbook references. Defaults to self-contained."
        ),
    )
    parser.add_argument("--output", help="Markdown draft path. Writes to stdout when omitted.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting --output if it exists.")
    parser.add_argument("--max-files", type=int, default=300, help="Maximum text-like files to inspect.")
    parser.add_argument("--max-bytes", type=int, default=256_000, help="Maximum bytes to read per file.")
    return parser.parse_args()


def normalize_skill_name(value: str, target: str = "codex") -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if target == "claude":
        parts = [part for part in value.split("-") if part not in {"anthropic", "claude"}]
        value = "-".join(parts)
    return value[:63].strip("-") or "repo-dev"


def is_text_candidate(path: Path) -> bool:
    if path.name in MANIFEST_NAMES or path.name in CONFIG_NAMES:
        return True
    if path.suffix.lower() in TEXT_EXTS:
        return True
    stem = path.stem.lower()
    return stem in DOC_NAMES


def iter_files(root: Path, max_files: int) -> Iterable[Path]:
    buckets: dict[str, list[Path]] = {"doc": [], "manifest": [], "config": [], "source": [], "test": [], "other": []}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".idea"))
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if not is_text_candidate(path):
                continue
            buckets[classify(path, root)].append(path)

    for paths in buckets.values():
        paths.sort(key=lambda path: priority_key(path, root))

    # Docs, manifests, and config files carry more convention signal than arbitrary source files.
    ordered: list[Path] = []
    for kind in ("doc", "manifest", "config", "test", "source", "other"):
        ordered.extend(buckets[kind])
    yield from ordered[:max_files]


def priority_key(path: Path, root: Path) -> tuple[int, int, str]:
    rel_parts = path.relative_to(root).parts
    parts = {part.lower() for part in rel_parts}
    name = path.name.lower()
    if name.startswith("readme") or name.startswith("contributing"):
        tier = 0
    elif "docs" in parts or "tutorial" in parts:
        tier = 1
    elif name == "skill.md":
        tier = 2
    elif rel_parts[0].lower() in {"src", "lib", "app", "packages"}:
        tier = 3
    elif path.name in MANIFEST_NAMES or path.name in CONFIG_NAMES:
        tier = 4
    elif "tests" in parts or "__tests__" in parts:
        tier = 5
    elif "examples" in parts:
        tier = 6
    else:
        tier = 7
    return (tier, len(rel_parts), path.as_posix())


def read_text(path: Path, max_bytes: int) -> str:
    data = path.read_bytes()[:max_bytes]
    if b"\x00" in data:
        return ""
    return data.decode("utf-8", errors="replace")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def classify(path: Path, root: Path) -> str:
    parts = {p.lower() for p in path.relative_to(root).parts}
    name = path.name
    name_lower = name.lower()
    stem = path.stem.lower()
    if name in MANIFEST_NAMES:
        return "manifest"
    if name in CONFIG_NAMES or path.suffix.lower() in {".toml", ".yaml", ".yml", ".ini", ".cfg"}:
        return "config"
    if stem in DOC_NAMES or "docs" in parts or path.suffix.lower() == ".md":
        return "doc"
    if (
        any(marker in parts for marker in TEST_MARKERS)
        or name_lower.startswith("test_")
        or name_lower.endswith("_test.py")
        or ".test." in name_lower
        or ".spec." in name_lower
    ):
        return "test"
    if path.suffix.lower() in SOURCE_EXTS:
        return "source"
    return "other"


def extract_package_scripts(root: Path) -> list[str]:
    package_json = root / "package.json"
    if not package_json.exists():
        return []
    try:
        data = json.loads(read_text(package_json, 256_000))
    except json.JSONDecodeError:
        return ["package.json exists but could not be parsed as JSON."]
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return []
    return [f"npm run {name}: {cmd}" for name, cmd in sorted(scripts.items())]


def extract_make_targets(root: Path) -> list[str]:
    makefile = root / "Makefile"
    if not makefile.exists():
        return []
    targets: list[str] = []
    pattern = re.compile(r"^([A-Za-z0-9_.-]+):(?:\s|$)")
    for line in read_text(makefile, 128_000).splitlines():
        match = pattern.match(line)
        if match and not match.group(1).startswith("."):
            targets.append(f"make {match.group(1)}")
    return targets[:20]


def detect_standard_commands(root: Path) -> list[str]:
    commands = []
    if (root / "pyproject.toml").exists() or (root / "pytest.ini").exists():
        commands.append("pytest")
    if (root / "Cargo.toml").exists():
        commands.extend(["cargo test", "cargo fmt", "cargo clippy"])
    if (root / "go.mod").exists():
        commands.extend(["go test ./...", "gofmt"])
    if (root / "package.json").exists():
        commands.extend(["npm install", "npm test"])
    return commands


def detect_tooling(files: list[Path], root: Path) -> list[str]:
    names = {path.name for path in files}
    suffixes = Counter(path.suffix.lower() for path in files if path.suffix)
    clues = []
    for name in sorted((MANIFEST_NAMES | CONFIG_NAMES) & names):
        clues.append(name)
    common_languages = [
        (".py", "Python"),
        (".ts", "TypeScript"),
        (".tsx", "TypeScript React"),
        (".js", "JavaScript"),
        (".go", "Go"),
        (".rs", "Rust"),
        (".java", "Java"),
        (".cs", "C#"),
    ]
    for ext, label in common_languages:
        if suffixes.get(ext):
            clues.append(f"{label} files: {suffixes[ext]}")
    if not clues:
        clues.append("No common manifest or language clue detected in scanned files.")
    return clues


def select_recommended(files_by_kind: dict[str, list[Path]], root: Path) -> list[str]:
    selected: list[Path] = []
    for kind in ("doc", "manifest", "config", "source", "test"):
        selected.extend(files_by_kind.get(kind, [])[:8 if kind in {"source", "test"} else 12])
    seen = set()
    result = []
    for path in selected:
        value = rel(path, root)
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def directory_overview(files: list[Path], root: Path, limit: int = 20) -> list[str]:
    counts: Counter[str] = Counter()
    for path in files:
        parts = path.relative_to(root).parts
        if len(parts) == 1:
            key = "."
        else:
            key = parts[0]
        counts[key] += 1
    return [f"{name}: {count} scanned files" for name, count in counts.most_common(limit)]


def role_map(paths: list[str], role: str) -> list[str]:
    return [f"{path}: {role}" for path in paths]


def first_sentence(text: str | None, limit: int = 180) -> str:
    if not text:
        return ""
    compact = " ".join(text.strip().split())
    if not compact:
        return ""
    match = re.search(r"(?<=[.!?])\s+", compact)
    if match:
        compact = compact[: match.start()]
    if len(compact) > limit:
        compact = compact[: limit - 3].rstrip() + "..."
    return compact


def python_symbols(path: Path, max_bytes: int) -> tuple[str, list[str], list[str]]:
    text = read_text(path, max_bytes)
    if not text:
        return "", [], []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "", [], []

    doc = first_sentence(ast.get_docstring(tree))
    symbols: list[str] = []
    imports: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names[:5])
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.append(module)
        elif isinstance(node, ast.ClassDef):
            methods = [
                child.name
                for child in node.body
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
                and not child.name.startswith("_")
            ]
            method_text = f" methods: {', '.join(methods[:10])}" if methods else ""
            symbols.append(f"class {node.name} (line {node.lineno}){method_text}")
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            symbols.append(f"function {node.name} (line {node.lineno})")

    return doc, symbols[:30], imports[:20]


def regex_symbols(path: Path, max_bytes: int) -> tuple[str, list[str], list[str]]:
    text = read_text(path, max_bytes)
    if not text:
        return "", [], []
    symbols: list[str] = []
    patterns = [
        r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        r"^\s*(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\b",
        r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=",
        r"^\s*func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    ]
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                symbols.append(f"{match.group(1)} (line {lineno})")
                break
        if len(symbols) >= 30:
            break
    return "", symbols, []


def summarize_code_file(path: Path, root: Path, max_bytes: int) -> str:
    relative = rel(path, root)
    if path.suffix.lower() == ".py":
        doc, symbols, imports = python_symbols(path, max_bytes)
    else:
        doc, symbols, imports = regex_symbols(path, max_bytes)

    parts = [f"### `{relative}`"]
    if doc:
        parts.append(f"- Module note: {doc}")
    if imports:
        parts.append(f"- Imports: {', '.join(imports[:12])}")
    if symbols:
        parts.append("- Symbols:")
        parts.extend(f"  - {symbol}" for symbol in symbols[:24])
    else:
        parts.append("- Symbols: no top-level symbols detected by the scanner.")
    return "\n".join(parts)


def likely_test_targets(source_path: str, test_paths: list[str]) -> list[str]:
    stem = Path(source_path).stem.lower().lstrip("_")
    candidates = []
    for test_path in test_paths:
        test_stem = Path(test_path).stem.lower()
        if stem and stem in test_stem:
            candidates.append(test_path)
    if not candidates and test_paths:
        candidates = test_paths[:3]
    return candidates[:5]


def source_map_block(
    root: Path,
    source_files: list[Path],
    test_files: list[Path],
    max_bytes: int,
) -> str:
    source_sections = [
        summarize_code_file(path, root, max_bytes) for path in source_files[:40]
    ]
    test_sections = [
        summarize_code_file(path, root, max_bytes) for path in test_files[:30]
    ]
    if not source_sections:
        source_sections = ["No source files were summarized."]
    if not test_sections:
        test_sections = ["No test files were summarized."]
    return f"""```markdown
# Source Map

This reference is bundled so future users can understand the repository's
modules, public symbols, and test surface without rereading the original
generation checkout. Paths are repo-root-relative.

## Source Modules

{chr(10).join(source_sections)}

## Test Modules

{chr(10).join(test_sections)}
```
"""


def task_playbook_block(
    root: Path,
    source_paths: list[str],
    test_paths: list[str],
    commands: list[str],
) -> str:
    mappings = []
    for source_path in source_paths[:30]:
        tests = likely_test_targets(source_path, test_paths)
        test_text = ", ".join(f"`{test}`" for test in tests) if tests else "no direct test match detected"
        mappings.append(f"- `{source_path}` -> {test_text}")

    command_text = bullet_list(commands, "No commands detected. Fill exact commands manually.")
    mapping_text = "\n".join(mappings) if mappings else "- No source-to-test map detected."

    return f"""```markdown
# Task Playbook

Use this playbook before opening source files. It is designed to make the skill
usable from its bundled knowledge package, then use the user's checkout only to
apply edits and verify drift.

## Default Flow

1. Identify the task category from the user's request.
2. Consult the source-to-test map below to choose the likely implementation and
   verification files.
3. Apply the smallest change in the user's checkout.
4. Run the narrowest relevant command first.
5. Escalate to broader tests only when shared behavior changes.

## Commands

{command_text}

## Source-To-Test Map

{mapping_text}

## Common Task Categories

- Public API export: update the package entrypoint and import tests.
- Command or group behavior: inspect command/core modules and command tests.
- Option or argument parsing: inspect parser/core/type modules and option or
  argument tests.
- User-visible errors: inspect exception/type/core modules and exact-output
  tests.
- Terminal UI or formatting: inspect terminal, formatting, or utility modules
  and their matching tests.
- Docs-only change: use docs commands and Markdown wrapping rules from
  `repo-conventions.md`.
```
"""


def portable_reference_block(
    root: Path,
    files: list[Path],
    commands: list[str],
    tooling: list[str],
    doc_paths: list[str],
    manifest_paths: list[str],
    config_paths: list[str],
    source_paths: list[str],
    test_paths: list[str],
) -> str:
    repo_name = root.name
    overview = directory_overview(files, root)
    file_roles = []
    file_roles.extend(role_map(doc_paths[:12], "documentation or repository guidance"))
    file_roles.extend(role_map(manifest_paths[:12], "dependency, build, or package metadata"))
    file_roles.extend(role_map(config_paths[:12], "tooling, CI, style, or environment config"))
    file_roles.extend(role_map(source_paths[:12], "representative implementation source"))
    file_roles.extend(role_map(test_paths[:12], "representative test coverage"))

    return f"""```markdown
# Repo Conventions

This reference is bundled with the skill so future users do not need access to
the original repository path used during skill generation. Paths are relative to
the repository root.

## Repository Identity

- Repository name: `{repo_name}`
- Original generation path: intentionally omitted for portability.
- Use this file as the source of repository conventions. Inspect a user's
  current checkout only for task-specific code context.

## Directory Overview

{bullet_list(overview, "No directory overview detected.", quote=False)}

## Commands

{bullet_list(commands, "No commands detected from common manifests. Add exact commands manually after reading repo docs.")}

## Tooling And Language Clues

{bullet_list(tooling)}

## Important Files And Roles

{bullet_list(file_roles, "No file roles detected.", quote=False)}

## Architecture

Summarize the repository's major subsystems here before sharing the skill. Do
not leave this section as "read the repo"; write down the actual conventions
observed from docs, source layout, and representative modules.

## Code Style

Record concrete style rules from config files and nearby code. Include naming,
module organization, import style, error handling, logging, dependency, and
generated-code rules that future agents should follow without rediscovering
them from the original checkout.

## Testing

Record test locations, fixtures, mocks, commands, and acceptance expectations.
Include the narrow test commands future agents should run for common edits.

## Pitfalls

List risky files, irreversible operations, migration rules, lockfile rules,
release metadata, vendored/generated files, or other repo-specific gotchas.
```
"""


def bullet_list(
    items: list[str], empty: str = "None detected.", quote: bool = True
) -> str:
    if not items:
        return f"- {empty}"
    if quote:
        return "\n".join(f"- `{item}`" for item in items)
    return "\n".join(f"- {item}" for item in items)


def platform_subject(target: str) -> str:
    return {
        "codex": "Codex",
        "claude": "Claude",
        "opencode": "OpenCode",
    }[target]


def platform_article(target: str) -> str:
    return "an" if target == "opencode" else "a"


def platform_install_notes(skill_name: str, target: str) -> list[str]:
    if target == "codex":
        return [
            f"`<skills-dir>/{skill_name}/SKILL.md`",
            f"`<skills-dir>/{skill_name}/agents/openai.yaml` for Codex UI metadata",
            f"`<skills-dir>/{skill_name}/references/repo-conventions.md` for longer facts",
        ]
    if target == "claude":
        return [
            f"Project: `.claude/skills/{skill_name}/SKILL.md`",
            f"Personal: `~/.claude/skills/{skill_name}/SKILL.md`",
            f"Supporting files live beside `SKILL.md`, such as `references/repo-conventions.md`.",
        ]
    return [
        f"Project: `.opencode/skills/{skill_name}/SKILL.md`",
        f"Global: `~/.config/opencode/skills/{skill_name}/SKILL.md`",
        "OpenCode also discovers compatible `.claude/skills/` and `.agents/skills/` layouts.",
    ]


def platform_frontmatter(skill_name: str, repo_name: str, target: str) -> str:
    subject = platform_subject(target)
    description = (
        f"Work in the {repo_name} repository using its observed development "
        f"conventions. Use when {subject} needs to modify, review, test, debug, "
        "or explain code in this repository while following its README, "
        "architecture, commands, style, and test practices."
    )
    if target == "opencode":
        return (
            "---\n"
            f"name: {skill_name}\n"
            f"description: {description}\n"
            "metadata:\n"
            f"  repo: {repo_name}\n"
            "  kind: repo-development\n"
            "---"
        )
    return (
        "---\n"
        f"name: {skill_name}\n"
        f"description: {description}\n"
        "---"
    )


def make_skill_draft(
    skill_name: str, repo_name: str, target: str, knowledge_depth: str
) -> str:
    display = skill_name.replace("-", " ").title()
    subject = platform_subject(target)
    article = platform_article(target)
    frontmatter = platform_frontmatter(skill_name, repo_name, target)
    if knowledge_depth == "self-contained":
        reference_step = (
            "Read the bundled `references/repo-conventions.md`, "
            "`references/source-map.md`, and `references/task-playbook.md` before "
            "making non-trivial changes."
        )
        playbook_step = (
            "Use the bundled task playbook to choose the likely implementation and "
            "tests before opening files."
        )
        missing_reference_text = "any bundled reference is missing"
    else:
        reference_step = (
            "Read the bundled `references/repo-conventions.md` before making "
            "non-trivial changes."
        )
        playbook_step = (
            "Use the bundled conventions to choose likely implementation and test "
            "areas before opening files."
        )
        missing_reference_text = "`references/repo-conventions.md` is missing"
    return f"""```markdown
{frontmatter}

# {display}

## Overview

Use the bundled repository conventions before making changes. This skill is portable: it must not depend on the original local repository path used during generation.

## Workflow

1. {reference_step}
2. Do not fetch, reopen, or depend on the original repository path used to generate this skill.
3. {playbook_step}
4. Open the user's checkout only to apply edits, verify drift, or inspect code that is missing from the bundled knowledge pack.
5. Use the setup, build, lint, format, and test commands recorded in the bundled reference.
6. Prefer local helpers, tests, and conventions over new abstractions.
7. Keep edits scoped to the relevant subsystem and preserve generated or vendored files unless the repo explicitly instructs otherwise.
8. Run the narrowest meaningful tests first, then broader checks when shared behavior changes.

## Output Rules

- Cite exact files, commands, or conventions when explaining repository-specific decisions.
- Mark uncertain conventions as assumptions instead of presenting them as rules.
- Do not introduce new dependencies, frameworks, or file organization patterns without repository evidence.
- Use this as {article} {subject} skill and keep platform-specific metadata minimal.
- If {missing_reference_text} or still contains placeholder text, say the skill is incomplete instead of rediscovering conventions from the original generation repo.
```
"""


def build_platform_sections(
    root: Path, skill_name: str, target: str, knowledge_depth: str
) -> str:
    targets = TARGETS if target == "all" else (target,)
    sections = []
    for platform in targets:
        platform_skill_name = normalize_skill_name(skill_name, platform)
        install_notes = bullet_list(
            platform_install_notes(platform_skill_name, platform), quote=False
        )
        skill_block = make_skill_draft(
            platform_skill_name, root.name, platform, knowledge_depth
        )
        title = platform_subject(platform)
        sections.append(
            f"""### {title}

Install layout:

{install_notes}

Starter skill:

{skill_block}"""
        )
    return "\n\n".join(sections)


def build_markdown(
    root: Path,
    skill_name: str,
    target: str,
    files: list[Path],
    knowledge_depth: str,
    max_bytes: int,
) -> str:
    repo_name = root.name
    files_by_kind: dict[str, list[Path]] = {"doc": [], "manifest": [], "config": [], "source": [], "test": [], "other": []}
    for path in files:
        files_by_kind[classify(path, root)].append(path)

    package_scripts = extract_package_scripts(root)
    make_targets = extract_make_targets(root)
    standard_commands = detect_standard_commands(root)
    commands = package_scripts + make_targets + standard_commands
    tooling = detect_tooling(files, root)
    recommended = select_recommended(files_by_kind, root)

    doc_paths = [rel(path, root) for path in files_by_kind["doc"][:20]]
    manifest_paths = [rel(path, root) for path in files_by_kind["manifest"][:20]]
    config_paths = [rel(path, root) for path in files_by_kind["config"][:20]]
    source_paths = [rel(path, root) for path in files_by_kind["source"][:20]]
    test_paths = [rel(path, root) for path in files_by_kind["test"][:20]]

    counts = Counter(classify(path, root) for path in files)
    platform_sections = build_platform_sections(
        root, skill_name, target, knowledge_depth
    )
    portable_reference = portable_reference_block(
        root,
        files,
        commands,
        tooling,
        doc_paths,
        manifest_paths,
        config_paths,
        source_paths,
        test_paths,
    )
    source_map = ""
    task_playbook = ""

    if knowledge_depth == "self-contained":
        source_map = source_map_block(
            root, files_by_kind["source"], files_by_kind["test"], max_bytes
        )
        task_playbook = task_playbook_block(root, source_paths, test_paths, commands)

    return f"""# Repo Skill Draft: {skill_name}

Repository name: `{repo_name}`

Target: `{target}`

Knowledge depth: `{knowledge_depth}`

Portability: generated skill content must use repo-root-relative paths and must
not depend on the absolute generation path.

## Scan Summary

- Text-like files scanned: {len(files)}
- Docs: {counts.get("doc", 0)}
- Manifests: {counts.get("manifest", 0)}
- Configs: {counts.get("config", 0)}
- Source files: {counts.get("source", 0)}
- Test files: {counts.get("test", 0)}

## Recommended Reading Order

{bullet_list(recommended)}

## Detected Commands

{bullet_list(commands, "No commands detected from common manifests. Inspect README and docs manually.")}

## Tooling And Framework Clues

{bullet_list(tooling)}

## Evidence Files

### Docs

{bullet_list(doc_paths)}

### Manifests

{bullet_list(manifest_paths)}

### Configs

{bullet_list(config_paths)}

### Representative Source

{bullet_list(source_paths)}

### Representative Tests

{bullet_list(test_paths)}

## Repo Conventions To Confirm Manually

- Architecture and subsystem boundaries
- Setup and environment variables
- Build, test, lint, format, and release commands
- Naming, import, error handling, logging, and API patterns
- Test fixture and mock conventions
- Generated, vendored, migration, or lock files that require special handling
- Risky commands or files future agents should avoid changing casually
- Replace placeholders in the portable reference before sharing the generated skill.
- Do not ship a generated skill that tells future users to inspect the original local repository path.

## Starter Generated Skills

{platform_sections}

## Portable `references/repo-conventions.md`

Copy this bundled reference into the generated skill and fill the placeholder
sections with observed facts before sharing it.

{portable_reference}

## Self-Contained `references/source-map.md`

Copy this bundled source map into the generated skill when using
`--knowledge-depth self-contained`.

{source_map or "Not generated. Re-run with `--knowledge-depth self-contained`."}

## Self-Contained `references/task-playbook.md`

Copy this bundled playbook into the generated skill when using
`--knowledge-depth self-contained`.

{task_playbook or "Not generated. Re-run with `--knowledge-depth self-contained`."}
"""


def main() -> int:
    args = parse_args()
    root = Path(args.repo).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: --repo must be an existing directory: {root}", file=sys.stderr)
        return 2

    skill_name = normalize_skill_name(args.skill_name)
    files = list(iter_files(root, args.max_files))
    markdown = build_markdown(
        root, skill_name, args.target, files, args.knowledge_depth, args.max_bytes
    )

    if args.output:
        output = Path(args.output).expanduser().resolve()
        if output.exists() and not args.overwrite:
            print(f"error: output exists; pass --overwrite to replace it: {output}", file=sys.stderr)
            return 3
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8", newline="\n")
        print(f"Wrote draft: {output}")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
