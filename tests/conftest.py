"""Shared test fixtures — ensures src/ is on sys.path for module imports."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
