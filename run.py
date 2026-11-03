#!/usr/bin/env python3
"""Entry point: python3 run.py <command> ...  (see notes_agent/cli.py)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from notes_agent.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
