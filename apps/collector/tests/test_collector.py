import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
COLLECTOR = ROOT_DIR / "apps" / "collector" / "src" / "collector.py"


class CollectorDroppedEventAccountingTests(unittest.TestCase):
    def run_collector(self, input_path: Path, outdir: Path, append: bool = False) -> subprocess.CompletedProcess[str]:
        command = ["python3", str(COLLECTOR), "--input", str(input_path), "--outdir", str(outdir)]
        if append:
            command.append("--append")
        return subprocess.run(
            command,
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )

    def test_summary_and_index_record_dropped_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_path = tmp_path / "events.ndjson"
            outdir = tmp_path / "out"
            input_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_valid_1",
                                "type": "session.started",
                                "occurred_at": "2026-04-21T00:00:00Z",
                                "session_id": "sess_a",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "codex",
                                    "component": "session",
                                    "origin": "test",
                                },
                                "payload": {"task": "demo"},
                            }
                        ),
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_invalid_1",
                                "type": "turn.started",
                                "occurred_at": "2026-04-21T00:00:01Z",
                                "session_id": "sess_a",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "codex",
                                    "component": "turn",
                                    "origin": "test",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_valid_2",
                                "type": "session.finished",
                                "occurred_at": "2026-04-21T00:00:02Z",
                                "session_id": "sess_a",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "codex",
                                    "component": "session",
                                    "origin": "test",
                                },
                                "payload": {"status": "completed"},
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_collector(input_path, outdir)

            self.assertIn("Dropped 1 invalid events", result.stdout)

            summary = json.loads((outdir / "sessions" / "sess_a.summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["event_count"], 2)
            self.assertEqual(summary["dropped_event_count"], 1)

            index = json.loads((outdir / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["dropped_event_count"], 1)
            self.assertEqual(
                index["dropped_events_by_session"],
                [{"session_id": "sess_a", "count": 1}],
            )

    def test_append_mode_merges_existing_sessions_and_dropped_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            outdir = tmp_path / "out"
            initial_input = tmp_path / "initial.ndjson"
            append_input = tmp_path / "append.ndjson"

            initial_input.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_valid_1",
                                "type": "session.started",
                                "occurred_at": "2026-04-21T00:00:00Z",
                                "session_id": "sess_a",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "codex",
                                    "component": "session",
                                    "origin": "test",
                                },
                                "payload": {"task": "first run"},
                            }
                        ),
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_invalid_1",
                                "type": "turn.started",
                                "occurred_at": "2026-04-21T00:00:01Z",
                                "session_id": "sess_a",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "codex",
                                    "component": "turn",
                                    "origin": "test",
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self.run_collector(initial_input, outdir)

            append_input.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_valid_2",
                                "type": "session.finished",
                                "occurred_at": "2026-04-21T00:00:03Z",
                                "session_id": "sess_a",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "codex",
                                    "component": "session",
                                    "origin": "test",
                                },
                                "payload": {"status": "completed"},
                            }
                        ),
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_valid_3",
                                "type": "session.started",
                                "occurred_at": "2026-04-21T00:00:04Z",
                                "session_id": "sess_b",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "openclaw",
                                    "component": "session",
                                    "origin": "test",
                                },
                                "payload": {"task": "second session"},
                            }
                        ),
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_invalid_2",
                                "type": "session.finished",
                                "occurred_at": "2026-04-21T00:00:05Z",
                                "session_id": "sess_b",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "openclaw",
                                    "component": "session",
                                    "origin": "test",
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = self.run_collector(append_input, outdir, append=True)

            self.assertIn("Append mode merged into", result.stdout)
            self.assertIn("Dropped 1 invalid events", result.stdout)

            summary_a = json.loads((outdir / "sessions" / "sess_a.summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary_a["event_count"], 2)
            self.assertEqual(summary_a["dropped_event_count"], 1)
            self.assertEqual(summary_a["status"], "completed")

            summary_b = json.loads((outdir / "sessions" / "sess_b.summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary_b["event_count"], 1)
            self.assertEqual(summary_b["dropped_event_count"], 1)

            session_log_a = (outdir / "sessions" / "sess_a.ndjson").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(session_log_a), 2)

            index = json.loads((outdir / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["session_count"], 2)
            self.assertEqual(index["dropped_event_count"], 2)
            self.assertEqual(
                index["dropped_events_by_session"],
                [
                    {"session_id": "sess_a", "count": 1},
                    {"session_id": "sess_b", "count": 1},
                ],
            )

    def test_session_pack_writes_aggregate_summary_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            outdir = tmp_path / "out"
            first_input = tmp_path / "first.ndjson"
            second_input = tmp_path / "second.ndjson"

            first_input.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_valid_1",
                                "type": "session.started",
                                "occurred_at": "2026-04-21T00:00:00Z",
                                "session_id": "sess_a",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "codex",
                                    "component": "session",
                                    "origin": "test",
                                },
                                "payload": {"task": "a"},
                            }
                        ),
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_valid_2",
                                "type": "session.finished",
                                "occurred_at": "2026-04-21T00:00:01Z",
                                "session_id": "sess_a",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "codex",
                                    "component": "session",
                                    "origin": "test",
                                },
                                "payload": {"status": "completed"},
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self.run_collector(first_input, outdir)

            second_input.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_valid_3",
                                "type": "session.started",
                                "occurred_at": "2026-04-21T00:00:02Z",
                                "session_id": "sess_b",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "openclaw",
                                    "component": "session",
                                    "origin": "test",
                                },
                                "payload": {"task": "b"},
                            }
                        ),
                        json.dumps(
                            {
                                "version": "0.1.0",
                                "id": "evt_invalid_1",
                                "type": "turn.started",
                                "occurred_at": "2026-04-21T00:00:03Z",
                                "session_id": "sess_b",
                                "agent_id": "lead",
                                "source": {
                                    "runtime": "openclaw",
                                    "component": "turn",
                                    "origin": "test",
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self.run_collector(second_input, outdir, append=True)

            pack = json.loads((outdir / "bundles" / "session-pack.json").read_text(encoding="utf-8"))
            self.assertEqual(pack["kind"], "turnscope.session.pack")
            self.assertEqual(pack["summary"]["session_count"], 2)
            self.assertEqual(pack["summary"]["event_count"], 3)
            self.assertEqual(pack["summary"]["dropped_event_count"], 1)
            self.assertEqual(pack["summary"]["runtimes"], ["codex", "openclaw"])


if __name__ == "__main__":
    unittest.main()
