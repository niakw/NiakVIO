#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
changed: list[str] = []


def write(path: str, text: str) -> None:
    p = ROOT / path
    current = p.read_text(encoding="utf-8")
    if current != text:
        p.write_text(text, encoding="utf-8")
        changed.append(path)


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if old not in text:
        if new in text:
            return
        raise AssertionError(f"{path}: anchor missing: {old[:120]!r}")
    if text.count(old) != 1:
        raise AssertionError(f"{path}: anchor count={text.count(old)} for {old[:100]!r}")
    write(path, text.replace(old, new, 1))


def regex_once(path: str, pattern: str, repl: str, flags: int = 0) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    out, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise AssertionError(f"{path}: regex anchor count={count}: {pattern[:120]}")
    write(path, out)


# Finalizer fast fixed-point: current release is 46, provenance intentionally
# retains 50 additional historical rows. Per-current-provider checks above the
# former equality are the authority.
replace_once(
    "scripts/reapply_published_overrides.py",
    '    if len(primary_by_id) != len(rows):\n        return False, "manifest-provenance-provider-count-drift"\n',
    "    # PROVENANCE intentionally retains the 50 archived provider rows beside\n"
    "    # the 46 current manifest providers. The loop above is authoritative for\n"
    "    # the current release: every current provider must exist in provenance and\n"
    "    # satisfy its input/reference/fixed-point contracts. Historical rows are\n"
    "    # knowledge only and must not force the release manifest back to 96 rows.\n",
)

# The two workflows that can mutate a release share one non-cancelling lock.
replace_once(
    ".github/workflows/release-finalize.yml",
    "concurrency:\n  group: provider-v3-release-finalization\n  cancel-in-progress: false",
    "concurrency:\n  group: niakvio-core-release-mutation-main\n  cancel-in-progress: false",
)
replace_once(
    ".github/workflows/domain-refresh.yml",
    "concurrency:\n  group: niakvio-core-domain-refresh-main\n  cancel-in-progress: true",
    "concurrency:\n  group: niakvio-core-release-mutation-main\n  cancel-in-progress: false",
)
replace_once(
    ".github/workflows/release-candidate-validation.yml",
    "      - '.github/triggers/final-validation-20260914.json'",
    "      - '.github/triggers/release-candidate-validation.json'",
)

# ARCHITECTURE: current 46, no synthetic series/movie, actual finalizer transaction.
replace_once("ARCHITECTURE.md", "ni reconstruire les 96 bundles.", "ni reconstruire les 46 bundles courants.")
replace_once("ARCHITECTURE.md", '{"supportedTypes":["anime","tv","series"]}', '{"supportedTypes":["anime","tv"]}')
replace_once("ARCHITECTURE.md", "anime épisodique via transport `tv`/`series` ;", "anime épisodique via transport `tv` ;")
replace_once(
    "ARCHITECTURE.md",
    "Les alias `series`, `show` et équivalents se normalisent vers la forme `tv` du client.",
    "`tv` est l’unique alias de transport synthétique ajouté à un provider anime-only. `series`, `show` et `movie` ne sont jamais ajoutés comme aliases synthétiques.",
)
replace_once(
    "ARCHITECTURE.md",
    "La reconstruction 96/96 appartient à `.github/workflows/provider-v3-reconstruct-all.yml`. Règle d’exploitation courante : **`main` est l’unique cible d’écriture active**. Le workflow peut utiliser un workspace runner et des artifacts éphémères, mais il ne doit pas créer ou maintenir une branche workbench persistante par défaut.",
    "La reconstruction courante **46/46** appartient à `.github/workflows/provider-v3-reconstruct-all.yml`. Elle travaille sur le SHA sélectionné et, lorsqu’un commit de reconstruction est demandé, **refuse toute écriture directe sur `main`** : la cible doit être une branche non-main explicite. Les 50 providers historiques restent des connaissances archivées, jamais des sorties de la reconstruction courante.",
)
architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
new_finalizer = "\n".join([
    "### Finalisation d’une release acceptée",
    "",
    "`.github/workflows/release-finalize.yml` est la transaction explicite de finalisation après acceptation de la pile de validation.",
    "",
    "Contrat :",
    "",
    "- en lancement manuel, l’entrée obligatoire est `expected_sha` ; sur push de son trigger permanent, le SHA d’événement joue le même rôle ;",
    "- le checkout doit correspondre exactement au SHA accepté et une baseline de génération de release est exportée avant toute mutation ;",
    "- les patches providers durables sont réappliqués sur les **46 providers courants**, puis le minimizer NiakVIO est amené à son fixed-point et vérifié ; les projections de manifests sont reconstruites et les générations non référencées sont prunées ;",
    "- les versions provider/manifest/cache/release ne sont synchronisées qu’après stabilisation de cette génération exacte ;",
    "- le transport Hub-46 épinglé, les hashes et l’intégrité de release sont ensuite reconstruits et validés ;",
    "- les commits de génération et de pinning sont préparés localement, puis publiés atomiquement uniquement si `origin/main` pointe toujours sur le SHA de base accepté ; tout mouvement concurrent de `main` fait échouer la transaction ;",
    "- une génération déjà finalisée peut rester un no-op ; aucune version provider/cache ne doit être inventée lorsque les bytes publiés n’ont pas changé.",
    "",
    "Le finalizer n’est ni une autorité de découverte, ni un moteur Learning, ni une reconstruction complète : sa rematérialisation éventuelle est strictement bornée aux patches durables et à la génération courante acceptée, dans la transaction atomique de release.",
    "",
    "## 9. Learning",
])
out, count = re.subn(r"### Finalisation d’une release acceptée\n\n.*?\n\n## 9\. Learning", new_finalizer, architecture, count=1, flags=re.S)
if count != 1:
    raise AssertionError(f"ARCHITECTURE.md: finalizer section count={count}")
write("ARCHITECTURE.md", out)
replace_once(
    "ARCHITECTURE.md",
    "Anime canonique peut être lancé via `anime/tv/series` sans devenir movie/tv canonique.",
    "Anime canonique peut être lancé via `anime/tv` sans devenir movie/tv canonique ; aucun alias synthétique `series` ou `movie` n’est publié.",
)

# VALIDATION current/archive split and transport projection.
replace_once(
    "VALIDATION.md",
    "Le catalogue reste **96 providers**. La campagne d’acceptation native finale utilise actuellement le scope physique **Hub-46** dérivé de `automation/evidence/hub-lab-matrix-46.json` et transporté par `native-hub46/manifest.json`. Les 50 autres lignes ne disparaissent pas du catalogue : elles restent séparées du dénominateur physique du Lab. Le nombre de routes est calculé depuis le scope courant et ses `supportedTypes` ; il ne doit pas être recopié comme constante historique.",
    "Le catalogue exécutable courant contient **46 providers**. La campagne d’acceptation native finale utilise ce scope physique Hub-46 dérivé de `automation/evidence/hub-lab-matrix-46.json` et transporté par `native-hub46/manifest.json`. Les **50 providers historiques** restent archivés comme connaissance/provenance hors du manifest courant ; ils ne sont pas des lignes OFF du catalogue exécutable. Le nombre de routes est calculé depuis le scope courant et ses `supportedTypes` ; il ne doit pas être recopié comme constante historique.",
)
replace_once("VALIDATION.md", "supportedTypes = [anime, tv, series]", "supportedTypes = [anime, tv]")
replace_once(
    "VALIDATION.md",
    "Les voies `anime`, `tv` et `series` restent des lancements compatibles sans élargir la capacité canonique ; `movie` n’est exposé que s’il est canonique.",
    "Les voies `anime` et `tv` restent des lancements compatibles sans élargir la capacité canonique. `series` n’est jamais synthétisé et `movie` n’est exposé que s’il est canonique.",
)
replace_once("VALIDATION.md", "« les 96 providers ont renvoyé des streams »", "« les 46 providers courants ont renvoyé des streams »")
replace_once(
    "VALIDATION.md",
    "activation 46/50, projections, versions cache-safe, hashes et release integrity restent synchronisés ;",
    "scope courant 46, archive historique 50, projections, versions cache-safe, hashes et release integrity restent correctement séparés et synchronisés ;",
)

# README EN/FR transport and finalizer wording.
replace_once("README.md", '"supportedTypes": ["anime", "tv", "series"]', '"supportedTypes": ["anime", "tv"]')
replace_once(
    "README.md",
    "`tv` and `series` are episodic transport aliases for anime. `movie` appears only when the provider declares canonical movie capability; transport aliases never widen semantic capability.",
    "`tv` is the episodic launch-compatibility alias for anime. NiakVIO does not synthesize `series`; `movie` appears only when the provider declares canonical movie capability. Transport aliases never widen semantic capability.",
)
replace_once(
    "README.md",
    "The accepted release is finalized explicitly through `release-finalize.yml`. It checks out the exact accepted SHA, uses either an explicit baseline or the oldest commit in the current release-version generation, and then synchronizes provider/manifest/cache/release versions, manifest projections, hashes and integrity metadata as one release transaction. It does **not** repair or reconstruct provider bytes.",
    "The accepted release is finalized explicitly through `release-finalize.yml`. It checks out and enforces the exact accepted `expected_sha`, exports the current release-generation baseline, reapplies durable patches to the 46 current providers, drives the NiakVIO minimizer to a verified fixed point, rebuilds projections, synchronizes provider/manifest/cache/release versions, then rebuilds the pinned Hub-46 transport and integrity hashes. The locally staged generation is published only by compare-and-swap if `main` has not moved. This is bounded release rematerialization, not discovery, Learning or full provider reconstruction.",
)
replace_once("README.fr.md", '"supportedTypes": ["anime", "tv", "series"]', '"supportedTypes": ["anime", "tv"]')
replace_once(
    "README.fr.md",
    "`tv` et `series` sont les alias de transport épisodique de l’anime. `movie` n’est exposé que si le provider déclare réellement une capacité canonique `movie` ; les alias de transport n’élargissent jamais la capacité sémantique.",
    "`tv` est l’alias de compatibilité de lancement épisodique de l’anime. NiakVIO ne synthétise pas `series` ; `movie` n’est exposé que si le provider déclare réellement une capacité canonique `movie`. Les alias de transport n’élargissent jamais la capacité sémantique.",
)
replace_once(
    "README.fr.md",
    "La release acceptée est finalisée explicitement via `release-finalize.yml`. Le workflow checkout le SHA accepté exact, utilise soit une baseline explicite soit le commit le plus ancien de la génération de version courante, puis synchronise versions provider/manifest/cache/release, projections des manifests, hashes et métadonnées d’intégrité dans une seule transaction de release. Il ne répare ni ne reconstruit les bytes providers.",
    "La release acceptée est finalisée explicitement via `release-finalize.yml`. Le workflow checkout et impose le `expected_sha` accepté exact, exporte la baseline de génération courante, réapplique les patches durables aux 46 providers courants, amène le minimizer NiakVIO à un fixed-point vérifié, reconstruit les projections, synchronise les versions provider/manifest/cache/release puis reconstruit le transport Hub-46 épinglé et les hashes d’intégrité. La génération préparée localement n’est publiée que par compare-and-swap si `main` n’a pas bougé. C’est une rematérialisation de release bornée, pas de la découverte, du Learning ou une reconstruction complète.",
)

# CONTRIBUTING / INSTALL / HEALTH.
replace_once("CONTRIBUTING.md", "supportedTypes = [anime, tv, series]", "supportedTypes = [anime, tv]")
replace_once(
    "CONTRIBUTING.md",
    "`tv` and `series` are episodic transport aliases. `movie` is present only for providers with canonical movie capability; aliases never authorize additional semantic content.",
    "`tv` is the episodic launch-compatibility alias. Do not synthesize `series`; `movie` is present only for providers with canonical movie capability. Aliases never authorize additional semantic content.",
)
replace_once("INSTALL.md", "La reconstruction forcée 96/96", "La reconstruction forcée 46/46")
replace_once(
    "INSTALL.md",
    "Le corpus de référence est versionné dans `.github/triggers/nuvio-client-lab.json` et couvre Interstellar, Breaking Bad S01E01 et Jujutsu Kaisen S01E01. La surface d'acceptation est exactement cinq Labs : TV Android, Mobile Android, Mobile iOS, Desktop macOS et Desktop Windows. Les Labs consomment les bytes NiakVIO exacts et les clients Nuvio officiels sans réparer, reconstruire ou réécrire les providers.",
    "Le corpus ordinaire est piloté par `.github/triggers/rotating-popular-corpus.json` ; `.github/triggers/nuvio-client-lab.json` conserve les fixtures ciblées/historiques de régression. La surface d'acceptation est exactement cinq Labs : TV Android, Mobile Android, Mobile iOS, Desktop macOS et Desktop Windows. Les Labs consomment les bytes NiakVIO exacts et les clients Nuvio officiels sans réparer, reconstruire ou réécrire les providers.",
)
replace_once("HEALTH-CHECK.md", "transport = anime + tv + series", "transport = anime + tv")

# Durable media-type/transport documentation rewritten from the actual invariant.
media_contract = "\n".join([
    "# NiakVIO media type / transport contract",
    "",
    "This is the durable contract separating **canonical content capability** from the **Nuvio launch surface**.",
    "",
    "## Core rule",
    "",
    "Provider selection is based on canonical semantic capability first. Transport compatibility must never widen that capability.",
    "",
    "| Canonical provider capability | Published `supportedTypes` |",
    "| --- | --- |",
    "| `movie` | `movie` |",
    "| `tv` | `tv` |",
    "| `movie + tv` | `movie + tv` |",
    "| anime-only (`anime`) | `anime + tv` |",
    "",
    "For an anime-only provider, `canonicalSupportedTypes` remains exactly `[\"anime\"]` while `supportedTypes` is exactly `[\"anime\", \"tv\"]`.",
    "",
    "`tv` is the only synthetic compatibility alias NiakVIO adds for anime-only providers. **Do not synthesize `series`, `show` or `movie`.** In particular, an anime-only provider does not gain a movie lane merely because a work is theatrical or feature-length. `movie` is published only when the provider has canonical movie capability.",
    "",
    "## Mandatory order",
    "",
    "1. Resolve trusted work identity and semantic type (`movie`, `tv`, `anime`).",
    "2. Gate providers from canonical capability / `canonicalSupportedTypes`.",
    "3. Project only the allowed Nuvio launch compatibility for the selected provider.",
    "4. Invoke the provider on that bounded surface.",
    "5. Keep semantic identity separate from launch transport throughout evidence and output processing.",
    "",
    "A launch alias never becomes permission to search or return a different semantic catalogue.",
    "",
    "## Manifest fields",
    "",
    "- `canonicalSupportedTypes` is semantic/provider-selection authority whenever transport compatibility differs from semantics.",
    "- `supportedTypes` is the Nuvio launch surface.",
    "- Current manifests accept only `movie`, `tv` and `anime` values.",
    "- Anime-only projection is `[\"anime\", \"tv\"]`; `series` is not part of the published contract.",
    "- `movie` transport is equivalent to canonical movie capability: no artificial anime-to-movie promotion is allowed.",
    "",
    "## Recognition and runtime gate",
    "",
    "Trusted metadata may refine a presented work into canonical `anime`, but provider compatibility is checked before provider-network work whenever the necessary identity is already known. Animation alone is not sufficient to classify ordinary Western animation as anime.",
    "",
    "A provider that is incompatible with the canonical work returns no result; it must not fall back to an arbitrary search on a transport alias.",
    "",
    "## Labs / evidence",
    "",
    "Native evidence keeps the two concepts separate:",
    "",
    "- logical/canonical type: semantic identity used for provider eligibility;",
    "- request/launch type: the bounded surface actually exercised by Nuvio.",
    "",
    "Coverage is derived from the current 46-provider manifest. The 50 archived historical providers remain knowledge/provenance only and are not injected into the current transport denominator.",
    "",
    "## Implementation authority",
    "",
    "Relevant surfaces include `scripts/materialize_provider_v3_all.py`, `scripts/enforce_provider_v3_semantic_transport_contract_v5.py`, `scripts/reapply_published_overrides.py`, `engine_v2/src/provider-catalog.mjs`, `automation/provider-v3-architecture.json` and the native media-type regressions.",
    "",
    "## Regression floor",
    "",
    "Tests must prove all of the following:",
    "",
    "- anime-only canonical capability stays `[\"anime\"]`;",
    "- anime-only launch projection stays `[\"anime\", \"tv\"]`;",
    "- no `series` synthesis;",
    "- no synthetic `movie` lane for anime-only providers;",
    "- canonical movie capability and published movie transport remain equivalent;",
    "- capability gating occurs before provider-network work when identity is already available.",
    "",
])
write("docs/media-type-transport-contract.md", media_contract)

# Prevent the documentation upgrader from reintroducing the retired 96/series model.
p = ROOT / "scripts/upgrade_native_lab_docs_v1.py"
t = p.read_text(encoding="utf-8")
replacements = {
    "The maintained catalogue remains **96 Provider Objects**. Final native acceptance uses the ": "The current executable catalogue contains **46 Provider Objects**. Final native acceptance uses the ",
    'explicit physical **Hub-46** scope from `automation/evidence/hub-lab-matrix-46.json`; disabled "\n        "or out-of-scope catalogue rows remain visible maintenance debt and are not silently deleted.': 'explicit physical **Hub-46** scope from `automation/evidence/hub-lab-matrix-46.json`; the 50 historical "\n        "providers remain archived knowledge/provenance outside the current manifest.',
    "Le catalogue maintenu reste **96 Provider Objects**. L’acceptation native finale utilise le ": "Le catalogue exécutable courant contient **46 Provider Objects**. L’acceptation native finale utilise le ",
    'scope physique explicite **Hub-46** défini par `automation/evidence/hub-lab-matrix-46.json` ; "\n        "les lignes désactivées ou hors scope restent visibles comme dette de maintenance et ne sont pas "\n        "supprimées artificiellement du catalogue.': 'scope physique explicite **Hub-46** défini par `automation/evidence/hub-lab-matrix-46.json` ; les 50 "\n        "providers historiques restent archivés comme connaissance/provenance hors du manifest courant.',
    "Le catalogue reste **96 providers**. La campagne d’acceptation native finale utilise actuellement ": "Le catalogue exécutable courant contient **46 providers**. La campagne d’acceptation native finale utilise ",
    'par `native-hub46/manifest.json`. Les 50 autres lignes ne disparaissent pas du catalogue : elles "\n        "restent séparées du dénominateur physique du Lab.': 'par `native-hub46/manifest.json`. Les 50 providers historiques restent archivés hors du manifest courant "\n        "et du dénominateur physique du Lab.',
}
for old, new in replacements.items():
    if old not in t:
        raise AssertionError(f"scripts/upgrade_native_lab_docs_v1.py: missing anchor {old[:90]!r}")
    t = t.replace(old, new, 1)
write("scripts/upgrade_native_lab_docs_v1.py", t)

replace_once(
    "engine_v2/src/provider-catalog.mjs",
    "// Nuvio may transport episodic anime as TV/series. Movie is never a",
    "// Nuvio may transport episodic anime as TV. Movie is never a",
)

# Lock release-mutator serialization in the workflow ownership regression.
replace_once(
    "tests/provider_v3_workflow_ownership_test.py",
    'domain=(ROOT/".github/workflows/domain-refresh.yml").read_text(encoding="utf-8")\nnonreg=',
    'domain=(ROOT/".github/workflows/domain-refresh.yml").read_text(encoding="utf-8")\nfinalizer=(ROOT/".github/workflows/release-finalize.yml").read_text(encoding="utf-8")\nnonreg=',
)
replace_once(
    "tests/provider_v3_workflow_ownership_test.py",
    'assert "requires 96/96 state" not in transaction\n',
    'assert "requires 96/96 state" not in transaction\nassert "group: niakvio-core-release-mutation-main" in domain\nassert "cancel-in-progress: false" in domain\nassert "group: niakvio-core-release-mutation-main" in finalizer\nassert "cancel-in-progress: false" in finalizer\n',
)

# Remove the dated trigger after its only workflow reference was migrated.
dated = ROOT / ".github/triggers/final-validation-20260914.json"
if dated.exists():
    dated.unlink()
    changed.append(str(dated.relative_to(ROOT)))

# Conservative trigger hygiene: only proof/diagnostic/date-named trigger files,
# and only when no tracked text file references their full path or basename.
tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()


def references(candidate: Path) -> list[str]:
    rel = candidate.relative_to(ROOT).as_posix()
    base = candidate.name
    hits: list[str] = []
    for name in tracked:
        if name in {rel, ".github/workflows/maintenance-final-hygiene-20260914.yml", ".github/scripts/final_hygiene_20260914.py"}:
            continue
        f = ROOT / name
        if not f.is_file():
            continue
        try:
            data = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if rel in data or base in data:
            hits.append(name)
    return hits


deleted_orphans: list[str] = []
trigger_dir = ROOT / ".github/triggers"
for candidate in sorted(trigger_dir.iterdir()):
    if not candidate.is_file():
        continue
    name = candidate.name.casefold()
    if not (re.search(r"20\d{6}", name) or "proof" in name or "diagnostic" in name):
        continue
    refs = references(candidate)
    if not refs:
        rel = candidate.relative_to(ROOT).as_posix()
        candidate.unlink()
        deleted_orphans.append(rel)
        changed.append(rel)

print("ORPHAN_TRIGGER_DELETED " + (",".join(deleted_orphans) if deleted_orphans else "none"))
print("PATCHED_FILES " + ",".join(dict.fromkeys(changed)))
