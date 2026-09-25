# NiakVIO — Brain Repair Architecture

> **Status:** architecture contract for the production Repair/Learning control plane.  
> **Scope:** provider diagnosis, isolated mutation, Learning escalation, same-byte validation and return to the canonical census.  
> **Non-goal:** this document does not freeze a provider count, a census result or a run status.

## 1. Objective

Brain Repair must scale from tens to hundreds of providers without turning each provider into a manual debugging session.

The system is successful only when it can:

- separate a provider defect from a harness, client, transport, WAF or domain-authority defect;
- choose a bounded repair hypothesis from current evidence and reusable experience;
- mutate provider-owned DATA/Bloc code only when evidence points to the provider layer;
- reject malformed or non-executable mutations before they contaminate canonical Repair;
- learn from real experiments without replaying the same failed method indefinitely;
- prove exact candidate bytes on current-byte execution before publication;
- preserve global Core contracts, including identity, media type, HLS integrity, presentation, branding, Stream Score and sanitizer;
- return every outcome to the census with an explicit evidence level.

The Brain is an **orchestrator of evidence and bounded experiments**, not an authority that can declare a provider healthy because a script completed.

## 2. Authority model

| Layer | Authority | May mutate provider bytes? |
| --- | --- | ---: |
| Current-byte census / Quick Yield | current published provider behavior | No |
| Route/Hub/Domain evidence | address and route observations | No, except dedicated domain transaction |
| Same-byte harness differential | execution-path ownership | No |
| Deterministic Repair planner | hypothesis selection | No |
| Brain Repair sandbox | provider-local experiment | Sandbox only |
| Brain LLM advisor | bounded mutation/strategy proposal | Isolated candidate only |
| Learning Lab | new strategy/evidence proposal | Proposal/sandbox only |
| Current-byte Retest | candidate acceptance evidence | No |
| Canonical publication/release gates | durable publication authority | Yes, only after required proof |

No LLM response, learned-memory row, route observation, browser reachability result or successful HTTP request is publication proof by itself.

## 3. Canonical execution graph

~~~text
CURRENT PUBLISHED BYTES
        |
        v
CURRENT-BYTE CENSUS / QUICK YIELD
        |
        +---- green FULL/PARTIAL ----------------------------> protect / no Repair
        |
        v
symptom + current evidence
        |
        v
BRAIN TARGET SELECTION
        |
        v
EXACT STAGING
(provider SHA pinned)
        |
        v
DEEP BASELINE
        |
        +---- same-byte Nuvio request > 0
        |     but Deep worker request == 0
        |                |
        |                v
        |       HARNESS DIFFERENTIAL
        |       - no provider mutation
        |       - no negative provider memory
        |       - no provider Learning debt
        |       - repair harness first
        |
        v
provider-owned request observed / causal provider evidence
        |
        v
DETERMINISTIC PLAN
        |
        +---- reusable known strategy ----> bounded sandbox experiment
        |
        +---- external Brain LLM strategy/mutation
        |            |
        |            v
        |    isolated structural + apply + execution validation
        |
        +---- no executable causal method
                     |
                     v
             LEARNING DISPATCH GATE
             - exact provider cohort
             - materially new fingerprint only
             - repeats suppressed
                     |
                     v
                 LEARNING
                     |
                     v
             proposal / new strategy
                     |
                     +------> returns to deterministic Repair
~~~

After any accepted provider-local candidate:

~~~text
accepted sandbox candidate
        -> compile durable provider DATA/Bloc representation
        -> rematerialize canonical Provider v3
        -> current-byte Retest
        -> identity + playback + preservation/non-regression gates
        -> census update
        -> publication/release transaction when applicable
~~~

A sandbox win that cannot be compiled or reproduced from current bytes is **not** a repair.

## 4. Harness parity is a prerequisite

Historically two execution paths could disagree:

- current-byte census: audit_provider_quick_yield.py → nuvio_tv_probe_tmdb_ci.cjs;
- Deep Repair: health_check.mjs → provider_worker.cjs.

This difference is now explicit architecture, not hidden implementation detail.

### 4.1 TMDB bootstrap contract

The Deep worker receives TMDB authority only through private bootstrap environment names.

Required lifecycle:

~~~text
health_check
  -> child env: NIAKVIO_TMDB_BOOTSTRAP_*
  -> provider_worker consumes and removes bootstrap env
  -> canonical TMDB globals exist only for module/Core initialization
  -> Core captures private closure/capability
  -> provider module load completes
  -> canonical TMDB globals are removed
  -> getStreams executes with no raw credential visible
~~~

The credential must never appear in persisted diagnostics or provider runtime output.

### 4.2 Same-byte differential contract

When Deep reports zero provider-owned requests, audit_brain_harness_differential.py may replay the **same fixture against the same staged SHA** through the production-like Nuvio probe.

Only this exact comparison is valid:

~~~text
same provider bytes
+ same fixture
+ Nuvio probe provider requests > 0
+ Deep worker provider requests == 0
= HARNESS DIFFERENTIAL
~~~

Consequences are mandatory:

- repairScope = harness-compatibility;
- provider mutation profiles become empty;
- no provider-negative experiment memory is written;
- provider is excluded from deferredLearningProviders;
- provider is removed from subsequent Repair waves until the harness is reconciled.

Transport/Tailscale/WAF analysis starts only after an actual provider-owned request exists. no_provider_request_observed is never a transport diagnosis by itself.

## 5. Provider Repair experiments

A provider enters mutation only after causal provider-layer evidence survives the harness boundary.

The planner may use:

- current request/response shape;
- current route/chain/terminal depth;
- capability strategy;
- sanitized historical successes/failures;
- positive program memory;
- current Learning priors;
- sanitized external Brain LLM guidance.

Historical memory is a **prior**, never acceptance authority.

### 5.1 Family-first scaling

Providers are grouped by causal family/signature for scheduling and transfer, for example:

- route/search gap;
- route-to-terminal gap;
- chain-terminal extraction gap;
- media/player extraction gap;
- candidate replay gap;
- provider transport gap;
- harness compatibility gap.

One representative case should validate a new generic strategy before expansion to the rest of its family. A full portfolio rerun is not a substitute for proving the strategy on one causal representative.

### 5.2 Negative experiment memory

A negative row is valid only when the intended experiment was actually executable or executed under the correct layer.

It must not be written for:

- same-byte harness differentials;
- a plan merely selected but never executable;
- provider-neutral staging drift;
- stale external LLM guidance;
- environment-only failures treated as provider defects.

Variant/generation memory exists to stop identical retries, not to make every future method impossible.

## 6. Brain LLM boundary

The LLM is useful for inventing a bounded method or mutation that deterministic Repair does not already know. It does not decide whether the repair is accepted.

For explicit Force:

1. LLM returns a bounded mutation/strategy, not a publication decision.
2. Mutation is checked against exact current source and intended provider scope.
3. Malformed, clipped, non-applicable or structurally invalid patches are rejected before canonical Repair.
4. Mutation is applied only in an isolated candidate workspace.
5. Provider bytes are rematerialized canonically.
6. Current-byte Retest and non-regression gates decide whether the candidate survives.

An empty Force artifact is not a successful Force repair.

## 7. Learning without loops

Learning is not the fallback for every failed Repair.

Automatic Repair → Learning is controlled by scripts/provider_learning_dispatch_gate.py and automation/provider-learning-dispatch-ledger.json.

A provider receives an automatic Learning dispatch only when there is a causal fingerprint containing both:

- a cause: failure class and/or signature;
- a method: profile, LLM strategy/profile or LLM experiment fingerprint.

The fingerprint intentionally excludes run IDs and timestamps.

~~~text
same provider
+ same causal signature
+ same strategy/profile/generation
+ same LLM experiment fingerprint
= same dispatch fingerprint
= DO NOT start Learning again
~~~

A changed signature, method, generation or LLM experiment may create a new fingerprint and therefore a new bounded Learning attempt.

The ledger retains the complete deduplicated per-provider history of dispatched fingerprints, not only the latest value. Therefore `A → B → A` remains suppressed: a previously dispatched causal method does not become eligible again merely because another method ran in between.

Missing causal fingerprint is fail-closed: no automatic Learning run.

Every automatic Learning launch receives an explicit `target_providers` cohort. Historical handoff debt may never silently expand the current cohort.

Canonical Repair, Fast Repair **and Brain Autopilot** must pass through the dispatch ledger. Autopilot may refresh transport/WAF evidence independently, but its provider/architecture Learning child run is launched only for a new execution-plan fingerprint. Fast Repair has one Learning path only: explicit targeted dispatch after the causal gate. It must not simultaneously arm a push trigger and launch an explicit run.

## 8. Domain Refresh is not Repair

Domain movement belongs to CORE - Domain Refresh, not Brain provider mutation.

direct_authority has two distinct semantics:

- **explicit_current**: strong refreshable current/LKG terminal. It protects against stale or ambiguous hub cards but may be replaced by a fresh authoritative primary/current/active declaration or deterministic official redirect.
- **operator_pin**: immutable manual terminal. Automatic Domain Refresh may not replace it.

This distinction prevents a manually observed current domain from becoming permanently frozen while retaining a true manual lock when one is required.

When a domain rotates, the domain transaction may update only address-owned DATA and connected domain derivatives. It must not invent a new route contract or modify unrelated Core/provider behavior.

## 9. Core preservation

A provider Repair is never allowed to publish a bundle that lost a common Core Bloc.

Canonical Core order:

~~~text
STREAM_FACTS
→ STREAM_IDENTITY
→ MEDIA_TYPE
→ STREAM_PRESENTATION
→ PROVIDER_BRANDING
→ SANITIZER
~~~

HLS Runtime Integrity and Stream Score remain separate common contracts integrated at their defined boundaries; provider-local repair must not duplicate or bypass them.

The public term is **Bloc**. Legacy compatibility field names such as provider_lego_scripts may remain in serialized DATA until a dedicated schema migration, but they are not architectural terminology.

## 10. Acceptance ladder

“Functional” is not a boolean emitted by one test. Evidence advances through this ladder:

1. provider bundle loaded;
2. capability/route recognized;
3. TMDB/media identity resolved when required;
4. provider-owned request observed;
5. backend/search/content request succeeded;
6. chain/terminal/player reached;
7. stream extracted;
8. stream structurally valid;
9. stream playback-verified;
10. work/year/season/episode identity verified;
11. language/quality/technical facts normalized;
12. badges/presentation/Stream Score correct;
13. Native client playback/UX evidence where required;
14. non-regression and release integrity preserved.

Statuses such as ROUTE PROVEN and CHAIN REACHED are useful progress evidence. They are not synonyms for playable provider.

## 11. Write boundaries

| Artifact | Repair | Force | Learning | Domain Refresh |
| --- | ---: | ---: | ---: | ---: |
| Provider DATA/Bloc candidate | Sandbox | Isolated candidate | Proposal/sandbox | Domain-owned fields only |
| Common Core | No direct write | No direct write | Proposal/PR only | No |
| Negative Repair memory | Valid executed provider experiment only | Valid isolated experiment only | Separate Learning memory | No |
| Learning dispatch ledger | After successful dispatch | After successful dispatch | Read/consume | No |
| Census | After canonical evidence | After canonical evidence | No direct healthy promotion | Domain metadata may be reprojected, not playback proof |
| main provider bytes | Gate-controlled only | Gate-controlled only | Never directly | Atomic domain transaction only |

## 12. Run discipline

Before any broad run:

1. confirm current main HEAD and active workflows;
2. verify no provider-input drift invalidates evidence;
3. verify relevant architecture tests are green;
4. select one representative provider per unresolved causal family;
5. run targeted evidence first;
6. inspect actual request/chain/stream result;
7. expand only after the generic fix is proven.

A long run that repeats the same fingerprint is a bug in orchestration, not “more confidence”.

## 13. Primary implementation files

Control plane:

- scripts/run_provider_brain_repair.py
- scripts/run_adaptive_deep_repair.py
- scripts/brain_repair_runtime.py
- scripts/provider_learning_dispatch_gate.py
- scripts/run_provider_fast_repair.py

Harness:

- scripts/health_check.mjs
- scripts/provider_worker.cjs
- scripts/nuvio_tv_probe_tmdb_ci.cjs
- scripts/audit_brain_harness_differential.py

Workflows:

- .github/workflows/provider-recognition-repair-v6.yml
- .github/workflows/provider-fast-repair.yml
- .github/workflows/brain-learning-lab.yml
- .github/workflows/domain-refresh.yml

Durable sanitized state:

- automation/brain-repair-memory.json
- automation/brain-positive-program-memory.json
- automation/provider-repair-learn-handoff-v1.json
- automation/provider-learning-dispatch-ledger.json
- automation/provider-census-status.json

## 14. Completion criteria for the repairer

The repairer is considered operationally validated only after all of the following are observed on current code:

- same-byte harness differential tests pass;
- Deep TMDB init-only bootstrap contract passes;
- repeated Learning fingerprint is suppressed;
- a genuinely new fingerprint is dispatched only to its exact provider cohort;
- at least one formerly false no_provider_request_observed representative reaches real provider-owned network observation in Deep;
- at least one provider-local candidate, when needed, survives sandbox → canonical materialization → current-byte Retest;
- no already-green provider regresses;
- census and durable memory reflect the proven result;
- broad portfolio expansion occurs only after representative family proof.

Until those runtime proofs exist, code-level architecture may be complete while provider repair remains **not yet fully validated**.
