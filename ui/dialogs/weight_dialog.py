"""Quick dialog for adding or subtracting grams from a supply's remaining weight."""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

from models import Supply
from ui.theme import BG2, BG3, BDR, TX, TX2, TX3, TEAL, GREEN, RED, AMBER, FONT, FONT_B, FONT_S, FONT_H


class WeightDialog(tk.Toplevel):
    """
    Shows current remaining/initial weight.
    User enters an amount and clicks + or -.
    Calls on_save(new_remaining_weight: float).
    """

    def __init__(self, parent, supply: Supply, on_save: Optional[Callable] = None):
        super().__init__(parent)
        self._supply  = supply
        self._on_save = on_save
        self.title('Ρύθμιση Βάρους')
        self.configure(bg=BG2)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self._center(parent, 400, 290)
        self._build()

    def _center(self, parent, w, h):
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry('{}x{}+{}+{}'.format(w, h, px, py))

    def _build(self):
        s   = self._supply
        rem = s.remaining_weight
        ini = s.initial_weight

        wrap = tk.Frame(self, bg=BG2, padx=24, pady=20)
        wrap.pack(fill='both', expand=True)

        # Title
        tk.Label(wrap, text='Ρύθμιση Βάρους', bg=BG2, fg=TX, font=FONT_H).pack(anchor='w')
        tk.Label(wrap, text=s.name, bg=BG2, fg=TX2, font=FONT_S).pack(anchor='w', pady=(2, 14))

        # Current weight display
        info = tk.Frame(wrap, bg=BG3, padx=14, pady=10)
        info.pack(fill='x', pady=(0, 14))

        rem_txt = '{:.1f}g'.format(rem) if rem is not None else '—'
        ini_txt = '{:.1f}g'.format(ini) if ini is not None else '—'
        pct_txt = ''
        if rem is not None and ini and ini > 0:
            pct = rem / ini * 100
            color = GREEN if pct > 50 else (AMBER if pct > 20 else RED)
            pct_txt = '  ({:.0f}%)'.format(pct)
        else:
            color = TX3

        tk.Label(info, text='Τρέχον υπόλοιπο:', bg=BG3, fg=TX2, font=FONT_S).pack(side='left')
        tk.Label(info, text=rem_txt + pct_txt, bg=BG3, fg=color, font=FONT_B).pack(side='left', padx=8)
        tk.Label(info, text='/ {}'.format(ini_txt), bg=BG3, fg=TX3, font=FONT_S).pack(side='left')

        # Amount entry
        amt_row = tk.Frame(wrap, bg=BG2)
        amt_row.pack(fill='x', pady=(0, 6))
        tk.Label(amt_row, text='Ποσότητα (g):', bg=BG2, fg=TX2, font=FONT_S).pack(side='left')
        self._amt = tk.StringVar()
        tk.Entry(amt_row, textvariable=self._amt, bg=BG3, fg=TX, insertbackground=TX,
                 relief='flat', font=FONT_B, bd=0, highlightthickness=1,
                 highlightbackground=BDR, highlightcolor=TEAL,
                 width=10).pack(side='left', padx=8)
        tk.Label(amt_row, text='g', bg=BG2, fg=TX3, font=FONT_S).pack(side='left')

        # Buttons
        bf = tk.Frame(wrap, bg=BG2)
        bf.pack(fill='x', pady=(12, 0))

        tk.Button(bf, text='Ακύρωση', command=self.destroy,
                  bg=BG3, fg=TX2, font=FONT, relief='flat',
                  padx=12, pady=6, cursor='hand2').pack(side='right', padx=(8, 0))
        tk.Button(bf, text='+ Προσθήκη', command=self._add,
                  bg='#14532d', fg=GREEN, font=FONT_B, relief='flat',
                  padx=12, pady=6, cursor='hand2').pack(side='right', padx=(6, 0))
        tk.Button(bf, text='− Αφαίρεση (Χρήση)', command=self._subtract,
                  bg='#3b1515', fg=RED, font=FONT_B, relief='flat',
                  padx=12, pady=6, cursor='hand2').pack(side='right')

    def _parse(self):
        try:
            val = float(self._amt.get().replace(',', '.'))
            if val <= 0:
                raise ValueError
            return val
        except (ValueError, AttributeError):
            messagebox.showerror('Σφάλμα', 'Εισάγετε έγκυρο αριθμό > 0', parent=self)
            return None

    def _subtract(self):
        amt = self._parse()
        if amt is None:
            return
        rem = self._supply.remaining_weight or 0.0
        new_val = rem - amt
        if new_val < 0:
            ok = messagebox.askyesno(
                'Αρνητικό βάρος',
                'Το αποτέλεσμα είναι αρνητικό ({:.1f}g).\nΣυνέχεια;'.format(new_val),
                parent=self)
            if not ok:
                return
        self._finish(new_val)

    def _add(self):
        amt = self._parse()
        if amt is None:
            return
        rem = self._supply.remaining_weight or 0.0
        self._finish(rem + amt)

    def _finish(self, new_weight: float):
        if self._on_save:
            self._on_save(round(new_weight, 2))
        self.destroy()
