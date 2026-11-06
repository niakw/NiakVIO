# NiakVIO — S00, mini-series and Brain outcome audit (2026-11-06)

## Ground truth

Main census run 42293945772 on SHA 6c09e4e: 46 provider records; 41 enabled in manifest; 21 FULL OK, 3 PARTIAL OK, 2 CANDIDATE OK, 17 repairQueue, 5 disabled lifecycle entries. These are evidence classifications, **not** total correct-episode playbacks.

Fast Brain Repair run 42294953966: 12 selected, 0 generated candidates, 0 validated, 12 Learning debts, no_new_repair_experiment. GitHub workflow SUCCESS is not provider success. Representative planning contains allowedProfiles=[] and learning_generations_exhausted; diagnostic/selector/transport gains do not equal generated -> compiled -> selected -> applied -> materialized -> executed -> identity-safe decoded media -> persisted.

## Runtime regression: special season 0

Reported: Spartacus S00E01 served regular season 1 or season 2 episode. Reproduced against current CORE.STREAM_IDENTITY.V1 before correction: direct S01E01, structured season=1 and player query season=1 escaped rejection for S00 requests. ProviderBase used Math.max(1, season), missed season=0 in nested structured payload, and could pick first available season if requested season was absent. This is a common infrastructure defect affecting many providers, not one website's parser.

TheTVDB official order assigns Gods of the Arena (Past Transgressions) S00E01; alternate order calls it S02E01; standalone mini-series indexes it S01E01. Each is a distinct **catalogue coordinate**, and a crosswalk must also bind episode title and work identity. Never turn all S01E01 or S02E01 into S00E01 by number alone. Sources: https://thetvdb.com/series/spartacus/seasons/official/0 and https://thetvdb.com/series/spartacus/seasons/alternate/2 and https://www.imdb.com/title/tt39020004/episodes/ .

## Remediation and acceptance

Shared Core v17 preserves explicit 0 and validates season contradictions for titles and structured/player provenance. ProviderBase preserves S00 in episode URL markers and scoped season tables. Missing season must not silently select season 1 for specials. Preserve opaque results as **unverified** unless proven; this fix cannot establish terminal byte identity from an opaque URL. All platform clients must honor the same request coordinates. A publication reconcile trigger is updated to rebuild active provider JS; its run and final SHA need explicit verification.

Tests: tests/special_season_zero_identity_test.py and Core Stream Metadata Gate. Need to verify materialized bundles, manifests, cached versions, then replay same TMDB request on TV/Mobile/Desktop, including late streams. Add a *verified* cross-catalog translation map only after episode title/work ID/alternate ordering evidence and non-regression across families. Do not overwrite provider title from TMDB or equate two different mini-series by the word Spartacus.

## Separate Brain blocker

Codex PRs in Brain-LLM #6–#20 mainly evolved context/budget/request transport, no provider-FULL improvements demonstrated by latest census. NiakVIO PR #266 title promises five repairs but changed probes/harness and workflows. Detailed attribution is needed before asserting causality for all provider losses. Brain must output executable novel methods rather than infinite exhausted strategy versions; compare generated proposal to exact current bytes, observed downstream media, and durable memory. 17 queue remains uncorrected.

## Status

**Root cause reproduced.** Core/ProviderBase code and regression tests prepared for publication; 16 representative isolated JS cases passed in diagnostic session. Not yet proof of production rebuild, end-to-end stream validation, client delivery or any provider repair. CI and final remote SHA are the authority.
