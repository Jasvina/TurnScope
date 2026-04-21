# OpenClaw Adapter

This package starts with the most stable documented OpenClaw surface: the gateway session store snapshot.

Current scope:

- consume `sessions.json`-style store snapshots
- synthesize canonical TurnScope session events from documented store metadata
- preserve token counters, origin metadata, and display labels in event attributes

## Files

- `src/map_session_store.py` - snapshot-to-events adapter
- `src/eval_samples.py` - fixture and golden regression runner
- `fixtures/sample-sessions-store.json` - sample store snapshot
- `golden/sample-sessions-store.expected.ndjson` - expected canonical output
- `../../docs/specs/adapter-mapping-openclaw.md` - mapping rationale and limits

## Try it

```bash
python3 packages/adapters-openclaw/src/map_session_store.py \
  --input packages/adapters-openclaw/fixtures/sample-sessions-store.json \
  --output /tmp/openclaw-store.ndjson

python3 apps/collector/src/collector.py \
  --input /tmp/openclaw-store.ndjson \
  --outdir apps/collector/data
```

Run the precision check:

```bash
python3 packages/adapters-openclaw/src/eval_samples.py
```
