# Collector

The collector is the local ingest path for TurnScope.

Current prototype:

- accepts NDJSON or JSON-array input
- validates required event fields
- keeps processing when some events fail validation
- supports `--append` mode for repeated ingest into an existing output directory
- writes one append-only session log per session
- writes one summary JSON sidecar per session
- writes one `*.bundle.json` file per session for easy web loading
- writes one `session-pack.json` file containing all sessions from the ingest batch
- writes one `index.json` file for quick session listing
- records dropped invalid-event counts in session summaries and in `index.json`

## Try it

```bash
python3 apps/collector/src/collector.py \
  --input packages/schema/examples/minimal-session.ndjson \
  --outdir apps/collector/data
```

Append a later ingest batch into the same output directory:

```bash
python3 apps/collector/src/collector.py \
  --input /tmp/more-events.ndjson \
  --outdir apps/collector/data \
  --append
```

Expected output:

- `apps/collector/data/sessions/sess_demo.ndjson`
- `apps/collector/data/sessions/sess_demo.summary.json`
- `apps/collector/data/bundles/sess_demo.bundle.json`
- `apps/collector/data/bundles/session-pack.json`
- `apps/collector/data/index.json`
