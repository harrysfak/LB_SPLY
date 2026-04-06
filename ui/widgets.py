"""
ui.widgets
──────────
Reusable, zero-business-logic UI primitives.
Every widget here is generic — it knows nothing about Supply or DataManager.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ui.theme import (
    BG, BG2, BG3, BDR, TX, TX2, TX3, TEAL,
    FONT, FONT_B, FONT_S, FONT_SB,
)


# ── FlatButton ─────────────────────────────────────────────────────────────

class FlatButton(tk.Button):
    """
    A border-less button with hover effect.
    bg / fg are the normal state colors.
    """
    def __init__(self, parent, text: str, command: Callable,
                 bg: str = BG3, fg: str = TX,
                 font=FONT_B, padx: int = 14, pady: int = 6,
                 **kwargs):
        self._bg = bg
        hover = _lighten(bg) if bg != BG3 else BG3
        super().__init__(
            parent, text=text, command=command,
            bg=bg, fg=fg, font=font,
            relief='flat', padx=padx, pady=pady,
            activebackground=hover, activeforeground=fg,
            cursor='hand2', bd=0, **kwargs,
        )
        self.bind('<Enter>', lambda _: self.config(bg=_lighten(bg)))
        self.bind('<Leave>', lambda _: self.config(bg=bg))

    def set_text(self, text: str) -> None:
        self.config(text=text)


def _lighten(hex_col: str) -> str:
    try:
        r = min(255, int(hex_col[1:3], 16) + 28)
        g = min(255, int(hex_col[3:5], 16) + 28)
        b = min(255, int(hex_col[5:7], 16) + 28)
        return f'#{r:02x}{g:02x}{b:02x}'
    except Exception:
        return hex_col


# ── StatCard ───────────────────────────────────────────────────────────────

class StatCard(tk.Frame):
    """Coloured metric card with a big number."""
    def __init__(self, parent, title: str, value, color: str = TEAL, sub: str = ''):
        super().__init__(parent, bg=BG3, padx=16, pady=14)
        tk.Label(self, text=title.upper(), bg=BG3, fg=TX3,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w')
        self._val_label = tk.Label(self, text=str(value), bg=BG3, fg=color,
                                   font=('Segoe UI', 26, 'bold'))
        self._val_label.pack(anchor='w')
        if sub:
            tk.Label(self, text=sub, bg=BG3, fg=TX3, font=FONT_S).pack(anchor='w')

    def update_value(self, value) -> None:
        self._val_label.config(text=str(value))


# ── ScrollableFrame ────────────────────────────────────────────────────────

class ScrollableFrame(tk.Frame):
    """
    A vertically scrollable container.
    Put child widgets inside .inner.
    """
    def __init__(self, parent, bg: str = BG2, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        vsb = ttk.Scrollbar(self, orient='vertical')
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0,
                                yscrollcommand=vsb.set)
        vsb.config(command=self.canvas.yview)
        vsb.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win  = self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.inner.bind('<Configure>', self._on_inner)
        self.canvas.bind('<Configure>', self._on_canvas)
        self.canvas.bind_all('<MouseWheel>', self._on_scroll)

    def _on_inner(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas(self, e):
        self.canvas.itemconfig(self._win, width=e.width)

    def _on_scroll(self, e):
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units')


# ── SearchBar ──────────────────────────────────────────────────────────────

class SearchBar(tk.Frame):
    """Search input with an icon prefix and an optional clear button."""
    def __init__(self, parent, placeholder: str = 'Αναζήτηση…',
                 on_change: Optional[Callable] = None, **kwargs):
        super().__init__(parent, bg=BG2, **kwargs)
        self._var = tk.StringVar()
        if on_change:
            self._var.trace_add('write', lambda *_: on_change(self._var.get()))

        tk.Label(self, text='🔍', bg=BG2, fg=TX3, font=FONT_S).pack(side='left')
        e = tk.Entry(self, textvariable=self._var, bg=BG3, fg=TX,
                     insertbackground=TX, relief='flat', font=FONT,
                     bd=0, highlightthickness=1,
                     highlightbackground=BDR, highlightcolor=TEAL,
                     width=30)
        e.pack(side='left', padx=(4, 0), fill='x', expand=True)

    @property
    def value(self) -> str:
        return self._var.get()

    def set(self, v: str) -> None:
        self._var.set(v)


# ── FilterCombo ────────────────────────────────────────────────────────────

class FilterCombo(tk.Frame):
    """Label + combobox pair for filter dropdowns."""
    def __init__(self, parent, label: str, choices: list[str],
                 on_change: Optional[Callable] = None, width: int = 14, **kwargs):
        super().__init__(parent, bg=BG2, **kwargs)
        tk.Label(self, text=label, bg=BG2, fg=TX2, font=FONT_S).pack(side='left', padx=(0, 4))
        self._var = tk.StringVar(value=choices[0])
        cb = ttk.Combobox(self, textvariable=self._var, values=choices,
                          state='readonly', font=FONT, width=width)
        cb.pack(side='left')
        if on_change:
            self._var.trace_add('write', lambda *_: on_change(self._var.get()))

    @property
    def value(self) -> str:
        return self._var.get()


# ── Separator ─────────────────────────────────────────────────────────────

def hsep(parent, padx: int = 0, pady: int = 0) -> tk.Frame:
    f = tk.Frame(parent, bg=BDR, height=1)
    f.pack(fill='x', padx=padx, pady=pady)
    return f


def vsep(parent) -> tk.Frame:
    return tk.Frame(parent, bg=BDR, width=1)


# ── StatusBar ─────────────────────────────────────────────────────────────

class StatusBar(tk.Frame):
    """Bottom bar with file info + message."""
    def __init__(self, parent):
        super().__init__(parent, bg=BG, pady=4)
        self._file_lbl = tk.Label(self, text='Κανένα αρχείο φορτωμένο',
                                  bg=BG, fg=TX3, font=FONT_S, anchor='w')
        self._file_lbl.pack(side='left', padx=12)
        self._msg_lbl  = tk.Label(self, text='', bg=BG, fg=TEAL,
                                  font=FONT_S, anchor='e')
        self._msg_lbl.pack(side='right', padx=12)

    def set_file(self, filename: str, n_supplies: int) -> None:
        self._file_lbl.config(
            text=f'📂  {filename}    •    {n_supplies} αναλώσιμα'
        )

    def flash(self, msg: str, color: str = TEAL) -> None:
        self._msg_lbl.config(text=msg, fg=color)
        self.after(3000, lambda: self._msg_lbl.config(text=''))
