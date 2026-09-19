#!/usr/bin/env python3
"""Document the current global-catalogue / physical-Lab sampling contract."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "NIAKVIO_NATIVE_ADAPTIVE_LAB_DOCS_V1"


def replace_once(path: Path, old: str, new: str, label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    if text.count(old) != 1:
        raise AssertionError(f"{label}: expected one anchor, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


def main() -> int:
    changed: list[str] = []

    en = ROOT / "README.md"
    en_anchor = (
        "A Desktop result does not automatically count as Android/iOS/TV evidence. "
        "Labs consume official clients as-is: an upstream compile, dependency, packaging, "
        "runtime, player or QuickJS failure stays visible instead of being patched inside "
        "NiakVIO merely to manufacture green CI.\n\n---\n"
    )
    en_block = (
        "A Desktop result does not automatically count as Android/iOS/TV evidence. "
        "Labs consume official clients as-is: an upstream compile, dependency, packaging, "
        "runtime, player or QuickJS failure stays visible instead of being patched inside "
        "NiakVIO merely to manufacture green CI.\n\n"
        f"<!-- {MARKER} -->\n"
        "### Native acceptance scope and adaptive sampling\n\n"
        "The current executable catalogue contains **46 Provider Objects**. Final native acceptance uses the "
        "explicit physical **Hub-46** scope from `automation/evidence/hub-lab-matrix-46.json`; the 50 historical "
        "providers remain archived knowledge/provenance outside the current manifest.\n\n"
        "The ordinary Lab corpus is not a fixed batch. `.github/triggers/rotating-popular-corpus.json` "
        "owns exactly three recent global reserves — **movie, TV and anime** — currently 32 works per "
        "lane, constrained to 2010 through the previous calendar year. A native campaign starts with "
        "exactly **1 movie + 1 TV episode + 1 anime episode**. A provider/lane advances to another work "
        "from the same reserve only after a clean `0 streams` result. Positive proof stops rotation; "
        "runtime/load/timeout/transport/player/identity failures stop and remain visible instead of being "
        "rotated away.\n\n"
        "Historical fixtures in `.github/triggers/nuvio-client-lab.json` remain available for targeted "
        "regression diagnostics, but they are not the ordinary global sampling authority.\n\n---\n"
    )
    if replace_once(en, en_anchor, en_block, "README EN native acceptance section"):
        changed.append(str(en.relative_to(ROOT)))

    fr = ROOT / "README.fr.md"
    fr_anchor = (
        "Une preuve Desktop ne vaut jamais automatiquement preuve Android/iOS/TV. Les Labs consomment "
        "les clients officiels tels quels : une erreur upstream de compilation, dépendance, packaging, "
        "runtime, player ou QuickJS reste visible au lieu d’être patchée dans NiakVIO uniquement pour "
        "fabriquer une CI verte.\n\n---\n"
    )
    fr_block = (
        "Une preuve Desktop ne vaut jamais automatiquement preuve Android/iOS/TV. Les Labs consomment "
        "les clients officiels tels quels : une erreur upstream de compilation, dépendance, packaging, "
        "runtime, player ou QuickJS reste visible au lieu d’être patchée dans NiakVIO uniquement pour "
        "fabriquer une CI verte.\n\n"
        f"<!-- {MARKER} -->\n"
        "### Scope d’acceptation native et échantillonnage adaptatif\n\n"
        "Le catalogue exécutable courant contient **46 Provider Objects**. L’acceptation native finale utilise le "
        "scope physique explicite **Hub-46** défini par `automation/evidence/hub-lab-matrix-46.json` ; les 50 "
        "providers historiques restent archivés comme connaissance/provenance hors du manifest courant.\n\n"
        "Le corpus Lab ordinaire n’est pas un batch fixe. `.github/triggers/rotating-popular-corpus.json` "
        "porte exactement trois réserves globales récentes — **movie, TV et anime** — actuellement 32 "
        "œuvres par lane, bornées de 2010 à l’année civile précédente. Une campagne native démarre avec "
        "exactement **1 film + 1 épisode TV + 1 épisode anime**. Un provider/lane ne passe à une autre "
        "œuvre de la même réserve qu’après un résultat propre `0 streams`. Une preuve positive arrête la "
        "rotation ; une erreur runtime/load/timeout/transport/player/identité s’arrête et reste visible au "
        "lieu d’être masquée par un changement de fixture.\n\n"
        "Les fixtures historiques de `.github/triggers/nuvio-client-lab.json` restent disponibles pour les "
        "diagnostics de régression ciblés, mais ne sont plus l’autorité d’échantillonnage global ordinaire.\n\n---\n"
    )
    if replace_once(fr, fr_anchor, fr_block, "README FR native acceptance section"):
        changed.append(str(fr.relative_to(ROOT)))

    validation = ROOT / "VALIDATION.md"
    fixture_old = (
        "La liste des fixtures est centralisée dans `.github/triggers/nuvio-client-lab.json`. "
        "Le trigger de validation complète est `.github/triggers/full-native-lab-validation.json`.\n"
    )
    fixture_new = (
        f"<!-- {MARKER} -->\n"
        "Le corpus global ordinaire est défini par `.github/triggers/rotating-popular-corpus.json` : "
        "exactement trois réserves `movie`, `tv`, `anime`, actuellement 32 œuvres chacune, de 2010 à "
        "l’année civile précédente. `.github/triggers/nuvio-client-lab.json` conserve les fixtures de "
        "régression ciblées/historiques. Le trigger de validation complète reste "
        "`.github/triggers/full-native-lab-validation.json`.\n"
    )
    if replace_once(validation, fixture_old, fixture_new, "VALIDATION corpus authority"):
        changed.append(str(validation.relative_to(ROOT)))

    coverage_old = (
        "Le catalogue reste **96 providers**. Le nombre de routes natives est calculé depuis le "
        "`manifest.json` courant et ses `supportedTypes` ; il ne doit pas être recopié comme constante "
        "historique dans la documentation.\n"
    )
    coverage_new = (
        "Le catalogue exécutable courant contient **46 providers**. La campagne d’acceptation native finale utilise "
        "le scope physique **Hub-46** dérivé de `automation/evidence/hub-lab-matrix-46.json` et transporté "
        "par `native-hub46/manifest.json`. Les 50 providers historiques restent archivés hors du manifest courant "
        "et du dénominateur physique du Lab. Le nombre de routes est calculé depuis le scope "
        "courant et ses `supportedTypes` ; il ne doit pas être recopié comme constante historique.\n"
    )
    if replace_once(validation, coverage_old, coverage_new, "VALIDATION 96 vs Hub46"):
        if str(validation.relative_to(ROOT)) not in changed:
            changed.append(str(validation.relative_to(ROOT)))

    native_anchor = (
        "Chaque provider est borné individuellement ; un timeout devient une observation, pas une boucle "
        "infinie de retry.\n\n## Cycle Provider v3\n"
    )
    native_block = (
        "Chaque provider est borné individuellement ; un timeout devient une observation, pas une boucle "
        "infinie de retry.\n\n"
        "### Rotation adaptative des œuvres\n\n"
        "Une exécution native commence par une seule œuvre de chaque réserve globale : **1 movie + 1 TV + "
        "1 anime**. Le reste des 32 œuvres/lane est une réserve, pas un batch. Seul un provider/lane qui a "
        "terminé normalement avec `0 streams` avance vers une autre œuvre de la même lane. Dès qu’un flux "
        "positif est prouvé, ce provider/lane sort de la rotation. Une erreur technique, un timeout, un "
        "échec de chargement/player/transport ou une contradiction d’identité ne déclenche jamais une "
        "rotation destinée à cacher l’erreur.\n\n"
        "Le gate final doit agréger ces essais successifs par provider/lane : `FULL`, `PARTIAL`, `RESAMPLE` "
        "et `ZERO` décrivent des preuves distinctes ; un clean miss de catalogue n’est pas une régression.\n\n"
        "## Cycle Provider v3\n"
    )
    if replace_once(validation, native_anchor, native_block, "VALIDATION adaptive rotation"):
        if str(validation.relative_to(ROOT)) not in changed:
            changed.append(str(validation.relative_to(ROOT)))

    print("NATIVE_ADAPTIVE_LAB_DOCS_V1_OK changed=" + (",".join(changed) if changed else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
