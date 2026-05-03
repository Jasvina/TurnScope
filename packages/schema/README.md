# TurnScope Schema

This package holds the canonical TurnScope event contract.

Current contents:

- `turnscope-event.schema.json` for the canonical event envelope
- `examples/` for realistic sample traces that drive collector and UI development

Notable examples:

- `examples/minimal-session.ndjson` for a clean happy-path session
- `examples/subagent-branch.ndjson` for delegation and warning-path rendering
- `examples/dropped-events-session.ndjson` for dropped invalid-event accounting demos

Design rules:

- preserve what happened, not just how a runtime named it
- keep the top-level event envelope stable and explicit
- allow runtime-specific detail inside `payload` and `attributes`
- prefer additive evolution over breaking renames
