"""
ui.app
──────
MainApp: the root Tk window.

Responsibilities:
  · Create the window + sidebar navigation
  · Instantiate all pages (once, not on every switch)
  · Route between pages with show/hide
  · Own the StatusBar
  · Pass DataManager down to every page

Nothing else.
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional

from data.manager import DataManager
from ui.theme import (
    BG, BG2, BG3, BDR, TX, TX2, TX3,
    TEAL, RED, AMBER,
    FONT, FONT_B, FONT_S, FONT_H,
    apply_ttk_style,
)
from ui.widgets import StatusBar, vsep

# Pages
from ui.pages import (
    DashboardPage, SuppliesPage,
    ProductsPage, AnalysesPage, BlueprintsPage,
    DataManagementPage,
)


# ── Sidebar nav item ───────────────────────────────────────────────────────

class NavItem(tk.Frame):
    def __init__(self, parent, icon: str, label: str, command, **kw):
        super().__init__(parent, bg=BG2, cursor='hand2', **kw)
        self._active   = False
        self._command  = command
        self._icon_lbl = tk.Label(self, text=icon, bg=BG2, fg=TX2,
                                  font=('Segoe UI', 14), width=3)
        self._icon_lbl.pack(side='left')
        self._text_lbl = tk.Label(self, text=label, bg=BG2, fg=TX2,
                                  font=FONT, anchor='w')
        self._text_lbl.pack(side='left', fill='x', expand=True)

        for w in (self, self._icon_lbl, self._text_lbl):
            w.bind('<Button-1>', lambda _: command())
            w.bind('<Enter>',    lambda _, w=w: self._hover(True))
            w.bind('<Leave>',    lambda _, w=w: self._hover(False))

    def set_active(self, active: bool):
        self._active = active
        bg   = BG3  if active else BG2
        fg   = TEAL if active else TX2
        font = FONT_B if active else FONT
        for w in (self, self._icon_lbl, self._text_lbl):
            w.config(bg=bg)
        self._text_lbl.config(fg=fg, font=font)
        self._icon_lbl.config(fg=fg)

    def _hover(self, on: bool):
        if self._active: return
        bg = BG3 if on else BG2
        for w in (self, self._icon_lbl, self._text_lbl):
            w.config(bg=bg)

    def set_badge(self, n: int):
        # Future: show a red dot for alerts
        pass


# ── Main window ────────────────────────────────────────────────────────────

class MainApp(tk.Tk):
    _NAV = [
        ('dashboard',       '📊', 'Dashboard'),
        ('supplies',        '🧪', 'Αναλώσιμα'),
        ('products',        '📦', 'Προϊόντα'),
        ('analyses',        '🔬', 'Αναλύσεις'),
        ('blueprints',      '🗂', 'Blueprints'),
        ('data_management', '🗄', 'Διαχείριση'),
    ]

    def __init__(self, dm: DataManager):
        super().__init__()
        self.dm = dm
        self.title('Lab Supply Management')
        self.geometry('1200x750')
        self.minsize(900, 600)
        self.configure(bg=BG2)
        apply_ttk_style(self)

        self._current: Optional[str] = None
        self._nav_items: dict[str, NavItem] = {}
        self._pages:     dict[str, tk.Frame] = {}

        self._build_layout()
        self._build_sidebar()
        self._build_pages()

        self.navigate('dashboard')
        self.after(100, self._after_startup)

    # ── Layout skeleton ───────────────────────────────────────────────────

    def _build_layout(self):
        # Sidebar  |  Content  (vertical split)
        self._sidebar = tk.Frame(self, bg=BG2, width=210)
        self._sidebar.pack(side='left', fill='y')
        self._sidebar.pack_propagate(False)

        vsep(self._sidebar).pack(side='right', fill='y')

        content_col = tk.Frame(self, bg=BG2)
        content_col.pack(side='left', fill='both', expand=True)

        self._content = tk.Frame(content_col, bg=BG2)
        self._content.pack(fill='both', expand=True)

        self.status_bar = StatusBar(content_col)
        self.status_bar.pack(fill='x', side='bottom')

    # ── Sidebar ────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        # Logo
        logo = tk.Frame(self._sidebar, bg=BG2, padx=14, pady=16)
        logo.pack(fill='x')
        tk.Label(logo, text='🧬', bg=BG2, fg=TEAL,
                 font=('Segoe UI', 22)).pack(anchor='w')
        tk.Label(logo, text='Lab Supply', bg=BG2, fg=TX,
                 font=FONT_H).pack(anchor='w')
        tk.Label(logo, text='Management', bg=BG2, fg=TX3,
                 font=FONT_S).pack(anchor='w')

        tk.Frame(self._sidebar, bg=BDR, height=1).pack(fill='x', pady=(0, 8))

        # Nav items
        nav_wrap = tk.Frame(self._sidebar, bg=BG2, padx=8)
        nav_wrap.pack(fill='x')
        for page_id, icon, label in self._NAV:
            item = NavItem(
                nav_wrap, icon, label,
                command=lambda p=page_id: self.navigate(p),
                pady=10,
            )
            item.pack(fill='x', pady=1)
            self._nav_items[page_id] = item

        # Bottom: file info
        tk.Frame(self._sidebar, bg=BDR, height=1).pack(fill='x', side='bottom', pady=(0, 0))
        self._file_label = tk.Label(
            self._sidebar, text='Χωρίς αρχείο', bg=BG2, fg=TX3,
            font=('Courier New', 8), wraplength=190, justify='left',
            padx=12, pady=8,
        )
        self._file_label.pack(side='bottom', fill='x')

        self.dm.subscribe(self._on_data_change)

    def _on_data_change(self):
        f = self.dm.current_file or ''
        n = len(self.dm.supplies)
        if f:
            import os
            self._file_label.config(
                text=f'{os.path.basename(f)}\n{n} αναλώσιμα',
                fg=TX2,
            )
        # Refresh current page if dashboard
        if self._current == 'dashboard':
            self._pages['dashboard'].show()

    # ── Pages ──────────────────────────────────────────────────────────────

    def _build_pages(self):
        self._pages['dashboard']       = DashboardPage(self._content, self.dm)
        self._pages['supplies']        = SuppliesPage(self._content, self.dm, self.status_bar)
        self._pages['products']        = ProductsPage(self._content, self.dm, self.status_bar)
        self._pages['analyses']        = AnalysesPage(self._content, self.dm, self.status_bar)
        self._pages['blueprints']      = BlueprintsPage(self._content, self.dm)
        self._pages['data_management'] = DataManagementPage(self._content, self.dm, self.status_bar)

        for page in self._pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            page.lower()    # hide all initially

    # ── Navigation ────────────────────────────────────────────────────────

    def navigate(self, page_id: str):
        if page_id not in self._pages:
            return
        if self._current and self._current in self._nav_items:
            self._nav_items[self._current].set_active(False)
            self._pages[self._current].lower()
        self._current = page_id
        self._nav_items[page_id].set_active(True)
        page = self._pages[page_id]
        page.lift()
        # Always call show() so pages refresh after data loaded from storage
        if hasattr(page, 'show'):
            page.show()

    def _after_startup(self):
        """Called once after mainloop starts — update status bar if data was restored."""
        if self.dm.has_data() and self.dm.current_file:
            import os
            self.status_bar.set_file(
                os.path.basename(self.dm.current_file),
                len(self.dm.supplies)
            )
