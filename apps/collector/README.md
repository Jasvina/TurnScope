# Collector

The collector is the local ingest path for TurnScope.

Current prototype:

- accepts NDJSON or JSON-array input
- validates required event fields
- writes one append-only session log per session
- writes one summary JSON sidecar per session
- writes one `*.bundle.json` file per session for easy web loading

## Try it

```bash
python3 apps/collector/src/collector.py \
  --input packages/schema/examples/minimal-session.ndjson \
  --outdir apps/collector/data
```

Expected output:

- `apps/collector/data/sessions/sess_demo.ndjson`
- `apps/collector/data/sessions/sess_demo.summary.json`
- `apps/collector/data/bundles/sess_demo.bundle.json`
