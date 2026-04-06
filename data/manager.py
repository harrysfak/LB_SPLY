"""
data.manager
────────────
DataManager — the single source of truth for all runtime data.

Rules:
  · All mutations go through DataManager methods.
  · No UI code here.
  · Observers (callbacks) are notified after every mutation.
  · Blueprints are snapshots of supplies at a point in time.
"""
from __future__ import annotations

import copy
import uuid
from datetime import datetime
from typing import Callable, Optional

from models import Supply, Product, Analysis, STATUSES


# ── Blueprint ─────────────────────────────────────────────────────────────

class Blueprint:
    def __init__(self, supplies: list[Supply], label: str):
        self.id       = str(uuid.uuid4())
        self.label    = label
        self.saved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.supplies = copy.deepcopy(supplies)   # immutable snapshot


# ── Diff result ───────────────────────────────────────────────────────────

class DiffResult:
    def __init__(self, added, removed, modified, label_a, label_b):
        self.added    = added        # list[Supply]
        self.removed  = removed      # list[Supply]
        self.modified = modified     # list[dict]  {supply, changes: list[dict]}
        self.label_a  = label_a
        self.label_b  = label_b


# ── Manager ───────────────────────────────────────────────────────────────

class DataManager:
    """
    Holds all in-memory data and exposes mutating methods.
    Call .subscribe(cb) to be notified of any change.
    """

    def __init__(self, auto_persist: bool = True):
        self._supplies:   list[Supply]   = []
        self._products:   list[Product]  = []
        self._analyses:   list[Analysis] = []
        self._blueprints: list[Blueprint] = []
        self._observers:  list[Callable] = []
        self.current_file: Optional[str]  = None
        self._auto_persist = auto_persist

        if auto_persist:
            from data import storage
            storage.load(self)

    # ── Subscription ──────────────────────────────────────────────────────

    def subscribe(self, cb: Callable) -> None:
        self._observers.append(cb)

    def _notify(self) -> None:
        for cb in self._observers:
            try: cb()
            except Exception: pass
        self._save()

    def _save(self) -> None:
        if self._auto_persist:
            from data import storage
            storage.save(self)

    # ── Read access ───────────────────────────────────────────────────────

    @property
    def supplies(self)   -> list[Supply]:   return list(self._supplies)
    @property
    def products(self)   -> list[Product]:  return list(self._products)
    @property
    def analyses(self)   -> list[Analysis]: return list(self._analyses)
    @property
    def blueprints(self) -> list[Blueprint]: return list(self._blueprints)

    def has_data(self) -> bool:
        return bool(self._supplies or self._products or self._analyses)

    def get_supply(self, supply_id: str) -> Optional[Supply]:
        return next((s for s in self._supplies if s.id == supply_id), None)

    # ── Load ──────────────────────────────────────────────────────────────

    def load(
        self,
        supplies:  list[Supply],
        products:  list[Product],
        analyses:  list[Analysis],
        file_path: str,
        auto_blueprint: bool = True,
    ) -> None:
        self._supplies  = supplies
        self._products  = products
        self._analyses  = analyses
        self.current_file = file_path
        if auto_blueprint:
            import os
            label = f"{os.path.basename(file_path)}  •  {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            self._blueprints.insert(0, Blueprint(supplies, label))
        self._notify()

    # ── Supply CRUD ───────────────────────────────────────────────────────

    def add_supply(self, supply: Supply) -> None:
        self._supplies.insert(0, supply)
        self._notify()

    def update_supply(self, supply_id: str, **kwargs) -> Optional[Supply]:
        s = self.get_supply(supply_id)
        if s is None:
            return None
        for k, v in kwargs.items():
            if hasattr(s, k):
                setattr(s, k, v)
        s.touch()
        self._notify()
        return s

    def delete_supply(self, supply_id: str) -> bool:
        before = len(self._supplies)
        self._supplies = [s for s in self._supplies if s.id != supply_id]
        changed = len(self._supplies) < before
        if changed: self._notify()
        return changed

    def delete_supplies(self, ids: set[str]) -> int:
        before = len(self._supplies)
        self._supplies = [s for s in self._supplies if s.id not in ids]
        removed = before - len(self._supplies)
        if removed: self._notify()
        return removed

    def set_status_bulk(self, ids: set[str], status: str) -> int:
        assert status in STATUSES
        count = 0
        for s in self._supplies:
            if s.id in ids:
                s.status = status
                s.touch()
                count += 1
        if count: self._notify()
        return count

    # ── Queries ───────────────────────────────────────────────────────────

    def expiring_within(self, days: int) -> list[Supply]:
        result = []
        for s in self._supplies:
            if s.status == 'Τελειωμένο': continue
            d = s.days_until_expiry()
            if d is not None and d <= days:
                result.append(s)
        return sorted(result, key=lambda x: x.days_until_expiry() or 0)

    def stats(self) -> dict:
        total  = len(self._supplies)
        by_status  = {st: 0 for st in STATUSES}
        by_type    = {}
        for s in self._supplies:
            by_status[s.status]  = by_status.get(s.status,  0) + 1
            by_type  [s.type  ]  = by_type  .get(s.type,    0) + 1
        return {
            'total':     total,
            'by_status': by_status,
            'by_type':   by_type,
            'expiring_30': len(self.expiring_within(30)),
            'expiring_60': len(self.expiring_within(60)),
        }

    # ── Blueprints ────────────────────────────────────────────────────────

    def save_blueprint(self, label: Optional[str] = None) -> Blueprint:
        label = label or "Snapshot  •  {}".format(datetime.now().strftime('%d/%m/%Y %H:%M'))
        bp = Blueprint(self._supplies, label)
        self._blueprints.insert(0, bp)
        self._save()
        return bp

    # ── Product CRUD ──────────────────────────────────────────────────────

    def add_product(self, product) -> None:
        self._products.insert(0, product)
        self._notify()

    def update_product(self, product_id: str, **kwargs):
        p = next((x for x in self._products if x.id == product_id), None)
        if p is None:
            return None
        for k, v in kwargs.items():
            if hasattr(p, k):
                setattr(p, k, v)
        self._notify()
        return p

    def delete_product(self, product_id: str) -> bool:
        before = len(self._products)
        self._products = [x for x in self._products if x.id != product_id]
        changed = len(self._products) < before
        if changed:
            self._notify()
        return changed

    # ── Analysis CRUD ─────────────────────────────────────────────────────

    def add_analysis(self, analysis) -> None:
        self._analyses.insert(0, analysis)
        self._notify()

    def update_analysis(self, analysis_id: str, **kwargs):
        a = next((x for x in self._analyses if x.id == analysis_id), None)
        if a is None:
            return None
        for k, v in kwargs.items():
            if hasattr(a, k):
                setattr(a, k, v)
        self._notify()
        return a

    def delete_analysis(self, analysis_id: str) -> bool:
        before = len(self._analyses)
        self._analyses = [x for x in self._analyses if x.id != analysis_id]
        changed = len(self._analyses) < before
        if changed:
            self._notify()
        return changed

    # ── Queries ───────────────────────────────────────────────────────────

    def get_unique_analysis_apps(self) -> list:
        apps = set()
        for s in self._supplies:
            if s.analysis_applications:
                for a in s.analysis_applications.split(','):
                    a = a.strip()
                    if a:
                        apps.add(a)
        return sorted(apps)

    def clear_all(self) -> None:
        """Wipe everything from memory and from disk."""
        self._supplies    = []
        self._products    = []
        self._analyses    = []
        self._blueprints  = []
        self.current_file = None
        from data import storage
        storage.clear()
        # Notify observers WITHOUT saving (file is intentionally deleted)
        _prev, self._auto_persist = self._auto_persist, False
        self._notify()
        self._auto_persist = _prev

    def diff_blueprints(self, id_a: str, id_b: str) -> Optional[DiffResult]:
        a = next((b for b in self._blueprints if b.id == id_a), None)
        b = next((b for b in self._blueprints if b.id == id_b), None)
        if a is None or b is None:
            return None

        map_a = {s.id: s for s in a.supplies}
        map_b = {s.id: s for s in b.supplies}

        added   = [s for sid, s in map_b.items() if sid not in map_a]
        removed = [s for sid, s in map_a.items() if sid not in map_b]

        WATCH = ['status', 'quantity', 'remaining_weight', 'initial_weight', 'location']
        modified = []
        for sid, s_new in map_b.items():
            if sid not in map_a: continue
            s_old = map_a[sid]
            changes = [
                {'field': f, 'from': getattr(s_old, f), 'to': getattr(s_new, f)}
                for f in WATCH
                if getattr(s_old, f) != getattr(s_new, f)
            ]
            if changes:
                modified.append({'supply': s_new, 'changes': changes})

        return DiffResult(added, removed, modified, a.label, b.label)
