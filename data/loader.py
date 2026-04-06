"""
data.loader
───────────
All Excel I/O lives here.  No Tkinter imports.  No global state.

Public API
──────────
load_workbook(path)  -> LoadResult
save_workbook(path, supplies, products, analyses) -> None  (raises on error)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from models import Supply, Product, Analysis


# ── Result type ────────────────────────────────────────────────────────────

@dataclass
class LoadResult:
    supplies:  list[Supply]
    products:  list[Product]
    analyses:  list[Analysis]
    warnings:  list[str]          # non-fatal issues (skipped rows, etc.)
    filename:  str
    path:      str


# ── Import ─────────────────────────────────────────────────────────────────

def load_workbook(path: str) -> LoadResult:
    """
    Load an xlsx file.  Returns a LoadResult.
    Raises ValueError for unrecoverable format errors.
    Raises FileNotFoundError if path does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f'Το αρχείο δεν βρέθηκε: {path}')

    try:
        sheets: dict = pd.read_excel(path, sheet_name=None, dtype=str)
    except Exception as exc:
        raise ValueError(f'Αδύνατη η ανάγνωση αρχείου Excel: {exc}') from exc

    warnings: list[str] = []

    supplies  = _parse_sheet(sheets, 'Supplies',  Supply.from_dict,  warnings)
    products  = _parse_sheet(sheets, 'Products',  Product.from_dict, warnings)
    analyses  = _parse_sheet(sheets, 'Analyses',  Analysis.from_dict, warnings)

    if not supplies and not products and not analyses:
        raise ValueError(
            'Δεν βρέθηκαν sheets "Supplies", "Products" ή "Analyses". '
            'Ελέγξτε τα ονόματα των sheets.'
        )

    # Validate each supply; collect warnings for rows that fail
    valid_supplies: list[Supply] = []
    for i, s in enumerate(supplies, start=2):     # row 2 = first data row
        errs = s.validate()
        if errs:
            warnings.append(f'Γραμμή {i} ({s.name or "?"}): {"; ".join(errs)}')
        else:
            valid_supplies.append(s)

    return LoadResult(
        supplies  = valid_supplies,
        products  = products,
        analyses  = analyses,
        warnings  = warnings,
        filename  = os.path.basename(path),
        path      = path,
    )


def _parse_sheet(sheets, name, factory, warnings):
    if name not in sheets:
        warnings.append(f'Sheet "{name}" δεν βρέθηκε — παραλείπεται.')
        return []
    df = sheets[name].where(sheets[name].notna(), None)
    rows = []
    for i, row in enumerate(df.to_dict('records'), start=2):
        try:
            rows.append(factory(row))
        except Exception as exc:
            warnings.append(f'{name} γραμμή {i}: {exc}')
    return rows


# ── Export ─────────────────────────────────────────────────────────────────

def save_workbook(
    path:      str,
    supplies:  list[Supply],
    products:  list[Product],
    analyses:  list[Analysis],
) -> None:
    """
    Write all three sheets to an xlsx file.
    Raises on any I/O or serialisation error.
    """
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        _df(supplies).to_excel(writer,  sheet_name='Supplies',  index=False)
        _df(products).to_excel(writer,  sheet_name='Products',  index=False)
        _df(analyses).to_excel(writer,  sheet_name='Analyses',  index=False)


def _df(items) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()
    return pd.DataFrame([x.to_dict() for x in items])
