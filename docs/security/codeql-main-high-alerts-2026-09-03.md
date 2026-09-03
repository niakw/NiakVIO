# CodeQL main — 25 High alerts: Bad HTML filtering regexp

Snapshot preserved from the user-provided GitHub Code Scanning export on **2026-09-03**.

- Branch in the original alert snapshot: `main`
- Tool: **CodeQL**
- Severity: **High**
- Rule: **Bad HTML filtering regexp**
- Alerts: **25** (`#158` through `#182`)
- Common historical location: generated `providers/*.js` bundles around line 877

> This file is evidence/audit input. It is not a runtime source of truth.
> Current Provider v3 security is gated by `tests/provider_html_filter_security_test.py`.
> The workbench fix replaces generic regex-based HTML stripping in ProviderBase and catalogue-alias Core with deterministic scanners; final closure still requires rematerializing all 96 providers and running security/CodeQL on the final SHA.

| Alert | Provider | Historical generated bundle |
|---:|---|---|
| [#182](https://github.com/niakw/NiakVIO/security/code-scanning/182) | `zinkmovies` | `providers/zinkmovies-0ea9fff3bce5e9d7.js` |
| [#181](https://github.com/niakw/NiakVIO/security/code-scanning/181) | `vixsrc` | `providers/vixsrc-962270ac55a114b1.js` |
| [#180](https://github.com/niakw/NiakVIO/security/code-scanning/180) | `vidnest` | `providers/vidnest-d17cae5c71b5f2ab.js` |
| [#179](https://github.com/niakw/NiakVIO/security/code-scanning/179) | `vidfast` | `providers/vidfast-09147b6367099072.js` |
| [#178](https://github.com/niakw/NiakVIO/security/code-scanning/178) | `topcartoons` | `providers/topcartoons-c2a2b67be969d41a.js` |
| [#177](https://github.com/niakw/NiakVIO/security/code-scanning/177) | `toflix` | `providers/toflix-c0c1de888f813cd5.js` |
| [#176](https://github.com/niakw/NiakVIO/security/code-scanning/176) | `purstream` | `providers/purstream-d5599514929b3e92.js` |
| [#175](https://github.com/niakw/NiakVIO/security/code-scanning/175) | `playimdb` | `providers/playimdb-549c49e54f8e6022.js` |
| [#174](https://github.com/niakw/NiakVIO/security/code-scanning/174) | `persianstremio` | `providers/persianstremio-b0ce48e322d034d4.js` |
| [#173](https://github.com/niakw/NiakVIO/security/code-scanning/173) | `netmirror` | `providers/netmirror-e709f9bae3a8d162.js` |
| [#172](https://github.com/niakw/NiakVIO/security/code-scanning/172) | `movieshunt` | `providers/movieshunt-4d04243dc6e3fda6.js` |
| [#171](https://github.com/niakw/NiakVIO/security/code-scanning/171) | `moviebox` | `providers/moviebox-95ad58252c18edfa.js` |
| [#170](https://github.com/niakw/NiakVIO/security/code-scanning/170) | `moonflix` | `providers/moonflix-2bd9fbdfc5b2dc03.js` |
| [#169](https://github.com/niakw/NiakVIO/security/code-scanning/169) | `kisskh` | `providers/kisskh-74b613dae92df7d0.js` |
| [#168](https://github.com/niakw/NiakVIO/security/code-scanning/168) | `hindmoviez` | `providers/hindmoviez-95363a5586a55e9c.js` |
| [#167](https://github.com/niakw/NiakVIO/security/code-scanning/167) | `frenchstream` | `providers/frenchstream-186f8537bd128448.js` |
| [#166](https://github.com/niakw/NiakVIO/security/code-scanning/166) | `einthusan` | `providers/einthusan-56e0e7070d356adb.js` |
| [#165](https://github.com/niakw/NiakVIO/security/code-scanning/165) | `dvdplay` | `providers/dvdplay-7d34f61f741bcdd2.js` |
| [#164](https://github.com/niakw/NiakVIO/security/code-scanning/164) | `ctgmovies` | `providers/ctgmovies-75523cf8168239d3.js` |
| [#163](https://github.com/niakw/NiakVIO/security/code-scanning/163) | `cinevibe` | `providers/cinevibe-f6b57b46eb03b5ca.js` |
| [#162](https://github.com/niakw/NiakVIO/security/code-scanning/162) | `cinemacity` | `providers/cinemacity-4454f5ff0525283e.js` |
| [#161](https://github.com/niakw/NiakVIO/security/code-scanning/161) | `castle` | `providers/castle-58499c3b61b3dcc6.js` |
| [#160](https://github.com/niakw/NiakVIO/security/code-scanning/160) | `animezey` | `providers/animezey-a7c6c65fca6f9d4f.js` |
| [#159](https://github.com/niakw/NiakVIO/security/code-scanning/159) | `animetsu` | `providers/animetsu-689350e5a129577d.js` |
| [#158](https://github.com/niakw/NiakVIO/security/code-scanning/158) | `allanime` | `providers/allanime-e182a7779fb22344.js` |

## Common root cause

The active workbench investigation traced these 25 alerts to the same generated ProviderBase pattern: generic HTML stripping via a regex of the form `/<[^>]+>/g`. A second similar pattern was also found in the catalogue-alias Core.

The workbench replaces those patterns with deterministic scanners:

- ProviderBase: `_htmlVisibleText()`
- Catalogue alias Core: `plainHtml()`

Permanent gates:

- `tests/provider_html_filter_security_test.py`
- manual Provider v3 reconstruction pre/post validation
- `CORE - Verify & Publish`
- `SEC - Final Gate`

## Closure criteria

These historical alerts are considered technically addressed for the next release only when all of the following are true on the same final workbench state:

1. 96/96 Provider v3 bundles are rematerialized from clean DATA + Lego;
2. the published 96/96 security test reports `bad_html_filter_regex=0`;
3. reverse reconstruction is 96/96 byte-identical;
4. CORE Quick is green on the rematerialized bytes;
5. CodeQL/security on the final branch/PR SHA does not recreate the High findings in release-reachable provider bundles.

