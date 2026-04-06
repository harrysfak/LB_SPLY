#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║       LAB SUPPLY MANAGEMENT  —  εκκίνηση                ║
║       python main.py                                     ║
╚══════════════════════════════════════════════════════════╝

Εξαρτήσεις:  pip install pandas openpyxl matplotlib
"""

import sys
import os

# Ensure the project root is on sys.path so all imports resolve
sys.path.insert(0, os.path.dirname(__file__))

from data.manager import DataManager
from ui.app import MainApp


def main():
    dm  = DataManager()
    app = MainApp(dm)
    app.mainloop()


if __name__ == '__main__':
    main()
