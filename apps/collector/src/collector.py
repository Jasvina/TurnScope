#!/usr/bin/env python3
"""Tiny local collector for TurnScope sample traces."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Dict, Any

REQUIRED_FIELDS = ["version", "id", "type", "occurred_at", "session_id", "source", "payload"]
EVENT_TYPE_ORDER = {
    "session.started": 0,
    "turn.started": 10,
    "tool.called": 20,
    "shell.started": 30,
    "shell.output": 31,
    "shell.finished": 32,
    "tool.finished": 40,
    "file.changed": 50,
    "approval.requested": 60,
    "approval.resolved": 61,
    "subagent.spawned": 70,
    "error.raised": 80,
    "turn.finished": 90,
    "session.finished": 100,
}


def event_sort_key(event: Dict[str, Any]) -> tuple[str, int, str]:
    return (
        event["occurred_at"],
        EVENT_TYPE_ORDER.get(event["type"], 999),
        event["id"],
    )


def load_events(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text[0] == "[":
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list of events")
        return data
    events = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
    return events


def validate_event(event: Dict[str, Any]) -> Iterable[str]:
    for field in REQUIRED_FIELDS:
        if field not in event:
            yield f"missing field: {field}"
    source = event.get("source")
    if source is not None and not isinstance(source, dict):
        yield "source must be an object"


def summarize(events: List[Dict[str, Any]], log_path: Path, summary_path: Path) -> Dict[str, Any]:
    counts = Counter(event["type"] for event in events)
    runtimes = sorted({event.get("source", {}).get("runtime", "unknown") for event in events})
    return {
        "session_id": events[0]["session_id"],
        "event_count": len(events),
        "first_timestamp": events[0]["occurred_at"],
        "last_timestamp": events[-1]["occurred_at"],
        "runtimes": runtimes,
        "status": infer_status(events),
        "counts": dict(counts),
        "turn_count": counts.get("turn.started", 0),
        "tool_call_count": counts.get("tool.called", 0),
        "shell_count": counts.get("shell.started", 0),
        "shell_output_count": counts.get("shell.output", 0),
        "file_change_count": counts.get("file.changed", 0),
        "approval_count": counts.get("approval.requested", 0),
        "subagent_count": counts.get("subagent.spawned", 0),
        "error_count": counts.get("error.raised", 0),
        "log_path": str(log_path),
        "summary_path": str(summary_path),
    }


def infer_status(events: List[Dict[str, Any]]) -> str:
    for event in reversed(events):
        if event["type"] == "session.finished":
            return event.get("payload", {}).get("status", "completed")
    for event in reversed(events):
        if event["type"] == "turn.finished":
            return event.get("payload", {}).get("status", "completed")
    return "incomplete"


def write_index(outdir: Path, summaries: List[Dict[str, Any]]) -> Path:
    index_path = outdir / "index.json"
    payload = {
        "version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "session_count": len(summaries),
        "sessions": sorted(summaries, key=lambda summary: summary["last_timestamp"], reverse=True),
    }
    index_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return index_path


def write_bundle(outdir: Path, summary: Dict[str, Any], events: List[Dict[str, Any]]) -> Path:
    bundles_dir = outdir / "bundles"
    bundles_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = bundles_dir / f"{summary['session_id']}.bundle.json"
    payload = {
        "version": "0.1.0",
        "kind": "turnscope.session.bundle",
        "summary": summary,
        "events": events,
    }
    bundle_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return bundle_path


def write_pack(outdir: Path, sessions: List[Dict[str, Any]]) -> Path:
    bundles_dir = outdir / "bundles"
    bundles_dir.mkdir(parents=True, exist_ok=True)
    pack_path = bundles_dir / "session-pack.json"
    payload = {
        "version": "0.1.0",
        "kind": "turnscope.session.pack",
        "generated_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "sessions": sessions,
    }
    pack_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return pack_path


def write_sessions(events: List[Dict[str, Any]], outdir: Path) -> List[Path]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[event["session_id"]].append(event)

    sessions_dir = outdir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    written = []
    summaries = []
    packs = []

    for session_id, session_events in grouped.items():
        session_events.sort(key=event_sort_key)
        log_path = sessions_dir / f"{session_id}.ndjson"
        summary_path = sessions_dir / f"{session_id}.summary.json"
        with log_path.open("w", encoding="utf-8") as handle:
            for event in session_events:
                handle.write(json.dumps(event, ensure_ascii=True) + "\n")
        summary = summarize(session_events, log_path.relative_to(outdir), summary_path.relative_to(outdir))
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        bundle_path = write_bundle(outdir, summary, session_events)
        summary["bundle_path"] = str(bundle_path.relative_to(outdir))
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        summaries.append(summary)
        packs.append({"summary": summary, "events": session_events})
        written.extend([log_path, summary_path, bundle_path])

    index_path = write_index(outdir, summaries)
    written.append(index_path)
    pack_path = write_pack(outdir, packs)
    written.append(pack_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect TurnScope events into local session files")
    parser.add_argument("--input", required=True, help="Path to NDJSON or JSON events")
    parser.add_argument("--outdir", default="apps/collector/data", help="Output directory for stored sessions")
    args = parser.parse_args()

    input_path = Path(args.input)
    outdir = Path(args.outdir)

    events = load_events(input_path)
    if not events:
        print("No events found.")
        return 0

    errors = []
    valid_events = []
    for event in events:
        problems = list(validate_event(event))
        if problems:
            errors.append({"event": event.get("id", "unknown"), "problems": problems})
            continue
        valid_events.append(event)

    written = write_sessions(valid_events, outdir)

    print(f"Loaded {len(events)} events from {input_path}")
    print(f"Stored {len(valid_events)} valid events")
    if errors:
        print(f"Dropped {len(errors)} invalid events")
        for error in errors:
            print(f"- {error['event']}: {', '.join(error['problems'])}")
    for path in written:
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
