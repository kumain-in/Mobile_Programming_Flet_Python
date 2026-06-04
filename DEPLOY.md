# DEPLOY.md — Manajemen Mahasiswa on Dokploy

Live deployment runs the Flet app as a **web server in a Docker container**.
Dokploy builds the image from the `Dockerfile`, serves it with uvicorn, and puts
a domain + automatic HTTPS (Traefik / Let's Encrypt) in front of it.

## Files that make this work
- `asgi.py` — exports the Flet ASGI app (`app`) via `export_asgi_app=True`, `no_cdn=True`.
- `Dockerfile` — python:3.12-slim → install `requirements.txt` → run
  `uvicorn asgi:app --host 0.0.0.0 --port 8550`.
- `.dockerignore` — keeps local DB/junk out of the image.
- `requirements.txt` — pinned: flet, flet-web, openpyxl, uvicorn.

## ⚠️ Data persistence (read this)
The "database" is an Excel file at `/app/data/students.xlsx`. A container's
filesystem is wiped on every redeploy/restart. **You must mount a persistent
volume at `/app/data`**, or every student you add disappears on the next deploy.
`db.py` auto-creates and seeds the file on first run inside that volume.

## Prerequisite: put the code in Git
Dokploy deploys from a Git provider (GitHub/GitLab/Gitea/Bitbucket) or a Docker
registry. Push this folder to a repo first:
```bash
git init && git add . && git commit -m "Manajemen Mahasiswa"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

## Dokploy steps
1. **Projects → Create Project** (e.g. "kampus").
2. Inside it, **Create Service → Application**.
3. **Provider**: connect GitHub (or paste a public Git URL) → pick the repo +
   `main` branch.
4. **Build Type**: select **Dockerfile** (path: `Dockerfile`).
5. **Deploy** once to build. It will fail to be reachable until you set the port
   + domain (next steps) — that's expected.
6. **Domains → Add Domain**:
   - Host: your domain/subdomain (e.g. `kampus.example.com`, DNS A-record → server IP).
   - **Container Port: `8550`**.
   - Enable HTTPS (Let's Encrypt). Traefik handles WebSockets automatically,
     which Flet needs — no extra config.
7. **Advanced → Volumes (Mounts) → Add**:
   - Type: **Volume Mount** (named volume) — Name: `students-data`,
     Mount path: **`/app/data`**.
8. **(Optional) Environment**: none required. The port is fixed at 8550 in the
   Dockerfile; if you change it, update the Domain's container port to match.
9. **Redeploy.** Open your domain — the app loads, and added students persist in
   the `students-data` volume.

## Update workflow
Push to `main` → in Dokploy hit **Deploy** (or enable **Auto Deploy** /
webhook so every push redeploys automatically).

## Caveats
- The xlsx file is a single-file store with no write locking — fine for a small
  internal app with light traffic, not for many simultaneous editors. If this
  grows, move `db.py` to SQLite/Postgres (the UI won't need changes).
- One container only. Don't scale to multiple replicas — they'd each have their
  own file view and clobber each other. Keep replicas = 1.

## Verify locally before deploying
```bash
pip install -r requirements.txt
python -m uvicorn asgi:app --host 0.0.0.0 --port 8550
# open http://localhost:8550
```
