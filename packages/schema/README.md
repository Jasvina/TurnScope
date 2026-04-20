# TurnScope Schema

This package holds the canonical TurnScope event contract.

Current contents:

- `turnscope-event.schema.json` for the canonical event envelope
- `examples/` for realistic sample traces that drive collector and UI development

Design rules:

- preserve what happened, not just how a runtime named it
- keep the top-level event envelope stable and explicit
- allow runtime-specific detail inside `payload` and `attributes`
- prefer additive evolution over breaking renames
