"""
Configuration file for pytest that modifies Python path to include the root directory.
This allows tests to import modules from the root directory.
"""

import os
import sys

# Get the root directory of the project (parent directory of tests)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the root directory to Python path
sys.path.insert(0, root_dir)
