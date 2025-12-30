"""API and network runtime settings (kept separate from `api/config.py` which should only expose endpoints).

This file contains values that are environment-dependent but are not endpoint definitions.
"""
import os

# This module previously contained API network defaults, but these are now
# defined in `api/config.py`. Keep this module minimal in case we add other
# non-endpoint settings in the future.

# (No network defaults defined here.)
