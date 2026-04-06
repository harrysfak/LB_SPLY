"""
ui.pages.data_management
────────────────────────
Export full backup to Excel, import backup, clear all data.
The backup format is identical to the original Excel (Supplies/Products/Analyses sheets).
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from data import storage
from data.loader import load_workbook, save_workbook
from data.manager import DataManager
from ui.theme import (
    BG, BG2, BG3, BDR, TX, TX2, TX3,
    TEAL, GREEN, RED, AMBER,
    FONT, FONT_B, FONT_S, FONT_H,
)
from ui.widgets import FlatButton, hsep


class DataManagementPage(tk.Frame):
    def __init__(self, parent, dm: DataManager, status_bar):
        super().__init__(parent, bg=BG2)
        self.dm         = dm
        self.status_bar = status_bar
        self._build()
        self.dm.subscribe(self._refresh_info)

    def _build(self):
        wrap = tk.Frame(self, bg=BG2)
        wrap.place(relx=0.5, rely=0.1, anchor='n', relwidth=0.7)

        # Title
        tk.Label(wrap, text='🗄  Διαχείριση Δεδομένων',
                 bg=BG2, fg=TX, font=FONT_H).pack(anchor='w', pady=(30, 4))
        tk.Label(wrap, text='Εξαγωγή, εισαγωγή και διαχείριση των δεδομένων της εφαρμογής.',
                 bg=BG2, fg=TX2, font=FONT_S).pack(anchor='w', pady=(0, 20))

        # ── Current data info ──────────────────────────────────────────
        info_card = tk.Frame(wrap, bg=BG3, padx=16, pady=12)
        info_card.pack(fill='x', pady=(0, 20))
        tk.Label(info_card, text='ΤΡΕΧΟΝΤΑ ΔΕΔΟΜΕΝΑ', bg=BG3, fg=TX3,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w')
        self._info_lbl = tk.Label(info_card, text='', bg=BG3, fg=TX2, font=FONT_S,
                                  justify='left')
        self._info_lbl.pack(anchor='w', pady=(4, 0))
        storage_path = storage.get_data_path()
        tk.Label(info_card,
                 text=f'Αρχείο αποθήκευσης: {storage_path}',
                 bg=BG3, fg=TX3, font=('Courier New', 8)).pack(anchor='w', pady=(4, 0))
        self._refresh_info()

        hsep(wrap, pady=4)

        # ── Export ────────────────────────────────────────────────────
        self._card(wrap,
            title='↓  Εξαγωγή Backup (Excel)',
            desc='Εξάγει όλα τα αναλώσιμα, προϊόντα και αναλύσεις σε αρχείο Excel\n'
                 'στην ίδια δομή με το αρχικό αρχείο (sheets: Supplies, Products, Analyses).',
            btn_text='Εξαγωγή Backup…',
            btn_color=TEAL,
            cmd=self._export,
        )

        # ── Import ────────────────────────────────────────────────────
        self._card(wrap,
            title='↑  Εισαγωγή Backup (Excel)',
            desc='Φορτώνει αρχείο Excel backup και ΑΝΤΙΚΑΘΙΣΤΑ τα τρέχοντα δεδομένα.\n'
                 'Αποθηκεύεται αυτόματα snapshot πριν την εισαγωγή.',
            btn_text='Εισαγωγή Backup…',
            btn_color=BLUE if False else AMBER,
            cmd=self._import,
        )

        hsep(wrap, pady=4)

        # ── Clear ─────────────────────────────────────────────────────
        self._card(wrap,
            title='🗑  Διαγραφή Όλων των Δεδομένων',
            desc='Διαγράφει μόνιμα όλα τα αναλώσιμα, τα snapshots και το αρχείο αποθήκευσης.\n'
                 'Η ενέργεια δεν μπορεί να αναιρεθεί.',
            btn_text='Διαγραφή Όλων…',
            btn_color=RED,
            btn_fg='#fff',
            cmd=self._clear,
            danger=True,
        )

    def _card(self, parent, title: str, desc: str,
              btn_text: str, btn_color: str, cmd,
              btn_fg: str = '#fff', danger: bool = False):
        card = tk.Frame(parent, bg=BG3, padx=16, pady=14)
        card.pack(fill='x', pady=(0, 12))

        top = tk.Frame(card, bg=BG3)
        top.pack(fill='x')
        tk.Label(top, text=title, bg=BG3, fg=RED if danger else TX,
                 font=FONT_B).pack(side='left', anchor='w')
        FlatButton(top, btn_text, cmd, bg=btn_color, fg=btn_fg,
                   font=FONT_S, padx=12, pady=5).pack(side='right')

        tk.Label(card, text=desc, bg=BG3, fg=TX2, font=FONT_S,
                 justify='left', wraplength=500).pack(anchor='w', pady=(6, 0))

    def _refresh_info(self, *_):
        n_s = len(self.dm.supplies)
        n_p = len(self.dm.products)
        n_a = len(self.dm.analyses)
        n_b = len(self.dm.blueprints)
        f   = self.dm.current_file
        fn  = os.path.basename(f) if f else '—'
        self._info_lbl.config(
            text=f'Τελευταίο αρχείο: {fn}\n'
                 f'Αναλώσιμα: {n_s}   Προϊόντα: {n_p}   '
                 f'Αναλύσεις: {n_a}   Snapshots: {n_b}'
        )

    def _export(self):
        if not self.dm.has_data():
            messagebox.showwarning('Χωρίς δεδομένα',
                'Δεν υπάρχουν δεδομένα για εξαγωγή.', parent=self)
            return
        path = filedialog.asksaveasfilename(
            title='Εξαγωγή backup',
            defaultextension='.xlsx',
            filetypes=[('Excel αρχεία', '*.xlsx')],
            initialfile='lab_supply_backup.xlsx',
        )
        if not path: return
        try:
            save_workbook(path, self.dm.supplies, self.dm.products, self.dm.analyses)
            self.status_bar.flash(f'Backup εξήχθη: {os.path.basename(path)}')
            messagebox.showinfo('Επιτυχία',
                f'Backup αποθηκεύτηκε:\n{path}', parent=self)
        except Exception as e:
            messagebox.showerror('Σφάλμα εξαγωγής', str(e), parent=self)

    def _import(self):
        path = filedialog.askopenfilename(
            title='Εισαγωγή backup',
            filetypes=[('Excel αρχεία', '*.xlsx *.xls')],
        )
        if not path: return

        if self.dm.has_data():
            ok = messagebox.askyesno(
                'Επιβεβαίωση εισαγωγής',
                'Η εισαγωγή θα ΑΝΤΙΚΑΤΑΣΤΗΣΕΙ τα τρέχοντα δεδομένα.\n\n'
                'Θέλετε να αποθηκευτεί snapshot πριν;',
                parent=self)
            if ok:
                self.dm.save_blueprint(
                    f'Πριν import {os.path.basename(path)}')

        try:
            result = load_workbook(path)
        except (ValueError, FileNotFoundError) as e:
            messagebox.showerror('Σφάλμα εισαγωγής', str(e), parent=self)
            return

        self.dm.load(result.supplies, result.products, result.analyses, path)
        self.status_bar.set_file(result.filename, len(result.supplies))
        msg = f'Εισήχθησαν {len(result.supplies)} αναλώσιμα'
        if result.warnings:
            msg += f' ({len(result.warnings)} προειδοποιήσεις)'
            messagebox.showwarning('Προειδοποιήσεις',
                '\n'.join(result.warnings[:15]), parent=self)
        self.status_bar.flash(msg)

    def _clear(self):
        confirm = messagebox.askyesno(
            'Επιβεβαίωση διαγραφής',
            '⚠️  Θα διαγραφούν ΜΟΝΙΜΑ όλα τα δεδομένα.\n\n'
            'Σιγουρεύεσαι;',
            icon='warning', parent=self)
        if not confirm: return

        confirm2 = messagebox.askyesno(
            'Τελευταία επιβεβαίωση',
            'Τελευταία επιβεβαίωση — δεν υπάρχει αναίρεση.',
            icon='warning', parent=self)
        if not confirm2: return

        self.dm.clear_all()
        self.status_bar.flash('Όλα τα δεδομένα διαγράφηκαν.', '#ef4444')


# Import BLUE here to avoid circular at module level
from ui.theme import BLUE
