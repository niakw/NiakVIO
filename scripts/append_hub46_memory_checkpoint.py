#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "MEMORY.md"
MARKER = "## Repair campaign checkpoint — 2026-09-13 Europe/Paris (Hub-46 only)"
CHECKPOINT = r'''

## Repair campaign checkpoint — 2026-09-13 Europe/Paris (Hub-46 only)

This checkpoint supersedes older 96-provider Lab scope **for the active repair campaign only**. The global product catalogue may remain 96 providers, but all repair parity/Labs in `fix/labs-5.21.44-20260912` must execute exactly the authoritative 46-provider Hub scope from `automation/evidence/hub-lab-matrix-46.json`. Do not shrink the published/global catalogue to manufacture green metrics, and do not expand this repair campaign back to all 96 providers.

### Branch / safety
- Active repair branch: `fix/labs-5.21.44-20260912`.
- `main` is not a repair write target and must not be merged/touched without explicit user authorization.
- Verified `main` head during this checkpoint: `8f57f8eb42885c0b6b898aa018e806a1b0f72467` (`chore(audit): refresh external AI audit logs [skip ci]`).
- Core provider timeout remains **25 s**.

### Streamflix Desktop timer compatibility
- Actual fix commit: `2ab26c2d78e2ef856cf9eb29d925216c447a8f30` — `fix(streamflix): tolerate missing desktop timer globals`.
- Direct `setTimeout`/`clearTimeout` usage is guarded; timerless Desktop-like runtime no longer throws `ReferenceError`.
- Durable regression: `tests/streamflix_timerless_runtime_test.cjs`, proven green in TEMP run `34750296391`.
- Streamflix still requires normal provider/lane revalidation like every other provider; timer compatibility alone is not a stream proof.

### Hub-46 scope and rotating corpus
- Authority: `automation/evidence/hub-lab-matrix-46.json`, exactly **46** rows.
- Native workflow scope guard is exact-set equality, not count-only.
- Rotating corpus replaces stale fixed-only fixture selection for active Hub-46 parity/Labs. It keeps movie/tv/anime lanes and rotates deterministically across known works while preserving known compatibility slugs.
- Previous Desktop 0/46 was diagnosed as **Lab infrastructure**, not 46 provider failures: the official native client reloaded the 96-provider `manifest.json`, and Desktop duration lookup still queried the legacy fixed trigger file for rotating slugs.
- Physical Lab manifest fix commit: `b18342a12b88af1825de8765ecb8011ceb5b78aa` — `fix(labs): load exact Hub-46 manifest in native clients`.
- Derived root manifest: `manifest-hub46.json`, exactly 46 rows, rooted beside `providers/` so relative provider filenames keep normal raw-GitHub semantics.
- Desktop/Mobile Android/TV Android runners use `manifest-hub46.json` whenever `NIAKVIO_PROVIDER_SCOPE_MATRIX` is active; iOS rewrites its raw manifest URL to the exact branch SHA + `manifest-hub46.json`.
- Desktop rotating duration lookup now comes from `scripts/rotating_corpus.py`, not `.github/triggers/nuvio-client-lab.json`.
- Native runs dispatched on exact SHA `b18342a12b88af1825de8765ecb8011ceb5b78aa`: Desktop `34755341606` (macOS + Windows), Android `34755342352` (TV + Mobile Android), iOS `34755343057`.

### Upstream parity v3 — authoritative queue before next provider repairs
Workflow run `34753648375`, scope 46, 3 rotating samples/lane, 25 s timeout:
- matched/tested: **45/46**; missing upstream mapping: **1** (`kehflix`); provider downloads failed: 0.
- status: **8 FULL / 11 REGRESSION / 11 RESAMPLE / 15 ZERO**.
- Certain manual regression providers (upstream stream exists while NiakVIO returns zero): `animesama-co`, `animevostfr`, `french-manga`, `kurage`, `playimdb`, `sekai`, `streamzo`, `uhdmovies`, `voiranime`, `voiranime-homes`, `voiranime-rip`.
- Exact certain regression lanes/fixtures:
  - `animesama-co`: anime / `my-hero-academia-s01e01` TMDB 65930.
  - `animevostfr`: anime / `fullmetal-alchemist-brotherhood-s01e01` TMDB 31911.
  - `french-manga`: movie / `jujutsu-kaisen-0` TMDB 810693; anime / `death-note-s01e01` TMDB 13916.
  - `kurage`: anime / `my-hero-academia-s01e01` TMDB 65930.
  - `playimdb`: movie / `oppenheimer` TMDB 872585; tv / `house-of-the-dragon-s01e01` TMDB 94997.
  - `sekai`: anime / `chainsaw-man-s01e01` TMDB 114410.
  - `streamzo`: movie / `colony-2021` TMDB 760873; tv / `the-boys-s01e01` TMDB 76479; anime / `demon-slayer-s01e01` TMDB 85937.
  - `uhdmovies`: movie / `fight-club` TMDB 550.
  - `voiranime`: anime / `death-note-s01e01` TMDB 13916.
  - `voiranime-homes`: anime / `death-note-s01e01` TMDB 13916.
  - `voiranime-rip`: anime / `failure-frame-s01e01` TMDB 245285.
- RESAMPLE providers (clean miss on sampled catalogue, not a proved Niak regression): `animesultra`, `animevost-fr`, `castle`, `coflix`, `hindmoviez`, `mallumv`, `movieshunt`, `mugiwarastream`, `papadustream`, `persianstremio`, `yflix`.
- Repair rule: prioritize certain regressions; RESAMPLE gets another catalogue sample; ZERO/both-fail is not rewritten blindly. Provider becomes FULL only when every declared required lane is proved.

### Pending after this checkpoint
- Read exact five-platform Native Lab outcomes on SHA `b18342a…`; do not call them green until each platform really executes the 46-provider physical manifest.
- Repair the 11 certain regression providers/lane failures above using A/B evidence; rerun parity and replace this census with the newer authoritative count.
- Re-sample the 11 RESAMPLE providers and classify external/catalogue misses separately from Niak regressions.
- Resolve/record Kehflix upstream mapping separately; do not fabricate parity.
- Keep TEMP workflow neutral after this checkpoint so no stale one-shot patch remains armed.
'''


def main() -> int:
    current = MEMORY.read_text(encoding="utf-8")
    if MARKER in current:
        print("FIELD_MEMORY_CHECKPOINT status=already-present")
        return 0
    MEMORY.write_text(current.rstrip() + CHECKPOINT + "\n", encoding="utf-8")
    print("FIELD_MEMORY_CHECKPOINT status=written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
