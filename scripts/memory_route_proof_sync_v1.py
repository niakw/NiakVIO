#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import textwrap

ROOT = Path(__file__).resolve().parents[1]

memory = ROOT / "MEMORY.md"
text = memory.read_text(encoding="utf-8")
marker = "## 2026-09-07 — Accepted 5.21.37 / Terminal Session V29 / live-yield checkpoint"
if marker not in text:
    checkpoint = textwrap.dedent(r'''

    ## 2026-09-07 — Accepted 5.21.37 / Terminal Session V29 / live-yield checkpoint

    - **This checkpoint supersedes all earlier wording that says the public release is still 5.21.35 or that 5.21.36/5.21.37 is pending.** Current public release is **5.21.37**.
    - Publication workflow: `FIX - Publish Terminal Session V29`, run **34120732027**, job **101737919476**, completed success.
    - Final publication commit: **`6f74939efa11b2c886e82002c242b923a4f87f6c`** (`fix(core): publish terminal labels and stale-session isolation V29`). Push to `main` completed successfully.
    - Public manifests verified after push: `manifest.json`, `vf/manifest.json`, `no-anime/manifest.json`, and `vf-no-anime/manifest.json` all report **5.21.37**.
    - 96/96 published Provider JS were rematerialized and physically verified to contain `tmdb-data-contract-launch-gate-v29-native-abort-race`, `requestAbortPromise(controller,requestToken)`, and presentation client-projection V20.
    - V29 closes the stale-session hole where a native QuickJS fetch bridge may ignore `AbortSignal`: provider fetch now races the native call against request cancellation. Functional regression with an intentionally never-resolving old native fetch completed in ~1 ms after supersede and observed only `/1/one` then `/2/one`; superseded fallback `/1/two` never reached network.
    - Terminal stream-label bug was localized outside provider-specific quality calculation: Engine V2 accepted labels such as `Kehflix - Inconnue` as provider names. Engine V2 now strips terminal placeholder suffixes and mirrors final projected `title` into `name`, matching the client-facing Core projection. Placeholder quality (`Unknown`, `Inconnue`, `N/A`, etc.) collapses to provider-only; meaningful qualities remain, including `1080p` and `2160p -> 4K`.
    - `CORE.STREAM_SANITIZER.V6` output guard passed across all 96; release integrity and fixed-point override checks passed.
    - Nuvio client upstream drift seen during release: NuvioDesktop audited contract remained accepted; NuvioMobile had a safe upstream advance; NuvioTV had a separate semantic-sensitive subtitle-cache drift requiring review. Provider publication intentionally continued against pinned audited client contract refs.

    ### Live yield on exact 5.21.37 candidate

    - Interstellar matrix tested **55 enabled movie-capable providers**. Only **6** returned automatic streams: `castle`, `hindmoviez`, `streamflix`, `streamzo`, `videasy`, `wookafr`. VF automatic providers: **2**, `streamzo` + `wookafr`. **49/55** returned no streams. This is materially better than the earlier native observation of only StreamZo/Kehflix/Castle in one client session, but still far below the 96-provider objective and must not be considered provider recovery completion.
    - Notably Kehflix returned zero in the CI Interstellar matrix even though it is a known viable provider in other live/native fixtures; treat this as route/runtime/fixture evidence, not provider-wide disablement.
    - User Desktop anime fixture was correctly identified as **The Unwanted Undead Adventurer S01E02**, IMDb `tt30177477`, not Hell Mode. Candidate matrix tested **62 episodic/anime-capable providers**: **2 positive** (`anime-sama`, `neko-sama`), network reached **49**, successful provider HTTP **37**.
    - Secondary Hell Mode S01E12 (`tt38646634`) matrix produced the same provider-positive set: **2/62**, `anime-sama` + `neko-sama`; network reached 49, successful HTTP 36.
    - These anime results prove the global `series -> tv/anime` transport is not completely broken, but extraction/runtime route yield is still severely underperforming after successful network access for many providers.
    - User Desktop logs separately showed DNS/host failures including `api.nakios.live`, `*.eat-peach.sbs`, and VidLink-related traffic. Current main domains can be alive while historical/API subdomains or route families are stale; domain, route, extraction and player evidence must remain separately classified.

    ### Current priority after 5.21.37

    1. Keep V29 terminal-label/session isolation immutable while provider recovery continues.
    2. Resume **proof-first real route recovery across all 96**, including disabled/off rows for recoverability; test a route live at discovery time and never promote static fragments as executable routes.
    3. Use `MAIN - Route Proof Reconstruction 96` as a non-public candidate workflow. Its baseline must derive from `.github/triggers/route-proof-reconstruction.json`, not be hard-coded to 5.21.35.
    4. For every candidate, compare live yield against the accepted 5.21.37 baselines: Interstellar 6/55 automatic (2 VF), Unwanted Undead 2/62, Hell Mode 2/62. A structurally green reconstruction that does not improve/accurately explain these results is not completion.
    5. Route families already requiring scrutiny include VidLink historical `/api/b/...` versus current documented `/movie/{tmdbId}` and `/tv/{tmdbId}/{season}/{episode}`, and Nakios principal-site versus stale `api.nakios.live`. Do not replace routes solely from documentation; require provider-specific executable HTTP proof before promotion.
    6. Preserve the five Native Labs requirement after route/runtime stabilization: TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows.
    7. Continue automatic `MEMORY.md` checkpoints for every important green/red run, root cause, architecture change, publication, native proof, and security proof.
    ''').rstrip()
    memory.write_text(text.rstrip() + "\n" + checkpoint + "\n", encoding="utf-8")
    print("MEMORY_CHECKPOINT_52137_ADDED")
else:
    print("MEMORY_CHECKPOINT_52137_ALREADY_PRESENT")

trigger_path = ROOT / ".github/triggers/route-proof-reconstruction.json"
trigger = json.loads(trigger_path.read_text(encoding="utf-8"))
trigger["retry"] = int(trigger.get("retry") or 0) + 1
trigger["expectedPublicBaseline"] = "5.21.37"
trigger["targetVersion"] = "5.21.38-candidate"
trigger["requiredFinalProof"] = "proof-v5-96+interstellar+unwanted-undead+hellmode+hotd"
trigger["triggeredAfter"] = "6f74939efa11b2c886e82002c242b923a4f87f6c"
trigger_path.write_text(json.dumps(trigger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("ROUTE_PROOF_TRIGGER_SYNCED expected=5.21.37")
