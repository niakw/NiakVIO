#!/usr/bin/env python3
"""Compatibility entry point for Provider v3 contract enrichment.

Provider contract recognition is NiakVIO-owned and source-agnostic. The durable
recognizer consumes JavaScript/static evidence already available to the pipeline;
the role classifier and expression analyzer extend it with safe static
understanding of route purpose, URL concatenation, request variables, POST bodies
and bounded decoded string evidence. No provider JavaScript is executed.
"""
import provider_contract_recognizer as _recognizer
from provider_route_role_classifier import install as _install_route_roles
from provider_route_expression_analyzer import install as _install_route_analyzer

_install_route_roles(_recognizer)
_install_route_analyzer(_recognizer)
from provider_contract_recognizer import *  # noqa: F401,F403,E402


if __name__ == "__main__":
    raise SystemExit(main())
