#!/usr/bin/env python3
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "MEMORY.md"
CHECKPOINTS = [
    (
        "## 2026-09-07 — Route recognition V6 retry/dependency checkpoint",
        r'''

## 2026-09-07 — Route recognition V6 retry/dependency checkpoint

- Active experimental branch: `workbench/route-recognition-v6`; no publication from this branch. The public accepted release remains whatever the earlier publication checkpoint says until an explicit verified publication occurs.
- Canonical Repair/Learn/Force engine is `scripts/run_provider_repair_pipeline_v6.py`; all three modes use the same recognition -> correction -> rematerialization -> targeted-yield path.
- Network skip set remains 9 previously validated providers: `allwish`, `anime-sama`, `castle`, `hindmoviez`, `kehflix`, `neko-sama`, `streamzo`, `videasy`, `wookafr`. Retry-4 run `34136291243` proved `tested=87 skipped=9 overlap=0`; common ProviderBase changes still rematerialize all 96 and therefore require deterministic 96-provider regressions.
- Retry-4 route census: 87 targeted, 39 providers with proven upstream routes, 238 targeted routes; merged proof = 46/96 providers and 299 routes. Post-reconstruction acceptance remained `raw=0 playable=0 verified=0`; 21 representative upstream-positive provider/type pairs were lost after reconstruction. Therefore route proof alone is not a repaired provider.
- Adaptive recognition retries are implemented: default 3 attempts, max 4, only for transient network/execution states (timeouts, reset/DNS-temporary, 408/425/429/5xx, worker-no-result/network exception). Deterministic source/runtime failures such as `MODULE_NOT_FOUND` and source-policy blocks are not retried.
- PlayIMDb is explicitly treated as a typed resolver/API family, not as a generic absolute-route or VidSrc-like multi-hop template. Its upstream currently calls `https://streamdata.vaplayer.ru/api.php`, uses `Origin/Referer` playback context from `nextgencloudfabric.com`, and returns URLs under `data.stream_urls`. V11/V12 work is scoped to proof-backed `typed-resolver-api` recipes; multi-hop/search/player chains are not flattened.
- A reconstruction parser defect was identified: plural resolver containers such as `stream_urls` were ignored by common `_sourceUrls`. V12 adds bounded explicit plural stream/source containers plus safe inherited playback headers (`Origin`, `Referer`, `User-Agent`, `Accept-Language`) without scanning arbitrary JSON URLs.
- `MODULE_NOT_FOUND` root cause: upstream Provider JS is executed from a temporary directory, so bare npm imports could not see NiakVIO's locked root `node_modules`. The single owner is `upgrade_provider_worker_module_resolution_v1.py`: only top-level declared dependencies may fall back to project-root resolution, Cheerio is redirected to parser-only `cheerio/slim`, and blocked Node built-ins remain blocked.
- Dependency probe run `34147056268` succeeded: 16/16 formerly `MODULE_NOT_FOUND` providers no longer hit that error; `allanime` immediately produced 4 proven routes. This is an environment/recognition recovery, not yet an end-to-end repaired provider until reconstructed `raw/playable` passes.
- Do not count PlayIMDb or AllAnime as repaired until the targeted post-reconstruction yield returns real streams. Do not expand the green skip set from route proof alone.
''',
    ),
    (
        "## 2026-09-07 — First V6 red-to-green acceptance: PlayIMDb",
        r'''

## 2026-09-07 — First V6 red-to-green acceptance: PlayIMDb

- Targeted canonical acceptance run `34147372929`, job `101822202535`, proved the first V6 unresolved provider repaired end-to-end: `playimdb`.
- Final reconstructed yield was `raw=1 playable=1 verified=1`; representative upstream-positive pairs were `2`, preserved `2`, lost `0`. Both movie and TV resolver paths therefore survived recognition -> DATA/recipe -> rematerialization -> reconstructed runtime.
- The repair is shared runtime behavior, not a hard-coded PlayIMDb provider patch: V7 classifies only proof-backed terminal TMDB resolver requests as `typed-resolver-api`; V11 allows only that class to execute without a search/base phase; V12 parses explicit plural source containers such as `data.stream_urls` and preserves the already-proven safe playback context (`Origin`, `Referer`, `User-Agent`, `Accept-Language`). Generic absolute routes and multi-hop/search/player providers remain excluded from this bypass.
- The same PlayIMDb acceptance job passed the full deterministic 96-provider gates: published CONFIG 96/96, Provider/Core Lego ownership, global stream output guard 96/96, episodic identity/year regressions, global media-type resolver, dual IMDb/TMDB identity, stream presentation, and presentation pipeline.
- This does not mean the 9 previously-green providers were network re-probed; they remained excluded from network recognition. It does prove the common V11/V12 rematerialization did not break the global 96-provider structural/runtime contracts.
- Parallel AllAnime acceptance was not a repair: its selected upstream fixture itself had zero streams, and reconstructed yield remained `raw=0 playable=0 verified=0`. Route proof alone is not promoted to green.
- NetMirror is the next typed-resolver candidate because retry-4 showed direct TMDB movie/episode resolver requests with positive upstream streams and the same old `provider_zero_before_provider_network` reconstructed failure class.
''',
    ),
]


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    appended = []
    for marker, block in CHECKPOINTS:
        if marker in text:
            continue
        text = text.rstrip() + block + "\n"
        appended.append(marker)
    if not appended:
        print("MEMORY_ROUTE_REPAIR_CHECKPOINTS already-present")
        return 0
    PATH.write_text(text, encoding="utf-8")
    print(f"MEMORY_ROUTE_REPAIR_CHECKPOINTS appended={len(appended)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
