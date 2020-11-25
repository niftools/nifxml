"""
Utility functions for nifxml module
"""

import sys


def export(clsorfn):
    """Export decorator"""
    mod = sys.modules[clsorfn.__module__]
    if hasattr(mod, '__all__'):
        mod.__all__.append(clsorfn.__name__)
    else:
        mod.__all__ = [clsorfn.__name__]
    return clsorfn
