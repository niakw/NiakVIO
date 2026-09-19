#!/usr/bin/env python3
"""CI entrypoint for catalogue breadth with TMDB credentials exposed to Provider JS."""
from pathlib import Path

import audit_provider_catalogue_breadth as breadth

breadth.PROBE = Path(__file__).resolve().with_name("nuvio_tv_probe_tmdb_ci.cjs")

if __name__ == "__main__":
    raise SystemExit(breadth.main())
