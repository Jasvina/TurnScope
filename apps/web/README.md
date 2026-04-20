# Web Prototype

This is a zero-dependency static prototype for the first TurnScope reading surface.

It is intentionally simple:

- one HTML file
- one CSS file
- one JS file
- sample event data embedded in the page

## Try it

```bash
cd apps/web
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

You can also paste NDJSON into the ingest panel and re-render the dashboard without a backend.
