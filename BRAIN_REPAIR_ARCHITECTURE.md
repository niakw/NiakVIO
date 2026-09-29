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

### 4.3 Interactive challenge evidence is not limited to HTTP errors

A provider/client transport gate may answer HTTP 200. The probe must therefore treat
high-confidence interactive challenge evidence as transport/WAF evidence even when
the response status is successful. This includes explicit Cloudflare Turnstile
wiring observed in bounded HTML or provider-loaded JavaScript (`cf-turnstile-response`
or the Cloudflare Turnstile client path). Bodies remain ephemeral and are never
persisted.

Causal precedence remains strict: a terminal hard network failure (exception or
HTTP >= 400) outranks an incidental earlier challenge, but a later harmless 200
asset/fallback request must not erase an already-observed interactive challenge.

Repair consequence: do not ask Provider Repair/Brain to fabricate challenge tokens
or mutate provider extraction code merely because the final media URL is absent.
Route the case through the existing WAF/browser/session qualification first; only a
reproducible provider-layer defect after that boundary is eligible for mutation.

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

### Targeted recovery evidence is an epoch snapshot, not a one-run scratch file

`automation/provider-targeted-regression-recovery-latest.json` is a cumulative
provider-evidence snapshot for one `sourceCensusRunId`. An explicit targeted
run updates only the providers it actually probes and retains untouched provider
rows from the same census epoch. The retained rows are evidence, not fresh proof;
their original observations are preserved byte-for-byte.

Evidence is never carried across a census boundary. When `sourceCensusRunId`
changes, targeted recovery starts a new snapshot instead of merging the previous
epoch. Sharded full-cohort runs remain independently merged from their shard
artifacts and do not inherit the repository snapshot into each shard.

This invariant prevents a one-provider diagnostic run from turning the other
unresolved providers into synthetic `not-probed` rows and forcing Brain to
rediscover evidence that already exists.

### Response-shape evidence

Targeted recovery may persist a bounded structural summary for provider responses.
It never persists response bodies, cookies, headers, query secrets or response
values. JSON evidence is limited to validated schema-key names, top-level type
and coarse array-size buckets. HTML/JavaScript evidence is limited to bounded
element/function counts and a closed marker vocabulary such as `player`,
`download`, `episode`, `hls-literal` or `turnstile`.

The purpose is causal diagnosis: distinguish “request reached a JSON API but the
expected `episode/sourceUrls` shape changed” from “HTML page contains no player”
without giving the Brain raw private content. NiakVIO sanitizes this summary before
persistence and Brain re-sanitizes it on ingestion.

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

## 6.2 Residential transport belongs to execution, not only diagnosis

When the integrated Repair WAF lane successfully activates a Tailscale residential
exit, that routing remains active through the **canonical provider FORCE/Repair
execution**. Qualifying a provider through the residential exit and then clearing
the exit before the real provider requests is a split-brain transport bug: WAF
evidence says the residential path is available while Deep Repair actually runs
from the GitHub-hosted address.

Required order:

~~~text
connect Tailscale -> select residential exit -> WAF/replay qualification
-> merge transport evidence -> canonical FORCE/Repair
-> clear residential exit -> final census merge
~~~

Cleanup is fail-safe (`always()`), but it must occur after canonical execution.


### 6.3 Brain-generated runtime Blocs

When the provider layer is causal and no existing runtime Bloc is sufficient, the
Brain may request a new bounded `provider_bloc` mutation. This is **not arbitrary
code generation**.

The model may supply only:

- a bounded snake_case family identifier;
- one stable request-local `window_id` selected from exact current-byte source windows;
- one exact local `find` snippet that occurs once inside that selected window;
- one bounded `replace` snippet.

The model is **not** responsible for repository-global text uniqueness. Brain-LLM
deterministically resolves the selected occurrence against the complete current
provider-owned source, minimizes unchanged copied context and expands exact
unchanged surrounding bytes only when global uniqueness requires it.

NiakVIO owns the implementation. `apply_brain_llm_force_mutations.py` validates
the current runtime/override fingerprint, rejects Core ownership markers,
placeholders and newly introduced process/eval/import capabilities, then renders a
trusted Python Bloc template. The model never chooses the repository path and
never emits Python.

Generated Bloc persistence is immutable/content-addressed:

~~~text
provider evidence
-> exact source windows with stable window_id
-> provider_bloc family + window-local find/replace
-> Brain structural anchor compilation
-> deterministic trusted renderer
-> scripts/provider_patches/brain_runtime_<family>_<fingerprint>_v1.py
-> register in canonical patch_scripts
-> isolated materialization
-> current-byte Retest + identity/playback + non-regression
-> publication only after the normal Force acceptance ladder
~~~

The managed ownership id is stable per family. If a later current-byte repair
evolves the same family, NiakVIO creates a new content-addressed file and swaps
provider registration to it; the prior file remains immutable in history. During
materialization the new version may modify only the existing family-owned
STARTFIX/CLOSEFIX body, preserving its original restore source. This makes
creation and evolution transactional without allowing the LLM to rewrite the
renderer or escape provider ownership.

Current provider bytes and the provider override are part of the signed mutation
context. Any drift invalidates the mutation before sandbox application. A
generated Bloc is still only a **candidate**: its existence, syntax or successful
materialization is never proof that a provider is repaired.
### 6.4 Brain synthesis owns structural targeting

The provider repair **intelligence boundary is asymmetric by design**:

- **NiakVIO-Brain-LLM owns synthesis**: causal interpretation, mutation-surface
  selection, structural target selection and conversion of the intended local
  code change into a concrete provider-local mutation;
- **NiakVIO owns execution and proof**: current bytes, immutable/generated Bloc
  materialization, sandbox execution, Deep comparison, playable-media proof,
  identity validation, current-byte retest, non-regression, census and
  publication.

A rejected LLM candidate is **not** a reason to teach NiakVIO a provider-specific
repair. If a candidate is ambiguous, partial, malformed, syntax-invalid,
non-causal or behaviorally neutral, the default ownership is Brain-LLM. NiakVIO
may gain only generic executor/validator capabilities needed to prove arbitrary
future candidates.

#### Structured-anchor contract

The LLM must not be responsible for inventing a repository-global unique text
anchor from raw source. That is a compiler concern.

The target architecture is:

~~~text
exact current provider-owned source
  -> Brain deterministic source windows / structural regions with stable ids
  -> LLM selects one region and expresses the smallest semantic local change
  -> Brain deterministically resolves that occurrence on full current bytes
  -> Brain minimizes unchanged prefix/suffix
  -> Brain expands exact surrounding context only as needed for uniqueness
  -> syntax / ownership / no-op / capability validation
  -> concrete bounded mutation
  -> NiakVIO isolated execution and proof
~~~

Required invariants:

1. source regions are exact current-byte slices and have stable ids inside one
   request;
2. the model identifies the region it used; it does not guess a global
   occurrence;
3. a snippet unique inside the selected region may be deterministically expanded
   with unchanged surrounding bytes until it is unique in the full source;
4. unchanged prefix/suffix emitted by the model is minimized before structural
   validation, so a local expression repair is not rejected merely because the
   model copied the beginning of an enclosing function;
5. if the selected snippet is still ambiguous inside its own region, cannot be
   made globally unique inside the bounded anchor budget, or would cross
   ownership boundaries, the Brain must abstain/retry — never let NiakVIO guess;
6. NiakVIO receives only the compiled concrete mutation and remains free to
   reject it through the normal proof ladder.

#### FULL OK reference library and novel mechanism rule

Brain-LLM may consult sanitized implementation patterns extracted from current
FULL OK providers and their validated Blocs/scripts. These references are
**optional prior art only**:

- retain transferable structure (session/fetch, player/iframe traversal, parsing,
  decoding, terminal media extraction, etc.);
- strip provider-specific addressing and identity (URLs, hosts, routes, tokens,
  provider literals);
- never grant proof authority to a reference merely because its source provider
  is FULL OK;
- allow the model to adapt one pattern, combine several, ignore every reference,
  or synthesize a **new independent provider-local Bloc/script**.

A new mechanism is not an exceptional fallback. It is a normal Brain output when
the current provider's evidence does not fit existing patterns. The constraint is
not 'use what already exists'; the constraint is 'stay provider-local, bounded,
structurally valid and prove the result in NiakVIO'.
#### Failure ownership rule

~~~text
bad reasoning / wrong target / bad anchor / malformed edit / no-op
    => Brain-LLM

missing generic mutation primitive / sandbox validator / proof capability
    => NiakVIO infrastructure

provider candidate runs but does not improve real behavior
    => negative execution evidence returned to Brain

candidate improves and passes all gates
    => NiakVIO may persist/publish
~~~

This rule is mandatory for future Repair work. It prevents repeated patches to
the execution repository from masking a weak generator and keeps the system
scalable when the provider population grows.

## 7. Learning is slot-owned

Normal Learning remains slot-owned and review-only. The explicit architecture
FORCE lane reuses the same sandbox workflow implementation, but it is a distinct
operator-owned execution mode: `architecture_force=true`,
`publish_proposal=false`.

The ordinary Learning window remains:
- the scheduled/manual `.github/workflows/brain-learning-lab.yml` slot;
- its own bounded continuation mechanism for that same slot;
- the availability watchdog may only restore a missing scheduled Learning window.

Repair/FORCE/Fast Repair/Autopilot may consume persisted sanitized Learning
priors. When current executable provider methods are exhausted, FORCE may hand
the exact unresolved cohort to the guarded architecture FORCE lane. That handoff
must never request a proposal PR and never grants provider publication authority.
Explicit FORCE Learning is concurrency-keyed by its exact target cohort: a newer
run may replace stale work for the same cohort, while independent cohorts in the
same 15-provider cycle must remain able to complete without cancelling each other.

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
| Common Core | No direct write | Guarded allowlisted architecture FORCE only | Proposal/PR only | No |
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
- A FORCE execution may dispatch only the explicit `architecture_force=true` lane for exact unresolved architecture debt, always with `publish_proposal=false`; this remains FORCE-owned, not normal proposal Learning.
- If a bounded FORCE run must resume because providers were not visited, the continuation remains FORCE-owned and preserves proposal suppression.
- Normal Learning remains an independent scheduled/manual research slot. It may consume persisted debt, evolve hypotheses and open reviewable PRs, but it does not directly apply provider fixes to production.

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


## Local FORCE evidence corpus

The local FORCE experiment farm is an evidence-generation lane, not a publication lane. Its aggregate results live under `automation/local-force-results/` and deliberately exclude raw provider responses, credentials, cookies, tokens, local filesystem paths and private conversation content.

The planner consumes persisted local FORCE candidate guidance only in Learning mode. Baseline-coincident local Deep candidates are marked ambiguous, confidence-capped and restricted to exact failure-class compatibility. They must be revalidated on current bytes before Repair can attribute causality.

Experiment scheduling is breadth-first by default: each provider receives a bounded batch before deeper variant exploration continues. This prevents early providers from monopolizing the experiment budget and makes the corpus representative enough to scale to hundreds of providers.

Authority remains: `local FORCE evidence -> Learning prior -> current-byte Repair/Deep/Retest -> production proof/persistence`.

## 2026-09-26 — Meta-learning and guarded architecture FORCE

The Brain no longer assumes that every future provider failure fits a fixed strategy list.

### Mandatory architecture layers

1. `causal_failure_taxonomy` — classify sanitized evidence into broad technical failure families.
2. `capability_gap_detector` — detect when the current provider/Core/Lab toolbox cannot discriminate or repair the observed case.
3. `meta_learning_gap_synthesis` — synthesize a genuinely new bounded strategy instead of recycling an exhausted profile.
4. `architecture_layer_synthesis` — decide whether the missing capability belongs to provider runtime, Core, harness/network, Learning, materialization/projection, client runtime, or a new layer.
5. `verification_contract_synthesis` — every new capability must carry causal evidence, identity/content safety, targeted proof and non-regression requirements.
6. `negative_memory_novelty_guard` — failed strategy/profile/fingerprint families cannot be silently relabelled as new work.
7. `force_architecture_promotion` — explicit FORCE may promote an executable architecture change only after allowlist validation, targeted tests and required CI.

`scripts/brain_meta_learning.py` is the provider-agnostic implementation. Known technical families include route/domain discovery, search/catalogue, session/WAF, network/TLS/DNS, API/schema, dynamic JS, player/embed, terminal media, token/crypto, identity, episodic mapping, pagination, rate/cache, runtime code, materialization/projection, stream metadata, media integrity and client/runtime divergence. Evidence outside this taxonomy is explicitly `unknown_new_failure`; it is not coerced into the closest known family.

Unknown failures can produce `novel_failure_gap_synthesis_v1`. If even the architectural layer is unknown, the Brain produces `novel_architecture_layer_synthesis_v1`.

### Explicit FORCE architecture lane

A FORCE Repair run that still has deferred architecture debt dispatches targeted Learning with `architecture_force=true`.

The Learning job reuses the already-pinned local Qwen runtime. `scripts/brain_architecture_force_materializer.py` accepts at most three bounded edits on allowlisted Brain/Core/Lab surfaces. It supports exact unique find/replace and isolated new Brain layer/test files. It rejects provider bundles, provider-disabled bytes, ProviderBase, manifests, provider overrides and provenance/publication surfaces.

A FORCE architecture run must produce a real executable diff. Proposal-only JSON/Markdown is not eligible for auto-promotion. The structural patch is exported as an artifact, replayed on the exact source checkout and re-tested. FORCE then stages only the generated-edit allowlist plus architecture metadata, rejects provider/publication boundaries, requires a stale-SHA lease guard, and pushes one commit directly to `main` without creating a PR or repair branch. The resulting main SHA must still pass Workflow Gate, Verify/Publish and non-regression; a failed gate is not a validated architecture repair.

Provider publication authority remains false throughout the architecture lane. Normal scheduled/manual Learning keeps its review-only PR behavior.

## Durable route evidence hygiene

Targeted recovery persists only the minimum route shape required by Brain Repair. Hosts, HTTP method/status and bounded response-shape metadata are retained, but path values are normalized before they enter repository evidence.

Numeric segments are represented as `{id}`. Long/high-entropy, encoded-object or token-like segments are represented as `{opaque}`. Query strings and response bodies are never part of this durable evidence surface.

This preserves the causal route family needed for clustering and repair planning without turning `automation/` into a store for transient credentials or opaque provider payloads. The redaction layer is evidence-only and cannot promote or repair a provider.

## GitHub FORCE convergence contract

GitHub execution must converge the requested provider cohort rather than merely execute one bounded slice.

1. `NiakVIO-Brain-LLM/main` is the code authority. The `niakvio-guidance` branch is a cache/evidence surface, never a prerequisite for checking out current Brain code.
2. Cached guidance is usable only when its embedded `brainLlmSha` equals the exact current Brain pin and its NiakVIO source passes the existing drift classifier.
3. Explicit architecture/FORCE guidance receives the structural generation budget supported by current Brain (768 tokens, 180 s model timeout, single worker). Routine Learning retains its smaller budget.
4. The canonical Recognition FORCE lane remains bounded and may stop with `unvisitedProviders`. Fleet convergence is currently provided by an explicit Fast Repair cohort covering the complete current repairQueue; stale Fast runs requeue on current `main`, and unresolved providers enter targeted Learning/architecture FORCE. Do not claim Recognition auto-resume until a YAML-safe, tested implementation exists.
5. Delegation never grants publication authority. Each accepted mutation still requires current-byte materialization, Deep/Retest, playable media, identity safety and relevant non-regression before persistence.

## Generated provider Bloc receiver contract

NiakVIO accepts Brain-generated `provider_bloc` replacements up to 1800 characters, matching the Brain's bounded complete-function invention surface. This does not grant publication authority.

Every generated Bloc still requires: exact provider-owned find bytes, unique current-byte occurrence, capability/placeholder checks, immutable generated patch materialization, baseline/candidate provider health comparison, current-byte Retest, playable stream improvement and identity safety before persistence.

## External FORCE partial-winner contract

An external Brain FORCE batch is a set of independent provider hypotheses, not an all-or-nothing transaction.

- The published Brain artifact may contain mutations for only a subset of the requested repair cohort; Brain abstention is a valid bounded outcome.
- NiakVIO fails closed if the artifact contains no requested executable candidate, is stale/inconsistent, or includes an unexpected provider.
- Present candidates are evaluated independently in isolated current-byte sandboxes.
- A rejected or absent candidate never blocks another provider's validated winner.
- With `requireExternalForceMutations=true`, unresolved providers do not fall through to canonical Repair in the same run. This preserves attribution to the Brain hypothesis.
- Only accepted winners are applied/materialized/retested, and any persisted winner explicitly triggers a fresh current-byte census.

Upstream Brain mutation-surface precedence is also causal: when a provider already owns a registered runtime resolver, that provider-specific runtime is attempted before a generic generated Bloc. NiakVIO still owns all proof and publication authority regardless of which surface generated the candidate.


## Orchestrator ownership boundary — mandatory

The repair orchestrator must **not hand-author provider runtime fixes** while validating Brain Repair.

- Brain/LLM owns provider-local mutation synthesis, including new provider functions, helpers, parsers, request logic and terminal extractors.
- NiakVIO owns evidence collection, mutation reception, exact-byte application in an isolated sandbox, current-byte Deep/Retest, playable-media and identity validation, non-regression, census and publication.
- Direct human/assistant edits to `scripts/provider_patches/*`, provider JS, provider-specific override recipes or provider-local runtime tests are not valid substitutes for a Brain-produced repair candidate.
- Infrastructure fixes are allowed only when they repair the repair system itself: harness, evidence freshness, routing, mutation receiver, sandbox, validation, pagination, timeouts, causal classification, publication guards or Core-wide behavior proven to be generic.
- If investigation reveals a plausible provider-local code change, it becomes **evidence/context for Brain**, not an orchestrator-applied provider patch.
- A provider may be called repaired only after a Brain-authored candidate survives the normal isolated current-byte proof chain.

This boundary exists specifically so NiakVIO validates an intelligent repair system rather than silently replacing it with manual provider maintenance.
## Compiler invariant: exact unit identity beats model wrapper identity

When compact FORCE selects a complete provider `function_unit`, the exact current-byte unit id owns the target identity. For a generated `provider_bloc`, a small model may return a single complete function wrapper with a nearby/wrong helper name; Brain may recover only its syntax-valid body and re-envelope it under the exact selected declaration. This normalization does not weaken authored `provider_patch` / `provider_js` signature guards: explicit async/name/parameter drift on authored surfaces remains invalid.

Structural prompt selection must respect its hard unit budget. On route/chain/media-extraction gaps it reserves causal graph capacity and follows direct calls plus named callback references (for example `.then(parser)` / `.map(normalize)`) to expose second-hop player/parser/terminal helpers. These are mutation-context rules only; NiakVIO isolated sandbox, playable proof, identity safety and non-regression remain the acceptance authority.
