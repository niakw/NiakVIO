<!-- NIAKVIO_MEMORY_PENDING_EMPTY -->

## 2026-09-12 — exact V34 manual-TV live matrix on rebuilt .44 candidate

- Work remains isolated to `fix/labs-5.21.44-20260912`; `main` remains untouched and no merge is authorized yet.
- Exact live workflow run **`34722151401`**, job **`103629901543`** completed successfully against the post-V34 rebuilt candidate. Matrix coverage was 24/24 result files with no infrastructure failures.
- Aggregate live result: **23 playable = 23 verified**, **0 semantic contradictions**, **0 returned 403 rows**.
- Interstellar / StreamZo now returns 1 playable + verified correct movie row and no contradiction; the prior wrong-documentary symptom is fixed by V34 route/media compatibility.
- Interstellar / VidRock now returns 2 playable + verified rows with no leaked 403 row; the old bad 403 stream is fail-closed while valid media remains.
- Ragna Crimson S1E4 / Anime-Sama now returns one valid ~720p row; the old invalid unknown row is no longer published.
- Hell Mode S2E10 / Mugiwara now returns **0** when the structured site data cannot prove S2E10, instead of eight wrong/default-season rows. Ragna S1E4 remains a valid Mugiwara structured match.
- Mushoku Tensei S3E11 / Anime-Sama now returns **2 playable + verified 1080p VOSTFR rows**, improving the previous no-provider/no-stream symptom.
- Remaining quality facts must stay evidence-driven: Purstream still resolves around 720p, Papadustream around 480p, and Castle may carry `1080P` presentation text while the verified media result remains classified 720p. Do not upgrade quality merely from labels when media proof is weaker.
- DesiFlix/PersianStreamio/MovieBox had runner-side network/HTTP failures in portions of this live pass; classify those with native device evidence rather than inventing provider fixes.
- House of the Dragon S1E2 / HindMoviez produced four HTTP-206 Matroska rows that the probe classified playable+verified, while the prior manual TV check reported them as apparently unplayable. This is a mandatory Native TV/player arbitration item for the five-Lab pass.
- The temporary live workflow was corrected before this run so it no longer writes stale provenance from the previous `5bc5...` rebuild; live evidence persistence is now based on inspected run results.
