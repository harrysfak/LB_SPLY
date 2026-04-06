"""Product — catalogue of supply product types."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

def _now() -> str: return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def _uid() -> str: return str(uuid.uuid4())


@dataclass
class Product:
    name:                  str
    id:                    str = field(default_factory=_uid)
    type:                  str = ''
    analysis_applications: str = ''
    created_at:            str = field(default_factory=_now)
    updated_at:            str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            'ID':                    self.id,
            'Name':                  self.name,
            'Type':                  self.type,
            'Analysis Applications': self.analysis_applications,
            'Created At':            self.created_at,
            'Updated At':            self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Product':
        def _s(v) -> str:
            s = str(v) if v is not None else ''
            return '' if s.lower() in ('nan', 'none', 'nat') else s.strip()
        return cls(
            id                    = _s(d.get('ID'))              or _uid(),
            name                  = _s(d.get('Name')),
            type                  = _s(d.get('Type')),
            analysis_applications = _s(d.get('Analysis Applications')),
            created_at            = _s(d.get('Created At'))      or _now(),
            updated_at            = _s(d.get('Updated At'))      or _now(),
        )
