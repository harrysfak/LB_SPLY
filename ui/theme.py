"""
ui.theme
────────
Single source of truth for every colour, font and style constant.
Change here → changes everywhere.
"""
import tkinter as tk
from tkinter import ttk

# ── Palette ────────────────────────────────────────────────────────────────
BG   = '#0f172a'
BG2  = '#1e293b'
BG3  = '#2d3f55'
BDR  = '#334155'
TX   = '#f1f5f9'
TX2  = '#94a3b8'
TX3  = '#64748b'

TEAL  = '#14b8a6'
GREEN = '#22c55e'
RED   = '#ef4444'
AMBER = '#f59e0b'
BLUE  = '#3b82f6'
PRP   = '#a855f7'

# Status → color
STATUS_COLOR = {
    'Ανοιχτό':    GREEN,
    'Κλειστό':    BLUE,
    'Τελειωμένο': RED,
}

# Type → color
TYPE_COLOR = {
    'Υποστρώματα':  TEAL,
    'Broths':       BLUE,
    'Supplements':  PRP,
    'Βιοχημικό Κιτ': AMBER,
    'Άλλα':         TX3,
}

# ── Fonts ──────────────────────────────────────────────────────────────────
FONT      = ('Segoe UI', 10)
FONT_B    = ('Segoe UI', 10, 'bold')
FONT_S    = ('Segoe UI', 9)
FONT_SB   = ('Segoe UI', 9, 'bold')
FONT_H    = ('Segoe UI', 13, 'bold')
FONT_MONO = ('Courier New', 9)

# ── Matplotlib dark params ─────────────────────────────────────────────────
MPL_RC = {
    'figure.facecolor':    BG2,
    'axes.facecolor':      BG2,
    'savefig.facecolor':   BG2,
    'text.color':          TX2,
    'axes.labelcolor':     TX3,
    'xtick.color':         TX3,
    'ytick.color':         TX3,
    'grid.color':          BDR,
    'axes.edgecolor':      BDR,
    'legend.facecolor':    BG3,
    'legend.edgecolor':    BDR,
    'axes.spines.top':     False,
    'axes.spines.right':   False,
    'font.size':           9,
    'axes.titlesize':      11,
    'axes.titlecolor':     TX,
}


# ── ttk style setup ────────────────────────────────────────────────────────

def apply_ttk_style(root: tk.Tk) -> None:
    s = ttk.Style(root)
    s.theme_use('clam')

    s.configure('.',              background=BG2, foreground=TX,  font=FONT)
    s.configure('TFrame',        background=BG2)
    s.configure('TLabel',        background=BG2, foreground=TX)
    s.configure('TScrollbar',    background=BG3, troughcolor=BG,
                arrowcolor=TX3, borderwidth=0, gripcount=0)

    s.configure('Treeview',
                background=BG2, foreground=TX, fieldbackground=BG2,
                borderwidth=0, rowheight=28, font=FONT)
    s.configure('Treeview.Heading',
                background=BG,  foreground=TX3, borderwidth=0,
                relief='flat',  font=FONT_SB)
    s.map('Treeview',
          background=[('selected', BG3)],
          foreground=[('selected', TEAL)])

    s.configure('TCombobox',
                fieldbackground=BG3, foreground=TX, background=BG3,
                selectbackground=TEAL, arrowcolor=TX2)
    s.map('TCombobox', fieldbackground=[('readonly', BG3)])

    s.configure('TEntry',
                fieldbackground=BG3, foreground=TX,
                insertcolor=TX, borderwidth=1, relief='flat')

    # Custom tag for sidebar active item
    s.configure('Active.TLabel', foreground=TEAL, background=BG3, font=FONT_B)
    s.configure('Idle.TLabel',   foreground=TX2,  background=BG2, font=FONT)
