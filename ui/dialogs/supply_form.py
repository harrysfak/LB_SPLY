"""
ui.dialogs.supply_form
──────────────────────
Modal dialog for adding or editing a single Supply.

The dialog knows about the Supply model (fields, validation) but
knows NOTHING about DataManager — it just calls the on_save callback
with a validated Supply instance.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from models import Supply, TYPES, STATUSES
from ui.theme import BG2, BG3, BDR, TX, TX2, TX3, TEAL, FONT, FONT_B, FONT_S, FONT_H


class SupplyFormDialog(tk.Toplevel):
    """
    Open with:
        SupplyFormDialog(parent, supply=None, on_save=callback)   # add
        SupplyFormDialog(parent, supply=s,    on_save=callback)   # edit
    """

    # (field_attr, display_label, widget_type, options_or_None)
    _FIELDS = [
        ('name',                  'Όνομα *',                 'entry',  None),
        ('lot',                   'LOT',                     'entry',  None),
        ('type',                  'Τύπος',                   'combo',  TYPES),
        ('status',                'Κατάσταση',               'combo',  STATUSES),
        ('quantity',              'Ποσότητα',                'num',    None),
        ('location',              'Τοποθεσία',               'entry',  None),
        ('initial_weight',        'Αρχικό Βάρος (g)',        'num',    None),
        ('remaining_weight',      'Υπόλοιπο Βάρος (g)',      'num',    None),
        ('best_before',           'Ημ. Λήξης (YYYY-MM-DD)',  'entry',  None),
        ('analysis_applications', 'Εφαρμογές Ανάλυσης',      'entry',  None),
    ]

    def __init__(
        self,
        parent,
        supply: Optional[Supply] = None,
        on_save: Optional[Callable[[Supply], None]] = None,
    ):
        super().__init__(parent)
        self._supply  = supply
        self._on_save = on_save
        self._vars: dict[str, tk.StringVar] = {}

        title = 'Επεξεργασία Αναλώσιμου' if supply else 'Νέο Αναλώσιμο'
        self.title(title)
        self.configure(bg=BG2)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        self._center(parent, 520, 580)
        self._build(title)
        self._populate()

    def _center(self, parent, w: int, h: int):
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f'{w}x{h}+{px}+{py}')

    def _build(self, title: str):
        wrap = tk.Frame(self, bg=BG2, padx=24, pady=20)
        wrap.pack(fill='both', expand=True)

        tk.Label(wrap, text=title, bg=BG2, fg=TX, font=FONT_H).pack(anchor='w', pady=(0, 14))

        grid = tk.Frame(wrap, bg=BG2)
        grid.pack(fill='x')
        grid.columnconfigure(1, weight=1)

        for row, (attr, lbl, wtype, options) in enumerate(self._FIELDS):
            tk.Label(grid, text=lbl + ':', bg=BG2, fg=TX2, font=FONT_S,
                     anchor='e', width=26).grid(row=row, column=0, padx=(0, 10),
                                                pady=5, sticky='e')
            var = tk.StringVar()
            self._vars[attr] = var

            if wtype == 'combo':
                w = ttk.Combobox(grid, textvariable=var, values=options,
                                 state='readonly', font=FONT, width=28)
            else:
                w = tk.Entry(grid, textvariable=var, bg=BG3, fg=TX,
                             insertbackground=TX, relief='flat', font=FONT,
                             bd=0, highlightthickness=1,
                             highlightbackground=BDR, highlightcolor=TEAL,
                             width=30)
            w.grid(row=row, column=1, sticky='ew', pady=5)

        # Button row
        bf = tk.Frame(wrap, bg=BG2)
        bf.pack(fill='x', pady=(18, 0))
        tk.Button(bf, text='Ακύρωση', command=self.destroy,
                  bg=BG3, fg=TX2, font=FONT, relief='flat',
                  padx=14, pady=6, cursor='hand2').pack(side='right', padx=(8, 0))
        tk.Button(bf, text='✓  Αποθήκευση', command=self._save,
                  bg=TEAL, fg='#fff', font=FONT_B, relief='flat',
                  padx=14, pady=6, cursor='hand2').pack(side='right')

    def _populate(self):
        """Fill form fields from existing supply (edit mode) or set sensible defaults."""
        s = self._supply
        for attr, _, wtype, options in self._FIELDS:
            var = self._vars[attr]
            if s:
                val = getattr(s, attr, None)
                var.set('' if val is None else str(val))
            else:
                # defaults for new supply
                if options:
                    var.set(options[0])
                else:
                    var.set('')

    def _save(self):
        # Collect raw values
        kwargs: dict = {}
        for attr, _, wtype, _ in self._FIELDS:
            raw = self._vars[attr].get().strip()
            if wtype == 'num':
                try:
                    if not raw:
                        kwargs[attr] = None if attr in ('initial_weight', 'remaining_weight') else 1
                    elif attr == 'quantity':
                        kwargs[attr] = int(raw)
                    else:
                        kwargs[attr] = float(raw) if '.' in raw else int(raw)
                except ValueError:
                    kwargs[attr] = raw if attr == 'quantity' else None
            else:
                kwargs[attr] = raw or None if attr in (
                    'lot', 'location', 'best_before', 'analysis_applications') else raw

        # Build Supply (preserve id / timestamps if editing)
        if self._supply:
            for k, v in kwargs.items():
                setattr(self._supply, k, v)
            supply = self._supply
        else:
            kwargs.setdefault('quantity', 1)
            supply = Supply(name=kwargs.pop('name', ''), **kwargs)

        # Validate
        errors = supply.validate()
        if errors:
            messagebox.showerror('Σφάλματα επικύρωσης',
                                 '\n'.join(f'• {e}' for e in errors),
                                 parent=self)
            return

        if self._on_save:
            self._on_save(supply)
        self.destroy()
