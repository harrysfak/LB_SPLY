"""
data.storage
────────────
Persist all application data to a single JSON file on disk.
Called by DataManager on every mutation and on startup.

Default location: <app_dir>/lab_supply_data.json
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.manager import DataManager

# Store the JSON next to main.py (i.e. inside the lab_supply folder)
_APP_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_FILE = os.path.join(_APP_DIR, 'lab_supply_data.json')


def get_data_path() -> str:
    return _DATA_FILE


def save(dm: 'DataManager') -> None:
    """Serialise DataManager state to JSON. Silent on error."""
    try:
        payload = {
            '_saved_at': datetime.now().isoformat(),
            '_version':  1,
            'current_file': dm.current_file,
            'supplies':  [s.to_dict() for s in dm.supplies],
            'products':  [p.to_dict() for p in dm.products],
            'analyses':  [a.to_dict() for a in dm.analyses],
            'blueprints': [
                {
                    'id':       bp.id,
                    'label':    bp.label,
                    'saved_at': bp.saved_at,
                    'supplies': [s.to_dict() for s in bp.supplies],
                }
                for bp in dm.blueprints
            ],
        }
        with open(_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f'[storage] save error: {exc}')


def load(dm: 'DataManager') -> bool:
    """
    Restore DataManager state from JSON.
    Returns True if data was found and loaded, False otherwise.
    """
    if not os.path.exists(_DATA_FILE):
        return False
    try:
        with open(_DATA_FILE, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        from models import Supply, Product, Analysis
        from data.manager import Blueprint

        supplies  = [Supply.from_dict(d)  for d in payload.get('supplies',  [])]
        products  = [Product.from_dict(d) for d in payload.get('products',  [])]
        analyses  = [Analysis.from_dict(d) for d in payload.get('analyses', [])]

        blueprints = []
        for bp_data in payload.get('blueprints', []):
            bp_supplies = [Supply.from_dict(d) for d in bp_data.get('supplies', [])]
            bp = Blueprint.__new__(Blueprint)
            bp.id       = bp_data['id']
            bp.label    = bp_data['label']
            bp.saved_at = bp_data.get('saved_at', '')
            bp.supplies = bp_supplies
            blueprints.append(bp)

        dm._supplies    = supplies
        dm._products    = products
        dm._analyses    = analyses
        dm._blueprints  = blueprints
        dm.current_file = payload.get('current_file')
        return True

    except Exception as exc:
        print(f'[storage] load error: {exc}')
        return False


def clear() -> None:
    """Delete the data file."""
    try:
        if os.path.exists(_DATA_FILE):
            os.remove(_DATA_FILE)
    except Exception as exc:
        print(f'[storage] clear error: {exc}')
