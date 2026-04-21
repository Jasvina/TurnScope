# Web Prototype

This is a zero-dependency static prototype for the first TurnScope reading surface.

It is intentionally simple:

- one HTML file
- one CSS file
- one JS file
- no build step
- supports pasted NDJSON plus uploaded collector output files

## Try it

```bash
cd apps/web
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

Current load modes:

- built-in sample trace
- pasted NDJSON
- uploaded `*.bundle.json`
- uploaded `index.json`
- uploaded `*.summary.json`
- uploaded `*.ndjson`
