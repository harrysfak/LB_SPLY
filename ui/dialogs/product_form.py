"""Modal dialog for add / edit Product."""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from models import Product, TYPES
from ui.theme import BG2, BG3, BDR, TX, TX2, TEAL, FONT, FONT_B, FONT_S, FONT_H


class ProductFormDialog(tk.Toplevel):
    def __init__(self, parent, product: Optional[Product] = None,
                 on_save: Optional[Callable] = None):
        super().__init__(parent)
        self._product = product
        self._on_save = on_save
        title = 'Επεξεργασία Προϊόντος' if product else 'Νέο Προϊόν'
        self.title(title)
        self.configure(bg=BG2)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self._center(parent, 460, 300)
        self._build(title)
        self._populate()

    def _center(self, parent, w, h):
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry('{}x{}+{}+{}'.format(w, h, px, py))

    def _build(self, title):
        wrap = tk.Frame(self, bg=BG2, padx=24, pady=20)
        wrap.pack(fill='both', expand=True)
        tk.Label(wrap, text=title, bg=BG2, fg=TX, font=FONT_H).pack(anchor='w', pady=(0, 14))

        g = tk.Frame(wrap, bg=BG2)
        g.pack(fill='x')
        g.columnconfigure(1, weight=1)

        fields = [
            ('name',                  'Όνομα *',              'entry'),
            ('type',                  'Τύπος',                'combo'),
            ('analysis_applications', 'Εφαρμογές Ανάλυσης',  'entry'),
        ]
        self._vars = {}
        for i, (attr, lbl, wtype) in enumerate(fields):
            tk.Label(g, text=lbl + ':', bg=BG2, fg=TX2, font=FONT_S,
                     anchor='e', width=24).grid(row=i, column=0, padx=(0, 10), pady=6, sticky='e')
            var = tk.StringVar()
            self._vars[attr] = var
            if wtype == 'combo':
                w = ttk.Combobox(g, textvariable=var, values=TYPES, state='readonly',
                                 font=FONT, width=28)
            else:
                w = tk.Entry(g, textvariable=var, bg=BG3, fg=TX, insertbackground=TX,
                             relief='flat', font=FONT, bd=0, highlightthickness=1,
                             highlightbackground=BDR, highlightcolor=TEAL, width=30)
            w.grid(row=i, column=1, sticky='ew', pady=6)

        bf = tk.Frame(wrap, bg=BG2)
        bf.pack(fill='x', pady=(16, 0))
        tk.Button(bf, text='Ακύρωση', command=self.destroy, bg=BG3, fg=TX2,
                  font=FONT, relief='flat', padx=14, pady=6, cursor='hand2').pack(side='right', padx=(8, 0))
        tk.Button(bf, text='✓  Αποθήκευση', command=self._save, bg=TEAL, fg='#fff',
                  font=FONT_B, relief='flat', padx=14, pady=6, cursor='hand2').pack(side='right')

    def _populate(self):
        p = self._product
        if p:
            self._vars['name'].set(p.name or '')
            self._vars['type'].set(p.type or (TYPES[0] if TYPES else ''))
            self._vars['analysis_applications'].set(p.analysis_applications or '')
        else:
            self._vars['type'].set(TYPES[0] if TYPES else '')

    def _save(self):
        name = self._vars['name'].get().strip()
        if not name:
            messagebox.showerror('Σφάλμα', 'Το Όνομα είναι υποχρεωτικό.', parent=self)
            return
        if self._product:
            self._product.name = name
            self._product.type = self._vars['type'].get()
            self._product.analysis_applications = self._vars['analysis_applications'].get().strip() or None
            prod = self._product
        else:
            prod = Product(
                name=name,
                type=self._vars['type'].get(),
                analysis_applications=self._vars['analysis_applications'].get().strip() or None,
            )
        if self._on_save:
            self._on_save(prod)
        self.destroy()
