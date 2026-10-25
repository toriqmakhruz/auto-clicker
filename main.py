"""
Main Entry Point untuk Auto Clicker Macro Pro
"""

import sys
import os

# Pastikan direktori kerja saat ini berada di path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from gui import main

if __name__ == "__main__":
    main()
