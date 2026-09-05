#!/usr/bin/env python3
"""Compatibility entry point for Provider v3 contract enrichment.

The production enrichment path is local-only: it consumes durable NiakVIO DATA,
reviewed recognition seeds and provider overrides. It performs no external
provider-repository lookup and executes no provider JavaScript.
"""
from provider_contract_local_enricher import *  # noqa: F401,F403


if __name__ == "__main__":
    raise SystemExit(main())
