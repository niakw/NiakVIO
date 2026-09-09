# NiakVIO checkpoint — 2026-09-09 — Core regression gate before Desktop rerun

- `CORE - Stream Metadata Contract` run `34331678345` passed fully on `fdfe7bca3cb5db544a90372bf21547a2bdf68668`.
- New `tests/core_runtime_nonregression_contract_test.py` passed and locks provider lab timeout >=60s (actual 70s), playback timeout >=18s (actual 18s), current 96-provider cardinality, quality-bearing stream `title` + `name`, `badgeIds`, `displayBadges`, `presentationFacts`, and requires the legacy 12–15s `publish_nuvio_tv_compat_v2.py` publisher to remain absent from current workflows.
- Remaining Core contract steps also passed: lossless metadata, presentation pipeline, quality recovery, sanitizer header/transport preservation, sanitizer fail-closed, and presentation fixed point.
- Static Core green is necessary but does not prove actual client UX/latency/session/player/badge rendering. Native Labs remain mandatory.
- Durable audit doc: `automation/CORE-REGRESSION-AUDIT.md`.
- Desktop prior run `34110935429` is invalid as provider-zero evidence because it failed before corpus execution on stale upstream test compilation. Test-only compatibility shim/policy v7/workflow wiring are now committed. Next step is a Desktop macOS+Windows rerun on a frozen HEAD; do not push unrelated commits while it runs.
