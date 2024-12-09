# src/humanizer/__init__.py
"""Humanizer package."""
from importlib.metadata import version, PackageNotFoundError
from humanizer.cli import cli

try:
    __version__ = version("humanizer")
except PackageNotFoundError:
    __version__ = "unknown"

def main():
    """Entry point for the command line interface."""
    return cli()

if __name__ == "__main__":
    main()
