# NiakVIO Brain — Learning Lab

Daily sandbox execution and sanitized cross-day memory. Nothing in this report publishes a provider or manifest to production automatically.

Generated: 2026-11-14T14:26:43.837Z

Learned skills observed: **45**
Negative-memory entries: **2040**
Historical high/critical unresolved: **0**
Native repair-priority providers: **2**
Native reader failures: **2588**
Targeted learning Lab: **multi_provider** — papadustream / undefined

## Highest-priority proposals

### 1. native_reader_failure_class — critical

Failure class: `playback_timeout`
Official native readers observed 148 playback_timeout failure(s). Prefer reader-causal repair before generic provider mutation.

Candidate composition: `diagnose-native-reader-timeout`

### 2. native_reader_repeated_signature — critical

Provider: `hindmoviez`
Failure class: `playback_timeout`
The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.

### 3. native_reader_repeated_signature — critical

Provider: `papadustream`
Failure class: `media_extraction_gap`
The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.

### 4. native_reader_repeated_signature — critical

Provider: `hindmoviez`
Failure class: `media_extraction_gap`
The same native-reader causal failure repeated. Stop generic retries; use the matching Brain v4 recipe and require a fresh reader proof before acceptance.

### 5. native_reader_provider_target — high

Provider: `hindmoviez`
Failure class: `playback_timeout`
Native player failure for this provider is causally classified as playback_timeout; retest the same provider/fixture/reader before broad repair.

### 6. native_reader_provider_target — high

Provider: `papadustream`
Failure class: `media_extraction_gap`
Native player failure for this provider is causally classified as media_extraction_gap; retest the same provider/fixture/reader before broad repair.

### 7. hidden_failure_discovered_by_learning — high

Provider: `hindmoviez`
Failure class: `targeted_lab_unresolved`
Learning found a stream/device failure that the Core sample may not expose; keep rotating fixtures, clients and stream positions.

### 8. hidden_failure_discovered_by_learning — high

Provider: `papadustream`
Failure class: `targeted_lab_unresolved`
Learning found a stream/device failure that the Core sample may not expose; keep rotating fixtures, clients and stream positions.

### 9. hidden_failure_discovered_by_learning — high

Provider: `coflix`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 10. hidden_failure_discovered_by_learning — high

Provider: `hindmoviez`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 11. hidden_failure_discovered_by_learning — high

Provider: `kehflix`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 12. hidden_failure_discovered_by_learning — high

Provider: `vidlove`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 13. hidden_failure_discovered_by_learning — high

Provider: `animevostfr`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 14. hidden_failure_discovered_by_learning — high

Provider: `voiranime-homes`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 15. hidden_failure_discovered_by_learning — high

Provider: `papadustream`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 16. hidden_failure_discovered_by_learning — high

Provider: `kurage`
Learning Lab found a stream/device failure that was not visible in the Core provider status.

Treat Core status as a hypothesis, retain this provider in the Learning queue, rotate fixture/device evidence and investigate the causal layer before proposing a production change.

### 17. skill_candidate — medium

Failure class: `variant_coverage_gap`
Repeated unresolved failure class without a trusted reusable skill.

Candidate composition: `enumerate-announced-player-variants → remove-premature-variant-short-circuit`

## Privacy

No raw URLs, tokens, header values, cookies, private notes or spreadsheet text are copied into persistent Brain learning state.
