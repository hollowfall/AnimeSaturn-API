"""
Executable entrypoint for python -m animesaturn and python animesaturn
"""
import sys
import os

if __package__ == "" or __package__ is None:
    # Executed directly as `python animesaturn`
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from animesaturn.cli import main
else:
    from .cli import main

if __name__ == "__main__":
    sys.exit(main())

