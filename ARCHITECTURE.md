# ARCHITECTURE.md
_Updated: 2026-06-04 | Type: Mobile / Cross-platform (Python + Flet)_

## Project
- Name: Manajemen Mahasiswa (Student Management)
- Purpose: CRUD app to manage student records, stored in a local `.xlsx` file
- Framework: Flet (Flutter-based Python UI) — **new API, Flet ≥ 0.85**
- Language: Python 3.x
- Platform targets: Desktop · Web · Android · iOS
- State management: in-memory `state` dict + `refresh()` re-render (no external lib)
- Storage: Local Excel file (`data/students.xlsx`, sheet `Mahasiswa`) via openpyxl

## Layer map

### Entrypoints
> `main.py` — `ft.run(main)` bootstrap (new Flet API; not `ft.app`)
- `main.py`

### UI / Screens (all in main.py, single `main(page)` function)
- Stage bar: caption + Desktop/Mobile segmented toggle
- App frame (fixed-width preview): app bar, toolbar, body, pager
- Desktop view: `DataTable` — NIM, Nama, Prodi, Angkatan, Email, IPK, Status, Aksi
- Mobile view: card list (same data, stacked)
- Toolbar: "Semua Mahasiswa" heading + registered count, live search field,
  status filter chips with per-status counts
- Add/Edit: `AlertDialog` with form fields + inline validation
- Delete: `AlertDialog` confirmation
- Toast: overlay container, auto-dismiss (~2.6s) via `threading.Timer`

### Services / DB
> Excel CRUD — reads/writes `data/students.xlsx`. UI never imports openpyxl.
- `db.py` — `Student` dataclass, `get_all()`, `exists()`, `add()`, `update()`, `delete()`
- Auto-creates + seeds 24 sample records on first run
- `get_all()` returns newest-first (rows reversed)

### Design tokens / lookups
- `constants.py` — institutional-blue palette, status palette, shape radii,
  `PRODI`, `ANGKATAN`, `STATUS`, `STATUS_ORDER`, `PER_PAGE`

### Models
- `Student` dataclass: `nim, nama, prodi, angkatan, email, ipk, status` (in db.py)

### Data
- `data/students.xlsx` — sheet `Mahasiswa`, header row + data rows

### Config / Dependencies
- `requirements.txt` — `flet>=0.85,<1.0`, `openpyxl>=3.1,<4.0`

## Student fields
| Field    | Type  | Notes                                        |
|----------|-------|----------------------------------------------|
| nim      | str   | primary key; 6–12 digits; unique; locked on edit |
| nama     | str   | required                                     |
| prodi    | str   | required; from `C.PRODI` dropdown            |
| angkatan | int   | required; from `C.ANGKATAN` dropdown         |
| email    | str   | required; basic format check                 |
| ipk      | float | required; 0.00–4.00; shown red if < 2.5      |
| status   | str   | required; `aktif` \| `cuti` \| `do` \| `lulus` |

## Features
- Desktop table ↔ mobile card toggle
- Live search across NIM / nama / prodi / email
- Status filter chips with live counts
- Pagination (`PER_PAGE = 10`)
- Add / Edit with inline validation; Delete confirmation; toast feedback
- Row/card selection highlight

## Key decisions
- xlsx as DB: simple, no server, inspectable in Excel
- Single-file UI (main.py): easy to follow for learning
- openpyxl over pandas: lighter dependency for pure CRUD
- `db.py` is the only module that touches openpyxl
- Targets the new Flet API (`ft.run`, `page.show_dialog`/`pop_dialog`,
  `ft.Padding`, `ft.Border.all`, `ft.Alignment.*`, `ft.Colors`) — legacy
  Flet (<0.70) will not run this code

## Status
- Complete and verified against Flet 0.85.2 + openpyxl 3.1.5 (2026-06-04):
  full render + CRUD + validation paths exercised headlessly, all passing.

## Related
- `CONTEXT.md` — stack, run instructions, conventions
- `DESIGN.md` — design system and component inventory
- `CHANGELOG.md` — change history
