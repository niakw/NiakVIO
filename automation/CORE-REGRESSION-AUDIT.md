# Core / native regression audit — 2026-09-09

This is a non-publication audit checkpoint. Static Core contracts do not replace native UX evidence.

## Provider portfolio signal

- Current manifest: 5.21.37, 96 providers.
- Exhaustive historical status matrix: `automation/PROVIDER-HISTORY-MATRIX.md`.
- Exact version evidence is isolated per snapshot; no 5.21.36/current fallback is permitted.
- Generated historical regression watch currently includes Kehflix, MoviesHunt and Purstream.
- Known-good lanes are immutable baselines until a candidate wins a live A/B check.

## Current field signal

TV field evidence on the currently published manifest remains materially better than Desktop:

- Interstellar: Castle, PersianStremio, StreamZo.
- The Unwanted Undead Adventurer: Anime-Sama.
- House of the Dragon S1E1: PersianStremio, DesiFlix, Castle.
- Desktop macOS field observation: no visible provider result.

This asymmetry is a systemic client/runtime signal and must not be flattened into provider-by-provider route failures.

## Core timeout and stream-presentation contract

`CORE - Stream Metadata Contract` run `34331678345` passed on commit `fdfe7bca3cb5db544a90372bf21547a2bdf68668`.

Validated in that run:

- workflow security preflight;
- provider invocation timeout floor: current client lab uses 70,000 ms;
- playback timeout floor: current client lab uses 18,000 ms;
- these two client-lab defaults are unchanged from the 5.21.36 snapshot;
- global lossless stream metadata contract;
- stream presentation pipeline;
- stream quality recovery;
- sanitizer transport/header preservation and fail-closed behavior;
- presentation fixed point;
- current presentation keeps quality-bearing `title` and `name`, `badgeIds`, `displayBadges`, and `presentationFacts`;
- legacy `publish_nuvio_tv_compat_v2.py` 12–15 s provider-specific publisher is not referenced by any current workflow and is therefore not publication-authoritative. The regression contract now fails if it becomes authoritative again.

Result: there is no current static evidence that the global Core client-lab timeout or stream-presentation metadata contract regressed from 5.21.36. This does **not** prove real client latency, badge rendering, stream session behavior or playback UX; those remain Native Lab gates.

## Desktop Lab invalid historical zero

The last final-five Desktop run `34110935429` did not execute the provider corpus.

Both desktop jobs were blocked before provider execution because official NuvioDesktop's `PlayerExitOrderingTest.kt` fake `PlayerEngineController` did not implement the newly required `applyAudioLanguagePreferences(languages: List<String>)` member. On macOS the native player bridge itself built successfully; the later `compileTestKotlinDesktop` failure prevented begin markers and left all 96 providers unexecuted.

Therefore the CI `0/96` from that run is lab-infrastructure evidence, not provider evidence.

A minimal test-only compatibility shim now exists:

- `scripts/native_desktop_upstream_test_compat.py`
- `tests/native_desktop_upstream_test_compat_test.py`
- `automation/native-human-ux-policy.json` v7 records the exact blocker and permits only the exact stale upstream commonTest fake-controller file.
- `.github/workflows/native-desktop-reader-acceptance.yml` applies the shim before corpus preparation and audits the resulting checkout.

The shim is fail-closed and idempotent. It never edits Nuvio production runtime, player, network, Gradle or OS behavior. Once upstream fixes the stale test itself, the shim becomes a no-op.

## Required next evidence

1. Run Desktop macOS and Windows on a frozen NiakVIO HEAD and prove that the corpus actually begins/executions are non-zero.
2. If Desktop reaches providers but still returns no streams while TV field evidence remains positive, investigate the real Desktop runtime path (provider loading/fetch/session) as a systemic regression before route repair.
3. Re-run TV Android, Mobile Android and Mobile iOS against the same final candidate.
4. Validate real stream metadata/badges, latency/session and production player outcomes from native evidence; static Core green is necessary but insufficient.
5. Keep residual provider route/data debt with LEARN after bounded Repair attempts; prioritize shared-family fixes and preserve proven historical/current lanes.

Publication remains blocked until the 96-provider proof, all five Native Labs and the final security/docs/minimizer/fixed-point gates are complete.
