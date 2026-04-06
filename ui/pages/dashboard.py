"""
ui.pages.dashboard
──────────────────
Summary stats + 2 charts + expiry alerts.
Intentionally limited to what gives real value.
Rebuilds charts on every show() call to stay current.
"""
from __future__ import annotations

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import tkinter as tk

from data.manager import DataManager
from models import STATUSES
from ui.theme import (
    BG, BG2, BG3, TX, TX2, TX3,
    TEAL, GREEN, RED, AMBER, BLUE,
    FONT, FONT_B, FONT_S, FONT_SB,
    STATUS_COLOR, TYPE_COLOR, MPL_RC,
)
from ui.widgets import ScrollableFrame, StatCard, hsep

plt.rcParams.update(MPL_RC)


class DashboardPage(tk.Frame):
    def __init__(self, parent, dm: DataManager):
        super().__init__(parent, bg=BG2)
        self.dm = dm
        self._canvas_widgets: list = []

    def show(self):
        """Called by the router each time this page becomes visible."""
        self._rebuild()

    def _rebuild(self):
        for w in self.winfo_children():
            w.destroy()
        self._canvas_widgets.clear()

        if not self.dm.has_data():
            self._build_empty()
            return

        sf = ScrollableFrame(self)
        sf.pack(fill='both', expand=True)
        p  = sf.inner

        self._build_stats(p)
        hsep(p, padx=20, pady=8)
        self._build_charts(p)
        hsep(p, padx=20, pady=8)
        self._build_expiry_alerts(p)

    # ── Empty state ───────────────────────────────────────────────────────

    def _build_empty(self):
        f = tk.Frame(self, bg=BG2)
        f.place(relx=.5, rely=.5, anchor='center')
        tk.Label(f, text='📊', bg=BG2, fg=TX3, font=('Segoe UI', 40)).pack()
        tk.Label(f, text='Δεν υπάρχουν δεδομένα', bg=BG2, fg=TX2,
                 font=FONT_B).pack(pady=(8, 0))
        tk.Label(f, text='Φορτώστε ένα Excel αρχείο από την καρτέλα Αναλώσιμα',
                 bg=BG2, fg=TX3, font=FONT_S).pack()

    # ── Stat cards ────────────────────────────────────────────────────────

    def _build_stats(self, parent):
        st  = self.dm.stats()
        row = tk.Frame(parent, bg=BG2)
        row.pack(fill='x', padx=20, pady=(20, 0))

        cards = [
            ('Σύνολο Αναλώσιμων', st['total'],                     TEAL,  ''),
            ('Ανοιχτά',           st['by_status']['Ανοιχτό'],      GREEN, 'σε χρήση'),
            ('Κλειστά',           st['by_status']['Κλειστό'],      BLUE,  'αδιάνοιχτα'),
            ('Τελειωμένα',        st['by_status']['Τελειωμένο'],   RED,   ''),
            ('Λήξη < 30 ημέρες',  st['expiring_30'],               AMBER, 'ειδοποιήσεις'),
        ]
        for title, val, color, sub in cards:
            card = StatCard(row, title, val, color, sub)
            card.pack(side='left', expand=True, fill='x', padx=(0, 10))

    # ── Charts ────────────────────────────────────────────────────────────

    def _build_charts(self, parent):
        row = tk.Frame(parent, bg=BG2)
        row.pack(fill='x', padx=20)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        st = self.dm.stats()

        # Chart 1 — Pie: type distribution
        frame1 = tk.Frame(row, bg=BG3)
        frame1.grid(row=0, column=0, sticky='nsew', padx=(0, 8), pady=4)
        tk.Label(frame1, text='Κατανομή ανά Τύπο',
                 bg=BG3, fg=TX2, font=FONT_SB, pady=8).pack()
        self._add_pie(frame1, st['by_type'])

        # Chart 2 — Bar: status breakdown per type
        frame2 = tk.Frame(row, bg=BG3)
        frame2.grid(row=0, column=1, sticky='nsew', padx=(8, 0), pady=4)
        tk.Label(frame2, text='Αναλώσιμα ανά Κατάσταση',
                 bg=BG3, fg=TX2, font=FONT_SB, pady=8).pack()
        self._add_status_bar(frame2, st['by_status'])

    def _add_pie(self, parent, by_type: dict):
        if not by_type:
            tk.Label(parent, text='Χωρίς δεδομένα', bg=BG3, fg=TX3,
                     font=FONT_S).pack(expand=True)
            return
        fig = Figure(figsize=(4.4, 3.0), tight_layout=True)
        ax  = fig.add_subplot(111)
        labels = list(by_type.keys())
        vals   = list(by_type.values())
        colors = [TYPE_COLOR.get(l, TX3) for l in labels]
        wedges, _, autotexts = ax.pie(
            vals, labels=labels, colors=colors,
            autopct='%1.0f%%', startangle=90,
            textprops={'color': TX2, 'fontsize': 8},
            wedgeprops={'linewidth': 0},
        )
        for at in autotexts:
            at.set_color(BG2); at.set_fontsize(8)
        self._embed(fig, parent)

    def _add_status_bar(self, parent, by_status: dict):
        fig = Figure(figsize=(4.4, 3.0), tight_layout=True)
        ax  = fig.add_subplot(111)
        labels = list(by_status.keys())
        vals   = [by_status.get(s, 0) for s in STATUSES]
        colors = [STATUS_COLOR.get(s, TX3) for s in STATUSES]
        bars = ax.bar(STATUSES, vals, color=colors, width=0.5, edgecolor='none')
        ax.bar_label(bars, padding=4, color=TX2, fontsize=9)
        ax.tick_params(colors=TX3, labelsize=9)
        ax.set_ylim(0, max(vals or [1]) * 1.2)
        self._embed(fig, parent)

    def _embed(self, fig, parent):
        c = FigureCanvasTkAgg(fig, master=parent)
        c.draw()
        c.get_tk_widget().pack(fill='both', expand=True, padx=8, pady=(0, 10))
        self._canvas_widgets.append(c)
        plt.close(fig)

    # ── Expiry alerts ─────────────────────────────────────────────────────

    def _build_expiry_alerts(self, parent):
        alerts = self.dm.expiring_within(90)
        if not alerts:
            return

        hdr = tk.Frame(parent, bg=AMBER, padx=14, pady=6)
        hdr.pack(fill='x', padx=20, pady=(0, 6))
        tk.Label(hdr, text=f'⚠  Λήξεις αναλωσίμων  ({len(alerts)} εντός 90 ημερών)',
                 bg=AMBER, fg=BG, font=FONT_B).pack(side='left')

        for s in alerts[:25]:
            d = s.days_until_expiry() or 0
            color = RED if d <= 30 else (AMBER if d <= 60 else GREEN)

            row = tk.Frame(parent, bg=BG3, pady=6, padx=10)
            row.pack(fill='x', padx=20, pady=2)
            tk.Frame(row, bg=color, width=4).pack(side='left', fill='y', padx=(0, 10))

            tk.Label(row, text=s.name, bg=BG3, fg=TX,
                     font=FONT_B, anchor='w').pack(side='left')
            tk.Label(row, text=s.type, bg=BG3, fg=TX2,
                     font=FONT_S).pack(side='left', padx=10)
            tk.Label(row, text=s.status, bg=BG3,
                     fg=STATUS_COLOR.get(s.status, TX3),
                     font=FONT_S).pack(side='left', padx=4)

            days_txt = 'ΛΗΞΗ!' if d <= 0 else f'{d} ημέρες'
            tk.Label(row, text=days_txt, bg=BG3, fg=color,
                     font=FONT_B).pack(side='right', padx=8)
            tk.Label(row, text=str(s.best_before or '')[:10],
                     bg=BG3, fg=TX3, font=('Courier New', 9)).pack(side='right')

        tk.Frame(parent, height=20, bg=BG2).pack()   # bottom padding
