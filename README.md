# Career Compass

An iPhone-first, static career decision PWA. It publishes a compact, evidence-labelled snapshot from the local `job_search` pipeline to GitHub Pages. It does **not** submit applications, log in to any service, access credentials, or claim live availability.

## Local preview

```powershell
python -m http.server 4173
```

Open `http://127.0.0.1:4173`.

## Refresh model

The static snapshot is an offline fallback. The generator is read-only against `job_search` and excludes descriptions and personal profile evidence.

```powershell
python scripts\build_snapshot.py --job-search-root C:\Users\mjb58\job_search
```

`data/refresh-bridge.json` stays disabled by default. When it is enabled with an authenticated personal HTTPS endpoint, the app's refresh button starts the complete local candidate engine, waits for completion, then loads `/api/jobs/public-snapshot`. It must never point to a public anonymous endpoint.

## Release boundary

GitHub Pages proves browser/PWA delivery only. Physical iPhone Safari/Home Screen installation, touch behavior, audio, safe-area behavior, offline recovery, and performance still require device evidence.
