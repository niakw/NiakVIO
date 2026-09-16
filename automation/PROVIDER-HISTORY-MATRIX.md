# Provider history & live classification — 46 current / historical archive

- Current manifest: **5.21.48**, providers: **46**.
- Historical snapshots are compared without cross-version fallback: **5.21.0 → 5.21.16 → 5.21.36 → current**.
- State legend: **🟢 positive**, **🟡 partial/degraded**, **🟠 LEARN debt**, **🔴 explicit failure**, **⚪ unknown/inconclusive**.
- A version/hash is not treated as green unless that exact snapshot has matching evidence.
- Live precedence for current: TV field evidence / current published-byte guard > reconstruction candidate > historical evidence.
- Desktop macOS field observation: **No provider returned a visible result on Desktop macOS in the user's current field test.**
- Non-regression policy: a known-good provider/lane is immutable until a replacement wins an A/B live check.

## Classification counts

- **UNVERIFIED**: 28
- **CURRENT_RED**: 6
- **HISTORICAL_GREEN_UNRETESTED**: 3
- **PARTIAL_PROTECT**: 3
- **CANDIDATE_GREEN**: 2
- **PROTECT**: 2
- **PARTIAL**: 1
- **UPSTREAM_DRIFT**: 1

## Version regression watch

- Providers with at least one **🟢 historical snapshot** and a **🔴/🟠 current state**: **3**.
- `kehflix`, `movieshunt`, `purstream`

## 46-current-provider matrix

| Provider | Types | Family | 5.21.0 state | 5.21.16 state | 5.21.36 state | Current state | Retained | 5.21.36 live | Current published/field | Class | Action |
|---|---|---|---|---|---|---|---:|---|---|---|---|
| 4khdhub | movie, tv | catalogue-html | 🔴 runtime-error · 1.0.37 / `4efd8276edad3398` | 🟡 provider-unreachable/playable-host · 1.0.46 / `e70dc206194911cc` | 🔴 no-streams · 1.0.60 / `18a059512a0cbd33` | 🔴 published-red · 1.0.74 / `4ab23ab9a1a32d0b` | 10 | movie:0 tv:0 | guard movie:0 tv:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| allanime | anime | tmdb-direct-api | ⚪ provider-unreachable/inconclusive · 1.0.21 / `7947316d3cbed215` | ⚪ provider-unreachable/inconclusive · 1.0.23 / `7947316d3cbed215` | 🔴 no-streams · 1.0.30 / `4309c59ca0f5eaa8` | ⚪ current-unverified · 1.0.44 / `82c8e18d09c5dacf` | 10 | anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| allwish | movie, tv | tmdb-direct-api | 🔴 runtime-error · 1.0.29 / `dd80ecdd13bc9c0f` | ⚪ provider-unreachable/inconclusive · 1.0.59 / `4840bc8a37b320d2` | 🟢 verified · 1.0.73 / `fae84d4c01870beb` | ⚪ current-untested · 1.0.86 / `76dc9ea8e5b8a614` | 10 | movie:✓ tv:✓ | — | **HISTORICAL_GREEN_UNRETESTED** | Retest published bytes before touching route/data. |
| anikototv | anime | — | 🟢 healthy · 1.0.56 / `08d395095a632a46` | 🟡 provider-unreachable/playable-host · 1.0.87 / `8aadc05c38391372` | 🔴 no-streams · 1.0.101 / `a7618bce82d44808` | ⚪ current-unverified · 1.0.114 / `1e4967cb5a455685` | 10 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| anime-sama | anime | catalogue-episodes-js | 🔴 no-streams · 1.1.91 / `10e285fc12662f4d` | 🟡 provider-unreachable/playable-host · 1.1.122 / `c77fc61495dd1d49` | 🟡 partial · 1.1.140 / `24dc0903ba664a12` | 🟡 field-green/partial · 1.1.155 / `54244e5aad1e6c86` | 10 | movie:0 anime:✓ | guard movie:0 anime:✓; field anime:✓ The Unwanted Undead Adventurer | **PARTIAL_PROTECT** | Freeze proven field lanes; LEARN only the bad lanes. |
| anime-ultime | anime | catalogue-form-html-embed | 🔴 no-streams · 0.0.28 / `bcfadc4b5a25574a` | ⚪ provider-unreachable/inconclusive · 0.0.58 / `9917da85493786d9` | 🔴 no-streams · 0.0.72 / `a97f953068636cc7` | ⚪ current-unverified · 0.0.85 / `3dd11bbfb777c774` | 10 | movie:0 tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animekai | anime | catalogue-html-embed | 🔴 no-streams · 1.0.28 / `a240cb19bce3a1ec` | ⚪ provider-unreachable/inconclusive · 1.0.59 / `f36ee061425c160d` | 🔴 no-streams · 1.0.78 / `29d0be2d7a992800` | ⚪ current-unverified · 1.0.91 / `5f3ee8141ed07d33` | 10 | anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animesalt | anime | catalogue-html-embed | 🔴 no-streams · 1.0.25 / `412e95313f655028` | ⚪ provider-unreachable/inconclusive · 1.0.32 / `4bee389bf085824a` | 🔴 no-streams · 1.0.46 / `f89d520cc66a908e` | ⚪ current-unverified · 1.0.59 / `793281ae7409aea8` | 10 +baseline | movie:0 tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animesama-co | anime | catalogue-form-html-embed | 🔴 no-streams · 1.0.37 / `21c48b781f50cc44` | 🟡 provider-unreachable/playable-host · 1.0.56 / `767e940fab243e49` | 🔴 no-streams · 1.0.74 / `f72d5dd0221bdd2b` | 🔴 published-red · 1.0.89 / `350249fca4e75642` | 10 | movie:0 anime:0 | guard movie:0 anime:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| animesultra | anime | dle-full-story | 🟡 blocked · 1.0.53 / `afc39c0d373675e5` | ⚪ provider-unreachable/inconclusive · 1.0.61 / `5d47d365269607fd` | 🔴 no-streams · 1.0.79 / `1ec689e62432d1a4` | ⚪ current-unverified · 1.0.92 / `4400fffbfdcd5f66` | 10 +baseline | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animetsu | anime | catalogue-html-embed | 🔴 no-streams · 1.0.18 / `a1feac6991df10db` | ⚪ provider-unreachable/inconclusive · 1.0.24 / `362792f44aea9e97` | 🔴 no-streams · 1.0.38 / `6bb397e9635523e4` | ⚪ current-unverified · 1.0.53 / `7d6b5d1e84b5f32c` | 10 | anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animevost-fr | anime | catalogue-html-embed | ⚪ — | ⚪ provider-unreachable/inconclusive · 0.0.25 / `644a80e107ed66cc` | 🔴 no-streams · 0.0.39 / `80fa3a00000fc600` | ⚪ current-unverified · 0.0.52 / `051c63df1f1062d4` | 10 | tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animevostfr | anime | wordpress-search-episode | 🔴 no-streams · 1.1.74 / `493f59d8056b0179` | 🟡 provider-unreachable/playable-host · 1.1.85 / `67e363cfbe37ba09` | 🔴 no-streams · 1.1.103 / `666957ed184dffbd` | 🟡 candidate-green · 1.1.116 / `8c01b586ec5f8d00` | 10 | movie:0 anime:0 | — | **CANDIDATE_GREEN** | Keep candidate; A/B against published bytes before promotion. |
| castle | movie, tv | catalogue-json-html-detail | 🟢 healthy · 2.0.35 / `defbe2701a5eb904` | 🔴 unavailable · 2.0.65 / `e588cade899cccbf` | 🟢 verified · 2.0.79 / `f9f1396b0939f955` | 🟢 field-verified · 2.0.92 / `20cfd8b307bdb405` | 10 | movie:✓ tv:✓ | field movie:✓ Interstellar; tv:✓ House of the Dragon S1E1 | **PROTECT** | Immutable live baseline; A/B required before replacement. |
| coflix | movie, tv, anime | catalogue-html | 🔴 no-streams · 1.0.48 / `d6d16a8e29693c08` | ⚪ provider-unreachable/inconclusive · 1.0.60 / `9b13b0c422060699` | 🔴 no-streams · 1.0.74 / `2a490577b4b8277f` | ⚪ current-unverified · 1.0.89 / `a9445da2713f49a7` | 10 | movie:0 tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| desiflix | movie, tv | stremio-json | 🟡 provider-unreachable/playable-host · 1.0.34 / `6b9f90ca348aa353` | 🟡 provider-unreachable/playable-host · 1.0.41 / `5cb266958e8b43de` | 🔴 no-streams · 1.0.64 / `22100513099b297e` | 🟡 field-green/partial · 1.0.74 / `01cfc7ff2cd3dd7e` | 0 | movie:0 tv:0 | guard movie:⚠ tv:✓; field tv:✓ House of the Dragon S1E1 | **PARTIAL_PROTECT** | Freeze proven field lanes; LEARN only the bad lanes. |
| flemmix | movie, tv | catalogue-html-embed | 🔴 runtime-error · 1.0.54 / `dedb61d806c7c1d6` | 🔴 no-streams · 1.0.64 / `18ea87541317477b` | 🔴 no-streams · 1.0.79 / `653c33fa401a00d2` | 🔴 published-red · 1.0.93 / `c02536f4da395a82` | 10 | movie:0 tv:0 | guard movie:0 tv:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| french-manga | anime | catalogue-html-embed | 🟢 healthy · 1.0.49 / `cbb3b26d43fea959` | 🟡 provider-unreachable/playable-host · 1.0.83 / `02c60e53f47b6927` | 🔴 no-streams · 1.0.101 / `21ccc21b1cd5e0fa` | 🟡 candidate-green · 1.0.114 / `63ce1ed8a74acb38` | 10 | movie:0 anime:0 | — | **CANDIDATE_GREEN** | Keep candidate; A/B against published bytes before promotion. |
| fullanime | anime | wordpress-search-episode | ⚪ — | ⚪ provider-unreachable/inconclusive · 0.0.25 / `17d89747ed077f44` | 🔴 no-streams · 0.0.39 / `c7b21640de1416af` | ⚪ current-unverified · 0.0.48 / `b51adb6e3c249389` | 0 | tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| hindmoviez | movie, tv | catalogue-form-html | 🟡 degraded · 1.0.34 / `a2fad478d23b3c67` | 🟡 degraded · 1.0.56 / `2afd92f17104b65c` | 🟡 partial · 1.0.70 / `3eb339d4e0b0bf13` | 🟡 published-partial · 1.0.84 / `fdf660568521d2b8` | 10 | movie:✓ tv:0 | guard movie:✓ tv:0 | **PARTIAL** | Preserve green lanes; LEARN failing lanes. |
| kehflix ⚠️ | movie, tv, anime | signed-player-api | ⚪ — | ⚪ provider-unreachable/inconclusive · 1.0.17 / `bfdd46578802aeee` | 🟢 verified · 1.0.51 / `064f32ab58f1fbf2` | 🔴 published-red · 1.0.66 / `e4c8b1d811b71d89` | 10 | movie:✓ tv:✓ anime:✓ | guard movie:0 tv:0 anime:0 | **UPSTREAM_DRIFT** | P1 LEARN/upstream refresh; do not rewrite Core as a fake regression fix. |
| kurage | anime | catalogue-html | ⚪ provider-unreachable/inconclusive · 1.0.27 / `b5240f665eb9c297` | ⚪ provider-unreachable/inconclusive · 1.0.36 / `6f2d4fa552dfc8ee` | 🔴 no-streams · 1.0.55 / `9ae58da956332c05` | ⚪ current-unverified · 1.0.68 / `e65c0fe891c16c05` | 10 | anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| mallumv | movie | catalogue-html-embed | 🔴 no-streams · 1.0.33 / `b4938cac084eca0e` | 🔴 unavailable · 1.0.64 / `863118576415a522` | 🔴 no-streams · 1.0.77 / `4b24dd9528fa01a3` | ⚪ current-unverified · 1.0.90 / `adf66799bf15a00b` | 10 | movie:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| moviebox | movie, tv | stremio-json | ⚪ provider-unreachable/inconclusive · 1.0.18 / `33507d0a8889b61b` | ⚪ provider-unreachable/inconclusive · 1.0.24 / `19a7b7bbaa035869` | 🔴 no-streams · 1.0.31 / `474398374977be95` | ⚪ current-unverified · 1.0.44 / `ea81f95a70d4417f` | 10 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| movieshunt ⚠️ | movie | catalogue-html | 🟢 healthy · 1.0.36 / `3aa3c567b2a014d9` | 🟡 provider-unreachable/playable-host · 1.0.51 / `ff486b0ec23ca8fc` | 🔴 no-streams · 1.0.64 / `e58b409178412c6e` | 🔴 published-red · 1.0.79 / `753b852cdd9afb1c` | 10 | movie:0 | guard movie:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| moviesmod | movie, tv | catalogue-form-html | 🔴 runtime-error · 1.0.28 / `edad1a7b333e5109` | ⚪ provider-unreachable/inconclusive · 1.0.36 / `ee171333c7a3c3f6` | 🔴 no-streams · 1.0.50 / `64e71c321ffd0757` | ⚪ current-unverified · 1.0.63 / `25f455ac73064bdc` | 10 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| mugiwarastream | anime | catalogue-json-html-detail | 🔴 no-streams · 1.0.60 / `7d28f3c2b7bc3578` | 🟡 provider-unreachable/playable-host · 1.0.71 / `7192e1a89082b113` | 🔴 no-streams · 1.0.89 / `d219aa0b1692c799` | ⚪ current-unverified · 1.0.102 / `e441b2b3296c73d4` | 10 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| neko-sama | anime | catalogue-html-embed | ⚪ — | 🟡 provider-unreachable/playable-host · 0.0.17 / `55c80ba9eebb7a65` | 🔴 no-streams · 0.0.31 / `44eb233db734113d` | ⚪ current-unverified · 0.0.44 / `3c2e87963729c0e0` | 10 | tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| papadustream | movie, tv, anime | catalogue-html-embed | 🔴 no-streams · 1.0.35 / `2d48289559aafe27` | 🟡 provider-unreachable/playable-host · 1.0.42 / `a26d6b94f047d941` | 🔴 no-streams · 1.0.56 / `6b1f7cfe1671a9db` | ⚪ current-unverified · 1.0.69 / `519fc88590c0e774` | 10 +baseline | movie:0 tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| persianstremio | movie, tv | stremio-json | 🟡 degraded · 1.4.36 / `7e31b6eedae47728` | 🟡 provider-unreachable/playable-host · 1.4.58 / `8c735f4b38215aea` | 🔴 no-streams · 1.4.72 / `5aad370c42f0bc9f` | 🟢 field-verified · 1.4.85 / `8f4399f53997346c` | 10 | movie:0 tv:0 | guard movie:✓ tv:✓; field movie:✓ Interstellar; tv:✓ House of the Dragon S1E1 | **PROTECT** | Immutable live baseline; A/B required before replacement. |
| playimdb | movie, tv | tmdb-direct-api | 🟢 healthy · 2.0.38 / `4b88cfbf96960a88` | 🟡 provider-unreachable/playable-host · 2.0.70 / `e33f87f4a7e4f3d7` | 🔴 no-streams · 2.0.84 / `c7d08723d76d91ad` | ⚪ current-unverified · 2.0.97 / `135786d462cabf00` | 10 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| purstream ⚠️ | movie, tv | tmdb-direct-api | 🟢 healthy · 3.0.37 / `04678dffa0c674e9` | 🟡 provider-unreachable/playable-host · 3.0.59 / `0a77b4d442370ffd` | 🔴 no-streams · 3.0.73 / `27128980d2e66c10` | 🔴 published-red · 3.0.87 / `a96b2783a6bece25` | 10 | movie:0 tv:0 | guard movie:0 tv:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| sekai | anime | slug-saga-inline-media | ⚪ provider-unreachable/inconclusive · 1.0.48 / `7947316d3cbed215` | ⚪ provider-unreachable/inconclusive · 1.0.50 / `7947316d3cbed215` | 🔴 no-streams · 1.0.68 / `cbb4ec48dfa2c28d` | ⚪ current-unverified · 1.0.81 / `4bb64096220c9d1c` | 10 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| showbox | movie, tv | catalogue-html | 🔴 runtime-error · 1.0.27 / `c450d3154b1b69b9` | ⚪ provider-unreachable/inconclusive · 1.0.57 / `b4aee24095349027` | 🔴 no-streams · 1.0.71 / `d6f66e7e18942c9b` | ⚪ current-unverified · 1.0.84 / `34427b639ee5a532` | 10 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| streamzo | movie, tv, anime | catalogue-html | 🟢 healthy · 1.0.62 / `0e0695a6398a6732` | 🟡 provider-unreachable/playable-host · 1.0.75 / `664cd45915ac001c` | 🟡 partial · 1.0.89 / `3ab1767966d7a1bc` | 🟡 field-green/partial · 1.0.102 / `4c6e3764cdae8d2c` | 10 | movie:✓ tv:⚠ anime:0 | guard movie:✓ tv:⚠ anime:0; field movie:✓ Interstellar | **PARTIAL_PROTECT** | P0 TV identity in LEARN; freeze movie path. |
| uhdmovies | movie, tv | catalogue-form-html | 🔴 no-streams · 1.0.17 / `faafa6b844017040` | ⚪ provider-unreachable/inconclusive · 1.0.49 / `41b2867bcc664c93` | 🔴 no-streams · 1.0.63 / `e6f0cc34b5ce7e9e` | 🔴 published-red · 1.0.76 / `efc3b90e8048e353` | 10 | movie:0 tv:0 | guard movie:0 tv:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| videasy | movie, tv | tmdb-direct-api | 🟢 healthy · 1.0.41 / `f9cb91b9df10ed43` | 🟡 provider-unreachable/playable-host · 1.0.71 / `51e53f85370dc234` | 🟡 partial · 1.0.85 / `5dc71b42b6b49e8a` | ⚪ current-untested · 1.0.98 / `8ab20147b3461fc4` | 10 | movie:⚠ tv:✓ | — | **HISTORICAL_GREEN_UNRETESTED** | Retest published bytes before touching route/data. |
| vidfast | movie, tv | catalogue-html-embed | 🟡 blocked · 1.0.21 / `3b6bb9c6bb0550a7` | 🟡 provider-unreachable/playable-host · 1.0.27 / `8c06edeea58a8ebb` | 🔴 no-streams · 1.0.41 / `ee6dbe52b16e6f16` | ⚪ current-unverified · 1.0.54 / `cedefacf35198b61` | 10 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| vidlove | movie, tv | tmdb-direct-api | 🟡 blocked · 1.0.30 / `f0abcd1a8ab6c822` | 🔴 no-streams · 1.0.60 / `efb1712141d044d6` | 🔴 no-streams · 1.0.74 / `849bb6600299c982` | ⚪ current-unverified · 1.0.87 / `f15d8604b41d1cf6` | 10 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| vidrock | movie, tv | catalogue-html | 🔴 unavailable · 1.0.24 / `e4f457c7daea80f5` | ⚪ provider-unreachable/inconclusive · 1.0.55 / `8e310b567b0fe5a6` | 🔴 no-streams · 1.0.69 / `c8939c8fd386a8e5` | ⚪ current-unverified · 1.0.83 / `90979c6d8ba068ae` | 10 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| voiranime | anime | wordpress-search-episode | 🔴 no-streams · 1.2.52 / `1aaecd3076ce5d80` | 🟡 provider-unreachable/playable-host · 1.2.69 / `9908ca75a64f9ab4` | 🔴 no-streams · 1.2.87 / `5d089315b3c068e4` | ⚪ current-unverified · 1.2.101 / `6bcc82dc7f40caa7` | 10 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| voiranime-homes | anime | catalogue-html-embed | 🔴 no-streams · 0.0.27 / `3bf64d238ad99eba` | 🟡 provider-unreachable/playable-host · 0.0.58 / `b40415f60370ad0b` | 🔴 no-streams · 0.0.72 / `b018e6aa40f1f817` | ⚪ current-unverified · 0.0.85 / `34ed2916a0ecd233` | 10 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| voiranime-rip | anime | catalogue-form-html-embed | 🔴 no-streams · 1.0.42 / `bfdd8bc581e9191d` | 🟡 provider-unreachable/playable-host · 1.0.61 / `4d13882f91995cea` | 🔴 no-streams · 1.0.79 / `f3d824fc948eed41` | ⚪ current-unverified · 1.0.92 / `393d54b54081e6f9` | 10 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| vostfree | anime | catalogue-html | 🟡 blocked · 1.1.70 / `1286c275654dac3a` | ⚪ provider-unreachable/inconclusive · 1.1.76 / `7a20c3198fde3b19` | 🔴 no-streams · 1.1.94 / `76c5fe1fbcad7173` | ⚪ current-unverified · 1.1.107 / `b79eaede0ccb9e1b` | 10 +baseline | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| wookafr | movie, tv | catalogue-html-embed | 🔴 no-streams · 1.0.42 / `06c24d8c26c50df0` | 🔴 unavailable · 1.0.50 / `73c72bc655edc9ea` | 🟢 verified · 1.0.64 / `3c1ac476d5c5e692` | ⚪ current-untested · 1.0.78 / `5808051aeed86e1e` | 10 | movie:✓ tv:✓ | — | **HISTORICAL_GREEN_UNRETESTED** | Retest published bytes before touching route/data. |
| yflix | movie, tv | catalogue-html-embed | 🔴 no-streams · 1.1.21 / `5bc4a93d15c1f685` | 🔴 no-streams · 1.1.27 / `f6ff420bc7d5882a` | 🔴 no-streams · 1.1.41 / `e76f97e3ced0e815` | ⚪ current-unverified · 1.1.54 / `20a1f87af79c361d` | 10 +baseline | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |

## Interpretation

- **🟢** means positive evidence tied to that exact version, not merely that the provider file existed.
- **🟡** means useful but incomplete evidence: partial lane, degraded/blocked health, wrong-content, or candidate-only.
- **🔴** means the exact snapshot/report produced an explicit failure such as no streams/runtime error or a current published-byte guard failure.
- **⚪** means unknown/inconclusive; it must never be silently treated as broken or green.
- Rows marked **⚠️** are regression-watch providers: an earlier exact snapshot was green while the current state is red/LEARN debt.
- `PROTECT` / `PARTIAL_PROTECT`: preserve proven lanes and require A/B live proof before replacement.
- `LEARN`: bounded manual Repair is exhausted; route/data discovery belongs to LEARN unless a shared family fix is proven.

### Priority/VF providers

- **4khdhub** — 🔴 CURRENT_RED: Current published-byte guard returns no verified requested lane. Action: LEARN/diagnose; compare history before any Core change.
- **anime-sama** — 🟡 PARTIAL_PROTECT: Current TV field evidence is positive, but CI exposes at least one bad/zero lane. Action: Freeze proven field lanes; LEARN only the bad lanes.
- **desiflix** — 🟡 PARTIAL_PROTECT: Current TV field evidence is positive, but CI exposes at least one bad/zero lane. Action: Freeze proven field lanes; LEARN only the bad lanes.
- **flemmix** — 🔴 CURRENT_RED: Current published-byte guard returns no verified requested lane. Action: LEARN/diagnose; compare history before any Core change.
- **hindmoviez** — 🟡 PARTIAL: Current published bytes have at least one verified lane and at least one failing/contradictory lane. Action: Preserve green lanes; LEARN failing lanes.
- **kehflix** — 🔴 UPSTREAM_DRIFT: 5.21.36 was historically green, but replaying the old 5.21.36 bytes against today's backend also fails. Action: P1 LEARN/upstream refresh; do not rewrite Core as a fake regression fix.
- **movieshunt** — 🔴 CURRENT_RED: Current published-byte guard returns no verified requested lane. Action: LEARN/diagnose; compare history before any Core change.
- **persianstremio** — 🟢 PROTECT: Current published manifest has direct TV field evidence. Action: Immutable live baseline; A/B required before replacement.
- **purstream** — 🔴 CURRENT_RED: Current published-byte guard returns no verified requested lane. Action: LEARN/diagnose; compare history before any Core change.
- **streamzo** — 🟡 PARTIAL_PROTECT: Movie is field/current green; TV wrong-content is reproduced by historical 5.21.36 bytes. Action: P0 TV identity in LEARN; freeze movie path.
- **uhdmovies** — 🔴 CURRENT_RED: Current published-byte guard returns no verified requested lane. Action: LEARN/diagnose; compare history before any Core change.

<!-- NON_REGRESSION_V3_START -->
## V3 non-regression ledger

This section is generated from four exact states: **5.21.0 → 5.21.16 → 5.21.36 → current**.
Historical evidence is never filled from a newer snapshot. A historical green that becomes unknown is explicit revalidation debt, not a silent pass.
Historical `supportedTypes` are transport/invocation compatibility only; only normalized or explicit canonical semantic declarations can create a semantic regression floor.

- Hard/contract regressions: **3** — `kehflix`, `movieshunt`, `purstream`
- Partial regressions: **1** — `streamzo`
- Revalidation debt: **6** — `allwish`, `anikototv`, `french-manga`, `playimdb`, `videasy`, `wookafr`
- Semantic/HLS contract regressions: **0** — none

### Guard semantics

- A provider that was green in an exact historical snapshot cannot become `unknown` without being put on the revalidation list.
- Every verified 5.21.36 lane becomes an explicit lane obligation until current/candidate proof supersedes it.
- Semantic capability and historical HLS losses are contract regressions, independently of transient network health.
- Historical bare `supportedTypes` never create a semantic floor because old releases mixed semantic types and transport aliases.
- The publication gate additionally unions the rolling accepted quick-yield baseline with these historical obligations, so future releases extend rather than reset the floor.
<!-- NON_REGRESSION_V3_END -->
