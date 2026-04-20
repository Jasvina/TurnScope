# OpenClaw Adapter Contract

This package will translate OpenClaw-native sessions, gateway logs, or runtime events into the TurnScope canonical schema.

Early mapping targets:

- session lifecycle
- agent and subagent activity
- gateway or runtime errors
- shell and tool activity where available
- approval-like waits and control-plane pauses

Suggested next additions:

- source inventory for Gateway, Dashboard, and session event surfaces
- mapping examples from raw OpenClaw artifacts to canonical events
- transport notes for files, WebSocket, or HTTP surfaces
