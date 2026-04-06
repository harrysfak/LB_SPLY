"""
ui.pages.blueprints
───────────────────
Snapshot management + detailed visual diff.
Each modified supply shows every changed field with old → new values.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import simpledialog, ttk, messagebox
from typing import Optional

from data.manager import DataManager, DiffResult
from ui.theme import (
    BG, BG2, BG3, BDR, TX, TX2, TX3,
    TEAL, GREEN, RED, AMBER,
    FONT, FONT_B, FONT_S, FONT_SB,
)
from ui.widgets import FlatButton, ScrollableFrame, hsep

FIELD_LABELS = {
    'status':           'Κατάσταση',
    'quantity':         'Ποσότητα',
    'remaining_weight': 'Υπόλοιπο βάρος',
    'initial_weight':   'Αρχικό βάρος',
    'location':         'Τοποθεσία',
}


class BlueprintsPage(tk.Frame):
    def __init__(self, parent, dm: DataManager):
        super().__init__(parent, bg=BG2)
        self.dm = dm
        self._build()
        self.dm.subscribe(self._refresh_list)

    def _build(self):
        bar = tk.Frame(self, bg=BG2, padx=12, pady=10)
        bar.pack(fill='x')
        FlatButton(bar, '💾  Αποθήκευση snapshot τώρα',
                   self._save_snapshot, bg=TEAL, fg='#fff').pack(side='left')
        tk.Label(bar, text='Αποθηκεύει την τρέχουσα κατάσταση των αναλωσίμων',
                 bg=BG2, fg=TX3, font=FONT_S).pack(side='left', padx=12)
        hsep(self)

        body = tk.Frame(self, bg=BG2)
        body.pack(fill='both', expand=True, padx=12, pady=10)
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Left ─────────────────────────────────────────────────────────
        lf = tk.Frame(body, bg=BG3, width=310)
        lf.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        lf.pack_propagate(False)

        tk.Label(lf, text='ΑΠΟΘΗΚΕΥΜΕΝΑ SNAPSHOTS', bg=BG3, fg=TX3,
                 font=('Segoe UI', 8, 'bold'), padx=10, pady=8,
                 anchor='w').pack(fill='x')
        hsep(lf)

        lb_f = tk.Frame(lf, bg=BG3)
        lb_f.pack(fill='both', expand=True, padx=4, pady=4)
        vsb = ttk.Scrollbar(lb_f, orient='vertical')
        self._bp_list = tk.Listbox(
            lb_f, bg=BG3, fg=TX, font=FONT_S,
            selectbackground=BG, selectforeground=TEAL,
            borderwidth=0, relief='flat', highlightthickness=0,
            yscrollcommand=vsb.set, activestyle='none',
        )
        vsb.config(command=self._bp_list.yview)
        vsb.pack(side='right', fill='y')
        self._bp_list.pack(fill='both', expand=True)

        hsep(lf)
        ctrl = tk.Frame(lf, bg=BG3, padx=10, pady=10)
        ctrl.pack(fill='x')
        ctrl.columnconfigure(1, weight=1)

        tk.Label(ctrl, text='Επιλέξτε A:', bg=BG3, fg=TX2,
                 font=FONT_S).grid(row=0, column=0, sticky='w', pady=3)
        self._cb_a = ttk.Combobox(ctrl, state='readonly', font=FONT_S, width=26)
        self._cb_a.grid(row=0, column=1, sticky='ew', padx=(6, 0), pady=3)

        tk.Label(ctrl, text='Επιλέξτε B:', bg=BG3, fg=TX2,
                 font=FONT_S).grid(row=1, column=0, sticky='w', pady=3)
        self._cb_b = ttk.Combobox(ctrl, state='readonly', font=FONT_S, width=26)
        self._cb_b.grid(row=1, column=1, sticky='ew', padx=(6, 0), pady=3)

        FlatButton(ctrl, 'Σύγκριση →', self._compare,
                   bg=TEAL, fg='#fff', font=FONT_S, padx=10, pady=5,
                   ).grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky='ew')

        # ── Right ─────────────────────────────────────────────────────────
        rf = tk.Frame(body, bg=BG2)
        rf.grid(row=0, column=1, sticky='nsew')
        rf.rowconfigure(1, weight=1)
        rf.columnconfigure(0, weight=1)

        self._diff_header = tk.Frame(rf, bg=BG2)
        self._diff_header.grid(row=0, column=0, sticky='ew')
        self._diff_scroll = ScrollableFrame(rf, bg=BG2)
        self._diff_scroll.grid(row=1, column=0, sticky='nsew')

        self._show_placeholder('Επιλέξτε δύο snapshots και πατήστε Σύγκριση.')
        self._refresh_list()

    def _refresh_list(self, *_):
        self._bp_list.delete(0, 'end')
        labels = []
        for bp in self.dm.blueprints:
            self._bp_list.insert('end',
                f'  {bp.label}  ({len(bp.supplies)} αναλώσιμα)')
            labels.append(bp.label)
        self._cb_a['values'] = labels
        self._cb_b['values'] = labels

    def _save_snapshot(self):
        if not self.dm.has_data():
            messagebox.showwarning('Προσοχή',
                'Δεν υπάρχουν δεδομένα.', parent=self)
            return
        label = simpledialog.askstring(
            'Όνομα snapshot',
            'Ετικέτα (αφήστε κενό για αυτόματη):',
            parent=self) or None
        self.dm.save_blueprint(label)

    def _compare(self):
        la, lb = self._cb_a.get(), self._cb_b.get()
        if not la or not lb:
            self._show_placeholder('Επιλέξτε και τα δύο snapshots.')
            return
        if la == lb:
            self._show_placeholder('Επιλέξτε δύο ΔΙΑΦΟΡΕΤΙΚΑ snapshots.')
            return
        id_a = next((b.id for b in self.dm.blueprints if b.label == la), None)
        id_b = next((b.id for b in self.dm.blueprints if b.label == lb), None)
        result = self.dm.diff_blueprints(id_a, id_b) if id_a and id_b else None
        if result:
            self._render_diff(result, la, lb)
        else:
            self._show_placeholder('Αδύνατη η σύγκριση.')

    def _show_placeholder(self, msg: str):
        for w in self._diff_header.winfo_children(): w.destroy()
        for w in self._diff_scroll.inner.winfo_children(): w.destroy()
        tk.Label(self._diff_scroll.inner, text=msg, bg=BG2, fg=TX3,
                 font=FONT_S).pack(pady=40)

    def _render_diff(self, r: DiffResult, la: str, lb: str):
        for w in self._diff_header.winfo_children(): w.destroy()

        tk.Label(self._diff_header, text=f'A: {la}', bg=BG2,
                 fg=TX2, font=FONT_S).pack(anchor='w', padx=12, pady=(10, 0))
        tk.Label(self._diff_header, text=f'B: {lb}', bg=BG2,
                 fg=TX2, font=FONT_S).pack(anchor='w', padx=12)

        sf = tk.Frame(self._diff_header, bg=BG2)
        sf.pack(fill='x', padx=12, pady=8)
        for txt, n, color in [
            (f'+ {len(r.added)} Νέα',               len(r.added),    GREEN),
            (f'− {len(r.removed)} Αφαιρέθηκαν',     len(r.removed),  RED),
            (f'~ {len(r.modified)} Τροποποιήθηκαν',  len(r.modified), AMBER),
        ]:
            tk.Label(sf, text=txt, bg=BG3, fg=color, font=FONT_SB,
                     padx=12, pady=5).pack(side='left', padx=(0, 8))

        if not any([r.added, r.removed, r.modified]):
            tk.Label(sf, text='Δεν υπάρχουν διαφορές.',
                     bg=BG2, fg=TX3, font=FONT_S).pack(side='left', padx=12)
        hsep(self._diff_header, padx=12)

        inner = self._diff_scroll.inner
        for w in inner.winfo_children(): w.destroy()

        if r.added:
            self._section(inner, f'Νέα αναλώσιμα  (+{len(r.added)})', GREEN)
            for s in r.added:
                self._basic_row(inner, s, GREEN, '+ νέο')

        if r.removed:
            self._section(inner, f'Αφαιρέθηκαν  (−{len(r.removed)})', RED)
            for s in r.removed:
                self._basic_row(inner, s, RED, '− αφαιρέθηκε')

        if r.modified:
            self._section(inner, f'Τροποποιήθηκαν  (~{len(r.modified)})', AMBER)
            for item in r.modified:
                self._modified_row(inner, item['supply'], item['changes'])

        tk.Frame(inner, height=20, bg=BG2).pack()

    def _section(self, parent, title: str, color: str):
        f = tk.Frame(parent, bg=BG2, padx=12, pady=(10, 4))
        f.pack(fill='x')
        tk.Label(f, text=title, bg=BG2, fg=color, font=FONT_B).pack(anchor='w')

    def _basic_row(self, parent, s, color: str, badge: str):
        row = tk.Frame(parent, bg=BG3, pady=7, padx=10)
        row.pack(fill='x', padx=12, pady=2)
        tk.Frame(row, bg=color, width=4).pack(side='left', fill='y', padx=(0, 10))
        col = tk.Frame(row, bg=BG3)
        col.pack(side='left', fill='x', expand=True)
        top = tk.Frame(col, bg=BG3)
        top.pack(fill='x')
        tk.Label(top, text=s.name, bg=BG3, fg=TX,
                 font=FONT_B, anchor='w').pack(side='left')
        tk.Label(top, text=s.type, bg=BG3, fg=TX2,
                 font=FONT_S).pack(side='left', padx=8)
        extra = f'Κατάσταση: {s.status}   Ποσ.: {s.quantity}'
        if s.lot:
            extra += f'   LOT: {s.lot}'
        tk.Label(col, text=extra, bg=BG3, fg=TX3,
                 font=('Courier New', 9)).pack(anchor='w')
        tk.Label(row, text=badge, bg=BG3, fg=color,
                 font=FONT_SB).pack(side='right', padx=8)

    def _modified_row(self, parent, s, changes: list):
        row = tk.Frame(parent, bg=BG3, pady=7, padx=10)
        row.pack(fill='x', padx=12, pady=2)
        tk.Frame(row, bg=AMBER, width=4).pack(side='left', fill='y', padx=(0, 10))
        col = tk.Frame(row, bg=BG3)
        col.pack(side='left', fill='x', expand=True)

        top = tk.Frame(col, bg=BG3)
        top.pack(fill='x')
        tk.Label(top, text=s.name, bg=BG3, fg=TX,
                 font=FONT_B, anchor='w').pack(side='left')
        tk.Label(top, text=s.type, bg=BG3, fg=TX2,
                 font=FONT_S).pack(side='left', padx=8)

        for ch in changes:
            lbl = FIELD_LABELS.get(ch['field'], ch['field'])
            frm = str(ch['from']) if ch['from'] is not None else '—'
            to  = str(ch['to'])   if ch['to']   is not None else '—'
            lf = tk.Frame(col, bg=BG3)
            lf.pack(fill='x', pady=1)
            tk.Label(lf, text=f'  {lbl}:',
                     bg=BG3, fg=TX3, font=FONT_S, width=20,
                     anchor='w').pack(side='left')
            tk.Label(lf, text=frm, bg=BG3, fg=RED,
                     font=('Courier New', 9)).pack(side='left')
            tk.Label(lf, text='  →  ', bg=BG3, fg=TX3,
                     font=FONT_S).pack(side='left')
            tk.Label(lf, text=to, bg=BG3, fg=GREEN,
                     font=('Courier New', 9)).pack(side='left')
