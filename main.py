"""
main.py -- Manajemen Mahasiswa (Student Management), Flet + Excel.

WHY THIS IS BUILT THE WAY IT IS
-------------------------------
Flet's current client renders some Material controls unreliably, so this app
deliberately sticks to primitives that always render:
  * NO DataTable           -> the student table is a grid of Container/Row/Text
  * NO modal AlertDialog    -> Add/Edit and Delete are INLINE panels (a "mode")
  * NO page.overlay         -> feedback is an inline banner
This is what makes "add a student" actually work across desktop/web/mobile.

MENTAL MODEL
------------
The whole app is one function, `main(page)`. All UI is rebuilt from a single
in-memory `state` dict by `render()`. There is no fine-grained reactivity:
when something changes we mutate `state` and call `render()`, which throws away
the old control tree and builds a fresh one. Simple and predictable.

`state["mode"]` is the screen switch: "list" (table) | "form" (add/edit) |
"delete" (confirm). Navigation helpers (go_list/go_add/go_edit/go_delete) set
the mode and re-render.

Data lives in data/students.xlsx and is reached only through db.py.
Run locally:  python main.py   (opens in your browser)
"""

import math
import flet as ft

import constants as C          # colors, status palette, dropdown lists, PER_PAGE
import db                      # Excel CRUD layer (the "database")
from db import Student         # the record dataclass


def main(page: ft.Page) -> None:
    """App entrypoint. Flet calls this once per user session with a `page`."""
    # --- page-level chrome ---
    page.title = "Manajemen Mahasiswa"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = C.BG
    page.theme = ft.Theme(font_family="Segoe UI")
    page.padding = ft.Padding(20, 18, 20, 32)
    page.scroll = ft.ScrollMode.AUTO

    # Single source of truth for the whole UI. Every handler mutates this and
    # then calls render(); the view is always a pure function of `state`.
    state = {
        "students": db.get_all(),  # cached list of all students (refreshed via reload())
        "query": "",               # current search text
        "filter": "semua",         # active status filter: semua | aktif | cuti | do | lulus
        "page": 1,                 # current pagination page (1-based)
        "mode": "list",            # which screen: list | form | delete
        "editing": None,           # Student being edited, or None when adding
        "deleting": None,          # Student pending deletion
        "msg": "",                 # one-shot feedback banner text
        "msg_kind": "ok",          # banner style: ok | warn
    }
    form = {}  # live TextField/Dropdown controls, populated while in form mode

    # ---------- data helpers ----------
    def reload():
        """Re-read all students from the spreadsheet into state (after a write)."""
        state["students"] = db.get_all()

    def counts():
        """Return how many students fall in each status, plus a 'semua' total.
        Drives the numbers shown on the filter chips."""
        c = {"semua": len(state["students"])}
        for k in C.STATUS_ORDER:
            c[k] = 0
        for s in state["students"]:
            c[s.status] = c.get(s.status, 0) + 1
        return c

    def filtered():
        """Apply the active status filter + search query to the student list.
        Search matches NIM, name, prodi, or email (case-insensitive)."""
        q = state["query"].strip().lower()
        out = []
        for s in state["students"]:
            if state["filter"] != "semua" and s.status != state["filter"]:
                continue
            if q and q not in (s.nim + " " + s.nama + " " + s.prodi + " " + s.email).lower():
                continue
            out.append(s)
        return out

    def flash(msg, kind="ok"):
        """Queue a one-shot banner message (shown on the next render, then cleared)."""
        state["msg"] = msg
        state["msg_kind"] = kind

    # ---------- small UI builders ----------
    def status_badge(key):
        """Colored pill for a status (Aktif/Cuti/DO/Lulus), styled from constants."""
        label, fg, bg, bd = C.STATUS[key]
        return ft.Container(
            content=ft.Row([ft.Container(width=7, height=7, border_radius=4, bgcolor=fg),
                            ft.Text(label, color=fg, size=12, weight=ft.FontWeight.W_600)],
                           spacing=6, tight=True),
            bgcolor=bg, border=ft.Border.all(1, bd), border_radius=C.R_PILL,
            padding=ft.Padding(8, 4, 10, 4))

    def ipk_text(s):
        """GPA text, shown in red when below 2.5 so at-risk students stand out."""
        return ft.Text(f"{s.ipk:.2f}", font_family="Consolas", size=14,
                       weight=ft.FontWeight.W_700, color=C.BAD if s.ipk < 2.5 else C.TEXT)

    def row_actions(s):
        """Edit + delete icon buttons for one student row. Closures capture `s`."""
        return ft.Row([
            ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_size=18, icon_color=C.TEXT_2,
                          tooltip="Edit", on_click=lambda e, st=s: go_edit(st)),
            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=C.DANGER,
                          tooltip="Hapus", on_click=lambda e, st=s: go_delete(st)),
        ], spacing=0, tight=True, alignment=ft.MainAxisAlignment.END)

    def btn(label, on_click, icon=None, kind="primary"):
        """Factory for the three button styles used in the app:
        primary (filled blue), danger (filled red), ghost (outlined)."""
        bg = {"primary": C.PRIMARY, "danger": C.DANGER}.get(kind, C.PRIMARY)
        if kind == "ghost":
            return ft.OutlinedButton(label, icon=icon, on_click=on_click,
                                     style=ft.ButtonStyle(color=C.TEXT_2,
                                                          shape=ft.RoundedRectangleBorder(radius=C.R)))
        return ft.FilledButton(label, icon=icon, on_click=on_click,
                               style=ft.ButtonStyle(bgcolor=bg, color="#FFFFFF",
                                                    shape=ft.RoundedRectangleBorder(radius=C.R),
                                                    padding=ft.Padding(16, 14, 16, 14)))

    # ---------- student table (hand-built grid, NOT ft.DataTable) ----------
    # (header label, fixed column width in px). width=None means "flex/expand".
    COLS = [("NIM", 108), ("NAMA LENGKAP", None), ("PRODI", 150), ("ANGKATAN", 84),
            ("EMAIL", 188), ("IPK", 60), ("STATUS", 100), ("AKSI", 92)]

    def cell(content, w):
        """One table cell. Fixed width when given, otherwise expands to fill."""
        return ft.Container(content=content, width=w, expand=(w is None),
                            padding=ft.Padding(6, 0, 6, 0), alignment=ft.Alignment.CENTER_LEFT)

    def etext(v, **kw):
        """Single-line ellipsized text, so long values never break row height."""
        kw.setdefault("size", 13)
        return ft.Text(v, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, **kw)

    def table(rows):
        """Render the given page of students as a header row + one Row per student.
        Wrapped in a horizontal scroll so narrow screens can pan the columns."""
        header = ft.Container(
            bgcolor=C.SURFACE_2, padding=ft.Padding(10, 12, 10, 12),
            border=ft.Border(bottom=ft.BorderSide(1, C.BORDER)),
            content=ft.Row([cell(ft.Text(t, size=11.5, weight=ft.FontWeight.W_700, color=C.MUTED), w)
                            for (t, w) in COLS], spacing=0))
        out = [header]
        for s in rows:
            # column order here must match COLS above
            out.append(ft.Container(
                bgcolor=C.SURFACE, border=ft.Border(bottom=ft.BorderSide(1, C.DIVIDER)),
                padding=ft.Padding(10, 9, 10, 9),
                content=ft.Row([
                    cell(etext(s.nim, font_family="Consolas", color=C.TEXT), 108),
                    cell(etext(s.nama, weight=ft.FontWeight.W_600, color=C.TEXT), None),
                    cell(etext(s.prodi, color=C.TEXT_2), 150),
                    cell(etext(str(s.angkatan), color=C.TEXT_2), 84),
                    cell(etext(s.email, color=C.TEXT_2), 188),
                    cell(ipk_text(s), 60),
                    cell(status_badge(s.status), 100),
                    cell(row_actions(s), 92),
                ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)))
        grid = ft.Column(out, spacing=0)
        return ft.Container(content=ft.Row([ft.Container(grid, width=1060)],
                                           scroll=ft.ScrollMode.AUTO))

    def empty(icon, title, sub):
        """Centered empty-state block (used for 'no data' and 'no search results')."""
        return ft.Container(
            padding=ft.Padding(40, 56, 40, 56), alignment=ft.Alignment.CENTER,
            content=ft.Column([
                ft.Container(content=ft.Icon(icon, color=C.PRIMARY, size=28), width=56, height=56,
                             border_radius=28, bgcolor=C.PRIMARY_TINT, alignment=ft.Alignment.CENTER),
                ft.Text(title, size=16, weight=ft.FontWeight.W_700, color=C.TEXT),
                ft.Text(sub, size=13.5, color=C.MUTED, text_align=ft.TextAlign.CENTER, width=360),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10))

    # ---------- filter chips / pagination ----------
    def chip(label, count, key):
        """One filter chip. Highlighted when it is the active filter; click sets it."""
        active = state["filter"] == key
        return ft.Container(
            content=ft.Row([
                ft.Text(label, size=13, weight=ft.FontWeight.W_600,
                        color="#FFFFFF" if active else C.TEXT_2),
                ft.Text(str(count), size=11, weight=ft.FontWeight.W_700,
                        color="#FFFFFF" if active else C.MUTED),
            ], spacing=7, tight=True),
            bgcolor=C.PRIMARY if active else C.SURFACE,
            border=ft.Border.all(1, C.PRIMARY if active else C.BORDER_STRONG),
            border_radius=C.R_PILL, padding=ft.Padding(13, 7, 13, 7), ink=True,
            on_click=lambda e, k=key: set_filter(k))

    def pager(total, total_pages):
        """Prev / numbered pages / next. Each number jumps to that page."""
        def num(n):
            active = n == state["page"]
            return ft.Container(
                content=ft.Text(str(n), size=13, weight=ft.FontWeight.W_600,
                                color="#FFFFFF" if active else C.TEXT_2),
                width=34, height=34, alignment=ft.Alignment.CENTER, border_radius=C.R_SM,
                bgcolor=C.PRIMARY if active else C.SURFACE,
                border=ft.Border.all(1, C.PRIMARY if active else C.BORDER_STRONG),
                ink=True, on_click=lambda e, p=n: set_page(p))
        prev = ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_size=18, icon_color=C.TEXT_2,
                             disabled=state["page"] == 1, on_click=lambda e: set_page(state["page"] - 1))
        nxt = ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_size=18, icon_color=C.TEXT_2,
                            disabled=state["page"] == total_pages,
                            on_click=lambda e: set_page(state["page"] + 1))
        return ft.Row([prev] + [num(n) for n in range(1, total_pages + 1)] + [nxt],
                      spacing=4, wrap=True)

    # ---------- inline Add / Edit form ----------
    def build_form_fields():
        """Create the 7 input controls for the form and stash them in `form`.
        Called when entering form mode so values survive re-renders (validation
        only mutates these existing controls, it doesn't rebuild them).
        When editing, fields are pre-filled and NIM is locked (it's the key)."""
        s = state["editing"]
        ed = s is not None
        form.clear()
        form["nim"] = ft.TextField(label="NIM", value=s.nim if ed else "", disabled=ed,
                                   hint_text="cth. 2021103001", border_color=C.BORDER_STRONG,
                                   focused_border_color=C.PRIMARY, text_size=14)
        form["nama"] = ft.TextField(label="Nama Lengkap", value=s.nama if ed else "",
                                    hint_text="cth. Rangga Aditya", border_color=C.BORDER_STRONG,
                                    focused_border_color=C.PRIMARY, text_size=14)
        form["prodi"] = ft.Dropdown(label="Program Studi", value=s.prodi if ed else None,
                                    options=[ft.dropdown.Option(p) for p in C.PRODI],
                                    border_color=C.BORDER_STRONG, text_size=14)
        form["angkatan"] = ft.Dropdown(label="Angkatan", value=str(s.angkatan) if ed else None,
                                       options=[ft.dropdown.Option(str(a)) for a in C.ANGKATAN],
                                       border_color=C.BORDER_STRONG, text_size=14)
        form["email"] = ft.TextField(label="Email Kampus", value=s.email if ed else "",
                                     hint_text="nama@student.univ.ac.id", border_color=C.BORDER_STRONG,
                                     focused_border_color=C.PRIMARY, text_size=14)
        form["ipk"] = ft.TextField(label="IPK", value=f"{s.ipk:.2f}" if ed else "",
                                   hint_text="0.00 - 4.00", border_color=C.BORDER_STRONG,
                                   focused_border_color=C.PRIMARY, text_size=14)
        form["status"] = ft.Dropdown(label="Status", value=s.status if ed else None,
                                     options=[ft.dropdown.Option(key=k, text=C.STATUS[k][0])
                                              for k in C.STATUS_ORDER],
                                     border_color=C.BORDER_STRONG, text_size=14)

    def validate():
        """Check every field, attach inline error_text where invalid, and return
        True only if all pass. Rules: NIM = 6-12 digits and unique (new records);
        name/prodi/angkatan/status required; email must look like an address;
        IPK must parse to a number in 0.00-4.00 (comma accepted as decimal)."""
        for f in form.values():
            f.error_text = None
        ok = True
        ed = state["editing"] is not None
        nim = (form["nim"].value or "").strip()
        existing = [x.nim for x in state["students"]]
        if not nim:
            form["nim"].error_text = "NIM wajib diisi."; ok = False
        elif not (nim.isdigit() and 6 <= len(nim) <= 12):
            form["nim"].error_text = "NIM harus 6-12 digit angka."; ok = False
        elif (not ed) and nim in existing:   # uniqueness only matters for new records
            form["nim"].error_text = "NIM ini sudah terdaftar."; ok = False
        if not (form["nama"].value or "").strip():
            form["nama"].error_text = "Nama wajib diisi."; ok = False
        if not form["prodi"].value:
            form["prodi"].error_text = "Pilih program studi."; ok = False
        if not form["angkatan"].value:
            form["angkatan"].error_text = "Pilih angkatan."; ok = False
        email = (form["email"].value or "").strip()
        if not email:
            form["email"].error_text = "Email wajib diisi."; ok = False
        elif not ("@" in email and "." in email.split("@")[-1] and " " not in email):
            form["email"].error_text = "Format email tidak valid."; ok = False
        ipk_raw = (form["ipk"].value or "").strip().replace(",", ".")
        try:
            v = float(ipk_raw)
            if v < 0 or v > 4:
                form["ipk"].error_text = "IPK harus 0.00 - 4.00."; ok = False
        except ValueError:
            form["ipk"].error_text = "IPK harus angka 0.00 - 4.00."; ok = False
        if not form["status"].value:
            form["status"].error_text = "Pilih status."; ok = False
        page.update()   # push the error_text changes to the screen
        return ok

    def save_form(e=None):
        """Validate, then write to the spreadsheet (update if editing, else add),
        refresh the cache, show a confirmation, and return to the list."""
        if not validate():
            return
        rec = Student(
            nim=(form["nim"].value or "").strip(),
            nama=(form["nama"].value or "").strip(),
            prodi=form["prodi"].value,
            angkatan=int(form["angkatan"].value),
            email=(form["email"].value or "").strip(),
            ipk=round(float((form["ipk"].value or "").strip().replace(",", ".")), 2),
            status=form["status"].value,
        )
        if state["editing"] is not None:
            db.update(rec); flash("Perubahan disimpan.")
        else:
            db.add(rec); flash("Mahasiswa berhasil ditambahkan.")
        reload()
        go_list()

    def form_panel():
        """The Add/Edit screen: title, the 7 fields laid out in rows, Batal/Simpan."""
        ed = state["editing"] is not None

        def two(a, b):
            """Put two fields side by side, each taking half the width."""
            return ft.Row([ft.Container(a, expand=True), ft.Container(b, expand=True)], spacing=16)

        return ft.Container(
            padding=ft.Padding(22, 20, 22, 22),
            content=ft.Column([
                ft.Text("Edit Mahasiswa" if ed else "Tambah Mahasiswa",
                        size=18, weight=ft.FontWeight.W_700, color=C.TEXT),
                ft.Text("Perbarui data mahasiswa." if ed else
                        "Lengkapi data berikut untuk menambahkan mahasiswa baru.",
                        size=13.5, color=C.TEXT_2),
                ft.Container(height=6),
                two(form["nim"], form["nama"]),
                two(form["prodi"], form["angkatan"]),
                form["email"],
                two(form["ipk"], form["status"]),
                ft.Container(height=8),
                ft.Row([
                    btn("Batal", lambda e: go_list(), kind="ghost"),
                    btn("Simpan Perubahan" if ed else "Simpan",
                        save_form, icon=ft.Icons.SAVE if ed else ft.Icons.PERSON_ADD_ALT_1),
                ], alignment=ft.MainAxisAlignment.END, spacing=10),
            ], spacing=14))

    def delete_panel():
        """The Delete confirmation screen for state['deleting']."""
        s = state["deleting"]

        def confirm(e):
            db.delete(s.nim)
            reload()
            flash("Data mahasiswa dihapus.", "warn")
            go_list()

        return ft.Container(
            padding=ft.Padding(22, 24, 22, 24), alignment=ft.Alignment.CENTER,
            content=ft.Column([
                ft.Container(content=ft.Icon(ft.Icons.DELETE_OUTLINE, color=C.DANGER, size=24),
                             width=52, height=52, border_radius=26, bgcolor=C.BAD_BG,
                             alignment=ft.Alignment.CENTER),
                ft.Text("Hapus Mahasiswa?", size=18, weight=ft.FontWeight.W_700, color=C.TEXT),
                ft.Text(f"Data {s.nama} (NIM {s.nim}) akan dihapus permanen "
                        "dan tidak dapat dibatalkan.", size=13.5, color=C.TEXT_2,
                        text_align=ft.TextAlign.CENTER, width=420),
                ft.Container(height=6),
                ft.Row([btn("Batal", lambda e: go_list(), kind="ghost"),
                        btn("Hapus", confirm, icon=ft.Icons.DELETE_OUTLINE, kind="danger")],
                       alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10))

    # ---------- navigation + event handlers ----------
    # Each of these mutates `state` then calls render() to repaint the screen.
    def go_list():
        """Return to the student list, clearing any edit/delete context."""
        state["mode"] = "list"; state["editing"] = None; state["deleting"] = None
        render()

    def go_add():
        """Open a blank Add form."""
        state["mode"] = "form"; state["editing"] = None
        build_form_fields(); render()

    def go_edit(s):
        """Open the Edit form pre-filled with student `s`."""
        state["mode"] = "form"; state["editing"] = s
        build_form_fields(); render()

    def go_delete(s):
        """Open the delete confirmation for student `s`."""
        state["mode"] = "delete"; state["deleting"] = s
        render()

    def set_query(v):
        """Live-search handler; resets to page 1 so results start at the top."""
        state["query"] = v; state["page"] = 1; render()

    def set_filter(k):
        """Status-chip handler; resets to page 1."""
        state["filter"] = k; state["page"] = 1; render()

    def set_page(p):
        """Pagination handler."""
        state["page"] = p; render()

    # Search box is created once (kept across renders) so focus/caret survive typing.
    search_field = ft.TextField(
        hint_text="Cari nama, NIM, prodi, atau email...", prefix_icon=ft.Icons.SEARCH,
        on_change=lambda e: set_query(e.control.value), border_color=C.BORDER_STRONG,
        focused_border_color=C.PRIMARY, bgcolor=C.SURFACE, text_size=14, height=44, expand=True)

    # `root` is the single container we repaint. Added to the page once; render()
    # only swaps its `.controls`.
    root = ft.Column(spacing=16)
    page.add(ft.Container(content=root, alignment=ft.Alignment.TOP_CENTER))

    # ---------- top-level screen sections ----------
    def header_bar():
        """Blue app header: brand on the left; on the right a 'Tambah' button in
        list mode, or a 'Kembali' (back) button while in a form/delete panel."""
        right = (btn("Tambah Mahasiswa", lambda e: go_add(), icon=ft.Icons.PERSON_ADD_ALT_1)
                 if state["mode"] == "list" else
                 btn("Kembali", lambda e: go_list(), icon=ft.Icons.ARROW_BACK, kind="ghost"))
        brand = ft.Row([
            ft.Container(content=ft.Text("SM", color="#FFFFFF", weight=ft.FontWeight.W_800, size=15),
                         width=36, height=36, border_radius=9,
                         bgcolor=ft.Colors.with_opacity(0.18, "#FFFFFF"),
                         alignment=ft.Alignment.CENTER),
            ft.Column([ft.Text("Manajemen Mahasiswa", color="#FFFFFF", size=17,
                               weight=ft.FontWeight.W_700),
                       ft.Text("Sistem Informasi Akademik",
                               color=ft.Colors.with_opacity(0.82, "#FFFFFF"), size=11.5)], spacing=1),
        ], spacing=12)
        return ft.Container(content=ft.Row([brand, right],
                                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            bgcolor=C.PRIMARY, padding=ft.Padding(20, 14, 20, 14),
                            border_radius=C.R_LG)

    def banner():
        """Inline success/warning message bar (replaces a pop-up toast)."""
        if not state["msg"]:
            return ft.Container(height=0)
        warn = state["msg_kind"] == "warn"
        return ft.Container(
            content=ft.Row([ft.Icon(ft.Icons.INFO if warn else ft.Icons.CHECK_CIRCLE,
                                    color=C.WARN if warn else C.OK, size=18),
                            ft.Text(state["msg"], size=13.5, color=C.TEXT,
                                    weight=ft.FontWeight.W_500)], spacing=8, tight=True),
            bgcolor=C.WARN_BG if warn else C.OK_BG,
            border=ft.Border.all(1, C.WARN_BD if warn else C.OK_BD),
            border_radius=C.R, padding=ft.Padding(12, 9, 12, 9))

    def card(content):
        """White rounded surface used to frame the table and the panels."""
        return ft.Container(content=content, bgcolor=C.SURFACE, border=ft.Border.all(1, C.BORDER),
                            border_radius=C.R_LG, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    def list_body():
        """Build the whole list screen: toolbar (title + search + chips), then the
        table (or an empty state), then the pagination footer. Handles paging math."""
        c = counts()
        chips = ft.Row([chip("Semua", c["semua"], "semua")] +
                       [chip(C.STATUS[k][0], c[k], k) for k in C.STATUS_ORDER],
                       spacing=8, wrap=True)
        toolbar = ft.Container(
            padding=ft.Padding(20, 18, 20, 6),
            content=ft.Column([
                ft.Row([ft.Text("Semua Mahasiswa", size=18, weight=ft.FontWeight.W_700, color=C.TEXT),
                        ft.Text(f"{c['semua']} terdaftar", size=13, color=C.MUTED)],
                       spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=4),
                search_field,
                ft.Container(height=2),
                chips,
            ], spacing=10))

        # paging math on the filtered result set
        rows_all = filtered()
        total = len(rows_all)
        total_pages = max(1, math.ceil(total / C.PER_PAGE))
        if state["page"] > total_pages:        # clamp if a filter shrank the list
            state["page"] = total_pages
        start = (state["page"] - 1) * C.PER_PAGE
        page_rows = rows_all[start:start + C.PER_PAGE]

        # three cases: no data at all, data but no match, or rows to show
        if len(state["students"]) == 0:
            inner = empty(ft.Icons.GROUP, "Belum ada data mahasiswa",
                          "Klik 'Tambah Mahasiswa' untuk mulai menambahkan data.")
            foot = None
        elif total == 0:
            inner = empty(ft.Icons.SEARCH_OFF, "Tidak ada hasil",
                          "Tidak ada mahasiswa yang cocok dengan pencarian atau filter.")
            foot = None
        else:
            inner = table(page_rows)
            frm = start + 1
            to = min(state["page"] * C.PER_PAGE, total)
            foot = ft.Container(
                padding=ft.Padding(20, 14, 20, 16),
                content=ft.Row([
                    ft.Text(f"Menampilkan {frm}-{to} dari {total} mahasiswa", size=13, color=C.TEXT_2),
                    pager(total, total_pages),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True, run_spacing=10))

        children = [toolbar, inner]
        if foot is not None:
            children.append(foot)
        return card(ft.Column(children, spacing=0))

    # ---------- the render loop ----------
    def render():
        """Rebuild the entire screen from `state` and push it to the browser.
        Picks the body by mode, prepends the header (+ banner if a message is
        queued), then clears the one-shot message so it shows exactly once."""
        body = (list_body() if state["mode"] == "list"
                else card(form_panel()) if state["mode"] == "form"
                else card(delete_panel()))
        controls = [header_bar()]
        if state["msg"]:
            controls.append(banner())
        controls.append(body)
        root.controls = controls
        page.update()
        state["msg"] = ""   # consume the one-shot banner

    render()   # first paint


if __name__ == "__main__":
    # Browser renderer (reliable on Flet 0.85). Remove view=... for a native window.
    ft.run(main, view=ft.AppView.WEB_BROWSER)
