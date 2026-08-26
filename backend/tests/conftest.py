import sys
from pathlib import Path


backend_directory = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_directory))