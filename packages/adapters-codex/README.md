# Codex Adapter

This package contains the first real runtime adapter in the repository.

Current scope:

- consume Codex app-server JSONL captures
- map supported JSON-RPC notifications and approval requests into TurnScope canonical events
- emit NDJSON ready for the collector
- compare fixture output against committed golden files

## Files

- `src/map_app_server.py` - bootstrap adapter implementation
- `src/eval_samples.py` - sample-driven precision check runner
- `fixtures/sample-app-server.jsonl` - sample Codex app-server stream
- `fixtures/tool-and-error-app-server.jsonl` - tool and error-oriented sample stream
- `golden/*.expected.ndjson` - expected canonical outputs for regression checks
- `expected_gaps.json` - explicitly allowed unmapped method keys during precision work
- `../schema/turnscope-event.schema.json` - target canonical envelope
- `../../docs/specs/adapter-mapping-codex.md` - mapping rationale and coverage notes

## Try it

```bash
python3 packages/adapters-codex/src/map_app_server.py \
  --input packages/adapters-codex/fixtures/sample-app-server.jsonl \
  --output /tmp/codex-adapter.ndjson
```

Then ingest the adapted output:

```bash
python3 apps/collector/src/collector.py \
  --input /tmp/codex-adapter.ndjson \
  --outdir apps/collector/data
```

Run the precision checks:

```bash
python3 packages/adapters-codex/src/eval_samples.py
```
