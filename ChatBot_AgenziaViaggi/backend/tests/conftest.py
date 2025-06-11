import os
import sys

# Aggiungi il percorso della directory backend al PYTHONPATH
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir) 