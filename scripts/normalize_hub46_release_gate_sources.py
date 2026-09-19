#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts"))
from current_provider_scope import active_provider_count, disabled_provider_count, visible_provider_count, assert_directory_contract
def main():
 assert_directory_contract(); print(f"CURRENT_PROVIDER_SOURCE_CONTRACT active={active_provider_count()} disabled={disabled_provider_count()} visible={visible_provider_count()} mutations=0"); return 0
if __name__=="__main__": raise SystemExit(main())
