"""
Supply — core domain model.

Every field is explicit and typed.
Validation is the model's responsibility, not the UI's.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

TYPES    = ['Υποστρώματα', 'Broths', 'Supplements', 'Βιοχημικό Κιτ', 'Άλλα']
STATUSES = ['Ανοιχτό', 'Κλειστό', 'Τελειωμένο']

# Excel column headers  →  used for both import and export
EXCEL_COLUMNS = [
    'ID', 'Name', 'Lot', 'Quantity', 'Type', 'Location', 'Status',
    'Remaining Weight', 'Initial Weight', 'Analysis Applications',
    'Best Before', 'Created At', 'Updated At',
]


def _now() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def _uid() -> str:
    return str(uuid.uuid4())


@dataclass
class Supply:
    name:                  str
    id:                    str           = field(default_factory=_uid)
    lot:                   str           = ''
    quantity:              int           = 1
    type:                  str           = TYPES[0]
    location:              str           = ''
    status:                str           = STATUSES[1]       # Κλειστό default
    remaining_weight:      Optional[float] = None
    initial_weight:        Optional[float] = None
    analysis_applications: str           = ''
    best_before:           Optional[str] = None              # 'YYYY-MM-DD'
    created_at:            str           = field(default_factory=_now)
    updated_at:            str           = field(default_factory=_now)

    # ── Validation ──────────────────────────────────────────────────────────
    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.name.strip():
            errors.append('Το Όνομα είναι υποχρεωτικό.')
        if self.type not in TYPES:
            errors.append(f'Μη έγκυρος τύπος: {self.type!r}')
        if self.status not in STATUSES:
            errors.append(f'Μη έγκυρη κατάσταση: {self.status!r}')
        if not isinstance(self.quantity, (int, float)):
            errors.append('Η ποσότητα πρέπει να είναι αριθμός.')
        elif int(self.quantity) != self.quantity:
            errors.append('Η ποσότητα πρέπει να είναι ακέραιος αριθμός.')
        elif self.quantity < 0:
            errors.append('Η ποσότητα δεν μπορεί να είναι αρνητική.')

        if self.remaining_weight is not None:
            if not isinstance(self.remaining_weight, (int, float)):
                errors.append('Το υπόλοιπο βάρος πρέπει να είναι αριθμός.')
            elif self.remaining_weight < 0:
                errors.append('Το υπόλοιπο βάρος δεν μπορεί να είναι αρνητικό.')

        if self.initial_weight is not None:
            if not isinstance(self.initial_weight, (int, float)):
                errors.append('Το αρχικό βάρος πρέπει να είναι αριθμός.')
            elif self.initial_weight < 0:
                errors.append('Το αρχικό βάρος δεν μπορεί να είναι αρνητικό.')
        if self.best_before:
            try:
                date.fromisoformat(self.best_before[:10])
            except ValueError:
                errors.append(f'Μη έγκυρη ημερομηνία λήξης: {self.best_before!r}')
        return errors

    # ── Computed properties ─────────────────────────────────────────────────
    def days_until_expiry(self) -> Optional[int]:
        if not self.best_before:
            return None
        try:
            return (date.fromisoformat(self.best_before[:10]) - date.today()).days
        except ValueError:
            return None

    def weight_pct(self) -> Optional[float]:
        """Percentage of initial weight remaining. None if data absent."""
        if self.remaining_weight is not None and self.initial_weight:
            return round(self.remaining_weight / self.initial_weight * 100, 1)
        return None

    def touch(self) -> None:
        self.updated_at = _now()

    # ── Serialisation ───────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            'ID':                    self.id,
            'Name':                  self.name,
            'Lot':                   self.lot,
            'Quantity':              self.quantity,
            'Type':                  self.type,
            'Location':              self.location,
            'Status':                self.status,
            'Remaining Weight':      self.remaining_weight,
            'Initial Weight':        self.initial_weight,
            'Analysis Applications': self.analysis_applications,
            'Best Before':           self.best_before,
            'Created At':            self.created_at,
            'Updated At':            self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Supply':
        def _s(v) -> str:
            s = str(v) if v is not None else ''
            return '' if s.lower() in ('nan', 'none', 'nat', 'pd.nat') else s.strip()

        def _f(v) -> Optional[float]:
            s = _s(v)
            try:   return float(s) if s else None
            except ValueError: return None

        def _i(v, default: int = 1) -> int:
            s = _s(v)
            try:   return int(float(s)) if s else default
            except ValueError: return default

        bb = _s(d.get('Best Before'))
        return cls(
            id                    = _s(d.get('ID'))              or _uid(),
            name                  = _s(d.get('Name')),
            lot                   = _s(d.get('Lot')),
            quantity              = _i(d.get('Quantity'), 1),
            type                  = _s(d.get('Type'))            or TYPES[0],
            location              = _s(d.get('Location')),
            status                = _s(d.get('Status'))          or STATUSES[1],
            remaining_weight      = _f(d.get('Remaining Weight')),
            initial_weight        = _f(d.get('Initial Weight')),
            analysis_applications = _s(d.get('Analysis Applications')),
            best_before           = bb[:10] if bb else None,
            created_at            = _s(d.get('Created At'))      or _now(),
            updated_at            = _s(d.get('Updated At'))      or _now(),
        )
