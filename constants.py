"""
constants.py -- design tokens & lookups for Manajemen Mahasiswa.

Pure data, no logic. Everything visual (colors, radii) and every fixed list
(programs, entry years, statuses) lives here so the rest of the app references
names like C.PRIMARY instead of hard-coded hex/strings. Change the look or the
dropdown choices in one place here and the whole UI follows.

Colors are plain hex strings, which Flet accepts anywhere a color is expected.
"""

# == Brand: institutional blue ===============================================
PRIMARY        = "#1B5FCC"   # app bar, filled buttons, active chip/page
PRIMARY_HOVER  = "#1551AE"
PRIMARY_PRESS  = "#113F86"
PRIMARY_TINT   = "#EAF1FC"   # light fill behind selected/active items
PRIMARY_TINT_2 = "#D7E5FA"
ON_PRIMARY     = "#FFFFFF"   # text/icons drawn on top of PRIMARY

# == Neutrals (cool grays) ===================================================
BG            = "#F4F6FA"    # page background
SURFACE       = "#FFFFFF"    # cards, table rows, panels
SURFACE_2     = "#FAFBFD"    # subtle fill (table header)
BORDER        = "#E4E9F1"    # card / table outline
BORDER_STRONG = "#D2DAE6"    # input borders, stronger dividers
DIVIDER       = "#EDF1F7"    # between table rows

TEXT   = "#19222E"           # primary text
TEXT_2 = "#51607A"           # secondary text
MUTED  = "#8694A9"           # hints, placeholders, empty states

# == Status palette ==========================================================
# Each status has a (foreground, background, border) trio for its badge/chip.
OK,   OK_BG,   OK_BD   = "#1B7F4C", "#E7F4EC", "#C6E6D2"   # Aktif (active)
WARN, WARN_BG, WARN_BD = "#8A5A00", "#FBF1D6", "#F0DEA8"   # Cuti  (on leave)
BAD,  BAD_BG,  BAD_BD  = "#C23A2E", "#FBEAE7", "#F2CEC8"   # DO    (dropped out) / low-GPA red
DONE, DONE_BG, DONE_BD = "#0F766E", "#DCF1EE", "#BBE3DD"   # Lulus (graduated)

DANGER       = "#D33A2C"     # delete button
DANGER_HOVER = "#B82E22"

TOAST_BG = "#19222E"         # (legacy) dark toast background

# == Shape (corner radii, px) ================================================
R_SM, R, R_LG, R_PILL = 6, 8, 12, 999   # small / default / large / fully-rounded

# == Lookups (dropdown options) ==============================================
PRODI = [
    "Teknik Informatika", "Sistem Informasi", "Teknik Elektro", "Teknik Sipil",
    "Manajemen", "Akuntansi", "Ilmu Hukum", "Psikologi",
    "Ilmu Komunikasi", "Desain Komunikasi Visual", "Arsitektur", "Kedokteran",
]

ANGKATAN = [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019]   # entry years (newest first)

# status key -> (display label, fg, bg, border). Keys are what db stores.
STATUS = {
    "aktif": ("Aktif", OK,   OK_BG,   OK_BD),
    "cuti":  ("Cuti",  WARN, WARN_BG, WARN_BD),
    "do":    ("DO",    BAD,  BAD_BG,  BAD_BD),
    "lulus": ("Lulus", DONE, DONE_BG, DONE_BD),
}
STATUS_ORDER = ["aktif", "cuti", "do", "lulus"]   # fixed order for chips/dropdown

PER_PAGE = 10   # rows per page in the student table
