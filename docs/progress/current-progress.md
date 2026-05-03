# TurnScope Current Progress

Last updated: 2026-04-21

This document is the public progress snapshot for TurnScope. It summarizes what exists now, what has been verified, what is still intentionally incomplete, and how future work should proceed.

For the detailed AI handoff log, see `codex_work`.

## Current state

TurnScope has moved from a concept repository into a working bootstrap project.

The repository now contains:

- a clear README and project thesis
- a GitHub-rendered poster asset
- a v0.1 architecture document
- a canonical event schema draft
- sample traces
- a local collector
- a static web prototype
- a Codex app-server adapter
- an OpenClaw session-store adapter
- fixture-driven precision checks
- session bundles and multi-session packs
- contributor and issue-template infrastructure

## Public positioning

TurnScope is positioned as:

> Local-first observability and replay for coding agents.

It is not another agent IDE or chat shell. It is an observability layer for understanding what happened during a coding-agent run.

The main product promise is:

- inspect every turn
- inspect every tool call
- inspect shell activity
- inspect file changes
- inspect approval waits
- inspect subagent branches
- replay or hand off the run as structured data

## Completed repository assets

### Project identity and README

- `README.md`
- `docs/assets/turnscope-hero.svg`
- `docs/assets/turnscope-panels.svg`
- `docs/assets/turnscope-poster.svg`
- `docs/design/turnscope-poster-philosophy.md`

The README now includes:

- badges
- hero visual
- product positioning
- poster section
- architecture overview
- prototype quickstart
- Codex and OpenClaw adapter commands
- roadmap and contribution entry points

### Architecture and specs

- `docs/specs/v0.1-architecture.md`
- `docs/specs/adapter-mapping-codex.md`
- `docs/specs/adapter-mapping-openclaw.md`

The architecture currently defines:

- runtime adapters
- collector ingest
- canonical event envelope
- session storage
- bundle and pack handoff formats
- web reading surface
- initial acceptance criteria

### Schema and examples

- `packages/schema/turnscope-event.schema.json`
- `packages/schema/examples/minimal-session.ndjson`
- `packages/schema/examples/subagent-branch.ndjson`

Canonical event types currently include:

- `session.started`
- `session.finished`
- `turn.started`
- `turn.finished`
- `tool.called`
- `tool.finished`
- `shell.started`
- `shell.output`
- `shell.finished`
- `file.changed`
- `approval.requested`
- `approval.resolved`
- `subagent.spawned`
- `error.raised`

### Collector

- `apps/collector/src/collector.py`
- `apps/collector/README.md`

Current collector capabilities:

- reads NDJSON or JSON-array event input
- validates required fields
- drops invalid events while continuing the ingest batch
- groups events by `session_id`
- writes per-session event logs
- writes per-session summary files
- writes per-session bundle files
- writes a multi-session `session-pack.json`
- writes `index.json`
- records dropped-event counts in summaries and in `index.json`
- applies canonical event ordering when timestamps are equal

Current collector outputs:

- `sessions/<session_id>.ndjson`
- `sessions/<session_id>.summary.json`
- `bundles/<session_id>.bundle.json`
- `bundles/session-pack.json`
- `index.json`

### Web prototype

- `apps/web/index.html`
- `apps/web/styles.css`
- `apps/web/app.js`
- `apps/web/README.md`

Current web capabilities:

- runs as static files with no build step
- loads pasted NDJSON
- loads `index.json`
- loads `*.summary.json`
- loads `*.bundle.json`
- loads `session-pack.json`
- supports multi-session picker
- supports timeline search
- supports event-type filtering
- supports clickable timeline rows
- shows selected raw canonical event JSON
- shows shell, diff, and subagent panels derived from currently visible events

### Codex adapter

- `packages/adapters-codex/src/map_app_server.py`
- `packages/adapters-codex/src/eval_samples.py`
- `packages/adapters-codex/fixtures/*.jsonl`
- `packages/adapters-codex/golden/*.expected.ndjson`
- `packages/adapters-codex/expected_gaps.json`

Current Codex adapter capabilities:

- consumes Codex app-server JSONL captures
- maps supported JSON-RPC notifications and approval requests to TurnScope events
- emits canonical NDJSON
- emits optional coverage report
- synthesizes session lifecycle events
- tracks mapped and unmapped methods by `method + item.type`
- runs fixture-vs-golden precision checks

Known Codex gap:

- `item/started:fileChange` is explicitly allowed in `expected_gaps.json` until a final canonical mapping decision is made.

### OpenClaw adapter

- `packages/adapters-openclaw/src/map_session_store.py`
- `packages/adapters-openclaw/src/eval_samples.py`
- `packages/adapters-openclaw/fixtures/sample-sessions-store.json`
- `packages/adapters-openclaw/golden/sample-sessions-store.expected.ndjson`

Current OpenClaw adapter capabilities:

- consumes documented OpenClaw session-store snapshots
- emits synthetic `session.started` and `session.finished` events
- preserves token counters and origin metadata
- marks snapshot status as `active_snapshot`
- runs fixture-vs-golden precision checks

Important OpenClaw limitation:

- current adapter is snapshot-based, not turn-level or tool-level event reconstruction.

## Verification completed

The following checks have been run successfully:

```bash
python3 packages/adapters-codex/src/eval_samples.py
python3 packages/adapters-openclaw/src/eval_samples.py
python3 -m py_compile apps/collector/src/collector.py \
  packages/adapters-codex/src/map_app_server.py \
  packages/adapters-codex/src/eval_samples.py \
  packages/adapters-openclaw/src/map_session_store.py \
  packages/adapters-openclaw/src/eval_samples.py
node --check apps/web/app.js
```

Additional verification:

- OpenClaw fixture -> adapter -> collector -> `session-pack.json`
- `session-pack.json` contains two sessions in the sample workflow
- same-timestamp lifecycle ordering keeps `session.started` before `session.finished`
- SVG assets parse as XML
- local HTTP smoke test passed on `apps/web`

## What is intentionally incomplete

TurnScope is still pre-alpha.

Not complete yet:

- full Codex event coverage
- full OpenClaw transcript or gateway-log event coverage
- real browser automation tests
- large-trace performance handling
- redaction profiles for sensitive payloads
- hosted backend
- SQLite or DuckDB storage
- OpenTelemetry / OpenInference export
- replay timeline comparison
- packaged CLI or install command

## Future optimization plan

### 1. Adapter precision

- collect more real Codex app-server JSONL samples
- add more fixture and golden pairs
- decide final handling for `item/started:fileChange`
- add token usage, plan updates, diff updates, and model reroute events once their canonical representation is clear
- expand OpenClaw beyond session-store snapshots using real transcript or gateway-log samples

### 2. Collector robustness

- add schema validation mode
- add redaction profiles before sharing bundles
- support append mode across repeated ingest runs
- support multi-session pack metadata and pack summaries

### 3. Web inspection

- add empty states and filter counts
- add raw-event copy button
- split raw view into envelope, payload, and attributes sections
- add timeline type chips
- add virtualized list rendering for large sessions
- add side-by-side session comparison

### 4. Export and replay

- define a stable bundle spec
- add OpenTelemetry-compatible export
- add OpenInference-compatible export
- add replay reconstruction helpers
- add baseline-vs-candidate diff mode

### 5. Open-source readiness

- add CI
- add pull request template
- add security policy
- add screenshots or generated PNG previews
- add package / CLI entrypoint once the shape stabilizes

## Recommended next milestone

The next milestone should be:

> TurnScope v0.1: load real Codex app-server captures, generate session packs, and inspect them in the web prototype with search, filtering, and raw-event debugging.

Acceptance criteria:

- one real Codex capture ingests successfully
- one real OpenClaw snapshot ingests successfully
- web loads the generated session pack
- search and event-type filters work on the generated pack
- raw event inspector helps explain adapter output
- sensitive fields can be redacted before sharing
