"""Academic Paper Reader Module - MVP Implementation"""

__version__ = "0.1.0"

# Import main classes for package-level access
from .pipeline import PaperReader
from .database import Database
from .config import get_config

__all__ = ['PaperReader', 'Database', 'get_config']
