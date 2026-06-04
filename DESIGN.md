# DESIGN.md
_Design system for Manajemen Mahasiswa — as implemented (institutional blue)_

## Overview
A cross-platform (desktop-first, mobile-ready) CRUD app for managing student
records, built in Flet (Flutter under the hood). The institutional-blue design
system is implemented 1:1 in `constants.py`; this doc describes what's shipped.

## Target users
- Teachers / academic administrative staff
- Desktop primary, mobile secondary
- Non-technical; clarity and speed over visual complexity

---

## Design tokens (implemented in `constants.py`)

### Brand — institutional blue
| Token          | Value     | Usage                                   |
|----------------|-----------|-----------------------------------------|
| PRIMARY        | `#1B5FCC` | App bar, filled buttons, active states  |
| PRIMARY_HOVER  | `#1551AE` | Hover                                   |
| PRIMARY_PRESS  | `#113F86` | Pressed                                 |
| PRIMARY_TINT   | `#EAF1FC` | Row hover / selected fill / active chip |
| PRIMARY_TINT_2 | `#D7E5FA` | Secondary tint                          |
| ON_PRIMARY     | `#FFFFFF` | Text/icons on primary                   |

### Neutrals (cool, low-chroma)
| Token         | Value     | Usage                       |
|---------------|-----------|-----------------------------|
| BG            | `#F4F6FA` | Page background             |
| SURFACE       | `#FFFFFF` | Cards, table, dialogs       |
| SURFACE_2     | `#FAFBFD` | Zebra / subtle fill         |
| BORDER        | `#E4E9F1` | Card & table outline        |
| BORDER_STRONG | `#D2DAE6` | Stronger outline / controls |
| DIVIDER       | `#EDF1F7` | Row / column lines          |
| TEXT          | `#19222E` | Primary text                |
| TEXT_2        | `#51607A` | Secondary text              |
| MUTED         | `#8694A9` | Tertiary / placeholders     |

### Status palette (label, fg, bg, border)
| Status | Label | fg        | bg        | border    |
|--------|-------|-----------|-----------|-----------|
| aktif  | Aktif | `#1B7F4C` | `#E7F4EC` | `#C6E6D2` |
| cuti   | Cuti  | `#8A5A00` | `#FBF1D6` | `#F0DEA8` |
| do     | DO    | `#C23A2E` | `#FBEAE7` | `#F2CEC8` |
| lulus  | Lulus | `#0F766E` | `#DCF1EE` | `#BBE3DD` |

- DANGER `#D33A2C` (delete) · TOAST_BG `#19222E`

### Shape & type
- Radii: `R_SM=6 · R=8 · R_LG=12 · R_PILL=999`
- Font family: Segoe UI (UI) · Consolas (NIM, IPK, email — monospace)

---

## Component inventory (as built)

### 1. Stage bar
- Caption: "Pratinjau interaktif — klik baris untuk memilih…"
- Right: segmented Desktop / Mobile toggle (active = PRIMARY)

### 2. App bar
- Left: "SM" badge + "Manajemen Mahasiswa" (+ subtitle on desktop)
- Right: "Tambah Mahasiswa" filled button ("Tambah" on mobile)
- Background: PRIMARY

### 3. Toolbar
- Left: "Semua Mahasiswa" heading + "{n} terdaftar" count (desktop)
- Right: search field (NIM / nama / prodi / email)
- Below: status filter chips with live counts (Semua + 4 statuses)

### 4a. Desktop DataTable
Columns: NIM · NAMA LENGKAP · PROGRAM STUDI · ANGKATAN · EMAIL KAMPUS ·
IPK (numeric, red if < 2.5) · STATUS (badge) · AKSI (edit / delete icons)
- Row hover + click-to-select highlight (PRIMARY_TINT)

### 4b. Mobile card list
- One card per student: name + NIM, status badge, prodi, angkatan, email,
  divider, IPK + action icons. Selected card gets BORDER_STRONG outline.

### 5. Pagination
- 10 per page; prev/next chevrons + numbered page buttons
- "Menampilkan {from}-{to} dari {total} mahasiswa"

### 6. Add / Edit dialog (AlertDialog)
Title: "Tambah Mahasiswa" / "Edit Mahasiswa"
Fields: NIM · Nama Lengkap · Program Studi (dropdown) · Angkatan (dropdown) ·
Email Kampus · IPK · Status (dropdown)
Validation (inline, red error text):
- NIM required, 6–12 digits, unique (locked when editing)
- Nama required · Prodi required · Angkatan required
- Email required + basic format check
- IPK required, 0.00–4.00 · Status required
Actions: Batal (text) · Simpan / Simpan Perubahan (filled)

### 7. Delete confirmation (AlertDialog)
Icon + "Hapus Mahasiswa?" + "Data {nama} (NIM {nim}) akan dihapus secara
permanen dan tidak dapat dibatalkan." Actions: Batal · Hapus (danger).

### 8. Toast
Bottom-center pill, auto-dismiss ~2.6s. Check icon (ok) / info icon (warn).

### 9. Empty states
- No data at all: "Belum ada data mahasiswa"
- No search/filter match: "Tidak ada hasil"

---

## Constraints
- Flet uses Material Design 3 as its base
- Colors via `ft.Colors.*` or hex strings; no CSS — styling is Python API
- Custom fonts must be `.ttf`/`.otf` loaded via `page.fonts`
- Consolas/Segoe UI are Windows system fonts; substitute per-platform if needed

## Open design questions (not yet implemented)
| Topic         | Current        | Question                          |
|---------------|----------------|-----------------------------------|
| Dark mode     | Light only     | Support it?                       |
| Sorting       | None           | Sortable table columns?           |
| Avatar        | None           | Initials avatar by name?          |
| Logo/branding | "SM" badge     | Real school logo?                 |
| Export        | None           | Export filtered list to xlsx/CSV? |

---

## Related files
- `ARCHITECTURE.md` — layer map and file structure
- `CONTEXT.md` — stack, run instructions, conventions
- `constants.py` — the source of truth for all tokens above
- `main.py` — all UI code
