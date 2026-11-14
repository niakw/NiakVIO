## 2026-11-14 — Routine architecture validation and France-only lifecycle authority

A successful Learning experiment always validates the generated Brain architecture proposal artifact. Routine Learning may materialize that proposal only inside the ephemeral validation workspace and run the architecture contracts; it gains no PR or production-write authority. Review publication remains gated by an explicit manual `publish_proposal=true` dispatch plus the repository allow variable. Direct `main` promotion remains exclusive to the existing `architecture_force=true` transaction and its separate proof/replay gates. This closes the previous gap where routine Learning could generate architecture proposals that were never exercised by the validation job.

Provider lifecycle authority is the current production union, not only `manifest.json`: Global rows plus strict catalog-owned `{general:false,vf:true}` France-only rows. Global persistence remains Global-only; exclusive French identities are updated through the catalog and VF projections. Static knowledge and materialization ledgers must match the union. A duplicate identity across Global and France-only fails closed, and no lifecycle operation grants provider activation or playback authority.

## 2026-11-14 — Lifecycle precedence and exact targeted Learning dispatch

Census lifecycle authority outranks retained variant/completeness observations. The batch planner may retain historical evidence separately but never admit a provider marked DISABLED or listed in lifecycleDisabledQueue into automatic execution. The causal router independently denies stale groups violating this rule. Targeted Learning reconstructs the batch plan from its exact checked-out source, checks both census run ID and trigger SHA, and carries the normalized cohort to subsequent phases. Routine multi-target dispatches may drop only known lifecycle-disabled identities, with explicit diagnostics; unknown/out-of-scope targets, empty filtered cohorts, and explicitly disabled FORCE targets fail closed. No scheduling result grants activation or playback authority.

## 2026-10-11 — Negative-memory capacity and provider-fair Learning retention at 800 hubs

The negative-experiment registry is an authoritative executed-evidence ledger, not an endless retry counter. Live evidence showed its 1000-row cap saturated across 20 providers; a resolved FULL provider still consumed >100 rows while underrepresented repair targets retained only a few. Both production Repair and isolated Learning **must read the same bounded** `production.negativeExperimentMemory.maxEntries` budget (currently 16,000; upper safety cap 20,000) and perform provider-fair overflow selection **after** combining all relevant executed, fingerprinted evidence. Do not pre-truncate a newly merged Learning ledger by input order or simply keep the latest 1,000 rows. Keep the existing key (provider, version, failure, signature, profile, program/implementation/LLM fingerprints and experiment variant/generation) and exact executionObserved flag; preserve positive program memory separately.

`scripts/brain_negative_memory_retention.py` selects at least 12 per represented provider before using remaining capacity for the globally highest failed fingerprints. `scripts/brain_repair_runtime.py::repair_memory` and `scripts/run_brain_learning_queue.py::merge_phase_learning_state` / `merge_wave_experiment_entries` now share this overflow rule. Regression tests demonstrate a new provider survives a saturated hot-provider history and that 800 × 20 unique signatures fit. Memory scope is bounded and private; no direct provider mutation/publication is authorized. A green memory test is **not** a playable-media or provider repair proof. Later acceptance still requires Qwen-generated causal edit → schema/byte compilation → actual applied provider/manifest bytes → identity-correct terminal playback → nonregression → persisted experience. The 16-provider queue stays open until verified.

## 2026-10-10 — Self-architecture FORCE contract inventory and full-cohort Brain retention

The generated Brain architecture can add executable strategy Lego at runtime. The synthetic transport exhaustion test must consequently consume the planner's exact `postExhaustionCandidateProfiles` inventory, reject repeated/unregistered profiles and allow at most `inventory.length + 1` replans to demonstrate convergence. A historical fixed 20-round bound caused FORCE `38066889059` to reject an otherwise structurally valid materialized strategy and spend extra 7B calls on futile test repair. Regression `68cea095` passed exact CORE Gate `38083389493`; it restores a **test invariant**, not provider-playback proof.

Private guidance has two independent cohort-preservation gates: `--stop-after-first-mutation` must be absent from full-cohort pages, and the deterministic FORCE preflight must compare `providerCount` to **actual requested page size**, never generated JSONL row count. A single generated candidate for a nine-provider page is not comprehensive coverage. Source-pinned guidance publication can tolerate strictly documentation-only Brain/main drift while rejecting any source/config/workflow/test drift; this preserves expensive negative observations but grants no publication or playback authority. Invalid `unit_id` in a Qwen edit now receives exact-current-`editable_units` feedback. All provider acceptance gates (model generation, compilation, source/manifest materialization, executed current bytes, identity and terminal playback, nonregression, persistence) are unchanged.

## 2026-10-10 — Fingerprinted LLM guidance after exhausted Learning (Brain-only)

Observed canonical Fast Repair `38064430286` on older SHA: 11 selected, zero accepted or compiled programs, with 9/11 plans lacking an executable probe (all 11 `llmAdvisorApplied=false`). The Learning planner had a categorical branch `(!experimentExhausted || !learningMode)` that suppressed ordinary Brain-LLM guidance precisely after Learning-generation exhaustion. The Brain's existing `llmAdvisorStrategyHint` already filters failed exact experiment fingerprints, enforces causal/provider identity and bounds a profile to three executed hypotheses; the blanket Learning exclusion discarded this safety-aware selector.

The executor selector now permits a **fingerprinted, genuinely untried** LLM proposal after generation exhaustion **only if no executable evolved strategy is already selected**. It rejects non-fingerprinted exhausted Learning advice, retained failed fingerprints, and exhausted executor families; accepted advice remains prior-only and is subject to real compilation, current-byte rematerialization, identity, playback and non-regression gates. Do not confuse this planner repair with an accepted provider program. The public Brain-LLM guidance branch previously covered 11/17 requested providers, and 7 of its provider/profile groups already have >=3 executed fingerprints in current memory; those need a genuinely new executable family through FORCE rather than repeated advice.

Real planner regression `tests/brain_exhausted_llm_novelty_test.py` replays fully exhausted installed graph families and verifies novel/failed/unfingerprinted/advisor-vs-evolved precedence. CORE Workflow Gate `38066575038` SUCCESS on exact SHA `0478d600`; job logs contain `Exhausted Learning LLM novelty/negative-memory replay passed`. Provider Non-Regression Gate `38066541768` SUCCESS on `58d5e1b8` (earlier SHA). Neither test claims terminal provider playback. Scope: Brain planning/orchestration; no manual provider changes.

## 2026-10-10 — Exact execution-context preflight before FORCE model generation

A Brain FORCE context selector must bind exact `new_strategy_id` guard lines, not substring-similar identifiers like `route_transition_graph_v1` and `route_transition_graph_v10`. Evolution prefers the **exhausted parent**; inspection prefers the named target. A unique exact executable guard is chosen deterministically, otherwise fuzzy context is bounded fallback only. Before any expensive model call for a new executable profile, run current Brain architecture contracts on the unmodified checkout. If the baseline fails, flag owner `baseline-brain-contract` and stop; Qwen must never be asked to repair a stale test assertion by mutating strategy code. A passing contract is necessary but never a substitute for source byte application, identity-matched terminal playback and non-regression. For a large provider cohort, iterate by causal failure family and preserve failures/successes with executable fingerprints; don't count a `vN` generation as a repaired provider.

## 2026-10-10 — GitHub Actions run-block size contract

Recognition/Repair workflow shell blocks must remain below GitHub's **21,000-character hard cap per `run` step**, with project budget at 20,500. The 2026-10-10 FORCE promotion run `38017039516` failed to dispatch provider replay after main promotion because a V6 evidence-persistence edit pushed the long `Persist Repair census state` step over that cap. Preserve long-lived behavior in versioned, executable and independently tested Brain scripts; keep only short invocation/ownership gates in YAML, and unit-test the maximum size. Invalid workflow dispatch is an infrastructure failure, never a provider repair failure.

## 2026-10-10 — Evidence-only retry for racing Repair producers

A Repair run that has already executed provider/runtime tests may lose a race at the final `main` push. The safe convergence rule is **not** to rebase stale published provider or census output without fresh execution. On a rejected evidence-only push, reset to latest main and persist only the run-unique Brain experiment report plus a non-authoritative provenance record (`publicationAllowed=false`, `currentBytePlaybackAuthority=false`, tested SHA retained), with at most three bounded attempts. An accepted provider candidate is never carried through this path. The next learning cycle can use the negative report as a prior, but FULL remains gated by new applied-byte playback proof.

## 2026-10-10 — Generated profile regression contracts and loop economics

Contract tests and architecture-deferred plans must be **data-driven from the Brain's actually installed strategy registry**; generated `terminal_transition_graph_vN` siblings are valid when registered and compiled. Each new sibling is replayed before a later fallback, and its failure must be execution-observed. Never hard-code an assumption that a given vN does not exist.

Autopilot/Fast Repair must distinguish `main` changes that can alter executed behavior (Brain source, provider bytes, strategy registries, negative/positive memory and semantic repairQueue) from pure metadata/census-history commits. When a stale Fast run accepted **zero** candidates, had already handed unresolved providers to Learning, and the remote-main change has **no executable, causal input or semantic census drift**, do not automatically replay the identical Fast cohort. Newly generated strategies and updated evidence still authorize ordinary fresh Repair. No status gains publication authority from this scheduling decision.

## 2026-10-10 — Strict laboratory playback versus durable accepted repair

A playable/identity-correct stream observed in the sandbox is **evidence** but not, by itself, a new repair. To become an executable candidate, a Brain-authored repair must first be accepted, compiled into persistent provider-owned DATA, and rematerialized on those exact bytes; it must then pass independent current-byte replay and non-regression. A healthy fixture with **zero accepted compiled repair program** must not be rematerialized from unchanged published bytes or reported as newly fixed. Route that positive laboratory observation to Brain Learning as an oracle for an actual reusable repair, without promotion authority. This is a global Repair pipeline contract, not a provider-specific exception.

## 2026-10-10 — Full-cohort executable replay before duplicate FORCE

Registered executable Repair profiles are capability assets. When `terminal_transition_graph_v2` is already installed, the planner must replay v2 with current-byte semantics and record its true executed outcome before another generated generation. Neither a stale regression test nor a single-provider FORCE should suppress processing of all 17 non-FULL providers. The two general paths — bounded Fast Brain and adaptive Learning — take exactly the census repairQueue, grouped by candidate replay, terminal extraction, regression, and network/transport evidence. Existing playable providers remain protected. A laboratory success is candidate evidence only, and WAF/network errors are classified separately from parser/provider implementation defects.

## 2026-10-10 — Observed provider frontier governs Brain exploration

The Brain cannot treat sending more HTTP 200 search requests to an already accessible provider as a new repair. Once the parent has one observed successful provider request, request-count-only child improvements must include a new observed provider-side frontier: search/catalogue to detail, episode, player/embed, then source/media. The initial provider request remains diagnostic progress. TMDB/infrastructure calls and unexecuted LLM labels have no progress authority. This is an exploration-chain selection rule, not a production acceptance shortcut: true FULL requires correct-title playable terminal media on current materialized bytes.
## 2026-10-09 — Preserve original-title query budget across generated Brain strategies

When TMDB returns localized and original titles, the generic Brain runtime must give each known title an opportunity to use the provider-owned search route **within a fixed global request budget**. Exhausting 12 search templates for the first localized title prevents original-title discovery and misclassifies a catalogue as `provider_network_zero_result`. The V7 runtime now reserves search slots for subsequent aliases, under the existing same-provider, TMDB identity and media terminal checks. A 200 catalogue search response alone is not a match: correct-title detail, player, terminal media and playback still determine success. Generated route-graph `v3+` enables this safe alias Lego only when the planner's failure class is search/route discovery; other strategies retain their settings.

## 2026-10-09 — Generative strategy must preserve owned discovery/salvage inheritance

A newly model-authored route strategy is novel in its **new causal evidence and bounded exploration**, but novelty does not authorize deleting the current provider's observed/owned search and request inputs or a parent strategy's safe response salvage Lego. `route_transition_graph_v3+` therefore merges current/learned route and request priors before speculative peer/generic routes and inherits the version-2 response salvage switch. The typed program compiler uses the same base-evidence invariant for future generated siblings. Old `route_transition_graph_v2` remains byte/behavior stable. All routes, bodies and streams still require per-provider ownership, title/media identity, terminal reachability and current-byte replay; a 200 search response with catalogue cards but no detail request is **lookup-only**, never a playable confirmation. The 4khdhub artifact `11642153694` (run `37983399735`) is the negative oracle.

## 2026-10-09 — Validate a new Brain executor before old exhausted siblings

The FORCE representative test must not bury a newly generated executable Repair profile beneath many already installed causal siblings. The forcePromotionEligible blueprint provides a preferred strategy ID, carried only in an explicit bounded FORCE replay. The planner accepts that hint **only when the profile belongs to the current failure family's registered strategy set** and has not been exhausted by an actual observed negative. Ordinary Repair/Fast production exploration has no preferred profile and follows the original ordering. This confirms new Brain generation is tested in executed source bytes; it does not grant publication authority or weaken identity-correct terminal playback requirements. Failure is retained as negative evidence, not retried unchanged.

## 2026-10-09 — Representative proof must exercise promoted architecture

A Brain-generated profile that passes code generation, compiler and four selection-gate checks is not validated until actual current-byte runtime exploration executes it. The FORCE publish workflow must hand off a representative provider via **mode=force**, not a one-wave **mode=repair**, and the canonical pipeline must propagate `--architecture-force` into the Brain runner. Three bounded exploratory waves are still constrained by time budget, same-provider media identity, non-regression and real terminal playable evidence. Strict negative-memory accounting requires `executionObserved=true` before suppressing an exhausted profile; a historical proposal alone cannot consume a legitimate experiment. Never promote a provider from a green architecture workflow or from `no_streams`.

## 2026-10-09 — Strategy identity and negative-learning invariance

`postExhaustionStrategyHint` must NOT invalidate previously executed negative memory for an existing versioned profile when a new unrelated strategy is added. The earlier whole-file `strategyImplementationFingerprint` included every sibling strategy and its selector set, so a successful Brain promotion of `route_transition_graph_v3` made exhausted `html_class_token_exact_v1`/v2 look fresh. This reset Learning and blocked selection of the new executable Brain strategy despite valid generated bytes. Derive a profile-scoped fingerprint from shared runtime plus the selected strategy guard/body, masking the selector registry and unrelated sibling branches. Honor legacy executed failures for the same profile even when their obsolete global fingerprint mismatches; introduce genuinely new capability as a **new versioned profile ID**. Unexecuted applicability failures are not authoritative negatives. The current Repair preflight and CORE Workflow Gate must test both fingerprint invariance and planner migration from observed old failures to the newly installed profile. Sandbox validation, terminal media identity and playable bytes remain independent mandatory gates.

## 2026-10-09 — FORCE dynamic post-exhaustion replay contract

A novel Qwen/Brain `recoveryProgram` was generated, materialized and promoted at `8904cc26` as `route_transition_graph_v3`; see exact artifact `11639134437` and program fingerprint `9bcd98df9bc2a498a3efda585577399b200eae15a1751b393364e87e8cb57fc3`. Live canonical Repair on those bytes then found a preflight **harness defect**, not a playable-provider failure: `brain_llm_advisor_execution_test.py` had assumed exactly 11 post-exhaustion strategies and failed after a new twelfth entered the planner. The convergence loop must derive its bound from the planner's actual unique candidate profiles plus a final exhaustion probe. Run this contract against the generated materialized/planner bytes *before* any architecture promotion and again on the applied promotion checkout; a green isolated materializer test alone must not authorize promotion if full Repair preflight would fail. No FULL state may be granted without a correct-title terminal stream on the published provider bytes.

## 2026-10-09 — Registry-scoped FORCE parent/child registration

A generated Repair strategy uses the adaptive runtime's `POST_EXHAUSTION_STRATEGY_PROFILES` selector, not every textual occurrence of a strategy identifier across the module. Existing strategy IDs legitimately also occur in route priorities and diagnostics. FORCE must require the **parent ID exactly once within that registry**, insert the new child exactly once within the same registry, preserve every other byte (including existing strategy priorities), and verify the independently generated child executor guard. Counting `source.count(parent_line)` across an entire module causes false ambiguity for legitimate parents and wastes model correction rounds on a deterministic pipeline defect. This class of Brain-owned registry/planner failure must stop model correction immediately with an ownership signal; it cannot be solved by asking Qwen to regenerate a recovery program. An executable profile still requires syntactic/materialized contract tests, exact applied artifact, title-matched terminal playback and non-regression before promotion.

## 2026-10-09 — Strategy replay provenance

Every generated typed `recoveryProgram` is compiled only from registered Lego source identifiers and recorded with a deterministic SHA-256 fingerprint, selected program and `priorOnlyUntilAppliedPlayback=true` in the FORCE artifact. This preserves the exact model decision for negative memory/RAG and controlled future replay. A saved response may be reapplied only through the same deterministic materialization, four-gate validation and current-byte playback checks; older allowlisted edit artifacts remain re-testable under the strict legacy path. Presence in a report is never a promotion or successful provider repair.

## 2026-10-09 — Typed recovery Lego generation for 7B FORCE

The Brain no longer relies on Qwen 7B correctly writing Python blocks under a strict raw `branchBody` schema. For novel Repair profiles, Qwen chooses a `recoveryProgram` (allowed observed route sources, direct/positive/peer routes, historical/current/peer request recipes, terminal-route filtering, causal transition mechanism, role ordering and bounded probe budgets). The generic Brain compiler produces the Python strategy branch from those choices, then the pre-existing deterministic materializer adds the three registration gates. A program using no new evidence source or mechanism relative to the exhausted parent is rejected. No candidate, provider bytes, secret, raw URL or arbitrary Python identifier can be supplied via this schema. A compiled strategy is an **experiment only** until the exact applied bytes replay on the correct title and yield verified playable terminal media without regressions. The old Python `branchBody` format is retained only for historical replay compatibility.

## 2026-10-09 — Durable and representative negative evidence

Fast Brain memory import between a stale run and its successor is permitted only for execution-observed negative signatures, after verifying that the source run belongs to the same repository/workflow, is an ancestor of the new main, and that provider/executor/source bytes are unchanged. Historical positive lab fixtures are **not** accepted as current provider proof. The 1000-entry negative memory budget first allocates a small per-provider floor, then retains the most severe remaining signatures globally, so new provider/failure families are not evicted before the Brain can learn. This changes the Brain retention pipeline, not any individual provider or Core publication authority.

## 2026-10-09 — Isolate new executable algorithm from the Brain selector

The Qwen FORCE model is given the exhausted parent executor's *algorithm body* as helper vocabulary whenever a unique parent/sibling boundary can be identified, instead of the surrounding `new_strategy_id` switch. It generates a novel algorithm; the Brain owns the distinct branch guard, Brain registry, JS planner and runtime registry. Nested model-authored guards may be eliminated only if AST proves they select **exclusively the new child** and have no fallback. Parent selector reads/writes, multi-child/multi-parent selectors, unexpected `else` and no-op algorithms still fail closed. Invalid model body text must not be fed back for repeated copying during correction. Synthetic tests prove selector isolation; actual recovery requires applied-byte current-content playable media.

> Schéma de composition Provider v3 et ownership GLOBAL/FAMILLE/PERSONNEL : [PROVIDER_FAMILY_ARCHITECTURE.md](PROVIDER_FAMILY_ARCHITECTURE.md).

# NiakVIO — Brain Repair Architecture

> **Status:** architecture contract for the production Repair/Learning control plane.  
> **Scope:** provider diagnosis, isolated mutation, Learning escalation, same-byte validation and return to the canonical census.  
> **Non-goal:** this document does not freeze a provider count, a census result or a run status.

## 2026-10-08 — FORCE: single runtime-edit model contract and deterministic wiring

The 7B architecture FORCE materializer must not ask Qwen to implement the same strategy in three large, unrelated languages/files. On a `requiresNewExecutableRepairProfile` blueprint:

1. The **model generates only `branchBody`**, a short executable Python algorithm using the bounded context around the exhausted parent. The Brain deterministically inserts this body under a *new* `elif new_strategy_id == child` immediately before the next uniquely anchored sibling; the model cannot change the parent guard or emit provider edits. Re-focused context must include the parent execution branch.
2. The Brain deterministically registers the new ID in `scripts/brain_repair_runtime.py`, the causal JS planner group in `engine_v2/scripts/plan-repairs.mjs`, and the adaptive runtime's *separate* `POST_EXHAUSTION_STRATEGY_PROFILES` selector set. The latter is a fourth executable gate inside the generated executor file; without it, the new branch is unreachable.
3. All three changed files and all four execution gates must pass syntax/structure tests, strict parent preservation, distinct child guard, **transactional rollback**, and an actual patch artifact containing the runtime executor. Every promoter must verify execution-profile installation again **after applying the Git patch**. No taxonomy-only or patch-without-executor success is accepted.
4. Materialized Brain architecture is **not** provider success. The strategy must be selected, execute against rematerialized current provider bytes, reach identity-matched terminal media and pass playback and non-regression. Only the canonical publication/census pipeline may promote a provider.

The 8 October 2026 failure `37834168084` showed a 7B corrective loop retrying the missing planner/registry wiring after contradictory three-surface correction instructions. Commits `1772d040` (pipeline) and `578487c8` (synthetic runtime-only regression) unify the generated edit contract. Current-SHA GitHub Workflow Gate, explicit FORCE and provider playback are independent acceptance gates; see `MEMORY.md` for their exact statuses.

## 2026-10-09 — Branch-body corrections must stay within the Brain pipeline

A Qwen branchBody may be wrapped in its own requested `if/elif new_strategy_id == child` despite the structured contract. The Brain validates the AST and extracts only a single exact-child body; it **never** copies or broadens an exhausted parent guard, accepts a second branch/else, or accepts a no-op implementation. Any other malformed algorithm must receive a bounded, targeted correction request **before** the normal bounded edit and materialized-test loop. A failure must be visible in Learning evidence; a model schema violation is not a provider failure. True acceptance still demands current-byte, correct-title terminal playback, not parser success.

## 2026-10-09 — Corrective sampling for rejected 7B executor bodies

FORCE starts at deterministic temperature zero. Real GitHub Learning run `37962219360` repeated an invalid selector-bearing executor body despite two bounded corrective calls. For new executable Repair profiles only, a **rejected** answer now uses temperature `0.2` to explore a different model-authored algorithm instead of deterministically repeating the rejected bytes. This is not a bypass: child-only guard unwrapping, AST rejection of selector access, parent preservation, four execution gates, materialized-contract tests, playback identity and exact Git artifact checks remain mandatory.

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
        +---- FULL/PARTIAL + no current completeness debt --> protect / no Repair
        |
        +---- multi-player/server/quality fan-out debt ------> Brain completeness Repair
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
- environment-only failures treated as provider defects;
- probe/audit infrastructure failures such as `invalid_probe_output`,
  `missing_tmdb_credential` or a harness `audit_error`.

Probe/audit infrastructure stages are classified outside provider Repair and are
neutral to provider technical/network failure streaks. One broken census bridge
must never turn an entire provider fleet into synthetic provider-code debt.

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

### 5.4 Dynamic multi-player/server completeness is Repair evidence

A provider is not complete merely because one returned stream is playable. Current
census must preserve bounded fan-out evidence from provider responses consumed by
the runtime:

- announced player/server candidates;
- hierarchical variants announced behind each consumed player/server response;
- player/server requests actually explored;
- distinct streams returned;
- declared quality heights and returned quality coverage.

The production-like quick census and Deep health use the same generic response
variant extractor. Provider-specific HTML/JSON remains provider-owned; the
observation layer records only bounded counts, hostnames and quality heights, not
raw response bodies or terminal URLs.

A current row may expose `variant_fanout_state` values including
`announced-not-explored`, `explored-not-resolved`, `returned-subset`,
`quality-gap`, and `fanout-observed`. A current dynamic gap is allowed to classify
a nominally `FULL OK`, `PARTIAL OK` or `CANDIDATE OK` provider as
`variant_coverage_gap` for Brain Repair. The same classification is projected
into the NiakVIO runtime planner's census prior. A targeted Learning sandbox that
temporarily returns `runtime_empty` or a transport failure cannot erase a current
sharded proof that the published provider is playable but incomplete; the
contradiction remains visible while completeness stays the causal Repair target.
Identity and media-safety contradictions still outrank completeness debt. This classification does not require a
hard-coded numeric cap to be found statically: static cap detection is a useful
prior, while current response fan-out is execution evidence.

The required Brain Repair loop is:

~~~text
current response announces N players/servers/variants
-> census measures explored requests + returned streams
-> Brain receives the same bounded fan-out row
-> if a subset is returned, classify variant_coverage_gap
-> Brain proposes the smallest provider-owned enumeration mutation
-> isolated materialization + playback + identity + completeness comparison
-> accept only on measurable fan-out gain with no regression
~~~

CoFlix is a representative validation case, not a provider-specific rule. The
same mechanism must cover any provider whose runtime truncates player, server,
quality, language, mirror or source enumeration.

### 5.5 Current provider-structure evidence is observation-only

A current provider page or API contract may be observed outside the provider's
existing runtime, for example when the provider has migrated to a new resolver and
the stale runtime can no longer reach the new structure. In that case Repair may
consume a bounded structured observation from
`automation/provider-current-structure-evidence.json`.

This channel is deliberately non-executable. It may contain only:

- the current origin hostname;
- normalized route paths and method/role labels;
- request key names, never request values;
- bounded player/server group counts and nested variant counts;
- bounded observed quality heights;
- bounded language labels.

It must never persist raw HTML, response bodies, cookies, headers, tokens, stream
URLs or query values. Both `proofAuthority` and `executionAuthority` remain
false. A route observed here may guide Brain diagnosis and mutation synthesis, but
it cannot become Provider DATA or publication authority without the ordinary
provider-owned execution, rematerialization, playback, identity and non-regression
gates.

This closes a specific Brain blind spot: if the current provider site exposes a
new player/server contract that the stale runtime never requests, current census
alone can only describe the stale path. Brain receives both facts and can repair
the provider-owned traversal rather than merely increasing a cap on obsolete
code.


The observation must also survive prompt construction. For provider FORCE,
current provider-structure evidence and current sharded fan-out evidence outrank
generic census prose in the bounded prompt. At minimum the model-visible
context must preserve the sanitized current origin, observed route path,
authority flags, bounded group/variant counts, and the current
announced/explored/returned gap. Prompt compaction must never silently drop
those fields while retaining only stale runtime source. If context pressure
requires further reduction, historical/retrieval prose is discarded first.

This is a Brain pipeline invariant, not a CoFlix exception. The same rule applies
whenever the runtime cannot observe the provider's current contract because the
old traversal never reaches it.


Canonical Repair V6 consumes the same observation channel, not only Learning.
The observation may influence sandbox hypothesis generation only:

- the current observed origin can outrank a stale provider runtime origin;
- observed route paths can enter the bounded direct-route hypothesis set;
- the indexed fan-out can raise the bounded player/embed exploration budget;
- an unknown HTTP method remains unknown. Repair must not fabricate a POST body
  or promote an observed route directly into Provider DATA.

When current structure exposes a route but leaves its request method unknown,
Repair may create a separate **contract probe**. A contract probe remains
experiment-only DATA: `proofAuthority=false`, `executionAuthority=false`,
`executable=false`. It carries only current origin, route, role and request-key
names. The adaptive sandbox may match it against bounded embedded JSON observed
on a current provider page and try only bounded GET, POST-form and POST-json
shapes after fixture identity fields agree.

Embedded provider-local values stay ephemeral. They may become durable only as a
causal binding when a replayable current response exposed the exact value and a
later successful request consumed it. Durable DATA stores
`{binding:<key>}`, never the literal provider-local value. This preserves the
UNKNOWN-method guard while allowing Repair to discover a changed request
contract without borrowing a peer method or hard-coding a provider-specific
guess.

A winning route/request program becomes persistent only from the request trace
that actually executed in an accepted current-byte candidate. Observation,
hypothesis, execution and proof remain distinct.

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

The Learning job reuses the already-pinned local Qwen runtime. `scripts/brain_architecture_force_materializer.py` accepts at most three bounded edits on allowlisted Brain/Core/Lab surfaces. It supports exact unique find/replace and isolated new Brain layer/test files. It rejects provider bundles, provider-disabled bytes, ProviderBase, manifests, provider overrides and provenance/publication surfaces. Plan validation is transactional and bounded: repeated anchors may be widened only from exact supplied source context, candidate-relative corrective edits are projected back onto the restored baseline, and invalid corrective plans receive at most two additional edit-validation rounds. Materialized syntax/contract correction is restricted to the file that actually failed; parser failures receive candidate/baseline-centered syntax-only guidance and at most three same-run correction rounds. Architecture novelty is durable across request/signature rotation: a strategy with retained negative execution evidence cannot be promoted again as the same `strategyId`. FORCE evolves it to a distinct next profile generation (for example `route_transition_graph_v1` -> `route_transition_graph_v2`) and promotion is rejected unless that new profile is wired end-to-end through the Repair registry, `engine_v2/scripts/plan-repairs.mjs`, and the adaptive runtime implementation. Taxonomy, metadata, comments, proposal JSON/Markdown, or other non-executable edits cannot satisfy that contract. Existing allowlisted files must use `replace`; `create` is reserved for genuinely absent Brain layer/test paths.

A FORCE architecture run must produce a real executable diff. Proposal-only JSON/Markdown is not eligible for auto-promotion. The structural patch is exported as an artifact, replayed on the exact source checkout and re-tested. FORCE then stages only the generated-edit allowlist plus architecture metadata, rejects provider/publication boundaries, requires a stale-SHA lease guard, and pushes one commit directly to `main` without creating a PR or repair branch. After a validated architecture promotion, exactly one current repairQueue representative is dispatched through canonical Repair before any cohort-wide retry. The resulting main SHA must still pass Workflow Gate, Verify/Publish and non-regression; a failed gate or failed representative replay is not a validated architecture/provider repair.

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

## Generic repair learning over provider hand patches

Provider-specific debugging may reveal a causal mechanism, but a hand-written provider patch is not the terminal architecture. Reusable mechanisms must be promoted into Brain-owned repair capabilities and re-tested through current-byte gates.

- `html_class_token_exact_v1` handles permissive JavaScript CSS-class RegExp builders where a dynamic class is followed by `\\b`. Hyphen/underscore are non-word characters, so that boundary can confuse a requested class with a longer class token.
- The Learning-only profile rewrites only that unsafe class-token terminator. It contains no provider identifiers, domains, routes or fixture-specific selectors.
- It is eligible as a post-exhaustion strategy for route/search gaps and still requires sandbox health, identity, media/playback and non-regression proof before any publication.
- Provider-specific source edits are evidence for capability synthesis, not a substitute for Brain Repair.



## Dynamic provider fan-out / completeness evidence

A provider is not considered complete merely because one playable stream exists. The read-only worker derives bounded, redacted fan-out hints from response bodies actually consumed by provider code: candidate player/server count, candidate hostnames and advertised quality heights. Raw URLs, tokens and response bodies are never persisted by this diagnostic.

Deep health preserves four separate stages: **announced candidates**, **candidate requests explored**, **streams returned**, and **streams actually playable/identity-safe**. It emits a diagnostic `variant_fanout_state` such as `announced-not-explored`, `explored-not-resolved`, `quality-gap`, or `fanout-observed`. These states do not demote a provider by themselves; they are evidence for Brain completeness repair and FORCE validation.

This closes the previous blind spot where census FULL OK meant “at least one terminal stream works” while a provider could silently lose later servers, languages or HD/4K variants.


### Hierarchical player → variant completeness

Completeness is measured across stages rather than by a single stream or server count. A provider response may announce a small set of player/server hosts; responses actually consumed from those hosts may in turn announce many terminal variants. The harness records bounded/redacted counts only and derives `announced_variant_candidates` by taking the strongest candidate count per explored player host+route, then summing those distinct nested observations. Raw player URLs, tokens and response bodies are not persisted.

Provider-local runtimes remain responsible for their own server/HTML/JSON structure. Brain receives the generic evidence and may remove a proven bounded fan-out truncation from exact current provider-owned bytes. FORCE acceptance requires no runtime, malformed-request, identity or playable regression; a larger distinct returned-stream set is a verified completeness gain only when current hierarchical fan-out evidence exists and sampled playability remains positive.

Index-only player menus are also observable without provider-specific class names. When a consumed response contains bounded numeric player controls (for example a `role="menuitem"` carrying `data-i`, `data-index`, `data-player-index` or `data-server-index`) inside clear player/server/media context, the harness records only the distinct candidate count. Bare scalar attributes such as `data-src="1"` are never promoted to URLs/hosts. This lets provider-specific DOMs such as a two-server menu expose completeness debt to Brain while keeping the evidence surface generic and redacted.


### Sharded census → Brain fan-out repair authority

The fast/sharded census must preserve the same bounded multi-reader/server evidence used by Deep Health. The CI probe extracts only sanitized counts, hostnames and advertised quality heights from response clones; response bodies, credentials and terminal URLs are not persisted. Each provider/lane census row carries:

- `announced_player_candidates` and `announced_variant_candidates`;
- `announced_player_hosts` and `announced_quality_heights`;
- `explored_player_requests` and `explored_player_hosts`;
- `streams_returned` and `variant_fanout_state`.

Brain Repair consumes the current sharded ledger as dynamic completeness evidence. A provider that is otherwise FULL/PARTIAL/CANDIDATE OK may therefore become a `variant_coverage_gap` target when several players/servers/variants are announced but traversal or returned streams are a strict subset. Static runtime cap detection and dynamic fan-out evidence are complementary: either can put the provider into the explicit completeness cohort, while publication still requires current-byte playback, identity and non-regression proof.


When repeated current-byte completeness experiments fail, Brain must progress by **causal mechanism**, not by repeatedly raising the same cap. Executed negative memory is therefore part of the selection contract. For bounded source lists, a later progression may change only traversal order (for example a bidirectional source frontier: first, last, second, penultimate) while preserving source-count bounds, deadlines, routes, identity rules and the global stream cap. Such a reorder is still only a hypothesis: it must pass the same strict playable quality/language/host gain and identity/non-regression gate before publication.



### FORCE repeated replace anchoring

Architecture FORCE may receive a model replace whose `find` text appears more than once in a large executable Repair surface. This is not automatically a model failure when the exact bounded source snippet is unique and the active blueprint's `strategyId` / `evolvesFromStrategyId` identifies one occurrence unambiguously.

The materializer may then select only the uniquely nearest occurrence to that strategy anchor and widen the replace with unchanged real neighboring bytes until the final `find` is globally unique. Equal-distance or otherwise ambiguous matches remain fail-closed and return to the normal corrective loop. This resolver is Brain infrastructure only; it does not grant provider mutation authority or weaken current-byte Repair validation.

### Architecture FORCE concurrency ownership

Explicit Architecture FORCE is a proof transaction, not ordinary targeted Learning. Its concurrency key is separated from routine Autopilot/Learning by cohort. Routine targeted Learning may cancel stale routine work in its own cohort lane, but must never cancel an in-flight FORCE before proposal, materialization, promotion and representative replay. Multiple FORCE requests for the same cohort queue rather than canceling one another. Promotion still uses the existing current-main/rebase guards, so this separation does not weaken Git or publication safety.

### Strategy-block anchoring for evolved FORCE profiles

When FORCE evolves an exhausted executable Repair profile (for example `route_transition_graph_v1 -> route_transition_graph_v2`), generated replaces in the adaptive runtime may contain text repeated across adjacent strategy branches. The materializer may resolve such a replace only when the prior strategy's exact `if/elif new_strategy_id == <evolvesFromStrategyId>` block contains that find exactly once. It then widens unchanged surrounding bytes until the final replace anchor is globally unique.

Compact corrective payloads may omit part of the original source window. In that case the same exact prior-strategy block may be located in current repository bytes and used as the sole fallback. Generic nearest-occurrence selection is not sufficient authority; ties, missing blocks, or multiple matches inside the owned block remain fail-closed.

Architecture FORCE failures must preserve sanitized proposal/report artifacts even when executable materialization fails. This evidence has diagnostic authority only and cannot publish provider or production bytes.

### Additive three-surface contract for new Repair profiles

A blueprint with `requiresNewExecutableRepairProfile=true` is a single three-surface transaction. Qwen must see bounded source context from the Repair registry, planner and adaptive runtime simultaneously and must return one replace edit for each surface. The exhausted `evolvesFromStrategyId` remains executable and recorded as negative experience; the new strategy is added, never substituted by renaming the prior strategy. Generic compact fallbacks that prefer one edit are not valid for this class of evolution.

Corrections preserve the same three-surface authority even when the first transactional failure is syntax or a focused Brain contract. The correction must remain additive, use all mandatory surfaces, and pass syntax, Brain contracts and new-profile wiring validation before promotion.

### Additive parent-preserving Repair profile evolution

When Architecture FORCE evolves an exhausted executable Repair profile, the new strategy is additive. The exact parent runtime guard `new_strategy_id == "<evolvesFromStrategyId>"` must remain independently executable and unchanged in `scripts/adaptive_runtime/runtime_repair.py`; the new strategy must be added as a separate sibling branch while also being registered in the Repair registry and planner. A merged condition that routes both ids through one branch is rejected even if the new id is present on all required surfaces. Blueprint implementation validation runs before generic contract tests so corrective feedback describes the causal architecture violation directly.


### Blueprint-aware repeated anchors across all Repair surfaces

Architecture FORCE uses the same blueprint-aware repeated-find resolver across the Repair registry, planner and adaptive runtime. Runtime branches first bind to the exact `new_strategy_id == evolvesFromStrategyId` block. Registry/planner surfaces may bind a repeated model `find` only when one occurrence is uniquely nearest to the parent/new strategy id in current bytes. Ties or missing strategy anchors remain fail-closed. This keeps compact corrective prompts deterministic without permitting arbitrary nearest-text mutation.


### route_transition_graph_v2 — reusable manual oracle

When `route_transition_graph_v1` is exhausted, Brain may select `route_transition_graph_v2` as a distinct post-exhaustion executor. v2 is same-provider-first: it combines retained positive/current/historical request programs, compiles transition prefixes only from provider-owned observed route DATA, and enables runtime response salvage so successful HTML/JSON/text responses can yield terminal/player URLs without guessed provider-local routes. It is registered in the planner, Repair runtime registry and adaptive runtime; negative-memory fingerprint rotation controls selection. This oracle is Brain infrastructure and must still pass representative provider replay and normal acceptance proof before cohort use.


### Exploration-chain transport integrity

The adaptive bounded planner overlay must preserve the explicit production exploration-chain bit on both initial `update_plans()` and later `replan_observation()` calls. Dropping the bit is a control-plane failure: registered post-exhaustion strategies remain visible as candidates but are incorrectly deferred as Learning debt. Normal production stays fail-closed because the bit is derived from `NUVIO_BRAIN_EXPLORATION_CHAIN=1`; only callers that explicitly own a bounded exploration/replay transaction enable it.


### Durable profile-id exhaustion and generation priority

Post-exhaustion strategy memory is conservative across historical schema changes. A failed profile row without an implementation fingerprint still exhausts that profile id; a new implementation must use a new generation/id such as `*_v2`. This prevents code movement elsewhere from resurrecting old failed executors.

For the route-terminal family, newer explicit generations are ordered ahead of their exhausted parent generation. In particular `route_transition_graph_v2` is preferred over `route_transition_graph_v1`, and in `search_gap` follows the exact HTML-token strategy so the Brain can move from parser-local recovery directly into same-provider observed transition traversal without replaying the historical v1 strategy chain.

### Repair upstream client snapshot: exact tree lineage + pending native audit

Provider Repair preflight now uses check_nuvio_client_upstreams.py --paths-only to verify exact current upstream branch HEAD, ancestry and all changed path names from commit/tree objects. Rename detection is disabled; old and new paths are conservatively retained. Unknown branches/history or missing tree objects stay fail-closed.
Semantic paths without readable patches are recorded as semantic_review_unverified_files and classified contract_review_required, never safe_advance_available. Linear known upstream drift can be exercised by isolated Brain Repair, with native reader acceptance still required. Native Labs continue their full semantic content audit. This is a Brain/Core pipeline correction, not a provider mutation.

### Stalled Repair → Learning ownership

An unsuccessful Repair wave with `stalled` or `exhausted` experiment rotation must not become a silent `no_new_repair_experiment` with an empty Learning handoff. The Brain assigns the remaining non-harness-differential providers to `deferredLearningProviders`, preserving the exact stall reason and all negative fingerprints. Learning may synthesize a new executable strategy; it does not gain publication authority without compile/materialization/current-byte media proof. This escalation never manually mutates individual provider code.



## FORCE novelty reconciliation (2026-10-08)

Before invoking Qwen for an evolved Repair profile, Learning reconciles the identifier across the Brain registry, JS Repair planner, and adaptive Python runtime. An already installed profile must be replayed with current-byte evidence instead of regenerated by FORCE. A partially installed profile is not executable proof. Only failed installed strategies can advance to a fresh version; provider publication still requires correct-content terminal playback, identity, non-regression and rematerialized byte validation.

## Cross-pipeline negative evidence (2026-10-08)

Architecture FORCE novelty must reconcile actual canonical Repair negative execution entries with sandbox Learning memory before choosing an evolved strategy id. Source: `automation/brain-repair-memory.json`; scope only the currently deferred providers, versioned strategy profiles, observed executions and positive failure counts. Unexecuted proposals, unverified media, other providers and WAF-only observations cannot count as exhausted. Inspect the installed strategy across registry, JavaScript planner and Python runtime; replay a fully installed executable strategy before asking Qwen to create it again. If its actual execution has already failed, synthesize a causally new strategy version and require current-byte compilation, correct content, playable media, non-regression and persistence before any provider promotion. No direct manual provider changes are authorized by this mechanism.

## FORCE materializer: deterministic executable wiring (2026-10-08)

The Brain LLM may generate one meaningful Python runtime **sibling** executor edit for a novel versioned repair profile. The Brain materializer then deterministically wires that version into `scripts/brain_repair_runtime.py` (post-exhaustion registry) and `engine_v2/scripts/plan-repairs.mjs` (scope-qualified causal family). This is infrastructure scaffolding, not a replacement for Qwen's behavioral strategy generation and not a provider-specific fix.

Fail-closed requirements: an installed version must not be regenerated; old strategy guard must remain unchanged; target and parent IDs must differ and be versioned; only recognized repair scopes with a real planner parent can be wired; every exact find must be uniquely anchored and bounded; every edit must be allowlisted; the three-file Python/Node materialization must parse and pass focused tests transactionally, with byte-exact rollback after validation. Brain or repaired provider code can only be promoted after actual current-byte, correct-content, playable media and non-regression proof. A green scaffolding test never counts as a provider success.

## 2026-11-07 — Exact-source rejected-unit diversification and strict proof parity

A failed Brain-proposed **pure deletion** is an executed planning counterexample, not a new strategy. Brain-LLM now attaches only SHA-256 of the rejected exact current-source Bloc unit to its validation feedback, excludes that same source unit from both prompt and constrained wire on retries (regardless of transient unit-ID reordering), and refuses an injected rejected unit in the converter. It may select another complete current-byte unit or abstain, but cannot silently apply a destructive deletion.

Hosted proof remains isolated with `publicationAuthority=false` and requires actual generated/validated/materalized provider bytes, playback+positive content identity and a **new decoded fixture control** without loss of existing decoded controls. The deterministic evaluator, not the hosted job's report presentation, decides the repair acceptability. `unresolvedFixtures` is reported as remaining work, **not** a second contradictory all-fixtures acceptance gate. This proves at most a concrete provider fixture improvement, not all categories/hubs. Production promotion requires separate exact-SHA publication and family non-regression. Security CodeQL stale-alert retirement uses independently complete High/Critical inventories, never a truncated total-list sample.

## 2026-11-07 — Generic GraphQL response error observations (Brain first)

- A successful HTTP status is not a valid media terminal. AllAnime hosted evidence (42326911944, `live-context.json`) contained JSON content_lookup 200s with GraphQL `errors[]`, `data:null`, and `data.episode:null` while all five fixtures returned zero streams. Blind provider mutation without categorizing GraphQL failure led to Brain deletion/no-op/abstention, not playback.
- `scripts/response_structure.cjs` now adds optional `graphql` **enum-only** evidence: bounded error count, allowlisted `extensions.code`, error category, data state, and allowlisted null roots. Raw response messages/URL/headers/body and arbitrary extension values never leave the source classifier. Brain-LLM must separately validate and admit these fixed categories into both current and previous verification. This is generic network observation **infrastructure**, not an AllAnime-specific workaround or proof of a repaired provider.
- The acceptance bar remains generated/compiled/applied/materialized/current-byte replay plus decoded, identity-correct media improvement without lost previously playable fixtures. Static tests do not establish terminal playback.

## 2026-11-07 — Brain causal GraphQL lookup selection (proof pending)

The Brain-LLM FORCE model first sees runtime facts from an exact source SHA and observed network events. A HTTP-200 GraphQL response with `errors[]` and null data is **not** a valid episode/stream result; those fixed-enum facts must survive RAG/prompt compaction. Brain-LLM `_graphql_causal_source_functions` now prioritizes current declared search/query/lookup producers found in the same observed lookup failure above generic terminal validators, while excluding functions already proven non-improving by negative memory. Only function names present in exact current source may be selected. The model cannot invent GraphQL queries/hosts, copy sensitive error messages or weaken identity and decoded-media requirements.

A passing static/Brain CI is **not** a provider recovery. The representative hosted workflow on main executes the pinned Brain causal-selection regression and must generate, compile, apply and materialize an exact edit, replay it against the same work, then prove decoded playable media with correct TMDB/S00 identity and no regressions. Until then, retain the provider's prior census status and the 17-provider repair queue.

## 2026-11-07 — Representative repair portfolio selection (no provider override)

The main-only hosted Brain proof had repeatedly selected AllAnime on every workflow-source push, consuming CPU-Qwen budget without producing a materialized candidate. The provider selector now uses the authoritative `automation/provider-census-status.json` repair eligibility and immutable archived hosted proof summaries to choose **one** current representative with a stronger retained candidate/historical/route basis, while penalizing repeated non-executable/no-op generations. Explicit manual selection is still confined to a known non-disabled provider. WAF, external transport exceptions, disabled and authority-blocked states are not promoted or mutated. The selection is deterministic and writes only the runner's `TARGET_PROVIDER` environment variable, never provider code or census status. The first successfully decoded/identity-safe repaired candidate is still mandatory before fleet promotion or broader family expansion.

## 2026-11-07 — Replay-only candidate classification is not an executable mutation

Brain-LLM maps a census `CANDIDATE OK` (or any retained candidateProof) to `candidate_replay_gap`, with high-confidence strategy `same_provider_candidate_program_replay`. The Brain policy explicitly marks that strategy as `NO_MUTATION_STRATEGIES`. Its required work is **locate exact candidate bytes and replay them against the current provider/media identity and decoded playback gate**. A generic Qwen mutation workflow cannot satisfy that obligation and must never override the no-mutation policy. The evidence-based synthesis selector now excludes these replay-only candidates from its eligible list, logs how many require replay, and rejects manual attempts to route one into synthesis. It still preserves them in the 17-provider census queue and does not mark the candidate resolved. The existing Remat Test track owns candidate reproduction until a verified candidate can be materially transferred; unrelated route/chain/regression failures remain eligible for real Brain synthesis and strict sandbox proof.

## 2026-11-07 — Persisted no-op rotation and replay provenance boundary

The representative source-mutation selector now assigns stronger *negative proof weight* to a generated no-op or pure deletion: a single 3B failure must not repeatedly consume another full inference budget merely because the provider has a high historical score. Historical timeouts receive a lower penalty (model/infrastructure rather than provider causality). This is deterministic, provider-agnostic and reversible as new evidence is recorded. Its unit test covers the actual regression-then-no-op pattern and ensures explicit manual requests remain distinct from automation. Changes to the selector now trigger the main-only sandbox test.

The Remat Test lane explicitly emits `candidateReplayProvenance` and `candidateProgramReplayPerformed=false`. It does **not** execute a historical Brain candidate program: it reconstructs *current structured DATA* then runs a current-byte retest. A retained `CANDIDATE OK` label such as the historical `run 34309729426` is not an executable program or current terminal proof. The diagnostic records historical run labels, current strict retest result and the required next stage (exact-program recovery or Brain reconstruction); it never invents missing patches, promotes statuses or weakens the decoded identity gate.

## 2026-11-07 — Category-specific decoded sandbox repair fixtures

The Brain candidate evaluator must not reuse an anime-only cross-provider playback
fixture collection for a movie- or TV-only provider. Strict Force validation now
derives the immutable comparison fixture set from the enabled provider's
\`manifest.json\` supportedTypes and the audited \`health-config.json\` reference
fixtures that have known positive expected durations. Baseline and candidate
run the same fixed examples. At least one real fixture per declared supported
media type is required; unknown or missing categories fail closed.

A candidate cannot nominate its own easier tests. The decoder must see at least
one new verified duration- and identity-safe decoded media control, while all
previously working fixture controls must be preserved. The pre-existing
anime-only \`check_cross_provider_playback\` harness retains its independent
fixed Jujutsu Kaisen/Hell Mode contract. A multi-category provider's unresolved
fixtures remain explicit in proof reports; a generated, materialized patch is
not automatically counted as a playable provider.

Regression and hosted proof preflight both run
\`tests/brain_strict_fixture_category_test.py\`. Direct manual provider repairs
remain out of scope; Brain-owned orchestration and validation are the only
modified production-facing surfaces here.

The decoded probe projection must pass the verified fixture's expected duration to the media-control predicate. The standalone 24-minute anime default is **not** a film/TV duration policy. Other identity/media/short-preview checks remain unchanged.


## 2026-11-07 — Decoded-repair negative feedback and roadmap authority

- Brain-LLM `057d8d0`/`1f7096b` extends generic source-locality negative feedback to the **executed and rejected** `decoded_repair_no_new_fixture_control` outcome. This is a source-selection/learning correction, not a provider fix. The source unit is rotated only if execution and materialization were proved **and** sanitized baseline/candidate metrics and numeric reader fanout are unchanged.
- The numeric fanout projection includes announced player/variant counts, explored player requests and maximal playable height, excluding raw URLs, headers and media payloads. Increasing actual exploration prevents premature 'non-improving function' rotation; announced options alone are not decoded playback.
- Real 4KHDHub proof `42358985990` showed 16 announced players, 1 visited, 0 streams before and after a materialized regex edit; this was rejected as `decoded_repair_no_new_fixture_control`. Brain LLM CI on `1f7096b` and a fresh hosted proof using that Brain pin are separate necessary checks.
- The canonical execution/decision checklist, 17-item repair queue snapshot, blockers and model/transport/escalation criteria now live in [`BRAIN_REPAIR_ROADMAP.md`](BRAIN_REPAIR_ROADMAP.md). Check current census and SHA before treating any snapshot as live state. Security #2531 retirement workflow `42359913056` returned SUCCESS but actually logged `FIELD_CODEQL_STALE_2531_DEFERRED` because of source drift, not a verified alert dismissal.


## 2026-11-07 — Sandbox feedback projection must preserve causal fanout progress

The hosted sandbox `scripts/run_hosted_brain_repair_loop.py::verification_feedback`
correctly extracts the **last executed candidate row** from the evaluation,
but previously projected only playable/returned stream and identity/fixture
counters, omitting `variantCoverage`. Consequently, even though the executor
recorded the number of actual reader requests, Brain-LLM never received those
numbers as `previous_verification`; its locality rotation could treat real
reader traversal progress as an unchanged failure.

NiakVIO `80e328f` now carries four non-negative bounded integers for each
baseline/candidate: announced player count, announced variant count, actually
explored player requests and maximum playable height. It **does not** project
hostnames, reader URLs, tokens, headers or raw network bodies. Regression
`5402f16` asserts the before/after counts and proves sensitive values are
not copied. Workflow `06eaea5` includes the bridge and regression in the
hosted push paths; `tests/hosted_brain_repair_loop_test.py` and the matching
Brain-LLM `test_force_execution_feedback.py` are now both preflight checks.

This change only makes an independent negative experiment observable to the
next Brain inference. It does not make player fanout an acceptance criterion;
strict decoded, identity-safe terminal playback and no-regression remain
mandatory. Exact-new-source hosted proof, CI logs and artifacts are required
before any success statement. See `BRAIN_REPAIR_ROADMAP.md` for the live
checkpoint and decision gates.


## 2026-11-07 — Count genuinely new decoded controls, not changes in weak playable URLs

Strict Brain media improvement formerly required `old['streams_playable']==0` plus `new_controls>0`. A pre-existing playable-but-undecoded URL could therefore be made *genuinely decoded* by a model patch while the deterministic validator still rejected it because the weaker original playable count was nonzero. This was a harness/acceptance defect, not evidence that a provider fix should be hand-written.

NiakVIO `43f9e361` counts an accepted **candidate fixture improvement** when the candidate has *more identity-safe decoded media controls* than the baseline; it **does not** relax the existing guard rejecting any loss of decoded controls or regression in returned/playable stream counts. `tests/brain_strict_fixture_category_test.py` commit `06ea7688` checks playable-but-undecoded→decoded with unchanged URL/stream count; historical wrong fixture, wrong movie duration and missing decode controls continue to be rejected. A passing fixture unit test cannot prove real provider playback. See [roadmap](BRAIN_REPAIR_ROADMAP.md), run `42361530133` for real hosted proof, and the exact-SHA Core and non-regression gates.


## 2026-11-07 — Cross-repo business contract and current transport ownership

- The Brain preflight and its repair evaluator must use the **same actual manifest-category fixture contract**; `972b079` runs `NIAKVIO_REQUIRE_DECODE_PROOF=1` for both initial observation and recheck, and the deterministic evaluator still alone accepts real media. Using a movie provider with two generic 24-minute anime examples was invalid architecture, not proof of poor model quality.
- `fixture_summary` may project identity before stream decode, but `9fed39c` now requires exact **catalogue** TMDB, season, episode, label and expected duration. Forged fixture facts do not become trusted duration or decoded probes. Do not let the model or provider redefine its own acceptance oracle.
- The preflight `blocked` with zero playable media is routed to transport-differential evidence, not code synthesis (`fbca89a`); `provider_unreachable` alone does **not** establish an external WAF and must retain possible provider/runtime repair eligibility (`b5f86d`).
- Confirmed security triage from [audit](docs/NIAKVIO_BRAIN_METIER_SECURITE_QUALITE_AUDIT_2026-11-07.md): 377 high CodeQL open on NiakVIO at inventory, 376 non-current bundle snapshots, #2531 a maintained test-only incomplete URL denylist now strengthened to positive expected origin (`d5325feb`); not an authority to bulk delete cache-addressed providers. Brain-LLM CodeQL open **0** after stronger URL parsing, independent of unreachable Dependabot/secrets inventory. Publication and client media need their own exact-SHA proof.


### 2026-11-07 — Provenance des candidats et dette de replay

Le statut `CANDIDATE OK` peut seulement indiquer un run historique ; il ne garantit pas que son programme mutation exact existe encore et puisse être rejoué. Le nouveau module Brain `replay_inventory` confronte chaque candidate de la repairQueue au fichier de mutations archivé, au provider exact et à son SHA source, puis produit uniquement des statuts non autoritatifs : `missing_exact_replay_program`, `historical_program_needs_safe_rematerialization`, `source_matched_program_needs_live_replay`. Même le dernier statut exige une application/sandbox/décodage indépendant. Le workflow hosted archive ce constat avant l'inférence locale ; il ne reconstruit pas arbitrairement un patch manquant. Les deux anciens candidats référencés par `run 34309729426` n'ont pas de fichier exact dans le dépôt courant.


## 2026-11-07 — Contrat de mémoire Brain : génération vs exécution

Le registre Brain conserve deux natures de preuves qu'il ne faut plus confondre :

- **Tentative de génération** : `not_generated`, aucun fichier candidat exécutable ; `generationAttemptObserved=true`, `executionObserved=false`. Un échec répété à empreinte d'implémentation `strategyImplementationFingerprint` strictement identique bloque la même génération afin de ne pas boucler ; une ancienne tentative sans empreinte fiable ne doit pas épuiser un exécuteur nouveau.
- **Exécution effectivement éprouvée** : `rejected` après génération/retest, `exploration_progress_nonpublishable` ou `accepted` ; seule une observation réelle garde `executionObserved=true`. Les rejets identité/lecture restent bloquants même si la génération structurelle fonctionne.
- **Indisponibilité de profil** : `profile_unavailable` n'est pas une tentative exécutée. Les anciennes lignes contradictoires (`executionObserved=true` sans enfant) sont normalisées lors de la lecture de mémoire, de la synthèse Learning et de la fusion des phases.
- **Fusion de mémoire** : si un ancien enfant a été exécuté puis qu'une phase ne parvient plus à le générer, l'échec réellement exécuté conserve son autorité ; l'inverse n'autorise pas à inventer une exécution.

Responsables modifiés : `scripts/brain_repair_runtime.py`, `engine_v2/scripts/plan-repairs.mjs`, `engine_v2/scripts/learning-lab.mjs`, `scripts/run_brain_learning_queue.py`. Tests : `tests/brain_generation_attempt_memory_test.py`, `tests/brain_learning_queue_experiment_ledger_test.py`, `tests/brain_cross_phase_experiment_memory_test.py`. Ces tests ne prouvent ni la lecture réseau, ni la matérialisation publiée, ni la réparation autonome d'un provider.

L'oracle 4KHDHub en mémoire (`0/0 → 1/1` film/épisode sur HTML local) demeure **evidence-only**, jamais une autorisation de publication. Il faut toujours : plan Brain → candidat exact → bytes exécutés → retest réseau/identité/stream terminal → non-régression → publication/persistance vérifiées.


## 2026-11-07 — Learning mémoire multi-hubs : rétention bornée et équitable

- **Cause d'évolutivité constatée :** `engine_v2/config/brain-policy.json` plafonnait `learningLab.memoryMaxEntries` à **1000**, alors que `production.negativeExperimentMemory.maxEntries` autorise **16000**. Le dernier Learning avait exactement `memory=1000`. À grande échelle, le tri global par date aurait supprimé toute l'expérience de hubs peu actifs, en privilégiant les fournisseurs les plus souvent retestés. Cet état était un problème de réutilisation, pas une preuve de réparations.
- **Correctif générique :** le plafond Learning est aligné sur le plafond de production `16000`, toujours borné (1 à 20000), et `engine_v2/scripts/learning-lab.mjs` utilise `retainBoundedBrainExperiments` depuis `engine_v2/src/brain-negative-memory-retention.mjs`. L'algorithme choisit par round-robin jusqu'à 12 expériences par provider avant d'utiliser la capacité restante selon la pertinence globale ; aucune mutation ni autorité de playback.
- **Protection de la configuration :** `engine_v2/config/brain-self-evolution.json` empêche le mécanisme d'auto-ajustement de redescendre silencieusement sous 16000 entrées (plage 16000–20000). À réévaluer uniquement avec un benchmark de mémoire, stockage et coût.
- **Test de charge représentatif :** `engine_v2/tests/brain-negative-memory-retention.test.mjs` simule **800 providers, 12 expériences chacun**, plus 18000 observations d'un hub dominant. Il exige 16000 entrées exactement, 800 providers préservés et au moins 12 expériences par provider, résultat stable à la relecture ; il contrôle aussi les limites d'auto-évolution. Couverture branchée aux Workflow Gate, Fast Repair et Learning.
- **Limites de preuve :** ce test prouve la conservation de données de contrôle à l'échelle visée, **pas** la performance réelle des 800 providers, le bon décodage ni la vitesse CI sur 800 hubs. Mesurer coût CPU/GC, taille d'artefact, I/O et efficacité de replay sur un run réel avant de déclarer l'optimisation complète.


## 2026-11-07 — Learning cross-run : conserver la dernière exécution réelle

Le rapport `engine_v2/scripts/learning-lab.mjs` ne peut plus remplacer `lastOutcome=rejected`/`executionObserved=true` par `not_generated` ou `profile_unavailable` quand un run ultérieur ne produit aucun nouvel enfant du **même profil/fingerprint**. La fusion conserve alors les compteurs bornés et la dernière exécution réelle ; elle enregistre séparément `generationAttemptObserved=true` pour l'échec de génération ultérieur. Si le nouveau run exécute réellement un enfant, sa nouvelle décision (rejet/acceptation) est prise en compte.

L'oracle `engine_v2/tests/learning-lab-memory.test.mjs` couvre la conservation d'un rejet `required_category_playable_proof:anime` après `not_generated`, et le scénario inverse où un vrai rejet `required_category_playable_proof:movie` arrive après une ancienne génération infructueuse. Les scénarios restent des contrats de mémoire et de causalité, **pas** des validations de média terminal. Le même principe s'applique au `run_brain_learning_queue.py` et au pipeline Fast.


## 2026-11-07 — FORCE : recherche de nouveauté causale avant génération coûteuse

**Observation réelle de la boucle :** le run [Learning 42385368377](https://github.com/niakw/NiakVIO/actions/runs/42385368377) a consacré plusieurs tentatives Qwen 7B à `route_transition_graph_v25`, puis le validateur AST a rejeté ses copies de `v14/v15` dont seuls les budgets numériques changeaient. La validation a correctement refusé la publication ; le défaut de Brain était de recommencer des générations non nouvelles.

**Nouvelle architecture générique (Brain-only) :** `_novel_recovery_lego_menu` part du **vrai runtime installé** et indexe tous les AST des profils d'une même famille, pas seulement son parent. Il compile des assemblages bornés de Lego existants (sources de recherche/direct/recipes, rôles terminaux, transitions internes et filtres) avec budgets fixes, compare les AST en ignorant les valeurs numériques et expose uniquement des programmes causalement distincts au modèle. Aucune URL, aucun domaine ni code spécifique à un provider n'est injecté.

Après un clone numérique et une correction du modèle également clonée, ou un timeout de correction, `_brain_lego_recovery_fallback` peut sélectionner une composition Brain distincte. Sa provenance est `typed-brain-causal-lego-selection` et `priorOnlyUntilAppliedPlayback=true`. L'exécution reste gouvernée par les mêmes barrières : identifiant nouveau, garde du parent intacte, câblage sur trois surfaces, AST/syntaxe, tests de contrat, matérialisation, identité film/épisode, stream terminal lisible, non-régression et persistance. Si aucune composition nouvelle n'est trouvée, le pipeline **échoue fermé** : jamais de clonage volontaire ni de statut réparé artificiel.

**Régression représentative :** `tests/brain_architecture_force_materializer_test.py` inspecte les branches existantes du vrai `scripts/adaptive_runtime/runtime_repair.py`, dont les 24 versions `route_transition_graph_v1–v24`, vérifie six compositions non clonées et simule deux propositions Qwen rejetées. Aucun provider n'est modifié par le test. La CI est à lire au SHA exact avant qualification de ce nouvel algorithme ; une composition nouvelle ne démontre **aucune** amélioration média en soi.

### FORCE architecture: exact executable rebase and representative replay

A changed `main` can be provider-neutral and still invalidate generated Brain code. The FORCE promotion rebase guard now reads the **exact diff being promoted**, intersects its touched paths with the source-to-current drift, and rejects overlapping planner/runtime/executor changes. That case must requeue on the current SHA rather than attempt a stale `git apply`. Unrelated append-only observations can still be rebased, but never override provider/source/architecture conflict checks or executable-byte validation.

The automatically dispatched representative FORCE replay is **not equivalent** to an ordinary production experiment. If a newly promoted profile is in the installed causal candidate family, it takes precedence even if older base profile generations remain unexhausted. This early selection is available only to an explicit exploratory FORCE request, cannot select arbitrary profile names, cannot override a real executed-negative history, and cannot publish on a route or parsing witness alone. Without this, [run 42414140056](https://github.com/niakw/NiakVIO/actions/runs/42414140056) reached `allanime` but used `adaptive_runtime_recovery` instead of the promoted `terminal_transition_graph_v9`. The real negative report is retained as a test witness; regenerated code still needs materialization, exact bytes, episode identity and terminal media proof.

## 2026-11-10 — Representative reverse inputs across source topologies

A reusable failure-family strategy is not equivalent to one representative
provider: verify independent current-source network witnesses for HTML
catalogue/download, JSON/GraphQL API, player/embed and blocked transport.
Keep TMDB API calls out of provider-source response topology classifications;
HTTP challenges cannot certify the origin's content. Brain family selection
can preserve same causal mechanism SHA while scheduling additional topology
witnesses; the six-source read-only reverse workflow records independent
exact source SHA and sanitized real-network response shapes. No source
observation, model candidate, HTML marker, HTTP 200 or returned URL promotes a
provider: promotion still requires Brain-produced compile→apply→rematerialize→
independent terminal decoded media/episode/subtitles→non-regression and
persisted experience on executed bytes. No manual provider-specific patches.

### Brain strict fixture type ownership: canonical content vs client aliases

For provider-specific decoded repair gates, use the published manifest's
non-empty `canonicalSupportedTypes` when present, otherwise declared
`supportedTypes`; these are *different* notions. Nuvio may route an anime
series through `tv`, but this does not qualify a second general-TV content
catalogue. Immutable title/episode fixtures are selected per **canonical
semantic** category and validated against exact executed tests; no
type widening, synthetic S00 remapping, unverified URLs or alias-success
promotion. `scripts/provider_semantics.cjs` uses this contract already;
Brain's `strict_repair_fixture_contract` and reverse diagnostics must match.

### 2026-11-10 — Source bytes into the actual Deep Brain planner

The Deep adapter must call `update_plans(registry, health, "deep", stage=stage)` with its exact staged current provider bundle directory. The planner's bounded `structuralRepairEvidence` requires the current source hash and is diagnostic-only. A synthetic direct planner test cannot substitute for this Deep stage-to-planner link. Selecting a structural Lego is not proof of repair; materialization, media decoding, episode/subtitle identity, safe replay and non-regression retain exclusive acceptance authority.

### 2026-11-10 — Canonical/adaptive Brain planner parity requirement

`run_adaptive_deep_repair.py` imports `scripts/adaptive_runtime/brain_repair_runtime.py` through the adaptive-first import order. Any canonical `brain_repair_runtime.update_plans` diagnostic input (including `stage` and its bounded `structuralRepairEvidence`) must be explicitly forwarded by this adaptive overlay into the *same* batch `items[].candidate` before the Node planner. The overlay may split/batch/defer transport errors but cannot silently drop evidence or change source authority. The integration test must invoke the adaptive planner function, not mock away its signature; blocked upstream responses remain negative controls. Terminal media decoding/identity/non-regression remain mandatory for repair acceptance.

### 2026-11-10 — Source-applicable post-exhaustion Lego selection

A profile named in the post-exhaustion family catalogue does not imply it can rewrite current provider bytes. For the exact HTML CSS-class token Lego, only the bounded, freshly computed `candidate.structuralRepairEvidence` from the staged source SHA may authorize selection. When absent, skip this executor and consider other strategies, not a fake `probe-targeted-repair` plan that runtime filters to zero candidates. Keep historical memory separate from current applicability. This is **selection validity**, not publication authority or a relaxation of identity/media requirements.

### 2026-11-10 — Post-exhaustion selection / test oracle parity

Do not restore unconditional `html_class_token_exact_v1` in the planner to satisfy a synthetic fixture. A current source-bound `structuralRepairEvidence` signal is necessary even after exhaustive failed strategies, and a missing source signature must instead select another causal strategy or declare Learning debt. The old tests `brain_llm_advisor_execution_test.py` and `brain_generation_attempt_memory_test.py` were incompatible with this newly required gate. Their positive cases now derive evidence from real retained provider-renderer bytes with the canonical analyzer; negative cases omit evidence and expect a different executor. No fixture proves media playback; generation, compilation, execution, decoded identity and non-regression must still pass independently.

### Availability / Brain fixture category authority — 2026-11-10

Explicit `canonicalSupportedTypes` from current provider manifest (and explicitly trusted independently live source variants) is stronger than provider description wording and Nuvio launch `supportedTypes`. Anime-only `anime,tv` transport aliases do NOT justify testing generic TV titles, even when a description says "TV episodes" or "séries". `scripts/provider_semantics.cjs::inferSupportedTypes` must select the exact canonical categories before `health_check.mjs` builds the rotated availability/deep fixtures. When no current canonical data exists, only then may the conservative description heuristic apply. The availability workflow runs a current-manifest 19-row canonical contract before probing. Neither a corrected fixture nor a single no-request result gives terminal playable-media or title/season/episode/subtitle identity proof; those checks remain mandatory for Brain repair and promotion.

### 2026-11-10 — Bounded causal attempt evidence across Deep → portfolio

Each Deep run's `repair-report.json.rounds[].attempts/rejected/exploration_progress` must reach the persisted portfolio status as a bounded `brain.attemptDiagnostics` array, including provider, round, phase, selected profile, status and *reason code* only. There must be no raw error messages (which may contain network URLs/headers), source text, patch bytes, request parameters or private context. This closes the diagnostic gap in which two different 0-accepted runs (no profile generated vs generated child rejected for playable proof) looked identical at the portfolio boundary. The trace is **evidence only**, never proof authority or permission to publish/override provider scripts.

### Availability-only second-title causal differential (2026-11-10)

The scheduled, diagnostic-only availability probe may spend one additional same-canonical-category real TMDB title ONLY after a first `no_provider_request_observed` without runtime error. This narrows "title-specific absence" vs "generic pre-network/Core gate" before Brain chooses provider network strategy. The retry does not widen `canonicalSupportedTypes`, does not alter Deep/Repair fixtures, does not grant playable-media authority and cannot promote published providers.

### Safe exact staged SHA lineage for Brain attempts (2026-11-10)

Deep records `parent_sha256` and `repair_sha256` on each generated attempt. Production Fast's `sanitized_brain_attempts` must preserve only valid full 64-hex values as `parentSha256` and `repairSha256` beside bounded profile/phase/status/reason; it must never upload raw unaccepted candidate JS. These IDs identify precisely which generated bytes were tested, do not prove playable media or permit publication, and are suitable for duplicate-attempt/negative-memory analysis.


### Runtime verification of zero-request ownership in the 6-topology reverse lab
`brain-multi-topology-reverse.yml` invokes the existing exact-staged-byte
`audit_brain_harness_differential.py` immediately after strict media-type
preflight. If and only if Deep's worker produced zero provider-origin requests
and the production-like Nuvio path *on the same compiled provider digest and
fixture* performs an owned request, label the case harness differential
(infrastructure). Otherwise keep ownership unproven; absence of network is
not a provider parse defect. Safe artifacts record categories, counts, SHA and
test invocation diagnostics without credentials or raw response bodies.
Preserve all six distinct provider families, never mark those probes as media
identity, provider repair, or production publication.


### Pinned cross-repository live Qwen replay with authenticated TMDB preflight
NiakVIO owns the TMDB secret context required to hydrate exact film/TV/anime
fixtures in its native runtime; the Brain repository's unauthenticated runner
cannot be assumed equivalent when Deep issues zero provider requests. A
least-privileged NiakVIO caller now executes the SHA-pinned Brain reusable
workflow, passing only TMDB metadata secrets while checking both exact
checkout refs. Neither repository uploads credentials, response bodies or raw
model patch input. A missing credential is an infrastructure error, not a
provider zero-request status. Publication remains disabled; even a model edit
must pass canonical source apply, materialized bytes, per-fixture baseline →
candidate → confirmation Deep with playable correct media identity, then
independent production acceptance.
