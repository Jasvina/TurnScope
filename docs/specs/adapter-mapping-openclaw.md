# OpenClaw Session Store to TurnScope Mapping

## Status

Bootstrap adapter for OpenClaw session-store snapshots.

## Primary sources

This mapping is grounded in official OpenClaw docs:

- Session Management: `https://openclawlab.com/en/docs/concepts/session/`
- Logging: `https://openclawlab.com/en/docs/gateway/logging/`
- Dashboard: `https://openclawlab.com/docs/web/dashboard/`

The most stable documented surface today is the session store on the gateway host:

- `~/.openclaw/agents/<agentId>/sessions/sessions.json`

Docs describe it as a map:

- `sessionKey -> { sessionId, updatedAt, ... }`

The docs also explicitly call the gateway the source of truth for session metadata and token counts.

## Why this adapter starts with the session store

OpenClaw exposes several useful surfaces, but not all are equally precise for bootstrap mapping.

- Session store shape is explicitly documented.
- Session entries carry token counts and origin metadata already used by UIs.
- Raw transcript JSONL and gateway file logs are useful, but the docs do not yet define a stable public schema for those lines.

So this adapter starts with the safest surface first: the session store snapshot.

## Important limitation

A session store entry is a snapshot, not a full replayable event stream.

That means this adapter emits **synthetic lifecycle events** around a snapshot so TurnScope can ingest and visualize OpenClaw state without pretending it has full turn-by-turn history.

## Mapping strategy

For each session store entry:

- emit `session.started`
- emit `session.finished`

Both events share the same `session_id`.

### `session.started`

- `occurred_at`: `createdAt` if present, otherwise `updatedAt`
- `payload`: origin, label, provider/channel, session key
- `attributes`: token counters and display metadata

### `session.finished`

- `occurred_at`: `updatedAt`
- `payload.status`: `active_snapshot`
- `payload`: session key and origin summary
- `attributes`: token counters and display metadata

## Why use `active_snapshot`

The store tells us a session exists and was last updated at a given time. It does **not** prove the session is terminally complete.

Using `active_snapshot` avoids falsely claiming a completed run while still giving TurnScope a consistent event shape to ingest.

## Current event coverage

This adapter intentionally covers only:

- `session.started`
- `session.finished`

That makes it useful for:

- session catalogs
- token-aware session browsing
- origin/provider filtering
- gateway-state snapshots

It is **not yet** a substitute for a full event-stream adapter.

## Next expansion options

- transcript JSONL adapter for turn-level reconstruction
- gateway log adapter for error and tool-execution signals
- combined adapter that merges session store + transcript + gateway logs into one richer event set
