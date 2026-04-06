"""Analysis — catalogue of lab analysis types."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

def _now() -> str: return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def _uid() -> str: return str(uuid.uuid4())


@dataclass
class Analysis:
    name:        str
    id:          str           = field(default_factory=_uid)
    description: str           = ''
    created_at:  str           = field(default_factory=_now)
    updated_at:  str           = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            'ID':          self.id,
            'Name':        self.name,
            'Description': self.description,
            'Created At':  self.created_at,
            'Updated At':  self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Analysis':
        def _s(v) -> str:
            s = str(v) if v is not None else ''
            return '' if s.lower() in ('nan', 'none', 'nat') else s.strip()
        return cls(
            id          = _s(d.get('ID'))          or _uid(),
            name        = _s(d.get('Name')),
            description = _s(d.get('Description')),
            created_at  = _s(d.get('Created At'))  or _now(),
            updated_at  = _s(d.get('Updated At'))  or _now(),
        )
