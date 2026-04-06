"""ui.pages.analyses  —  full CRUD analyses catalogue."""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, ttk

from data.manager import DataManager
from ui.dialogs import AnalysisFormDialog
from ui.theme import BG, BG2, BG3, TX, TX2, TX3, TEAL, RED, FONT, FONT_B, FONT_S
from ui.widgets import SearchBar, FlatButton, StatusBar, hsep

COLUMNS = [
    ('name',        'Όνομα Ανάλυσης', 260, 'w'),
    ('description', 'Περιγραφή',      240, 'w'),
    ('created_at',  'Δημιουργήθηκε',  130, 'center'),
]


class AnalysesPage(tk.Frame):
    def __init__(self, parent, dm: DataManager, status_bar: StatusBar = None):
        super().__init__(parent, bg=BG2)
        self.dm         = dm
        self.status_bar = status_bar
        self._search_val = ''
        self._build()
        self.dm.subscribe(self._refresh)

    def show(self):
        self._refresh()

    def _build(self):
        bar = tk.Frame(self, bg=BG, padx=12, pady=9)
        bar.pack(fill='x')
        tk.Label(bar, text='🔬  Αναλύσεις', bg=BG, fg=TX, font=FONT_B).pack(side='left')
        FlatButton(bar, '+ Προσθήκη', self._add, bg=TEAL, fg='#fff',
                   padx=12, pady=5).pack(side='right')

        hsep(self)

        fbar = tk.Frame(self, bg=BG2, padx=12, pady=8)
        fbar.pack(fill='x')
        self._search_w = SearchBar(fbar, on_change=self._on_search)
        self._search_w.pack(side='left')
        self._count_lbl = tk.Label(fbar, text='', bg=BG2, fg=TX3, font=FONT_S)
        self._count_lbl.pack(side='right')
        hsep(self)

        f = tk.Frame(self, bg=BG2)
        f.pack(fill='both', expand=True, padx=10, pady=4)
        vsb = ttk.Scrollbar(f, orient='vertical')
        cols = [c[0] for c in COLUMNS]
        self.tree = ttk.Treeview(f, columns=cols, show='headings',
                                 yscrollcommand=vsb.set)
        for cid, hdr, w, anc in COLUMNS:
            self.tree.heading(cid, text=hdr)
            self.tree.column(cid, width=w, anchor=anc)
        self.tree.tag_configure('stripe', background='#182535')
        vsb.config(command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)

    def _on_search(self, val):
        self._search_val = val
        self._refresh()

    def _refresh(self, *_):
        self.tree.delete(*self.tree.get_children())
        s = self._search_val.lower()
        rows = [a for a in self.dm.analyses
                if not s or s in a.name.lower()
                or s in (a.description or '').lower()]
        for i, a in enumerate(rows):
            self.tree.insert('', 'end', iid=a.id, values=(
                a.name,
                a.description or '—',
                a.created_at[:10],
            ), tags=('stripe',) if i % 2 == 1 else ())
        self._count_lbl.config(text='{} / {} αναλύσεις'.format(len(rows), len(self.dm.analyses)))

    def _add(self):
        AnalysisFormDialog(self, on_save=self._save_new)

    def _save_new(self, analysis):
        self.dm.add_analysis(analysis)
        if self.status_bar:
            self.status_bar.flash('Προστέθηκε: {}'.format(analysis.name))

    def _on_double_click(self, _):
        iid = self.tree.focus()
        if not iid:
            return
        a = next((x for x in self.dm.analyses if x.id == iid), None)
        if a:
            AnalysisFormDialog(self, analysis=a, on_save=self._save_edit)

    def _on_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.selection_set(iid)
        a = next((x for x in self.dm.analyses if x.id == iid), None)
        if not a:
            return
        menu = tk.Menu(self, tearoff=0, bg=BG3, fg=TX,
                       activebackground=TEAL, activeforeground='#fff', relief='flat')
        menu.add_command(label='✏️  Επεξεργασία',
                         command=lambda: AnalysisFormDialog(self, analysis=a,
                                                            on_save=self._save_edit))
        menu.add_separator()
        menu.add_command(label='🗑  Διαγραφή', command=lambda: self._delete(a))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _save_edit(self, analysis):
        self.dm.update_analysis(analysis.id,
                                name=analysis.name,
                                description=analysis.description)
        if self.status_bar:
            self.status_bar.flash('Ενημερώθηκε: {}'.format(analysis.name))

    def _delete(self, analysis):
        if messagebox.askyesno('Διαγραφή',
                'Να διαγραφεί η "{}";'.format(analysis.name), parent=self):
            self.dm.delete_analysis(analysis.id)
            if self.status_bar:
                self.status_bar.flash('Διαγράφηκε: {}'.format(analysis.name), RED)
