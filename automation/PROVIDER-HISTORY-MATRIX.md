# Provider history & live classification — 46 current / 50 historical archive

- Current manifest: **5.21.44**, providers: **46**.
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
| 4khdhub | movie, tv | catalogue-html | 🔴 runtime-error · 1.0.37 / `4efd8276edad3398` | 🟡 provider-unreachable/playable-host · 1.0.46 / `e70dc206194911cc` | 🔴 no-streams · 1.0.60 / `18a059512a0cbd33` | 🔴 published-red · 1.0.67 / `bccb95f756317003` | 0 | movie:0 tv:0 | guard movie:0 tv:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| allanime | anime | tmdb-direct-api | ⚪ provider-unreachable/inconclusive · 1.0.21 / `7947316d3cbed215` | ⚪ provider-unreachable/inconclusive · 1.0.23 / `7947316d3cbed215` | 🔴 no-streams · 1.0.30 / `4309c59ca0f5eaa8` | ⚪ current-unverified · 1.0.36 / `1dd67d123aa7627a` | 0 | anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| allwish | movie, tv | tmdb-direct-api | 🔴 runtime-error · 1.0.29 / `dd80ecdd13bc9c0f` | ⚪ provider-unreachable/inconclusive · 1.0.59 / `4840bc8a37b320d2` | 🟢 verified · 1.0.73 / `fae84d4c01870beb` | ⚪ current-untested · 1.0.79 / `80f02b511015e059` | 0 | movie:✓ tv:✓ | — | **HISTORICAL_GREEN_UNRETESTED** | Retest published bytes before touching route/data. |
| anikototv | anime, movie | tmdb-direct-api | 🟢 healthy · 1.0.56 / `08d395095a632a46` | 🟡 provider-unreachable/playable-host · 1.0.87 / `8aadc05c38391372` | 🔴 no-streams · 1.0.101 / `a7618bce82d44808` | ⚪ current-unverified · 1.0.107 / `f9c4a20c9c8b4648` | 0 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| anime-sama | anime | catalogue-episodes-js | 🔴 no-streams · 1.1.91 / `10e285fc12662f4d` | 🟡 provider-unreachable/playable-host · 1.1.122 / `c77fc61495dd1d49` | 🟡 partial · 1.1.140 / `24dc0903ba664a12` | 🟡 field-green/partial · 1.1.147 / `2ccfbe84da7613fb` | 0 | movie:0 anime:✓ | guard movie:0 anime:✓; field anime:✓ The Unwanted Undead Adventurer | **PARTIAL_PROTECT** | Freeze proven field lanes; LEARN only the bad lanes. |
| anime-ultime | anime, movie, tv | catalogue-form-html-embed | 🔴 no-streams · 0.0.28 / `bcfadc4b5a25574a` | ⚪ provider-unreachable/inconclusive · 0.0.58 / `9917da85493786d9` | 🔴 no-streams · 0.0.72 / `a97f953068636cc7` | ⚪ current-unverified · 0.0.78 / `8287634dd2dac8ae` | 0 | movie:0 tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animekai | anime | catalogue-html-embed | 🔴 no-streams · 1.0.28 / `a240cb19bce3a1ec` | ⚪ provider-unreachable/inconclusive · 1.0.59 / `f36ee061425c160d` | 🔴 no-streams · 1.0.78 / `29d0be2d7a992800` | ⚪ current-unverified · 1.0.84 / `42a6b781064fd93a` | 0 | anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animesalt | anime, movie, tv | catalogue-html-embed | 🔴 no-streams · 1.0.25 / `412e95313f655028` | ⚪ provider-unreachable/inconclusive · 1.0.32 / `4bee389bf085824a` | 🔴 no-streams · 1.0.46 / `f89d520cc66a908e` | ⚪ current-unverified · 1.0.52 / `942540f74f790b2c` | 0 | movie:0 tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animesama-co | movie, anime | catalogue-form-html-embed | 🔴 no-streams · 1.0.37 / `21c48b781f50cc44` | 🟡 provider-unreachable/playable-host · 1.0.56 / `767e940fab243e49` | 🔴 no-streams · 1.0.74 / `f72d5dd0221bdd2b` | 🔴 published-red · 1.0.81 / `a8ebcb2e301ed7f0` | 0 | movie:0 anime:0 | guard movie:0 anime:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| animesultra | movie, anime | dle-full-story | 🟡 blocked · 1.0.53 / `afc39c0d373675e5` | ⚪ provider-unreachable/inconclusive · 1.0.61 / `5d47d365269607fd` | 🔴 no-streams · 1.0.79 / `1ec689e62432d1a4` | ⚪ current-unverified · 1.0.85 / `c580e4ec6756bbc1` | 0 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animetsu | anime | catalogue-html-embed | 🔴 no-streams · 1.0.18 / `a1feac6991df10db` | ⚪ provider-unreachable/inconclusive · 1.0.24 / `362792f44aea9e97` | 🔴 no-streams · 1.0.38 / `6bb397e9635523e4` | ⚪ current-unverified · 1.0.45 / `8bc474f161c3b75f` | 0 | anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animevost-fr | anime, tv | catalogue-html-embed | ⚪ — | ⚪ provider-unreachable/inconclusive · 0.0.25 / `644a80e107ed66cc` | 🔴 no-streams · 0.0.39 / `80fa3a00000fc600` | ⚪ current-unverified · 0.0.45 / `f62bf49abedfb5ed` | 0 | tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| animevostfr | movie, anime | wordpress-search-episode | 🔴 no-streams · 1.1.74 / `493f59d8056b0179` | 🟡 provider-unreachable/playable-host · 1.1.85 / `67e363cfbe37ba09` | 🔴 no-streams · 1.1.103 / `666957ed184dffbd` | 🟡 candidate-green · 1.1.109 / `e385662e55991595` | 0 | movie:0 anime:0 | — | **CANDIDATE_GREEN** | Keep candidate; A/B against published bytes before promotion. |
| castle | movie, tv | catalogue-json-html-detail | 🟢 healthy · 2.0.35 / `defbe2701a5eb904` | 🔴 unavailable · 2.0.65 / `e588cade899cccbf` | 🟢 verified · 2.0.79 / `f9f1396b0939f955` | 🟢 field-verified · 2.0.85 / `da2d65fcf1685488` | 0 | movie:✓ tv:✓ | field movie:✓ Interstellar; tv:✓ House of the Dragon S1E1 | **PROTECT** | Immutable live baseline; A/B required before replacement. |
| coflix | movie, tv, anime | catalogue-html | 🔴 no-streams · 1.0.48 / `d6d16a8e29693c08` | ⚪ provider-unreachable/inconclusive · 1.0.60 / `9b13b0c422060699` | 🔴 no-streams · 1.0.74 / `2a490577b4b8277f` | ⚪ current-unverified · 1.0.81 / `f6a91b480317d5c3` | 0 | movie:0 tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| desiflix | movie, tv | stremio-json | 🟡 provider-unreachable/playable-host · 1.0.34 / `6b9f90ca348aa353` | 🟡 provider-unreachable/playable-host · 1.0.41 / `5cb266958e8b43de` | 🔴 no-streams · 1.0.64 / `22100513099b297e` | 🟡 field-green/partial · 1.0.71 / `2346b740e879d126` | 0 | movie:0 tv:0 | guard movie:⚠ tv:✓; field tv:✓ House of the Dragon S1E1 | **PARTIAL_PROTECT** | Freeze proven field lanes; LEARN only the bad lanes. |
| flemmix | movie, tv | catalogue-html-embed | 🔴 runtime-error · 1.0.54 / `dedb61d806c7c1d6` | 🔴 no-streams · 1.0.64 / `18ea87541317477b` | 🔴 no-streams · 1.0.79 / `653c33fa401a00d2` | 🔴 published-red · 1.0.86 / `bf6d371163f9509b` | 0 | movie:0 tv:0 | guard movie:0 tv:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| french-manga | movie, anime | catalogue-html-embed | 🟢 healthy · 1.0.49 / `cbb3b26d43fea959` | 🟡 provider-unreachable/playable-host · 1.0.83 / `02c60e53f47b6927` | 🔴 no-streams · 1.0.101 / `21ccc21b1cd5e0fa` | 🟡 candidate-green · 1.0.107 / `b96561f6331fd81f` | 0 | movie:0 anime:0 | — | **CANDIDATE_GREEN** | Keep candidate; A/B against published bytes before promotion. |
| fullanime | anime, tv | wordpress-search-episode | ⚪ — | ⚪ provider-unreachable/inconclusive · 0.0.25 / `17d89747ed077f44` | 🔴 no-streams · 0.0.39 / `c7b21640de1416af` | ⚪ current-unverified · 0.0.45 / `09cc2baa8f3302f0` | 0 | tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| hindmoviez | movie, tv | catalogue-form-html | 🟡 degraded · 1.0.34 / `a2fad478d23b3c67` | 🟡 degraded · 1.0.56 / `2afd92f17104b65c` | 🟡 partial · 1.0.70 / `3eb339d4e0b0bf13` | 🟡 published-partial · 1.0.76 / `216f69b0d25ecf2f` | 0 | movie:✓ tv:0 | guard movie:✓ tv:0 | **PARTIAL** | Preserve green lanes; LEARN failing lanes. |
| kehflix ⚠️ | movie, tv, anime | signed-player-api | ⚪ — | ⚪ provider-unreachable/inconclusive · 1.0.17 / `bfdd46578802aeee` | 🟢 verified · 1.0.51 / `064f32ab58f1fbf2` | 🔴 published-red · 1.0.58 / `9115853eff9c64a5` | 0 | movie:✓ tv:✓ anime:✓ | guard movie:0 tv:0 anime:0 | **UPSTREAM_DRIFT** | P1 LEARN/upstream refresh; do not rewrite Core as a fake regression fix. |
| kurage | anime | catalogue-html | ⚪ provider-unreachable/inconclusive · 1.0.27 / `b5240f665eb9c297` | ⚪ provider-unreachable/inconclusive · 1.0.36 / `6f2d4fa552dfc8ee` | 🔴 no-streams · 1.0.55 / `9ae58da956332c05` | ⚪ current-unverified · 1.0.61 / `8c8b8bc023c67454` | 0 | anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| mallumv | movie | catalogue-html-embed | 🔴 no-streams · 1.0.33 / `b4938cac084eca0e` | 🔴 unavailable · 1.0.64 / `863118576415a522` | 🔴 no-streams · 1.0.77 / `4b24dd9528fa01a3` | ⚪ current-unverified · 1.0.83 / `d9628824c2e25b7b` | 0 | movie:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| moviebox | movie, tv | stremio-json | ⚪ provider-unreachable/inconclusive · 1.0.18 / `33507d0a8889b61b` | ⚪ provider-unreachable/inconclusive · 1.0.24 / `19a7b7bbaa035869` | 🔴 no-streams · 1.0.31 / `474398374977be95` | ⚪ current-unverified · 1.0.37 / `86e12a35b37a0a2b` | 0 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| movieshunt ⚠️ | movie | catalogue-html | 🟢 healthy · 1.0.36 / `3aa3c567b2a014d9` | 🟡 provider-unreachable/playable-host · 1.0.51 / `ff486b0ec23ca8fc` | 🔴 no-streams · 1.0.64 / `e58b409178412c6e` | 🔴 published-red · 1.0.71 / `8061282f37ee7064` | 0 | movie:0 | guard movie:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| moviesmod | movie, tv | catalogue-form-html | 🔴 runtime-error · 1.0.28 / `edad1a7b333e5109` | ⚪ provider-unreachable/inconclusive · 1.0.36 / `ee171333c7a3c3f6` | 🔴 no-streams · 1.0.50 / `64e71c321ffd0757` | ⚪ current-unverified · 1.0.56 / `2053eef179901ad1` | 0 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| mugiwarastream | anime | catalogue-json-html-detail | 🔴 no-streams · 1.0.60 / `7d28f3c2b7bc3578` | 🟡 provider-unreachable/playable-host · 1.0.71 / `7192e1a89082b113` | 🔴 no-streams · 1.0.89 / `d219aa0b1692c799` | ⚪ current-unverified · 1.0.95 / `d7c4903587c954a8` | 0 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| neko-sama | anime, tv | catalogue-html-embed | ⚪ — | 🟡 provider-unreachable/playable-host · 0.0.17 / `55c80ba9eebb7a65` | 🔴 no-streams · 0.0.31 / `44eb233db734113d` | ⚪ current-unverified · 0.0.37 / `85cec404ccf7c30c` | 0 | tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| papadustream | movie, tv, anime | catalogue-html-embed | 🔴 no-streams · 1.0.35 / `2d48289559aafe27` | 🟡 provider-unreachable/playable-host · 1.0.42 / `a26d6b94f047d941` | 🔴 no-streams · 1.0.56 / `6b1f7cfe1671a9db` | ⚪ current-unverified · 1.0.62 / `59953ee2e97cc7e7` | 0 | movie:0 tv:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| persianstremio | movie, tv | stremio-json | 🟡 degraded · 1.4.36 / `7e31b6eedae47728` | 🟡 provider-unreachable/playable-host · 1.4.58 / `8c735f4b38215aea` | 🔴 no-streams · 1.4.72 / `5aad370c42f0bc9f` | 🟢 field-verified · 1.4.78 / `88642b021fa87956` | 0 | movie:0 tv:0 | guard movie:✓ tv:✓; field movie:✓ Interstellar; tv:✓ House of the Dragon S1E1 | **PROTECT** | Immutable live baseline; A/B required before replacement. |
| playimdb | movie, tv | tmdb-direct-api | 🟢 healthy · 2.0.38 / `4b88cfbf96960a88` | 🟡 provider-unreachable/playable-host · 2.0.70 / `e33f87f4a7e4f3d7` | 🔴 no-streams · 2.0.84 / `c7d08723d76d91ad` | ⚪ current-unverified · 2.0.90 / `488c8b3e1e9b0ea4` | 0 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| purstream ⚠️ | movie, tv | tmdb-direct-api | 🟢 healthy · 3.0.37 / `04678dffa0c674e9` | 🟡 provider-unreachable/playable-host · 3.0.59 / `0a77b4d442370ffd` | 🔴 no-streams · 3.0.73 / `27128980d2e66c10` | 🔴 published-red · 3.0.79 / `521ecff31aa05049` | 0 | movie:0 tv:0 | guard movie:0 tv:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| sekai | movie, anime | slug-saga-inline-media | ⚪ provider-unreachable/inconclusive · 1.0.48 / `7947316d3cbed215` | ⚪ provider-unreachable/inconclusive · 1.0.50 / `7947316d3cbed215` | 🔴 no-streams · 1.0.68 / `cbb4ec48dfa2c28d` | ⚪ current-unverified · 1.0.74 / `0a8028a0ae59a465` | 0 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| showbox | movie, tv | catalogue-html | 🔴 runtime-error · 1.0.27 / `c450d3154b1b69b9` | ⚪ provider-unreachable/inconclusive · 1.0.57 / `b4aee24095349027` | 🔴 no-streams · 1.0.71 / `d6f66e7e18942c9b` | ⚪ current-unverified · 1.0.77 / `2269f45264780f55` | 0 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| streamzo | movie, tv, anime | catalogue-html | 🟢 healthy · 1.0.62 / `0e0695a6398a6732` | 🟡 provider-unreachable/playable-host · 1.0.75 / `664cd45915ac001c` | 🟡 partial · 1.0.89 / `3ab1767966d7a1bc` | 🟡 field-green/partial · 1.0.95 / `39dcec5295f43021` | 0 | movie:✓ tv:⚠ anime:0 | guard movie:✓ tv:⚠ anime:0; field movie:✓ Interstellar | **PARTIAL_PROTECT** | P0 TV identity in LEARN; freeze movie path. |
| uhdmovies | movie, tv | catalogue-form-html | 🔴 no-streams · 1.0.17 / `faafa6b844017040` | ⚪ provider-unreachable/inconclusive · 1.0.49 / `41b2867bcc664c93` | 🔴 no-streams · 1.0.63 / `e6f0cc34b5ce7e9e` | 🔴 published-red · 1.0.69 / `cb515ee698b61785` | 0 | movie:0 tv:0 | guard movie:0 tv:0 | **CURRENT_RED** | LEARN/diagnose; compare history before any Core change. |
| videasy | movie, tv | tmdb-direct-api | 🟢 healthy · 1.0.41 / `f9cb91b9df10ed43` | 🟡 provider-unreachable/playable-host · 1.0.71 / `51e53f85370dc234` | 🟡 partial · 1.0.85 / `5dc71b42b6b49e8a` | ⚪ current-untested · 1.0.91 / `83f952818016314a` | 0 | movie:⚠ tv:✓ | — | **HISTORICAL_GREEN_UNRETESTED** | Retest published bytes before touching route/data. |
| vidfast | movie, tv | catalogue-html-embed | 🟡 blocked · 1.0.21 / `3b6bb9c6bb0550a7` | 🟡 provider-unreachable/playable-host · 1.0.27 / `8c06edeea58a8ebb` | 🔴 no-streams · 1.0.41 / `ee6dbe52b16e6f16` | ⚪ current-unverified · 1.0.47 / `4b69155954623ee0` | 0 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| vidlove | movie, tv | tmdb-direct-api | 🟡 blocked · 1.0.30 / `f0abcd1a8ab6c822` | 🔴 no-streams · 1.0.60 / `efb1712141d044d6` | 🔴 no-streams · 1.0.74 / `849bb6600299c982` | ⚪ current-unverified · 1.0.80 / `ec83947d30449c77` | 0 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| vidrock | movie, tv | catalogue-html | 🔴 unavailable · 1.0.24 / `e4f457c7daea80f5` | ⚪ provider-unreachable/inconclusive · 1.0.55 / `8e310b567b0fe5a6` | 🔴 no-streams · 1.0.69 / `c8939c8fd386a8e5` | ⚪ current-unverified · 1.0.75 / `7800d7fdbe59194b` | 0 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| voiranime | movie, anime | wordpress-search-episode | 🔴 no-streams · 1.2.52 / `1aaecd3076ce5d80` | 🟡 provider-unreachable/playable-host · 1.2.69 / `9908ca75a64f9ab4` | 🔴 no-streams · 1.2.87 / `5d089315b3c068e4` | ⚪ current-unverified · 1.2.93 / `9a15ce3e55403114` | 0 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| voiranime-homes | anime, movie | catalogue-html-embed | 🔴 no-streams · 0.0.27 / `3bf64d238ad99eba` | 🟡 provider-unreachable/playable-host · 0.0.58 / `b40415f60370ad0b` | 🔴 no-streams · 0.0.72 / `b018e6aa40f1f817` | ⚪ current-unverified · 0.0.78 / `a9a9de806b75661b` | 0 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| voiranime-rip | movie, anime | catalogue-form-html-embed | 🔴 no-streams · 1.0.42 / `bfdd8bc581e9191d` | 🟡 provider-unreachable/playable-host · 1.0.61 / `4d13882f91995cea` | 🔴 no-streams · 1.0.79 / `f3d824fc948eed41` | ⚪ current-unverified · 1.0.85 / `c03288b4793683ac` | 0 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| vostfree | movie, anime | catalogue-html | 🟡 blocked · 1.1.70 / `1286c275654dac3a` | ⚪ provider-unreachable/inconclusive · 1.1.76 / `7a20c3198fde3b19` | 🔴 no-streams · 1.1.94 / `76c5fe1fbcad7173` | ⚪ current-unverified · 1.1.100 / `42837b52afcb2097` | 0 | movie:0 anime:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |
| wookafr | movie, tv | catalogue-html-embed | 🔴 no-streams · 1.0.42 / `06c24d8c26c50df0` | 🔴 unavailable · 1.0.50 / `73c72bc655edc9ea` | 🟢 verified · 1.0.64 / `3c1ac476d5c5e692` | ⚪ current-untested · 1.0.70 / `df1d9f74ad39a82e` | 0 | movie:✓ tv:✓ | — | **HISTORICAL_GREEN_UNRETESTED** | Retest published bytes before touching route/data. |
| yflix | movie, tv | catalogue-html-embed | 🔴 no-streams · 1.1.21 / `5bc4a93d15c1f685` | 🔴 no-streams · 1.1.27 / `f6ff420bc7d5882a` | 🔴 no-streams · 1.1.41 / `e76f97e3ced0e815` | ⚪ current-unverified · 1.1.47 / `b4b91d495b10eb3d` | 0 | movie:0 tv:0 | — | **UNVERIFIED** | Continue portfolio sweep; route/data debt goes to LEARN after bounded attempts. |

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
