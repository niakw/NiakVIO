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

### 5.3 Positive program memory is durable

A strictly accepted provider-local runtime program is not merely a historical
counter. When a sandbox experiment satisfies strict playable improvement and its
accepted program compiles into Provider v3 DATA, its sanitized executable
program is persisted in `automation/brain-positive-program-memory.json`.

Required invariants:

- positive program memory is prior-only and never publication authority;
- a same-provider positive program may survive diagnostic failure-label drift;
- it may be replayed in canonical Repair for that **same provider** after the
  ordinary deterministic family is exhausted;
- same-provider replay is bounded by its aggregate positive-program fingerprint;
- a failed exact fingerprint is remembered and cannot loop forever;
- it may never jump to another provider as an untrusted peer transfer;
- every replay must still pass current-byte playback, identity and
  non-regression gates;
- evidence-only commits and orchestration cleanups must never reset validated
  positive memory to an older or empty state.

`scripts/recover_brain_positive_program_memory.py` is the fail-safe for accidental
state loss. It only reconstructs rows from historical Brain reports that:

1. were accepted as `strict_playable_stream_improvement`;
2. improved playable count;
3. were recorded as compiled by the accepted-program pipeline; and
4. still compile under the current Provider v3 compiler.

Recovery is idempotent and does **not** make the historical route/media current
proof. It merely restores the bounded candidate program so current bytes can
retest it.

`tests/brain_positive_program_repository_continuity_test.py` requires the
committed memory to already be a superset of every currently recoverable strict
historical positive. A silent `entries: []` regression is therefore a CI
failure.

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

### 6.1 FORCE executes current bytes, not repository migrations

Explicit FORCE is a provider-local current-byte recovery mode. It must **not**
replay historical repository upgrade/migration scripts before testing a provider.

Those migrations exist to evolve an older checkout toward the current
architecture. Re-running them inside FORCE is both unnecessary and unsafe: an
already-current Core/ProviderBase may legitimately no longer contain an old
anchor, and a global migration failure must never block a provider-local Force
candidate.

Therefore, in `run_provider_repair_pipeline_v6.py`:
- `mode=force` skips the historical migration list entirely;
- current source syntax/contracts are validated directly;
- provider-local Force candidates are isolated/rematerialized/retested;
- Core/architecture evolution remains outside Force.

### 6.1 Multiple advisor hypotheses

A provider may receive up to three distinct sanitized Brain-LLM advisor
experiment fingerprints for the same causal failure. They are **alternative
experiments**, never a combined patch.

Execution is strictly sequential and attributable:

~~~text
baseline + advisor A -> test
  failure -> record fingerprint A only
baseline + advisor B -> test
  failure -> record fingerprint B only
baseline + advisor C -> test
  success/failure -> attribute only to C
~~~

Fast Repair automatically expands its effective wave budget to the number of
distinct still-eligible advisor fingerprints in the selected portfolio, capped
at three. A provider must remain in the same Repair portfolio while an untried
advisor fingerprint exists; it may not be moved to Learning merely because the
first advisor experiment failed.

Only after all current advisor alternatives are failed, unavailable or
otherwise non-executable may that provider become Learning debt.

For a multi-provider portfolio, this happens concurrently by provider: the
14-provider cohort is not serialized into 14 independent runs. Each provider
advances through its own A/B/C sequence inside the same bounded portfolio run,
while validated reusable strategies may transfer across compatible provider
families in later waves.

## 7. Learning is slot-owned

Learning is **not** a fallback child workflow of Repair, FORCE or Autopilot.

The only allowed Learning execution is the independent Learning window:
- the scheduled/manual `.github/workflows/brain-learning-lab.yml` slot;
- its own bounded continuation mechanism for that same slot;
- the availability watchdog may only restore a missing scheduled Learning window.

Repair/FORCE/Fast Repair/Autopilot may consume previously persisted sanitized
Learning priors, but they only **record unresolved causal debt** for the next
Learning window. They must never dispatch `brain-learning-lab.yml` themselves.

The causal fingerprint/dispatch ledger remains useful to the Learning slot for
deduplication:

~~~text
same provider
+ same causal signature
+ same strategy/profile/generation
+ same LLM experiment fingerprint
= same Learning debt fingerprint
= do not spend the Learning slot on the same method again
~~~

This separation is deliberate:
- production time stays FORCE/Repair-owned;
- a failed 14-provider cohort cannot silently consume the Learning budget;
- Learning remains a distinct architecture/evidence phase;
- FORCE can keep iterating through current executable mutations and deterministic
  alternatives without changing execution mode.

A changed signature, method, generation or LLM experiment may create new Learning
debt, but that debt waits for the next dedicated Learning slot.

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

Explicit FORCE is also **single-run bounded**:
- FORCE never self-dispatches another FORCE run;
- unvisited providers are persisted as unresolved evidence;
- a new FORCE run requires a materially changed executable method, mutation set,
  provider bytes, or explicit operator trigger;
- the Repair/FORCE workflow has no schedule. Scheduled Learning belongs only to
  the dedicated Learning workflow.

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
- broad portfolio expansion occurs only after representative family proof;
- durable positive-program memory contains every strict historical positive that
  the current compiler can still recover;
- an exhausted same-provider Repair can replay an exact positive-program
  fingerprint without routing that replay through Learning first.

Until those runtime proofs exist, code-level architecture may be complete while provider repair remains **not yet fully validated**.

## FORCE ownership versus Learning slot

`mode=force` is the operator-owned recovery lane for providers that remain unresolved after ordinary Repair. Its contract is deliberately different from Learning:

- FORCE first evaluates current sanitized Brain-LLM provider-local mutations in isolated sandboxes.
- A mutation may be applied automatically only after current-byte improvement, identity/playback validation and the normal non-regression/publication gates.
- A FORCE execution must not dispatch `brain-learning-lab.yml` for its unresolved cohort. The unresolved debt may be persisted for later analysis, but ownership of the current execution remains FORCE.
- If a bounded FORCE run must resume because providers were not visited, the continuation remains `mode=force`.
- Learning remains an independent scheduled/manual research slot. It may consume persisted debt, evolve hypotheses and open reviewable PRs, but it does not directly apply provider fixes to production.

This separation prevents a FORCE request from silently degrading into proposal-only Learning while preserving Learning as the long-horizon hypothesis/evolution lane.



## Local FORCE experiment farm

For large unresolved cohorts, GitHub Actions is the **final proof/publication lane**, not the high-volume hypothesis generator.

`scripts/local/run_force_experiment_farm.py` provides a resumable local sandbox:
- default scope = current census `repairQueue`;
- existing Brain-LLM guidance is tried first when available;
- additional deterministic experiments are generated and deduplicated by fingerprint;
- previously executed negative fingerprints are skipped;
- Quick screens every hypothesis;
- only Quick improvements receive a fresh-from-current-bytes Deep retest;
- each provider runs in its own detached worktree;
- default parallelism is 2 providers and can be raised explicitly;
- a Deep winner stops further experiments for that provider by default;
- `STATE.json` allows restart/resume without repeating completed fingerprints;
- `WINNING_GUIDANCE.json` contains only non-authoritative winning advisor rows;
- the farm never pushes, dispatches GitHub workflows, publishes provider bytes, or enters the Learning planner mode.

Typical current-cohort run:

~~~bash
python3 scripts/local/run_force_experiment_farm.py \
  --variants-per-provider 24 \
  --workers 2 \
  --deep-rounds 3
~~~

For a focused provider:

~~~bash
python3 scripts/local/run_force_experiment_farm.py \
  --provider mallumv \
  --variants-per-provider 64 \
  --workers 1
~~~

The local winner is **evidence, not publication authority**. FORCE/GitHub must still replay the winning experiment against current bytes and pass playback, identity and non-regression gates before persistence.
