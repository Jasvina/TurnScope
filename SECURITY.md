# Security Policy

TurnScope is pre-alpha, but security reports still matter.

## What to report

Please report issues that could expose users or their data, including:

- secrets, tokens, or credentials appearing in traces or exports
- unsafe file writes or path handling in the collector or adapters
- injection issues in the web prototype
- broken redaction or data-scrubbing behavior
- privilege or sandbox boundary problems

## How to report

- Prefer a private GitHub security advisory if the repository has that enabled.
- Otherwise open a GitHub issue titled `[Security] ...` and avoid including live secrets, tokens, customer data, or unredacted traces.
- Include the affected component, the commit or version you tested, the steps to reproduce, and why the issue is security relevant.

## Safe handling

- Redact sensitive payloads before attaching logs or screenshots.
- Do not paste production credentials or personal data into public issues.
- If a trace is needed, include the smallest redacted example that still shows the problem.
