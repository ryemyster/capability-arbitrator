"""
File: cleanup_generated_artifacts.py
Purpose: Removes generated local files that should not live in source control.
Why it exists: Developers need one safe reset command for telemetry, test outputs,
and Python caches without deleting source code or virtual environments.
How it works: Walks known generated paths, deletes matching files/directories,
and supports a dry-run mode for review before cleanup.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GENERATED_PATHS = [
    ".pytest_cache",
    ".google-agents-cli",
    ".ruff_cache",
    ".mypy_cache",
    ".ty",
    ".uv-cache",
    ".coverage",
    ".mypy_cache",
    "dist",
    "build",
    "dist/*",
    "htmlcov",
    "coverage.xml",
    "adk_debug.yaml",
    ".google-agents-cli/adk_debug.yaml",
    "deployment_metadata.json",
    "telemetry_db.json",
    "app/telemetry_db.json",
    "tests/load_test/.results",
    "artifacts/",
]

GENERATED_PATTERNS = [
    "**/__pycache__",
    "**/*.pyc",
    "**/*.pyo",
    "**/.DS_Store",
]

PROTECTED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
}


def _is_protected(path: Path) -> bool:
    """Return True when a path is inside a directory this script must not delete."""
    try:
        relative = path.resolve().relative_to(ROOT)
    except ValueError:
        return True
    return any(part in PROTECTED_PARTS for part in relative.parts)


def _iter_targets() -> list[Path]:
    """Collect all generated paths that currently exist in the repository."""
    targets = [ROOT / item for item in GENERATED_PATHS if (ROOT / item).exists()]
    for pattern in GENERATED_PATTERNS:
        targets.extend(path for path in ROOT.glob(pattern) if path.exists())
    unique = sorted(
        {path.resolve(): path for path in targets if not _is_protected(path)}.values(),
        key=lambda path: len(path.relative_to(ROOT).parts),
    )
    selected: list[Path] = []
    for path in unique:
        if not any(_is_relative_to(path, parent) for parent in selected):
            selected.append(path)
    return sorted(selected, key=lambda path: str(path.relative_to(ROOT)))


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Return True when path is the same as parent or lives inside parent."""
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _remove_path(path: Path) -> None:
    """Delete one generated file or directory."""
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def cleanup(dry_run: bool) -> int:
    """Remove generated artifacts and return the number of paths found."""
    targets = _iter_targets()
    if not targets:
        print("No generated artifacts found.")
        return 0

    action = "Would remove" if dry_run else "Removing"
    for path in targets:
        print(f"{action}: {path.relative_to(ROOT)}")
        if not dry_run:
            _remove_path(path)
    print(
        f"{'Found' if dry_run else 'Removed'} {len(targets)} generated artifact path(s)."
    )
    return len(targets)


def main() -> None:
    """Parse command-line flags and run cleanup."""
    parser = argparse.ArgumentParser(
        description="Remove generated local artifacts such as telemetry, caches, and test outputs."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting anything.",
    )
    args = parser.parse_args()
    cleanup(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
