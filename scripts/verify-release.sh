#!/usr/bin/env bash
set -euo pipefail

VERSION="1.0.8"

find_python() {
  local candidates=()
  if [[ -n "${CIVICCODE_RELEASE_PYTHON:-}" ]]; then
    candidates+=("${CIVICCODE_RELEASE_PYTHON}")
  fi
  command -v python3 >/dev/null 2>&1 && candidates+=("$(command -v python3)")
  command -v python >/dev/null 2>&1 && candidates+=("$(command -v python)")
  command -v py >/dev/null 2>&1 && candidates+=("py -3")
  [[ -x "/c/Windows/py.exe" ]] && candidates+=("/c/Windows/py.exe -3")
  [[ -x "/mnt/c/Windows/py.exe" ]] && candidates+=("/mnt/c/Windows/py.exe -3")
  if command -v powershell.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then
    local win_python
    win_python="$(powershell.exe -NoProfile -Command "(Get-Command python -ErrorAction SilentlyContinue).Source" 2>/dev/null | tr -d '\r' | head -n 1)"
    if [[ -n "$win_python" ]]; then
      candidates+=("$(wslpath -u "$win_python")")
    fi
  fi

  for candidate in "${candidates[@]}"; do
    if ${candidate} -c "import pytest, ruff, build" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(find_python)" || {
  echo "FAIL: Python launcher not found. Install Python or add python/python3/py to PATH." >&2
  exit 1
}

echo "==> Version surface check"
${PYTHON_BIN} - <<'PY'
from pathlib import Path
import tomllib

version = "1.0.8"
root = Path(".")
pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
assert pyproject["project"]["version"] == version, pyproject["project"]["version"]
namespace: dict[str, str] = {}
exec((root / "civiccode" / "__init__.py").read_text(encoding="utf-8"), namespace)
assert namespace["__version__"] == version, namespace["__version__"]
for path in [
    "README.md",
    "README.txt",
    "USER-MANUAL.md",
    "CHANGELOG.md",
    "docs/index.html",
    "SECURITY.md",
]:
    text = (root / path).read_text(encoding="utf-8")
    assert "0.1.0.dev0" not in text, f"stale dev version in {path}"
print("PASS: version surfaces synchronized")
PY

echo "==> Product test suite"
# Release-provenance gate is ignored here because it is exercised below inside
# the isolated virtualenv against the real CivicCore dependency path.
${PYTHON_BIN} -m pytest -q --ignore=tests/test_release_provenance_gate.py

if [[ "${CIVICCODE_SKIP_ISOLATED_PROVENANCE:-0}" == "1" ]]; then
  echo "==> Release-provenance tooling tests against CivicCore shared-ingestion dependency"
  echo "SKIP: isolated provenance test already ran in this CI job"
else
  echo "==> Release-provenance tooling tests against CivicCore shared-ingestion dependency"
  ${PYTHON_BIN} - <<'PY'
from __future__ import annotations

import shutil
import subprocess
import tempfile
import venv
from pathlib import Path

wheel_url = "https://github.com/CivicSuite/civiccore/releases/download/v1.2.0/civiccore-1.2.0-py3-none-any.whl#sha256=a94ce958e36fb03c8d961e4db4672ce5bcfa25765c57d75886e999cf15703ec7"
temp_dir = Path(tempfile.mkdtemp(prefix="civiccode-release-provenance-"))

try:
    venv.EnvBuilder(with_pip=True).create(temp_dir)
    candidates = [
        temp_dir / "Scripts" / "python.exe",
        temp_dir / "Scripts" / "python",
        temp_dir / "bin" / "python",
    ]
    venv_python = next((path for path in candidates if path.exists()), None)
    if venv_python is None:
        raise RuntimeError("could not locate release-provenance virtualenv python")

    subprocess.run(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "pytest",
            wheel_url,
        ],
        check=True,
    )
    subprocess.run(
        [str(venv_python), "-m", "pytest", "-q", "tests/test_release_provenance_gate.py"],
        check=True,
    )
finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
PY
fi

echo "==> Documentation gate"
bash scripts/verify-docs.sh

echo "==> Placeholder import gate"
${PYTHON_BIN} scripts/check-civiccore-placeholder-imports.py

echo "==> Ruff"
${PYTHON_BIN} -m ruff check .

echo "==> React frontend build"
if command -v npm >/dev/null 2>&1; then
  npm ci
  npm run typecheck
  npm run build
else
  echo "FAIL: npm not found. Install Node.js to typecheck and build the CivicCode React frontend." >&2
  exit 1
fi

echo "==> Public browser QA"
if command -v node >/dev/null 2>&1; then
  if [[ "${PYTHON_BIN}" == /mnt/c/* || "${PYTHON_BIN}" == /c/* ]]; then
    if command -v powershell.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then
      WIN_ROOT="$(wslpath -w "$PWD")"
      WIN_PYTHON="$(wslpath -w "${PYTHON_BIN}")"
      powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
        "Set-Location -LiteralPath '${WIN_ROOT}'; [Environment]::SetEnvironmentVariable('PYTHON', '${WIN_PYTHON}', 'Process'); node scripts/browser-public-surfaces-qa.cjs"
    else
      PYTHON="${PYTHON_BIN}" node scripts/browser-public-surfaces-qa.cjs
    fi
  else
    PYTHON="${PYTHON_BIN}" node scripts/browser-public-surfaces-qa.cjs
  fi
else
  echo "FAIL: node not found. Install Node.js to run public browser QA." >&2
  exit 1
fi

echo "==> Build artifacts"
rm -rf dist
${PYTHON_BIN} -m build
${PYTHON_BIN} - <<'PY'
from pathlib import Path
import hashlib

dist = Path("dist")
wheel = dist / "civiccode-1.0.8-py3-none-any.whl"
sdist = dist / "civiccode-1.0.8.tar.gz"
assert wheel.exists(), f"missing {wheel}"
assert sdist.exists(), f"missing {sdist}"
lines = []
for path in [wheel, sdist]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {path.name}\n")
(dist / "SHA256SUMS.txt").write_text("".join(lines), encoding="utf-8")
print("PASS: build artifacts and SHA256SUMS.txt created")
PY

echo "VERIFY-RELEASE: PASSED"
