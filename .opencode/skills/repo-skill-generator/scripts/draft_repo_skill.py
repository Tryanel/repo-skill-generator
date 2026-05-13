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
SCRIPT_LANGUAGES = ("auto", "python", "typescript", "javascript", "go", "rust", "ruby")
SCRIPT_LANGUAGE_EXTENSIONS = {
    ".go": "go",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".ts": "typescript",
    ".tsx": "typescript",
}
SCRIPT_OUTPUT_EXTENSIONS = {
    "go": ".go",
    "javascript": ".js",
    "python": ".py",
    "ruby": ".rb",
    "rust": ".rs",
    "typescript": ".ts",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a repository and draft a source-neutral capability skill plan."
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
            "portable drafts source-neutral capability docs only; self-contained "
            "also drafts generation-only analysis and planning references. "
            "Defaults to self-contained."
        ),
    )
    parser.add_argument(
        "--skill-purpose",
        choices=("capability", "development"),
        default="capability",
        help=(
            "capability generates a skill for recreating repository capabilities "
            "as same-language callable functions; development generates a skill for modifying "
            "the original repository. Defaults to capability."
        ),
    )
    parser.add_argument("--output", help="Markdown draft path. Writes to stdout when omitted.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting --output if it exists.")
    parser.add_argument(
        "--max-files",
        type=int,
        default=0,
        help="Maximum text-like files to inspect when --sample-scan is used. 0 means no limit.",
    )
    parser.add_argument("--max-bytes", type=int, default=256_000, help="Maximum bytes to read per file.")
    parser.add_argument(
        "--full-scan",
        action="store_true",
        default=True,
        help=(
            "Default. Scan every text-like file that is not skipped by directory rules or "
            "--exclude, ignoring --max-files. Use this when capabilities may live "
            "outside common source directories."
        ),
    )
    parser.add_argument(
        "--sample-scan",
        dest="full_scan",
        action="store_false",
        help="Use --max-files sampling instead of the default full scan.",
    )
    parser.add_argument(
        "--focus",
        action="append",
        default=[],
        help=(
            "Repo-root-relative directory or file that should be treated as core. "
            "Repeat for multiple paths, for example --focus dag --focus plugin/templates."
        ),
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help=(
            "Repo-root-relative directory or file to include even when it would "
            "normally be skipped, for example --include third_party/templates."
        ),
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help=(
            "Repo-root-relative directory or file to skip for this scan. Repeat "
            "for multiple paths."
        ),
    )
    parser.add_argument(
        "--scope-note",
        default="",
        help="User-provided scan intent, such as 'dag and plugin templates are the core mining scripts'.",
    )
    parser.add_argument(
        "--script-focus",
        action="append",
        default=[],
        help=(
            "Repo-root-relative file, directory, or operation label whose behavior "
            "should be turned into callable functions in the generated skill. Repeat "
            "for multiple script candidates."
        ),
    )
    parser.add_argument(
        "--script-note",
        default="",
        help=(
            "User-provided instruction for what to expose as generated skill "
            "functions, such as 'make SQL rendering and DAG scheduling callable'."
        ),
    )
    parser.add_argument(
        "--script-output-dir",
        help=(
            "Directory where same-language callable function files should be "
            "written. When omitted, the draft records the planned files but does "
            "not create them."
        ),
    )
    parser.add_argument(
        "--script-language",
        choices=SCRIPT_LANGUAGES,
        default="auto",
        help=(
            "Language for generated callable function files. Defaults to auto, "
            "which uses script target evidence or the repository's primary source language."
        ),
    )
    parser.add_argument(
        "--script-api",
        choices=("function", "cli", "both"),
        default="function",
        help=(
            "Shape of generated function files. Defaults to function for direct "
            "callable APIs; use both only when a CLI wrapper is also needed."
        ),
    )
    parser.add_argument(
        "--script-overwrite",
        action="store_true",
        help="Allow overwriting files in --script-output-dir.",
    )
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


def looks_like_text(path: Path, sample_size: int = 4096) -> bool:
    try:
        data = path.read_bytes()[:sample_size]
    except OSError:
        return False
    if not data:
        return True
    if b"\x00" in data:
        return False
    decoded = data.decode("utf-8", errors="replace")
    if not decoded:
        return False
    replacement_ratio = decoded.count("\ufffd") / max(len(decoded), 1)
    if replacement_ratio > 0.05:
        return False
    control_chars = sum(
        1 for char in decoded if ord(char) < 32 and char not in "\n\r\t\f\b"
    )
    return control_chars / max(len(decoded), 1) < 0.05


def normalize_scope_paths(values: list[str]) -> tuple[str, ...]:
    normalized = []
    for value in values:
        path = value.replace("\\", "/").strip().strip("/")
        if path:
            normalized.append(path.lower())
    return tuple(normalized)


def path_matches_scope(path: Path, root: Path, scopes: tuple[str, ...]) -> bool:
    if not scopes:
        return False
    relative = rel(path, root).lower()
    return any(relative == scope or relative.startswith(f"{scope}/") for scope in scopes)


def dir_matches_scope(dirpath: str, root: Path, scopes: tuple[str, ...]) -> bool:
    if not scopes:
        return False
    path = Path(dirpath)
    try:
        relative = path.relative_to(root).as_posix().lower()
    except ValueError:
        return False
    if relative == ".":
        return False
    return any(relative == scope or relative.startswith(f"{scope}/") for scope in scopes)


def iter_files(
    root: Path,
    max_files: int,
    focus_paths: tuple[str, ...],
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
    include_unknown_text: bool = False,
) -> Iterable[Path]:
    buckets: dict[str, list[Path]] = {"doc": [], "manifest": [], "config": [], "source": [], "test": [], "other": []}
    for dirpath, dirnames, filenames in os.walk(root):
        kept_dirs = []
        for dirname in sorted(dirnames):
            child = Path(dirpath) / dirname
            if dir_matches_scope(str(child), root, exclude_paths):
                continue
            if dirname.startswith(".idea"):
                continue
            if dirname in SKIP_DIRS and not dir_matches_scope(str(child), root, include_paths):
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if path_matches_scope(path, root, exclude_paths):
                continue
            if not is_text_candidate(path) and not (
                include_unknown_text and looks_like_text(path)
            ):
                continue
            buckets[classify(path, root)].append(path)

    for paths in buckets.values():
        paths.sort(key=lambda path: priority_key(path, root, focus_paths, include_paths))

    # Docs, manifests, and config files carry more convention signal than arbitrary source files.
    ordered: list[Path] = []
    for kind in ("doc", "manifest", "config", "test", "source", "other"):
        ordered.extend(buckets[kind])
    if max_files <= 0:
        yield from ordered
    else:
        yield from ordered[:max_files]


def priority_key(
    path: Path, root: Path, focus_paths: tuple[str, ...], include_paths: tuple[str, ...]
) -> tuple[int, int, str]:
    rel_parts = path.relative_to(root).parts
    parts = {part.lower() for part in rel_parts}
    name = path.name.lower()
    in_focus = path_matches_scope(path, root, focus_paths)
    in_include = path_matches_scope(path, root, include_paths)
    if in_focus:
        tier = 0
    elif name.startswith("readme") or name.startswith("contributing"):
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
    scope_rank = 0 if in_focus else 1 if in_include else 2
    return (scope_rank, tier, len(rel_parts), path.as_posix())


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
    for kind in ("doc", "manifest", "config", "source", "test", "other"):
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


def infer_capability_role(path: str) -> str:
    lowered = path.lower()
    if any(token in lowered for token in ("dag", "workflow", "pipeline", "flow")):
        return "workflow orchestration or data pipeline capability"
    if any(token in lowered for token in ("plugin", "template", "sql", "query", "database", "db")):
        return "plugin, template, SQL, or database integration capability"
    if any(token in lowered for token in ("script", "job", "task", "worker")):
        return "scripted job or task execution capability"
    if any(token in lowered for token in ("model", "feature", "mine", "mining", "extract")):
        return "data mining, feature extraction, or modeling capability"
    if any(token in lowered for token in ("api", "client", "connector", "adapter")):
        return "API, connector, adapter, or integration capability"
    if any(token in lowered for token in ("config", "conf", "yaml", "json", "toml")):
        return "configuration-driven behavior"
    return "general capability"


def human_title_from_scope(scope: str) -> str:
    return source_neutral_module_name(scope)


def source_neutral_module_name(path: str) -> str:
    role = infer_capability_role(path)
    mapping = {
        "workflow orchestration or data pipeline capability": "Workflow Orchestration",
        "plugin, template, SQL, or database integration capability": "Template And Integration",
        "scripted job or task execution capability": "Task Execution",
        "data mining, feature extraction, or modeling capability": "Data Capability",
        "API, connector, adapter, or integration capability": "External Integration",
        "configuration-driven behavior": "Configuration",
        "general capability": "General Capability",
    }
    return mapping.get(role, "General Capability")


def capability_inventory(paths: list[str], focus_paths: tuple[str, ...]) -> list[str]:
    selected = []
    seen = set()
    for path in paths:
        if focus_paths and not any(path.lower() == f or path.lower().startswith(f"{f}/") for f in focus_paths):
            continue
        if path not in seen:
            seen.add(path)
            selected.append(path)

    if not selected:
        selected = paths[:30]

    return [f"{path}: {infer_capability_role(path)}" for path in selected[:40]]


def source_neutral_capability_inventory(paths: list[str], focus_paths: tuple[str, ...]) -> list[str]:
    raw = capability_inventory(paths, focus_paths)
    seen: set[str] = set()
    result: list[str] = []
    for item in raw:
        path, _, role = item.partition(": ")
        name = source_neutral_module_name(path)
        if name in seen:
            continue
        seen.add(name)
        result.append(f"{name}: {role or 'capability'}")
    return result[:20]


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


def capability_map_block(
    root: Path,
    commands: list[str],
    tooling: list[str],
    doc_paths: list[str],
    manifest_paths: list[str],
    config_paths: list[str],
    source_paths: list[str],
    test_paths: list[str],
    other_paths: list[str],
    focus_paths: tuple[str, ...],
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
    scope_note: str,
    script_focus_paths: tuple[str, ...],
    script_note: str,
) -> str:
    all_evidence = source_paths + config_paths + other_paths + doc_paths + manifest_paths
    inventory = source_neutral_capability_inventory(all_evidence, focus_paths)
    return f"""```markdown
# Capability Map

This is the user-facing map of this skill's native capabilities.

## Capability Modules

{bullet_list(inventory, "No source-neutral capability modules detected yet.", quote=False)}

## Details To Complete After User Approval

- Purpose of each approved capability.
- Supported inputs, schemas, options, and configuration.
- Outputs, side effects, error behavior, and edge cases.
- Required same-language functions in `scripts/`.
- Short examples that show the skill's own API and workflow.

## User-Facing Rules

- Present these capabilities as this skill's own capabilities.
- Do not refer to generation materials, checkouts, paths, file names, or
  evidence lists.
- Prefer concise behavior contracts and runnable examples over implementation
  history.

## Inputs To Extract

- Configuration values, environment variables, CLI flags, templates, schemas,
  records, and plugin metadata that users must provide.
- Example inputs for each approved capability.
- External service assumptions such as databases, queues, APIs, object stores,
  schedulers, or model runtimes, written generically.

## Outputs To Reproduce

- Files, database writes, reports, API calls, logs, metrics, generated SQL,
  transformed datasets, or scheduled jobs produced by the capability.
- Error behavior, retries, fallbacks, and validation outcomes.
```
"""


def implementation_blueprint_block(
    commands: list[str],
    source_paths: list[str],
    test_paths: list[str],
    focus_paths: tuple[str, ...],
    scope_note: str,
    script_focus_paths: tuple[str, ...],
    script_note: str,
) -> str:
    return f"""```markdown
# Implementation Blueprint

Use this blueprint to write new same-language functions or tools with
the capabilities documented in `capability-map.md`. Treat the bundled
references and scripts as the complete capability contract.

## Reimplementation Flow

1. Pick the capability from `capability-map.md`.
2. Use `capability-map.md`, `callable-scripts.md`, tests, examples, and
   templates to identify the relevant algorithms, configuration, and contracts.
3. Define a standalone same-language function API first. Add a CLI wrapper only
   if the user asked for one.
4. Recreate behavior from documented contracts: inputs, outputs, transforms,
   database templates, scheduling semantics, retries, and error handling.
5. Replace framework-specific dependencies with small adapters or standard
   library equivalents when possible.
6. Create parity tests from examples, templates, fixtures, or sample data. Keep
   runtime dependencies bundled, standard, or explicitly documented.
7. Document any missing behavior as an explicit assumption.
8. If the user requested script helpers, implement and test same-language
   functions under `scripts/` before sharing the skill. Do not ship functions
   that still raise placeholder errors.

## Suggested Standalone Function Shape

- Direct exported function such as `renderSql(...)`, `buildDag(...)`, or
  `parse_record(...)`, matching the skill's selected language.
- Small dataclasses or typed dictionaries for config and records.
- Pure functions for parsing, transformation, template rendering, and output.
- Adapter layer for databases, APIs, object stores, schedulers, or filesystem
  writes.
- CLI wrapper only at the edge, and only when requested.

## Verification

- Write fixture tests against each user-facing function.
- Include happy-path, invalid input, edge case, and external-service mock cases
  where relevant.
- If the generated skill includes a CLI wrapper, test the wrapper separately
  from the direct function API.

## Dependency Policy

- Prefer standard library or minimal dependencies for each skill function.
- Use third-party dependencies only when they are essential to the capability.
- Isolate external services behind adapters so tests can use local fixtures.
- Preserve security-sensitive behavior such as credential handling, SQL
  parameterization, path validation, and destructive-operation guards.
```
"""


def script_base_from_scope(scope: str) -> str:
    clean = scope.replace("\\", "/").strip().strip("/")
    parts = [part for part in clean.split("/") if part and part not in {".", ".."}]
    if not parts:
        parts = ["repo_capability"]
    if "." in parts[-1]:
        stems = [Path(parts[-1]).stem]
    else:
        stems = parts[-2:]
    base = "_".join(stems)
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_").lower()
    base = re.sub(r"_{2,}", "_", base) or "repo_capability"
    if base[0].isdigit():
        base = f"capability_{base}"
    return base


def snake_identifier(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    value = re.sub(r"_{2,}", "_", value) or "run_capability"
    if value[0].isdigit():
        value = f"run_{value}"
    return value


def camel_identifier(value: str) -> str:
    parts = [part for part in snake_identifier(value).split("_") if part]
    if not parts:
        return "runCapability"
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def pascal_identifier(value: str) -> str:
    return "".join(part.capitalize() for part in snake_identifier(value).split("_") if part) or "RunCapability"


def function_name_from_scope(scope: str, language: str) -> str:
    base = snake_identifier(source_neutral_module_name(scope))
    if language in {"javascript", "typescript"}:
        return camel_identifier(base)
    if language == "go":
        return pascal_identifier(base)
    return snake_identifier(base)


def script_filename_from_scope(scope: str, language: str, used: set[str]) -> str:
    base = snake_identifier(source_neutral_module_name(scope))
    extension = SCRIPT_OUTPUT_EXTENSIONS.get(language, ".py")
    name = f"{base}{extension}"
    if name not in used:
        used.add(name)
        return name
    index = 2
    while True:
        candidate = f"{base}_{index}{extension}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        index += 1


def paths_for_scope(root: Path, files: list[Path], scope: str, limit: int = 8) -> list[str]:
    scope_norm = scope.replace("\\", "/").strip().strip("/").lower()
    matches = []
    for path in files:
        relative = rel(path, root)
        lowered = relative.lower()
        if lowered == scope_norm or lowered.startswith(f"{scope_norm}/"):
            matches.append(relative)

    if not matches:
        candidate = root / scope
        if candidate.exists():
            try:
                matches.append(rel(candidate, root))
            except ValueError:
                pass

    def rank(path: str) -> tuple[int, int, str]:
        suffix = Path(path).suffix.lower()
        if suffix in SOURCE_EXTS:
            tier = 0
        elif suffix in {".sql", ".yaml", ".yml", ".json", ".toml"}:
            tier = 1
        elif suffix == ".md":
            tier = 3
        else:
            tier = 2
        return (tier, path.count("/"), path)

    return sorted(dict.fromkeys(matches), key=rank)[:limit]


def primary_script_language(files: list[Path]) -> str:
    counts: Counter[str] = Counter()
    for path in files:
        language = SCRIPT_LANGUAGE_EXTENSIONS.get(path.suffix.lower())
        if language:
            counts[language] += 1
    if not counts:
        return "python"
    return counts.most_common(1)[0][0]


def language_for_script_target(
    root: Path,
    files: list[Path],
    scope: str,
    preferred_language: str,
) -> str:
    if preferred_language != "auto":
        return preferred_language
    for evidence_path in paths_for_scope(root, files, scope):
        language = SCRIPT_LANGUAGE_EXTENSIONS.get(Path(evidence_path).suffix.lower())
        if language:
            return language
    return primary_script_language(files)


def quoted_list(items: list[str], quote: str = '"') -> str:
    if not items:
        return ""
    return ", ".join(f"{quote}{item}{quote}" for item in items)


def python_function_code(
    script_path: str,
    function_name: str,
    evidence_paths: list[str],
    api_shape: str,
) -> str:
    cli = ""
    if api_shape in {"cli", "both"}:
        cli = f'''

def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", dest="input_data", help="Input value or file path.")
    args = parser.parse_args()
    result = {function_name}(args.input_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    return f'''"""Standalone callable capability functions for {script_path}.

Fill this module from bundled skill references before sharing the generated
skill. Keep it self-contained.
"""

from __future__ import annotations

from typing import Any


def {function_name}(input_data: Any = None, config: dict[str, Any] | None = None) -> Any:
    """Run this capability.

    Implement this function from the bundled capability map, examples, templates,
    and tests. Preserve the documented inputs, outputs, validation, and errors.
    """
    raise NotImplementedError("Implement and test this same-language function before shipping.")
{cli}'''


def typescript_function_code(
    script_path: str,
    function_name: str,
    evidence_paths: list[str],
    api_shape: str,
) -> str:
    cli = ""
    if api_shape in {"cli", "both"}:
        cli = f'''

if (import.meta.url === `file://${{process.argv[1]}}`) {{
  const result = await {function_name}(process.argv[2]);
  console.log(JSON.stringify(result, null, 2));
}}
'''
    return f'''/**
 * Standalone callable capability functions for {script_path}.
 *
 * Fill this module from bundled skill references before sharing the generated
 * skill. Keep it self-contained.
 */

export type CapabilityConfig = Record<string, unknown>;

export async function {function_name}(
  inputData: unknown = undefined,
  config: CapabilityConfig = {{}},
): Promise<unknown> {{
  void inputData;
  void config;
  throw new Error("Implement and test this same-language function before shipping.");
}}
{cli}'''


def javascript_function_code(
    script_path: str,
    function_name: str,
    evidence_paths: list[str],
    api_shape: str,
) -> str:
    cli = ""
    if api_shape in {"cli", "both"}:
        cli = f'''

if (import.meta.url === `file://${{process.argv[1]}}`) {{
  const result = await {function_name}(process.argv[2]);
  console.log(JSON.stringify(result, null, 2));
}}
'''
    return f'''/**
 * Standalone callable capability functions for {script_path}.
 *
 * Fill this module from bundled skill references before sharing the generated
 * skill. Keep it self-contained.
 */

export async function {function_name}(inputData = undefined, config = {{}}) {{
  void inputData;
  void config;
  throw new Error("Implement and test this same-language function before shipping.");
}}
{cli}'''


def go_function_code(
    script_path: str,
    function_name: str,
    evidence_paths: list[str],
    api_shape: str,
) -> str:
    return f'''// Package scripts contains standalone callable capability functions for {script_path}.
package scripts

import "fmt"

// {function_name} runs this capability.
// Implement it from the bundled capability map, examples, templates, and tests before sharing.
func {function_name}(inputData any, config map[string]any) (any, error) {{
	return nil, fmt.Errorf("implement and test this same-language function before shipping")
}}
'''


def rust_function_code(
    script_path: str,
    function_name: str,
    evidence_paths: list[str],
    api_shape: str,
) -> str:
    return f'''//! Standalone callable capability functions for {script_path}.
//! Fill this module from bundled skill references before sharing the generated skill.

pub fn {function_name}(input_data: &str) -> Result<String, String> {{
    let _ = input_data;
    Err("implement and test this same-language function before shipping".to_string())
}}
'''


def ruby_function_code(
    script_path: str,
    function_name: str,
    evidence_paths: list[str],
    api_shape: str,
) -> str:
    return f'''# Standalone callable capability functions for {script_path}.
# Fill this file from bundled skill references before sharing the generated skill.

def {function_name}(input_data = nil, config = {{}})
  raise NotImplementedError, 'Implement and test this same-language function before shipping.'
end
'''


def starter_function_code(
    language: str,
    script_path: str,
    function_name: str,
    evidence_paths: list[str],
    api_shape: str,
) -> str:
    if language == "typescript":
        return typescript_function_code(script_path, function_name, evidence_paths, api_shape)
    if language == "javascript":
        return javascript_function_code(script_path, function_name, evidence_paths, api_shape)
    if language == "go":
        return go_function_code(script_path, function_name, evidence_paths, api_shape)
    if language == "rust":
        return rust_function_code(script_path, function_name, evidence_paths, api_shape)
    if language == "ruby":
        return ruby_function_code(script_path, function_name, evidence_paths, api_shape)
    return python_function_code(script_path, function_name, evidence_paths, api_shape)


def build_script_artifacts(
    root: Path,
    files: list[Path],
    script_focus_paths: tuple[str, ...],
    preferred_language: str,
    api_shape: str,
) -> list[dict[str, object]]:
    used_names: set[str] = set()
    artifacts: list[dict[str, object]] = []
    for scope in script_focus_paths[:8]:
        language = language_for_script_target(root, files, scope, preferred_language)
        file_name = script_filename_from_scope(scope, language, used_names)
        script_path = f"scripts/{file_name}"
        function_name = function_name_from_scope(scope, language)
        evidence = paths_for_scope(root, files, scope)
        role = infer_capability_role(scope)
        artifacts.append(
            {
                "scope": scope,
                "language": language,
                "path": script_path,
                "function_name": function_name,
                "evidence": evidence,
                "role": role,
                "code": starter_function_code(language, script_path, function_name, evidence, api_shape),
            }
        )
    return artifacts


def write_script_artifacts(
    output_dir: Path,
    artifacts: list[dict[str, object]],
    overwrite: bool,
) -> list[Path]:
    written: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts:
        relative = Path(str(artifact["path"]))
        name = relative.name
        target = output_dir / name
        if target.exists() and not overwrite:
            raise FileExistsError(f"script output exists; pass --script-overwrite to replace it: {target}")
        target.write_text(str(artifact["code"]).rstrip() + "\n", encoding="utf-8", newline="\n")
        written.append(target)
    return written


def callable_scripts_block(
    source_paths: list[str],
    focus_paths: tuple[str, ...],
    script_focus_paths: tuple[str, ...],
    script_note: str,
    script_language: str,
    script_api: str,
    script_output_dir: str | None,
    script_artifacts: list[dict[str, object]],
) -> str:
    if not script_focus_paths:
        candidate_scopes = list(focus_paths) or source_paths[:8]
        candidates = [f"{scope}: {infer_capability_role(scope)}" for scope in candidate_scopes[:12]]
        return f"""~~~markdown
# Callable Function Files

No `--script-focus` paths were provided. If the generated skill should include
callable same-language functions, choose stable, repeatable capabilities and
rerun the scanner with one or more `--script-focus PATH_OR_LABEL` values and a
`--script-output-dir` pointing at the generated skill's `scripts/` directory.

## Candidate Areas

{bullet_list(candidates, "No script candidates detected.", quote=False)}

## Shipping Rule

Only include files under `scripts/` after implementing and testing direct
callable functions. Do not ship placeholder files, absolute generation paths,
or undocumented wrappers/dependencies.
~~~
"""

    contract_lines = []
    for artifact in script_artifacts:
        capability_name = human_title_from_scope(str(artifact["scope"]))
        contract_lines.append(
            "- `{path}` exports `{function}` in `{language}` for **{capability}** "
            "({role}).".format(
                path=artifact["path"],
                function=artifact["function_name"],
                language=artifact["language"],
                capability=capability_name,
                role=artifact["role"],
            )
        )

    return f"""~~~markdown
# Callable Function Files

Use this reference as an index for completed function files under `scripts/`.
This skill should ship same-language callable functions, not only Markdown
descriptions. Function files must implement the behavior described by the
capability map, examples, templates, and tests.

## User Script Note

{script_note or "None provided."}

## Function API Summary

- Script language: `{script_language}`
- Script API shape: `{script_api}`
- Function files live under this skill's `scripts/` directory.

## Requested Script Contracts

{chr(10).join(contract_lines)}

## Shipping Rule

- Keep function files standalone and portable.
- Prefer same-language exports that other code can import directly.
- Do not require code outside this skill unless the user explicitly requested a
  wrapper.
- Preserve security-sensitive behavior such as credential handling, SQL
  parameterization, path validation, and destructive-operation guards.
- Run each function through at least one fixture or parity test before
  sharing this skill.
- Do not ship function files that still raise placeholder `NotImplementedError`
  or equivalent placeholder errors.
~~~
"""


def task_playbook_block(
    root: Path,
    source_paths: list[str],
    test_paths: list[str],
    commands: list[str],
    focus_paths: tuple[str, ...],
    scope_note: str,
) -> str:
    return f"""```markdown
# Task Playbook

Use this playbook with this skill's own capability docs and function files.

## Default Flow

1. Identify the task category from the user's request.
2. Start with `capability-map.md` to find the relevant capability.
3. Use `references/callable-scripts.md` to locate the bundled function, when one exists.
4. Use `implementation-blueprint.md` for behavior rules and dependency policy.
5. Run the narrowest fixture or parity test for the capability.
6. If behavior is underspecified, ask the user for inputs, examples, or expected
   outputs instead of guessing unspecified implementation details.

## Common Task Categories

- Function behavior: update the bundled function and its fixture tests.
- Template or SQL rendering: verify generated text exactly and include injection
  or escaping tests when relevant.
- Data transformation: verify schemas, null handling, ordering, and idempotency.
- Integration adapter: isolate external services behind mocks or local fixtures.
- Docs-only change: update capability docs, examples, and contracts only.
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
    other_paths: list[str],
    focus_paths: tuple[str, ...],
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
    scope_note: str,
) -> str:
    capability_modules = source_neutral_capability_inventory(
        source_paths + config_paths + other_paths + doc_paths + manifest_paths,
        focus_paths,
    )

    return f"""```markdown
# Capability Conventions

This reference describes how this skill's capabilities are organized and used.

## Capability Areas

{bullet_list(capability_modules, "No source-neutral capability areas detected yet.", quote=False)}

## Runtime And Language Clues

{bullet_list(tooling)}

## Architecture Pattern

Describe the final skill's conceptual modules, data flow, and public function
surface in source-neutral language.

## Function Style

Record naming, input/output, error handling, logging, dependency, and generated
file rules for the bundled functions.

## Testing

Record fixture shape, mocks, commands, and acceptance expectations for the
skill's own functions.

## Pitfalls

List unsafe operations, irreversible writes, credential handling, external
service assumptions, and other user-facing gotchas.
```
"""


def consultation_plan_block(
    capability_paths: list[str],
    focus_paths: tuple[str, ...],
    script_artifacts: list[dict[str, object]],
    full_scan: bool,
) -> str:
    capabilities = source_neutral_capability_inventory(capability_paths, focus_paths)
    function_lines = []
    for artifact in script_artifacts:
        function_lines.append(
            "- `{function}` in `{path}` ({language}) for {capability}".format(
                function=artifact["function_name"],
                path=artifact["path"],
                language=artifact["language"],
                capability=human_title_from_scope(str(artifact["scope"])),
            )
        )
    return f"""```markdown
# User Approval Proposal

Before creating the final skill, show the user a source-neutral proposal and ask
what should be included, renamed, omitted, or packaged as functions.

## Scan Coverage

- Full scan used: `{full_scan}`
- Source details are generation-only and must not appear in the final skill.

## Candidate Capability Modules

{bullet_list(capabilities, "No source-neutral capability candidates detected yet.", quote=False)}

## Candidate Function Files

{bullet_list(function_lines, "No function files requested yet.", quote=False)}

## Decisions Needed From User

- Which capability modules should appear in `references/capability-map.md`?
- Which module details should be expanded into `references/capability-conventions.md`?
- Which capabilities should become same-language functions under `scripts/`?
- Which capabilities should be omitted, merged, or renamed?
- What examples, input/output contracts, or edge cases should be included?
- Should the final skill include an auditable source map? Default: no.

## Final Skill Privacy Rule

The final skill must speak as if these are its own native capabilities. Do not
include source project names, source paths, source file names, source maps,
generation evidence, or phrases like "learned from" and "original repository".
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
            f"`<skills-dir>/{skill_name}/references/capability-conventions.md` for longer facts",
        ]
    if target == "claude":
        return [
            f"Project: `.claude/skills/{skill_name}/SKILL.md`",
            f"Personal: `~/.claude/skills/{skill_name}/SKILL.md`",
            f"Supporting files live beside `SKILL.md`, such as `references/capability-conventions.md`.",
        ]
    return [
        f"Project: `.opencode/skills/{skill_name}/SKILL.md`",
        f"Global: `~/.config/opencode/skills/{skill_name}/SKILL.md`",
        "OpenCode also discovers compatible `.claude/skills/` and `.agents/skills/` layouts.",
    ]


def platform_frontmatter(
    skill_name: str, repo_name: str, target: str, skill_purpose: str
) -> str:
    subject = platform_subject(target)
    if skill_purpose == "capability":
        description = (
            "Perform the domain capabilities bundled with this skill as "
            f"same-language functions or tools. Use when {subject} needs these "
            "workflows, templates, data transforms, integrations, or domain "
            "functions directly and self-containedly."
        )
    else:
        description = (
            f"Work in the {repo_name} repository using its observed development "
            f"conventions. Use when {subject} needs to modify, review, test, debug, "
            "or explain code in this repository while following its README, "
            "architecture, commands, style, and test practices."
        )
    if target == "opencode":
        metadata = (
            f"  kind: repo-{skill_purpose}\n"
            "  source_visibility: hidden\n"
            if skill_purpose == "capability"
            else f"  repo: {repo_name}\n  kind: repo-{skill_purpose}\n"
        )
        return (
            "---\n"
            f"name: {skill_name}\n"
            f"description: {description}\n"
            "metadata:\n"
            f"{metadata}"
            "---"
        )
    return (
        "---\n"
        f"name: {skill_name}\n"
        f"description: {description}\n"
        "---"
    )


def make_skill_draft(
    skill_name: str,
    repo_name: str,
    target: str,
    knowledge_depth: str,
    skill_purpose: str,
) -> str:
    display = skill_name.replace("-", " ").title()
    subject = platform_subject(target)
    article = platform_article(target)
    frontmatter = platform_frontmatter(skill_name, repo_name, target, skill_purpose)
    if knowledge_depth == "self-contained":
        if skill_purpose == "capability":
            reference_step = (
                "Read the bundled `references/capability-map.md`, "
                "`references/implementation-blueprint.md`, "
                "`references/capability-conventions.md`, optional "
                "`references/callable-scripts.md`, and same-language files under "
                "`scripts/` before implementing capability functions."
            )
            playbook_step = (
                "Use the capability map and implementation blueprint to design "
                "standalone same-language functions."
            )
        else:
            reference_step = (
                "Read the bundled `references/repo-conventions.md`, "
                "`references/source-map.md`, and `references/task-playbook.md` before "
                "making non-trivial changes."
            )
            playbook_step = (
                "Use the bundled task playbook to choose the likely implementation and "
                "tests before opening files."
            )
        if skill_purpose == "capability":
            missing_reference_text = "any bundled capability reference or function file is missing"
            missing_action_text = "say the skill is incomplete and ask for the missing contract, example, or expected output."
        else:
            missing_reference_text = "any bundled reference is missing"
            missing_action_text = "say the skill is incomplete instead of rediscovering conventions from the original generation repo."
    else:
        if skill_purpose == "capability":
            reference_step = (
                "Read the bundled `references/capability-map.md` and "
                "`references/capability-conventions.md`, plus optional "
                "`references/callable-scripts.md` and `scripts/`, before writing "
                "or using capability functions."
            )
            playbook_step = (
                "Use the bundled capability notes to design standalone functions."
            )
        else:
            reference_step = (
                "Read the bundled `references/repo-conventions.md` before making "
                "non-trivial changes."
            )
            playbook_step = (
                "Use the bundled conventions to choose likely implementation and test "
                "areas before opening files."
            )
        if skill_purpose == "capability":
            missing_reference_text = "`references/capability-conventions.md` is missing"
            missing_action_text = "say the skill is incomplete and ask for the missing contract, example, or expected output."
        else:
            missing_reference_text = "`references/repo-conventions.md` is missing"
            missing_action_text = "say the skill is incomplete instead of rediscovering conventions from the original generation repo."
    if skill_purpose == "capability":
        overview = (
            "Use this skill's bundled capability docs and same-language functions "
            "directly. Treat the documented capabilities as native to this skill."
        )
        independence_step = (
            "Treat the bundled docs, examples, tests, and function files as the "
            "source of truth for this skill."
        )
        checkout_step = (
            "If a required behavior is not documented, ask for the missing input, "
            "example, expected output, or acceptance criteria."
        )
        output_rule = (
            "Keep outputs within the documented capability contracts and bundled function APIs."
        )
        workflow_tail = (
            "5. Use the contracts, templates, examples, and tests recorded in the bundled references.\n"
            "6. Prefer direct same-language function exports and minimal dependencies.\n"
            "7. Preserve behavior, inputs, outputs, validation, and error handling described in the capability references.\n"
            "8. Build parity tests from examples, fixtures, templates, and observed expected outputs.\n"
            "9. If completed function files are bundled under `scripts/`, import and reuse those functions for matching operations."
        )
        script_rule = (
            "Do not treat function starter files as complete tools; bundled "
            "functions must be implemented and tested."
        )
    else:
        overview = (
            "Use the bundled repository conventions before making changes. This "
            "skill is portable: it must not depend on the original local repository "
            "path used during generation."
        )
        independence_step = (
            "Do not fetch, reopen, or depend on the original repository path used to generate this skill."
        )
        checkout_step = (
            "Open the user's checkout only to apply edits, verify drift, or inspect "
            "code that is missing from the bundled knowledge pack."
        )
        output_rule = (
            "Do not introduce new dependencies, frameworks, or file organization "
            "patterns without repository evidence."
        )
        workflow_tail = (
            "5. Use the commands, conventions, and test evidence recorded in the bundled references.\n"
            "6. Follow existing repository interfaces, dependencies, naming, and file organization.\n"
            "7. Preserve behavior, validation, and error handling unless the user asks for a behavior change.\n"
            "8. Add or update tests that match the repository's observed testing style.\n"
            "9. If completed helper functions are bundled under `scripts/`, use them only for their documented repeatable operations."
        )
        script_rule = (
            "Do not rely on function starter files as repository facts; bundled "
            "functions must be implemented and tested."
        )
    if skill_purpose == "capability":
        explain_rule = (
            "Cite bundled capability sections, function APIs, examples, or tests when explaining decisions."
        )
        uncertainty_rule = (
            "Mark undocumented behavior as an assumption and ask for a concrete contract or example."
        )
    else:
        explain_rule = (
            "Cite exact files, commands, or conventions when explaining repository-specific decisions."
        )
        uncertainty_rule = (
            "Mark uncertain conventions as assumptions instead of presenting them as rules."
        )
    return f"""```markdown
{frontmatter}

# {display}

## Overview

{overview}

## Workflow

1. {reference_step}
2. {independence_step}
3. {playbook_step}
4. {checkout_step}
{workflow_tail}

## Output Rules

- {explain_rule}
- {uncertainty_rule}
- {output_rule}
- {script_rule}
- Use this as {article} {subject} skill and keep platform-specific metadata minimal.
- If {missing_reference_text} or still contains placeholder text, {missing_action_text}
```
"""


def build_platform_sections(
    root: Path, skill_name: str, target: str, knowledge_depth: str, skill_purpose: str
) -> str:
    targets = TARGETS if target == "all" else (target,)
    sections = []
    for platform in targets:
        platform_skill_name = normalize_skill_name(skill_name, platform)
        install_notes = bullet_list(
            platform_install_notes(platform_skill_name, platform), quote=False
        )
        skill_block = make_skill_draft(
            platform_skill_name, root.name, platform, knowledge_depth, skill_purpose
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
    focus_paths: tuple[str, ...],
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
    scope_note: str,
    skill_purpose: str,
    script_focus_paths: tuple[str, ...],
    script_note: str,
    script_language: str,
    script_api: str,
    script_output_dir: str | None,
    script_artifacts: list[dict[str, object]],
    full_scan: bool,
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
    other_paths = [rel(path, root) for path in files_by_kind["other"][:20]]

    counts = Counter(classify(path, root) for path in files)
    capability_paths = source_paths + config_paths + other_paths + doc_paths + manifest_paths
    consultation_plan = consultation_plan_block(
        capability_paths, focus_paths, script_artifacts, full_scan
    )
    platform_sections = build_platform_sections(
        root, skill_name, target, knowledge_depth, skill_purpose
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
        other_paths,
        focus_paths,
        include_paths,
        exclude_paths,
        scope_note,
    )
    source_map = ""
    task_playbook = ""
    capability_map = ""
    implementation_blueprint = ""
    callable_scripts = ""

    if knowledge_depth == "self-contained":
        source_map = source_map_block(
            root, files_by_kind["source"], files_by_kind["test"], max_bytes
        )
        task_playbook = task_playbook_block(
            root, source_paths, test_paths, commands, focus_paths, scope_note
        )

    if skill_purpose == "capability":
        capability_map = capability_map_block(
            root,
            commands,
            tooling,
            doc_paths,
            manifest_paths,
            config_paths,
            source_paths,
            test_paths,
            other_paths,
            focus_paths,
            include_paths,
            exclude_paths,
            scope_note,
            script_focus_paths,
            script_note,
        )
        implementation_blueprint = implementation_blueprint_block(
            commands,
            source_paths,
            test_paths,
            focus_paths,
            scope_note,
            script_focus_paths,
            script_note,
        )
        callable_scripts = callable_scripts_block(
            source_paths,
            focus_paths,
            script_focus_paths,
            script_note,
            script_language,
            script_api,
            script_output_dir,
            script_artifacts,
        )

    return f"""# Capability Skill Distillation Draft: {skill_name}

This draft has two kinds of content:

- **Generation-only analysis** may mention source paths and evidence. Do not copy
  it into the final skill.
- **Final skill templates** must be source-neutral. The generated skill should
  present the distilled capabilities as its own native capabilities.

Training project name (generation-only): `{repo_name}`

Target: `{target}`

Knowledge depth: `{knowledge_depth}`

Skill purpose: `{skill_purpose}`

Full scan: `{full_scan}`

Final skill privacy: final generated skill content must not include source
project names, source paths, source file names, or generation evidence.

User scan scope: {scope_note or "not provided"}

Focus paths: {", ".join(f"`{item}`" for item in focus_paths) or "none"}

Extra include paths: {", ".join(f"`{item}`" for item in include_paths) or "none"}

Extra exclude paths: {", ".join(f"`{item}`" for item in exclude_paths) or "none"}

Script focus paths: {", ".join(f"`{item}`" for item in script_focus_paths) or "none"}

Script note: {script_note or "not provided"}

Script language: `{script_language}`

Script API: `{script_api}`

Script output dir: `{script_output_dir or "not provided"}`

Generated function files: {", ".join(f"`{artifact['path']}`" for artifact in script_artifacts) or "none"}

## Scan Summary

- Text-like files scanned: {len(files)}
- Docs: {counts.get("doc", 0)}
- Manifests: {counts.get("manifest", 0)}
- Configs: {counts.get("config", 0)}
- Source files: {counts.get("source", 0)}
- Test files: {counts.get("test", 0)}
- Other text files: {counts.get("other", 0)}

## Required User Approval Checkpoint

Do not create the final skill until the user approves or edits this proposal.

{consultation_plan}

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

### Other Text Evidence

{bullet_list(other_paths)}

## Generation Analysis To Complete Manually

- Architecture and subsystem boundaries
- Setup and environment variables
- Build, test, lint, format, and release commands
- Naming, import, error handling, logging, and API patterns
- Test fixture and mock conventions
- Generated, vendored, migration, or lock files that require special handling
- Risky commands or files future agents should avoid changing casually
- Convert source-specific findings into source-neutral capability names before
  writing the final skill.
- Replace placeholders in the source-neutral references before sharing the generated skill.
- Do not ship a generated skill that tells future users to inspect generation materials.

## Starter Generated Skills

{platform_sections}

## Source-Neutral `references/capability-conventions.md`

Copy this source-neutral reference into the target capability skill and fill
the placeholder sections after user approval.

{portable_reference}

## Capability `references/capability-map.md`

Copy this capability map into the target skill when the purpose is
`capability`.

{capability_map or "Not generated. Re-run with `--skill-purpose capability`."}

## Self-Contained `references/source-map.md`

Draft-only evidence for the agent creating the skill. For capability skills,
do not ship this to end users by default; internalize the relevant behavior into
`capability-map.md`, `implementation-blueprint.md`, tests, and same-language
function files under `scripts/`. For development skills, you may copy it when a
source map is useful.

{source_map or "Not generated. Re-run with `--knowledge-depth self-contained`."}

## Capability `references/implementation-blueprint.md`

Copy this implementation blueprint into the target skill when the purpose is
`capability`.

{implementation_blueprint or "Not generated. Re-run with `--skill-purpose capability`."}

## Capability `references/callable-scripts.md`

Copy this function index into the target skill when the user wants callable
helpers. The actual usable artifacts should be same-language function files
under `scripts/`; implement them before sharing.

{callable_scripts or "Not generated. Re-run with `--skill-purpose capability`."}

## Self-Contained `references/task-playbook.md`

Copy this bundled playbook into the target skill when using
`--knowledge-depth self-contained`.

{task_playbook or "Not generated. Re-run with `--knowledge-depth self-contained`."}
"""


def main() -> int:
    args = parse_args()
    root = Path(args.repo).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: --repo must be an existing directory: {root}", file=sys.stderr)
        return 2

    output_path = None
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        if output_path.exists() and not args.overwrite:
            print(f"error: output exists; pass --overwrite to replace it: {output_path}", file=sys.stderr)
            return 3

    skill_name = normalize_skill_name(args.skill_name)
    focus_paths = normalize_scope_paths(args.focus)
    include_paths = normalize_scope_paths(args.include)
    exclude_paths = normalize_scope_paths(args.exclude)
    script_focus_paths = normalize_scope_paths(args.script_focus)
    max_files = 0 if args.full_scan else args.max_files
    files = list(
        iter_files(
            root,
            max_files,
            focus_paths,
            include_paths,
            exclude_paths,
            include_unknown_text=args.full_scan,
        )
    )
    script_artifacts = build_script_artifacts(
        root,
        files,
        script_focus_paths,
        args.script_language,
        args.script_api,
    )
    if args.script_output_dir and script_artifacts:
        try:
            written = write_script_artifacts(
                Path(args.script_output_dir).expanduser().resolve(),
                script_artifacts,
                args.script_overwrite,
            )
        except FileExistsError as error:
            print(f"error: {error}", file=sys.stderr)
            return 4
        for path in written:
            print(f"Wrote function file: {path}")
    markdown = build_markdown(
        root,
        skill_name,
        args.target,
        files,
        args.knowledge_depth,
        args.max_bytes,
        focus_paths,
        include_paths,
        exclude_paths,
        args.scope_note,
        args.skill_purpose,
        script_focus_paths,
        args.script_note,
        args.script_language,
        args.script_api,
        args.script_output_dir,
        script_artifacts,
        args.full_scan,
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8", newline="\n")
        print(f"Wrote draft: {output_path}")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
