from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER = REPO_ROOT / "docs" / "ops" / "tier1-retrofit-ledger.json"
CHECK = REPO_ROOT / "scripts" / "check-tier1-ledger.py"


def test_co4_tier1_ledger_static_check_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECK), "--ledger", str(LEDGER)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "PASS: 2 Townlight/townlight_code CO-4 target release(s) are ledgered" in result.stdout


def test_co4_tier1_ledger_marks_target_tags_as_pre_gate_only() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = ledger["entries"]

    assert ledger["upstream_attested_baseline"]["tag"] == "v0.22.1"
    assert [entry["tag"] for entry in entries] == ["v0.1.17", "v0.1.18"]
    assert all(entry["ledger_status"] == "pre_gate_no_attestation_do_not_promote" for entry in entries)
    assert all(entry["attestation_status"] == "none_pre_gate" for entry in entries)
    assert all(
        "release-attestation.json" not in {asset["name"] for asset in entry["release_assets"]}
        for entry in entries
    )
