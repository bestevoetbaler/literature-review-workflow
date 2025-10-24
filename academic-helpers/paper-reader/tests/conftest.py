"""
Pytest configuration and fixtures for academic-helpers/paper-reader.

This file configures pytest and imports shared fixtures from the fixtures module.
"""

import sys
from pathlib import Path

# Add parent directories to path for imports
# This allows 'from academic_helpers.paper_reader...' imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Also add paper-reader root for relative imports
paper_reader_root = Path(__file__).parent.parent
sys.path.insert(0, str(paper_reader_root))

# Import all fixtures from fixtures/conftest.py
from tests.fixtures.conftest import *  # noqa: F401, F403


# Additional configuration can be added here
