"""Staff-facing operational readiness read model for CivicCode."""

from __future__ import annotations

from typing import Any


OPERATIONAL_READINESS_LANES = ("handoff", "import", "sync")
OPERATIONAL_READINESS_RECORD_TYPES = ("retry_queue", "replay_record", "delta_cursor")


def build_operational_readiness(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize existing operational retry/replay/cursor records for operators."""

    deduped_records = _dedupe_records(records)
    lanes = {
        lane: _lane_readiness(lane, [record for record in deduped_records if record["lane"] == lane])
        for lane in OPERATIONAL_READINESS_LANES
    }
    missing_lanes = [lane for lane, payload in lanes.items() if payload["status"] == "missing_state"]
    queued_lanes = [lane for lane, payload in lanes.items() if payload["queued_retry_count"] > 0]
    status = _overall_status(missing_lanes, queued_lanes, deduped_records)
    fixes = _overall_fixes(missing_lanes, queued_lanes, lanes, deduped_records)
    return {
        "status": status,
        "message": _status_message(status),
        "fixes": fixes,
        "counts": {
            "records": len(deduped_records),
            "retry_queue": _count_records(deduped_records, "retry_queue"),
            "replay_record": _count_records(deduped_records, "replay_record"),
            "delta_cursor": _count_records(deduped_records, "delta_cursor"),
            "lanes_with_state": sum(1 for payload in lanes.values() if payload["record_count"] > 0),
        },
        "lanes": lanes,
        "records": deduped_records,
        "data_source": {
            "kind": "existing_operational_state",
            "includes": ["handoff", "import", "sync"],
            "external_deployment_required": False,
            "network_required": False,
        },
        "code_answer_behavior": "not_available",
    }


def _lane_readiness(lane: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    queued_retries = [
        record
        for record in records
        if record["record_type"] == "retry_queue" and record["status"] == "queued"
    ]
    replay_records = [record for record in records if record["record_type"] == "replay_record"]
    delta_cursors = [record for record in records if record["record_type"] == "delta_cursor"]
    if queued_retries:
        status = "needs_attention"
    elif not records:
        status = "missing_state"
    else:
        status = "ready"
    return {
        "lane": lane,
        "status": status,
        "record_count": len(records),
        "queued_retry_count": len(queued_retries),
        "replay_count": len(replay_records),
        "delta_cursor_count": len(delta_cursors),
        "latest_record_at": max((record["updated_at"] for record in records), default=None),
        "fixes": _lane_fixes(lane, records, queued_retries, replay_records, delta_cursors),
    }


def _lane_fixes(
    lane: str,
    records: list[dict[str, Any]],
    queued_retries: list[dict[str, Any]],
    replay_records: list[dict[str, Any]],
    delta_cursors: list[dict[str, Any]],
) -> list[str]:
    fixes = []
    if not records:
        fixes.append(_missing_lane_fix(lane))
    if queued_retries:
        fixes.append(_queued_retry_fix(lane))
    if lane in {"import", "sync"} and records and not replay_records:
        fixes.append(f"Run one {lane} operation so operators can see the latest outcome.")
    if lane == "handoff" and records and not replay_records:
        fixes.append(
            "Create a corrected CivicClerk handoff event with a new external_event_id "
            "so operators can see the latest outcome."
        )
    if lane == "sync" and records and not delta_cursors:
        fixes.append(
            "Complete one successful codifier sync run so the next delta cursor is visible to operators."
        )
    return fixes


def _missing_lane_fix(lane: str) -> str:
    fixes = {
        "handoff": (
            "Create a CivicClerk handoff event or failed-handoff fixture before relying on handoff "
            "retry/replay readiness."
        ),
        "import": (
            "Run a local import bundle from a fixture or file drop before relying on import "
            "retry/replay readiness."
        ),
        "sync": (
            "Configure a codifier sync source and run one already-fetched local payload before "
            "relying on sync cursor readiness."
        ),
    }
    return fixes[lane]


def _queued_retry_fix(lane: str) -> str:
    fixes = {
        "handoff": (
            "Open the failed CivicClerk event in CivicClerk, attach the missing ordinance packet, "
            "then send a corrected new handoff event with a new external_event_id."
        ),
        "import": "Open the failed import job, correct the bundle data, then use the retry endpoint.",
        "sync": "Fix the source payload or circuit-breaker cause, then rerun the configured codifier source.",
    }
    return fixes[lane]


def _overall_status(
    missing_lanes: list[str],
    queued_lanes: list[str],
    records: list[dict[str, Any]],
) -> str:
    if not records:
        return "missing_state"
    if queued_lanes:
        return "needs_attention"
    if missing_lanes:
        return "partial"
    return "ready"


def _overall_fixes(
    missing_lanes: list[str],
    queued_lanes: list[str],
    lanes: dict[str, dict[str, Any]],
    records: list[dict[str, Any]],
) -> list[str]:
    if not records:
        return [
            "Run at least one local import, codifier sync, or CivicClerk handoff operation so staff can inspect operational readiness."
        ]
    fixes = []
    for lane in [*queued_lanes, *missing_lanes]:
        fixes.extend(lanes[lane]["fixes"])
    return _unique(fixes)


def _status_message(status: str) -> str:
    messages = {
        "ready": "Operational retry, replay, and cursor evidence is available for all lanes.",
        "partial": "Operational readiness is available, but at least one lane has no current state yet.",
        "needs_attention": "Operational state includes queued retry work that staff must resolve.",
        "missing_state": "No operational retry, replay, or cursor records are available yet.",
    }
    return messages[status]


def _count_records(records: list[dict[str, Any]], record_type: str) -> int:
    return sum(1 for record in records if record["record_type"] == record_type)


def _dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = {record["record_id"]: record for record in records}
    return sorted(
        deduped.values(),
        key=lambda record: (
            record["lane"],
            record["record_type"],
            record["created_at"],
            record["record_id"],
        ),
    )


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


__all__ = ["build_operational_readiness"]
