# CONTEXT.md
_Working context for Student Management App — Flet + Python_

## Stack
- Python 3.x + Flet **≥ 0.85** (new API — `ft.run`, `page.show_dialog`)
- openpyxl for .xlsx read/write
- No external state library — an in-memory `state` dict + `refresh()` re-render

## Run
```bash
pip install -r requirements.txt
python main.py
```

## Conventions
- `db.py` owns all Excel I/O — UI never touches openpyxl directly
- `data/students.xlsx` (sheet `Mahasiswa`) auto-created + seeded by db.py on first run
- UI calls `refresh()` after every mutation to rebuild the view

## Environment
- OS: Windows (dev machine)
- Workspace: A:\RD\Tugas1\Mobile_Programming_Flet_Python\

## References
- Flet docs: https://flet.dev/docs/
- Flet controls: https://flet.dev/docs/controls/
- openpyxl docs: https://openpyxl.readthedocs.io/
