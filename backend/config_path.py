"""
Python path configuration for AutoRFP Backend.
This module configures the Python import path to resolve relative imports.
"""

import sys
import os

def setup_python_path():
    """Setup Python path for proper module imports."""
    # Get the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add backend directory to Python path if not already there
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
        print(f"Added {backend_dir} to Python path")
    
    return backend_dir

# Configure path on import
setup_python_path()
