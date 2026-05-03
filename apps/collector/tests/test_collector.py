import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
COLLECTOR = ROOT_DIR / "apps" / "collector" / "src" / "collector.py"


class CollectorDroppedEventAccountingTests(unittest.TestCase):
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

            result = subprocess.run(
                ["python3", str(COLLECTOR), "--input", str(input_path), "--outdir", str(outdir)],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=True,
            )

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


if __name__ == "__main__":
    unittest.main()
