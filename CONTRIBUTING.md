# Contributing to TurnScope

Thanks for helping build TurnScope.

This project is still early, so the best contributions are usually the ones that make the direction sharper, the event model cleaner, or the first demo easier to understand.

## Before you start

Please read these first:

- `README.md`
- `docs/specs/v0.1-architecture.md`
- `docs/progress/current-progress.md`
- `docs/community/release-checklist.md`
- `codex_work`

`codex_work` matters on purpose. It is the persistent handoff log for both humans and AI agents. If you make meaningful progress, update it.

## Good first contributions

- improve the event schema
- add sample traces and fixtures
- propose adapter mappings for a runtime
- improve the web prototype interaction model
- harden the collector's ingest behavior
- clarify docs where the product thesis is still fuzzy

## Working principles

- keep the project local-first by default
- prefer deletion and simplification over new layers
- preserve runtime neutrality where possible
- keep the canonical schema clean and explicit
- document important design decisions close to the code
- update `codex_work` after meaningful work sessions

## Repository areas

- `apps/collector` for local ingest and session storage
- `apps/web` for the viewing surface and prototype UI
- `packages/schema` for the canonical event model and fixtures
- `packages/adapters-*` for runtime-specific mappings
- `docs/specs` for architecture and decision records

## Making changes

### Docs

If you change project direction, architecture, or contributor expectations:

- update the relevant doc
- update `README.md` if the external story changed
- append a short entry to `codex_work`

### Code

If you change behavior:

- keep diffs small and explainable
- prefer stable contracts over clever abstractions
- add or update example traces when they help explain the change
- add basic verification notes to `codex_work`
- run `./scripts/verify.sh` before opening a pull request when your change touches code or shipped docs

## Validation

At this stage, good validation can be lightweight, but it should be real.

Examples:

- run the collector against a sample trace
- verify generated summary files look correct
- open the web prototype and confirm the layout renders
- inspect that docs and example commands still make sense

The standard project verification entrypoint is:

```bash
./scripts/verify.sh
```

## Issues and proposals

When opening an issue, help us answer one of these quickly:

- what pain point does this solve?
- what runtime or workflow does it affect?
- what evidence should we preserve in the canonical schema?
- what would success look like in the UI?

## Style expectations

- use clear names over clever names
- keep prose concrete
- keep example data realistic enough to drive design
- avoid adding dependencies unless they unlock a clear milestone

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Community

- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
