# NiakVIO Brain — Learning Lab

Daily sandbox execution and sanitized cross-day memory. Nothing in this report publishes a provider or manifest to production automatically.

Generated: 2026-10-04T01:11:22.247Z

Learned skills observed: **4**
Negative-memory entries: **912**
Historical high/critical unresolved: **0**
Native repair-priority providers: **7**
Native reader failures: **2548**
Targeted learning Lab: **multi_provider** — kehflix / undefined

## Highest-priority proposals

### 1. native_reader_failure_class — critical

Failure class: `media_extraction_gap`
Official native readers observed 2378 media_extraction_gap failure(s). Prefer reader-causal repair before generic provider mutation.

Candidate composition: `capture-media-network → inspect-player-javascript`

### 2. native_reader_failure_class — critical

Failure class: `playback_timeout`
Official native readers observed 148 playback_timeout failure(s). Prefer reader-causal repair before generic provider mutation.

Candidate composition: `diagnose-native-reader-timeout`

### 3. native_reader_repeated_signature — critical

Provider: `hindmoviez`
Failure class: `playback_timeout`
The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.

### 4. native_reader_repeated_signature — critical

Provider: `hindmoviez`
Failure class: `media_extraction_gap`
The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.

### 5. native_reader_repeated_signature — critical

Provider: `coflix`
Failure class: `media_extraction_gap`
The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.

### 6. native_reader_repeated_signature — critical

Provider: `allwish`
Failure class: `media_extraction_gap`
The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.

### 7. native_reader_repeated_signature — critical

Provider: `kehflix`
Failure class: `media_extraction_gap`
The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.

### 8. native_reader_repeated_signature — critical

Provider: `uhdmovies`
Failure class: `media_extraction_gap`
The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.

### 9. native_reader_repeated_signature — critical

Provider: `animekai`
Failure class: `media_extraction_gap`
The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.

### 10. native_reader_provider_target — high

Provider: `hindmoviez`
Failure class: `playback_timeout`
Native player failure for this provider is causally classified as playback_timeout; retest the same provider/fixture/reader before broad repair.

### 11. native_reader_provider_target — high

Provider: `coflix`
Failure class: `media_extraction_gap`
Native player failure for this provider is causally classified as media_extraction_gap; retest the same provider/fixture/reader before broad repair.

### 12. native_reader_provider_target — high

Provider: `allwish`
Failure class: `media_extraction_gap`
Native player failure for this provider is causally classified as media_extraction_gap; retest the same provider/fixture/reader before broad repair.

### 13. native_reader_provider_target — high

Provider: `kehflix`
Failure class: `media_extraction_gap`
Native player failure for this provider is causally classified as media_extraction_gap; retest the same provider/fixture/reader before broad repair.

### 14. native_reader_provider_target — high

Provider: `uhdmovies`
Failure class: `media_extraction_gap`
Native player failure for this provider is causally classified as media_extraction_gap; retest the same provider/fixture/reader before broad repair.

### 15. native_reader_provider_target — high

Provider: `vidlove`
Failure class: `media_extraction_gap`
Native player failure for this provider is causally classified as media_extraction_gap; retest the same provider/fixture/reader before broad repair.

### 16. native_reader_provider_target — high

Provider: `animekai`
Failure class: `media_extraction_gap`
Native player failure for this provider is causally classified as media_extraction_gap; retest the same provider/fixture/reader before broad repair.

### 17. hidden_failure_discovered_by_learning — high

Provider: `allwish`
Failure class: `targeted_lab_unresolved`
Learning found a stream/device failure that the Core sample may not expose; keep rotating fixtures, clients and stream positions.

### 18. hidden_failure_discovered_by_learning — high

Provider: `coflix`
Failure class: `targeted_lab_unresolved`
Learning found a stream/device failure that the Core sample may not expose; keep rotating fixtures, clients and stream positions.

### 19. hidden_failure_discovered_by_learning — high

Provider: `hindmoviez`
Failure class: `targeted_lab_unresolved`
Learning found a stream/device failure that the Core sample may not expose; keep rotating fixtures, clients and stream positions.

### 20. hidden_failure_discovered_by_learning — high

Provider: `kehflix`
Failure class: `targeted_lab_unresolved`
Learning found a stream/device failure that the Core sample may not expose; keep rotating fixtures, clients and stream positions.

### 21. hidden_failure_discovered_by_learning — high

Provider: `coflix`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 22. hidden_failure_discovered_by_learning — high

Provider: `hindmoviez`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 23. hidden_failure_discovered_by_learning — high

Provider: `kehflix`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 24. skill_candidate — medium

Failure class: `variant_coverage_gap`
Repeated unresolved failure class without a trusted reusable skill.

Candidate composition: `enumerate-announced-player-variants → remove-premature-variant-short-circuit`

### 25. avoid_failed_profile — medium

Provider: `coflix`
Failure class: `transport_blocked`
Profile: `adaptive_runtime_recovery`
The same sandbox profile failed 2 consecutive time(s) for this provider/signature. Collect different evidence or use another repair hypothesis before retrying it.

### 26. avoid_failed_profile — medium

Provider: `hindmoviez`
Failure class: `search_gap`
Profile: `adaptive_runtime_recovery`
The same sandbox profile failed 2 consecutive time(s) for this provider/signature. Collect different evidence or use another repair hypothesis before retrying it.

### 27. avoid_failed_profile — medium

Provider: `vidlove`
Failure class: `transport_blocked`
Profile: `adaptive_runtime_recovery`
The same sandbox profile failed 2 consecutive time(s) for this provider/signature. Collect different evidence or use another repair hypothesis before retrying it.

## Privacy

No raw URLs, tokens, header values, cookies, private notes or spreadsheet text are copied into persistent Brain learning state.
