"""Pytest configuration for literature-review tests."""
import sys
from pathlib import Path

# Add parent directory to Python path so modules can be imported
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
