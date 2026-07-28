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

The refresh button inserts an authenticated per-user row into Supabase `refresh_runs` and polls that row for stage, progress, and completion. A dedicated local worker claims queued runs, reads the complete variable-length preference set through a secret-checked database function, runs the fixed local candidate engine, and atomically publishes both status and the personalized snapshot. The public bundle contains no desktop URL or worker credential.

## Release boundary

GitHub Pages proves browser/PWA delivery only. Physical iPhone Safari/Home Screen installation, touch behavior, audio, safe-area behavior, offline recovery, and performance still require device evidence.
