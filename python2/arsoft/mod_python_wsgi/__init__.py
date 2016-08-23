"""Package to wrap legacy mod_python code in WSGI apps."""
import sys
import os.path

__all__ = ['request', 'wrap']

mod_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, mod_dir)
