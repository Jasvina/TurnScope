# Release checklist

Use this before tagging a release, publishing a demo, or updating the public status of the project.

## Documentation and packaging

- [ ] README quickstart commands still work on a clean checkout.
- [ ] README links point to files that exist.
- [ ] Issue templates still match the current product surface.
- [ ] `docs/progress/current-progress.md` reflects the current state of the repo.
- [ ] `SECURITY.md` is present and linked from the README or issue templates.
- [ ] Any public screenshots or demo assets still match the UI.

## Demo readiness

- [ ] Codex sample ingest still works.
- [ ] OpenClaw sample ingest still works.
- [ ] The collector still produces session bundles and the session pack.
- [ ] The web prototype still loads the sample bundle.
- [ ] Sample data is redacted before it is shared outside the repo.

## Release notes

- [ ] Note what changed.
- [ ] Note what is intentionally incomplete.
- [ ] Link to the relevant docs or issues.
- [ ] Call out any adapter or schema changes that affect external contributors.
