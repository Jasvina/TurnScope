# Codex Adapter Contract

This package will translate Codex-native runtime events into the TurnScope canonical schema.

Early mapping targets:

- session lifecycle
- turn lifecycle
- tool calls
- shell commands
- approval requests and resolutions
- child agent spawning
- file-change summaries when available

Adapter output rule:

- preserve Codex semantics when possible, but emit canonical event names at the top level

Suggested next additions:

- mapping table from Codex event names to TurnScope types
- fixture traces
- edge-case notes for partial or delayed events
