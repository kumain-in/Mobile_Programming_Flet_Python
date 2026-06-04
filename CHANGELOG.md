# CHANGELOG

## 2026-06-04 (runtime fixes — gray body / unusable window)
### Fixed
- **Default to browser renderer.** `main.py` entrypoint now runs
  `ft.run(main, view=ft.AppView.WEB_BROWSER)`. Flet 0.85's native desktop
  client renders `DataTable` (and the toolbar inputs) as a gray placeholder
  box; the web CanvasKit renderer draws them correctly. To use the native
  window instead, remove the `view=...` argument.
- **Toast no longer blocks input.** The toast was added to `page.overlay` as a
  full-screen `expand=True` container at startup and never removed, so it
  intercepted all clicks/typing/scroll. Now anchored to a 60px bottom strip
  and attached only while a message is showing.
- **Root layout.** Removed `expand=True` from the app-frame wrapper (invalid as
  a child of a scrolling `Column`).
- Repaired a truncated write of `main.py` (file had been cut off mid-`stage_bar`).

### Verified
- Re-ran headless render + CRUD harness after the rebuild: initial render,
  mobile/desktop toggle, filters, and a valid ADD persisting to xlsx all pass;
  startup `page.overlay` confirmed empty.

## 2026-06-04 (docs sync)
### Changed
- Rewrote `ARCHITECTURE.md` and `DESIGN.md` to match the shipped app. They
  previously described an earlier English scaffold (id/name/age/grade, no
  search/filter/pagination). Now reflect the real Indonesian app: fields
  `nim/nama/prodi/angkatan/email/ipk/status`, desktop↔mobile views, live
  search, status filter chips, pagination, validation, and the full
  institutional-blue token set from `constants.py`.
- `CONTEXT.md`: corrected workspace path (`D:\New folder\…` →
  `A:\RD\Tugas1\…`), noted Flet ≥ 0.85 new API, and the `refresh()` (not
  `build_table()`) re-render convention.

## 2026-06-04
### Verified
- Full code audit against installed **Flet 0.85.2** + **openpyxl 3.1.5**.
  All API symbols and control constructors used in `main.py` resolve on the
  new Flet API surface (`ft.run`, `page.show_dialog`/`pop_dialog`, `ft.Padding`,
  `ft.Border.all`, `ft.Alignment.*`, `ft.Colors`, `DataTable`, `Dropdown.Option`).
- End-to-end xlsx CRUD round-trip (seed 24 → add → update → delete) passes;
  field types persist correctly (`nim:str`, `angkatan:int`, `ipk:float`).

### Changed
- `requirements.txt`: pinned `flet>=0.85,<1.0` and `openpyxl>=3.1,<4.0`.
  Previously unpinned — a fresh install could pull legacy Flet (<0.70), whose
  old API (`ft.app`, `ft.padding`, `ft.border`) is incompatible with this code
  and crashes on import.

### Notes (not changed)
- `data/students.xlsx` remains the single source of truth (sheet `Mahasiswa`,
  headers: NIM, Nama, Prodi, Angkatan, Email, IPK, Status). Auto-created and
  seeded by `db.py` on first run; UI never touches openpyxl directly.
- `ARCHITECTURE.md` / `DESIGN.md` still describe the earlier English scaffold
  (id/name/age/grade) and are stale vs. the shipped Indonesian app. Left
  untouched pending an explicit docs-sync request.

## 2026-06-04 (replace DataTable — the real "gray box" cause)
### Fixed
- **Desktop table no longer renders as a gray box.** Rebuilt `desktop_table()`
  using `Row`/`Container`/`Column` primitives instead of `ft.DataTable`. Flet
  0.85's client paints `DataTable` (and the `DataRow` string-keyed state-color
  map) as a blank gray rectangle; the primitive grid renders on every Flet
  client. Same columns, selection highlight, ellipsis overflow, and per-row
  edit/delete actions as before.
- Verified with a 9-point headless smoke test: 10 rows render with real seed
  data, mobile/desktop toggle, live search narrows to the right row, and a
  valid add persists to students.xlsx.

### Note
- The editor repeatedly truncated main.py's tail on save; the file was rebuilt
  and recompiled via the shell. Current main.py: compiles clean, 557 lines.

## 2026-06-04 (rebuild — fix "can't add student")
### Rebuilt main.py
- Root cause of the broken app: Flet 0.85's client doesn't reliably render
  `DataTable` (gray box) or drive `AlertDialog` (add/edit silently failed).
- Rebuilt the UI from scratch using only primitives (Container/Row/Column/Text)
  and **inline panels instead of modal dialogs**:
  - List screen: header, search, status filter chips, primitive table, pagination.
  - Add/Edit: inline form panel with the same validation (NIM 6-12 digits +
    unique + locked on edit, required name/prodi/angkatan, email format,
    IPK 0-4, status).
  - Delete: inline confirmation panel.
  - Feedback: inline success/warn banner (no overlay).
- `db.py` (xlsx database) and `constants.py` (tokens/lookups) unchanged.
- Entry point runs in the browser by default (`view=ft.AppView.WEB_BROWSER`).
- Verified with a 10-point headless smoke test driving the REAL inline flow:
  render (10 rows), add persists to xlsx (24->25), edit (NIM locked), delete
  (25->24), search narrows to 1, filter DO -> 2. All pass.

## 2026-06-04 (deploy — Dokploy / Docker)
### Added
- `asgi.py` — production ASGI entrypoint (`ft.run(..., export_asgi_app=True,
  no_cdn=True)`); served with uvicorn.
- `Dockerfile` (python:3.12-slim → uvicorn asgi:app on :8550), `.dockerignore`.
- `DEPLOY.md` — step-by-step Dokploy guide incl. the required persistent volume
  mount at /app/data so the xlsx DB survives redeploys.
- `requirements.txt`: added pinned flet-web==0.85.2 and uvicorn==0.49.0.
### Verified
- `uvicorn asgi:app` serves HTTP 200 and the Flet web client loads
  (startup complete, requests logged).

## 2026-06-04 (developer comments + bug fix)
### Fixed
- main.py line 353 had a syntax error introduced after the rebuild:
  `btn("Tambah Mahasiswa", color="#FFFFFF", lambda e: go_add(), ...)` — a keyword
  arg before a positional arg, and `btn()` has no `color` param. This made the
  whole app fail to import (likely the "still unusable" symptom). Restored to
  `btn("Tambah Mahasiswa", lambda e: go_add(), icon=...)`.
### Changed
- Added human-readable docstrings/comments throughout main.py, db.py, and
  constants.py explaining what each core function does and the key design
  decisions (single-state + full re-render model, inline panels vs dialogs,
  primitive grid vs DataTable, xlsx-as-DB and how to swap it later). No logic
  changed beyond the fix above.
### Verified
- All modules compile and import together; inline-flow smoke test passes again
  (render, ADD 24→25, EDIT with NIM locked, DELETE 25→24); db.py CRUD round-trip OK.
