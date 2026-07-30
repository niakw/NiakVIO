#!/usr/bin/env python3
"""Regression: the obsolete global stream-output guard must stay removed."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
result=subprocess.run([sys.executable,str(ROOT/'tests/provider_capabilities_test.py')],check=False)
raise SystemExit(result.returncode)
