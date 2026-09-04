#!/usr/bin/env python3
'''Upgrade the common ProviderBase reader through cumulative runtime v6 fixes.

The verified v5 upgrader is preserved verbatim in
upgrade_provider_base_runtime_v5_legacy.py.  This stable entry point keeps
existing workflows compatible while always applying the current cumulative
reader fixes.
'''
from __future__ import annotations

import upgrade_provider_base_runtime_v5_legacy as runtime_v5
import upgrade_provider_base_runtime_v6 as runtime_v6


def patch() -> bool:
    changed_v5 = runtime_v5.patch()
    runtime_v5.validate()
    changed_v6 = runtime_v6.patch()
    return bool(changed_v5 or changed_v6)


def validate() -> None:
    runtime_v5.validate()
    runtime_v6.validate()


def main() -> int:
    changed = patch()
    validate()
    print(
        'PROVIDER_BASE_RUNTIME_CURRENT_OK '
        f'changed={str(changed).lower()} v5=1 v6=1 '
        'external_ids=1 traversal_eligibility=1 nested_priority=1'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
