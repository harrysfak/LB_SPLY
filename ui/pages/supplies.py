"""
ui.pages.supplies  —  full CRUD + analysis filter + weight adjustment
"""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, ttk

from data.manager import DataManager
from models import TYPES, STATUSES
from ui.dialogs import SupplyFormDialog, WeightDialog
from ui.theme import (
    BG, BG2, BG3, BDR, TX, TX2, TX3,
    TEAL, GREEN, RED, BLUE, AMBER,
    FONT, FONT_B, FONT_S, FONT_SB, FONT_MONO,
    STATUS_COLOR,
)
from ui.widgets import FlatButton, SearchBar, FilterCombo, StatusBar, hsep

COLUMNS = [
    ('name',                  'Όνομα',        220, 'w'),
    ('type',                  'Τύπος',        105, 'w'),
    ('status',                'Κατάσταση',     90, 'center'),
    ('quantity',              'Ποσ.',           48, 'center'),
    ('_weight',               'Βάρος',          90, 'center'),
    ('analysis_applications', 'Ανάλυση',       170, 'w'),
    ('best_before',           'Λήξη',           85, 'center'),
    ('lot',                   'LOT',            65, 'center'),
]


class SuppliesPage(tk.Frame):
    def __init__(self, parent, dm: DataManager, status_bar: StatusBar):
        super().__init__(parent, bg=BG2)
        self.dm         = dm
        self.status_bar = status_bar
        self._sort_col  = 'name'
        self._sort_rev  = False
        self._search_val = ''
        self._type_val   = 'Όλοι'
        self._stat_val   = 'Όλες'
        self._anal_val   = 'Όλες'
        self._build()
        self.dm.subscribe(self._on_data_change)

    def show(self):
        self._rebuild_analysis_filter()
        self._refresh()

    def _on_data_change(self):
        self._rebuild_analysis_filter()
        self._refresh()

    # ── Build ─────────────────────────────────────────────────────────────

    def _build(self):
        self._build_toolbar()
        hsep(self)
        self._build_filter_row()
        hsep(self)
        self._build_table()
        self._build_bottom_bar()

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=BG, padx=12, pady=9)
        bar.pack(fill='x')
        tk.Label(bar, text='🧪  Αναλώσιμα', bg=BG, fg=TX, font=FONT_B).pack(side='left')
        FlatButton(bar, '+ Προσθήκη', self._add, bg=TEAL, fg='#fff',
                   padx=12, pady=5).pack(side='right')
        FlatButton(bar, '↓ Export', self._export_excel,
                   padx=12, pady=5).pack(side='right', padx=6)
        FlatButton(bar, '↑ Import', self._import_excel,
                   padx=12, pady=5).pack(side='right')

    def _build_filter_row(self):
        bar = tk.Frame(self, bg=BG2, padx=12, pady=8)
        bar.pack(fill='x')

        self._search_widget = SearchBar(bar, on_change=self._on_search)
        self._search_widget.pack(side='left', padx=(0, 10))

        self._type_combo = FilterCombo(
            bar, 'Τύπος:', ['Όλοι'] + TYPES,
            on_change=self._on_type_filter, width=13)
        self._type_combo.pack(side='left', padx=(0, 8))

        self._stat_combo = FilterCombo(
            bar, 'Κατάσταση:', ['Όλες'] + STATUSES,
            on_change=self._on_stat_filter, width=11)
        self._stat_combo.pack(side='left', padx=(0, 8))

        # Analysis filter — built dynamically
        self._anal_frame = tk.Frame(bar, bg=BG2)
        self._anal_frame.pack(side='left')
        self._anal_combo_widget = None
        self._anal_var = tk.StringVar(value='Όλες')
        self._rebuild_analysis_filter()

    def _rebuild_analysis_filter(self):
        for w in self._anal_frame.winfo_children():
            w.destroy()
        apps = ['Όλες'] + self.dm.get_unique_analysis_apps()
        tk.Label(self._anal_frame, text='Ανάλυση:', bg=BG2, fg=TX2,
                 font=FONT_S).pack(side='left', padx=(0, 4))
        cb = ttk.Combobox(self._anal_frame, textvariable=self._anal_var,
                          values=apps, state='readonly', font=FONT_S, width=20)
        cb.pack(side='left')
        self._anal_var.trace_add('write', lambda *_: self._on_anal_filter(self._anal_var.get()))

    def _on_search(self, val):
        self._search_val = val
        self._refresh()

    def _on_type_filter(self, val):
        self._type_val = val
        self._refresh()

    def _on_stat_filter(self, val):
        self._stat_val = val
        self._refresh()

    def _on_anal_filter(self, val):
        self._anal_val = val
        self._refresh()

    def _build_table(self):
        frame = tk.Frame(self, bg=BG2)
        frame.pack(fill='both', expand=True, padx=10, pady=4)
        vsb = ttk.Scrollbar(frame, orient='vertical')
        hsb = ttk.Scrollbar(frame, orient='horizontal')
        cols = [c[0] for c in COLUMNS]
        self.tree = ttk.Treeview(
            frame, columns=cols, show='headings',
            selectmode='extended',
            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
        )
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        for cid, hdr, w, anc in COLUMNS:
            self.tree.heading(cid, text=hdr,
                              command=lambda c=cid: self._toggle_sort(c))
            self.tree.column(cid, width=w, minwidth=40, anchor=anc)

        self.tree.tag_configure('open',         foreground=GREEN)
        self.tree.tag_configure('closed',       foreground=BLUE)
        self.tree.tag_configure('done',         foreground=TX3)
        self.tree.tag_configure('stripe',       background='#182535')
        self.tree.tag_configure('expiry_red',   foreground=RED)
        self.tree.tag_configure('expiry_amber', foreground=AMBER)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    def _build_bottom_bar(self):
        self._bot = tk.Frame(self, bg=BG, pady=5, padx=12)
        self._bot.pack(fill='x', side='bottom')
        self._count_lbl = tk.Label(self._bot, text='', bg=BG, fg=TX3, font=FONT_S)
        self._count_lbl.pack(side='left')
        self._sel_frame = tk.Frame(self._bot, bg=BG)
        self._sel_frame.pack(side='right')

    # ── Data ──────────────────────────────────────────────────────────────

    def _filtered(self):
        s  = self._search_val.lower()
        tf = self._type_val
        sf = self._stat_val
        af = self._anal_val
        result = []
        for x in self.dm.supplies:
            if s and not any(s in str(getattr(x, a) or '').lower()
                             for a in ('name', 'lot', 'analysis_applications', 'location')):
                continue
            if tf != 'Όλοι' and x.type != tf:
                continue
            if sf != 'Όλες' and x.status != sf:
                continue
            if af != 'Όλες':
                apps = x.analysis_applications or ''
                if af.lower() not in apps.lower():
                    continue
            result.append(x)
        result.sort(
            key=lambda x: str(getattr(x, self._sort_col) or '').lower(),
            reverse=self._sort_rev,
        )
        return result

    def _refresh(self, *_):
        self.tree.delete(*self.tree.get_children())
        rows = self._filtered()
        for i, s in enumerate(rows):
            rw, iw = s.remaining_weight, s.initial_weight
            if rw is not None and iw:
                weight = '{:.0f}/{:.0f}g'.format(rw, iw)
            elif rw is not None:
                weight = '{:.0f}g'.format(rw)
            else:
                weight = '—'
            vals = (
                s.name,
                s.type,
                s.status,
                s.quantity,
                weight,
                (s.analysis_applications or '')[:36],
                (s.best_before or '')[:10],
                s.lot or '—',
            )
            tags = []
            stat_tag = {'Ανοιχτό': 'open', 'Κλειστό': 'closed', 'Τελειωμένο': 'done'}.get(s.status, '')
            if stat_tag:
                tags.append(stat_tag)
            d = s.days_until_expiry()
            if d is not None and s.status != 'Τελειωμένο':
                if d <= 30:
                    tags.append('expiry_red')
                elif d <= 60:
                    tags.append('expiry_amber')
            if i % 2 == 1:
                tags.append('stripe')
            self.tree.insert('', 'end', iid=s.id, values=vals, tags=tuple(tags))

        total = len(self.dm.supplies)
        shown = len(rows)
        self._count_lbl.config(
            text='{} / {} αναλώσιμα'.format(shown, total)
        )
        self._update_sel_bar(set())

    def _toggle_sort(self, col):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False
        self._refresh()

    # ── Selection ─────────────────────────────────────────────────────────

    def _on_select(self, _):
        self._update_sel_bar(set(self.tree.selection()))

    def _update_sel_bar(self, sel):
        for w in self._sel_frame.winfo_children():
            w.destroy()
        if not sel:
            return
        n = len(sel)
        tk.Label(self._sel_frame, text='{} επιλεγμένα  →'.format(n),
                 bg=BG, fg=TEAL, font=FONT_S).pack(side='left', padx=(0, 8))
        for st in STATUSES:
            FlatButton(self._sel_frame, st,
                       command=lambda s=st: self._bulk_status(s),
                       font=FONT_S, padx=8, pady=3).pack(side='left', padx=2)
        FlatButton(self._sel_frame, '🗑 Διαγραφή', self._bulk_delete,
                   bg='#3b1515', fg=RED, font=FONT_S, padx=8, pady=3,
                   ).pack(side='left', padx=(10, 0))

    def _bulk_status(self, status):
        ids = set(self.tree.selection())
        n = self.dm.set_status_bulk(ids, status)
        self.status_bar.flash('{} αναλώσιμα → {}'.format(n, status))

    def _bulk_delete(self):
        ids = set(self.tree.selection())
        if not messagebox.askyesno('Επιβεβαίωση',
                'Να διαγραφούν {} αναλώσιμα;'.format(len(ids)), parent=self):
            return
        n = self.dm.delete_supplies(ids)
        self.status_bar.flash('Διαγράφηκαν {}'.format(n), RED)

    # ── Add / Edit / Weight ───────────────────────────────────────────────

    def _add(self):
        SupplyFormDialog(self, on_save=self._save_new)

    def _save_new(self, supply):
        self.dm.add_supply(supply)
        self.status_bar.flash('Προστέθηκε: {}'.format(supply.name))

    def _on_double_click(self, _):
        iid = self.tree.focus()
        if not iid:
            return
        s = self.dm.get_supply(iid)
        if s:
            self._show_action_menu(s)

    def _show_action_menu(self, supply):
        menu = tk.Menu(self, tearoff=0, bg=BG3, fg=TX, activebackground=TEAL,
                       activeforeground='#fff', relief='flat', bd=0)
        menu.add_command(label='✏️  Επεξεργασία',
                         command=lambda: SupplyFormDialog(self, supply=supply,
                                                          on_save=self._save_edit))
        menu.add_command(label='⚖️  Ρύθμιση βάρους',
                         command=lambda: WeightDialog(self, supply,
                                                      on_save=lambda w: self._save_weight(supply, w)))
        menu.add_separator()
        menu.add_command(label='🗑  Διαγραφή',
                         command=lambda: self._delete_one(supply))
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _save_edit(self, supply):
        supply.touch()
        self.dm._notify()
        self.status_bar.flash('Ενημερώθηκε: {}'.format(supply.name))

    def _save_weight(self, supply, new_weight):
        self.dm.update_supply(supply.id, remaining_weight=new_weight)
        self.status_bar.flash('Βάρος → {:.1f}g'.format(new_weight))

    def _delete_one(self, supply):
        if messagebox.askyesno('Διαγραφή', 'Να διαγραφεί το "{}";'.format(supply.name),
                                parent=self):
            self.dm.delete_supply(supply.id)
            self.status_bar.flash('Διαγράφηκε: {}'.format(supply.name), RED)

    # ── Import / Export ───────────────────────────────────────────────────

    def _import_excel(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title='Φόρτωση Excel',
            filetypes=[('Excel', '*.xlsx *.xls')])
        if not path:
            return
        from data.loader import load_workbook
        try:
            result = load_workbook(path)
        except (ValueError, FileNotFoundError) as e:
            messagebox.showerror('Σφάλμα φόρτωσης', str(e), parent=self)
            return
        self.dm.load(result.supplies, result.products, result.analyses, path)
        self.status_bar.set_file(result.filename, len(result.supplies))
        msg = 'Φορτώθηκαν {}'.format(len(result.supplies))
        if result.warnings:
            msg += '  ({} warnings)'.format(len(result.warnings))
            messagebox.showwarning('Προειδοποιήσεις',
                '\n'.join(result.warnings[:15]), parent=self)
        self.status_bar.flash(msg)

    def _export_excel(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            title='Εξαγωγή Excel', defaultextension='.xlsx',
            filetypes=[('Excel', '*.xlsx')])
        if not path:
            return
        from data.loader import save_workbook
        try:
            save_workbook(path, self.dm.supplies, self.dm.products, self.dm.analyses)
            self.status_bar.flash('Εξήχθη: {}'.format(path))
        except Exception as e:
            messagebox.showerror('Σφάλμα εξαγωγής', str(e), parent=self)
