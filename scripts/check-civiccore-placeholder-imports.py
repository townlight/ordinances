"""Fail if CivicCode source imports unreleased CivicCore placeholder packages."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDERS = {
    "rbac",
    "audit",
    "search",
    "notifications",
    "connectors",
    "exemptions",
    "onboarding",
    "catalog",
    "verification",
}
SOURCE_ROOTS = [ROOT / "civiccode", ROOT / "tests"]


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for source_root in SOURCE_ROOTS:
        if source_root.exists():
            files.extend(source_root.rglob("*.py"))
    return files


def _imported_placeholder(node: ast.AST) -> str | None:
    if isinstance(node, ast.Import):
        for alias in node.names:
            parts = alias.name.split(".")
            if len(parts) >= 2 and parts[0] == "civiccore" and parts[1] in PLACEHOLDERS:
                return parts[1]
    if isinstance(node, ast.ImportFrom) and node.module:
        parts = node.module.split(".")
        if len(parts) >= 2 and parts[0] == "civiccore" and parts[1] in PLACEHOLDERS:
            return parts[1]
    return None


def main() -> int:
    failures: list[str] = []
    for path in _iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            placeholder = _imported_placeholder(node)
            if placeholder:
                rel = path.relative_to(ROOT)
                failures.append(
                    f"{rel}: civiccore.{placeholder} is not an approved CivicCode dependency yet. "
                    "See AGENTS.md section CivicCore placeholder warning."
                )
    if failures:
        print("PLACEHOLDER-IMPORT-CHECK: FAILED")
        for failure in failures:
            print(failure)
        return 1
    print(f"PLACEHOLDER-IMPORT-CHECK: PASSED ({len(_iter_python_files())} source files scanned)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
