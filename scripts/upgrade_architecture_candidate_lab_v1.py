#!/usr/bin/env python3
"""Reconcile architecture docs with isolated candidate repair and adaptive Hub-46 Labs."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "ARCHITECTURE.md"
MARKER = "NIAKVIO_CANDIDATE_HUB46_ARCH_V1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected 1 anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    original = text

    old_rebuild = (
        "La reconstruction 96/96 appartient à `.github/workflows/provider-v3-reconstruct-all.yml`. "
        "Règle d’exploitation courante : **`main` est l’unique cible d’écriture active**. Le workflow "
        "peut utiliser un workspace runner et des artifacts éphémères, mais il ne doit pas créer ou "
        "maintenir une branche workbench persistante par défaut.\n"
    )
    new_rebuild = (
        f"<!-- {MARKER} -->\n"
        "La reconstruction 96/96 appartient à `.github/workflows/provider-v3-reconstruct-all.yml`. "
        "`main` reste la branche de **production/publication**. Une campagne de réparation ou de "
        "certification peut travailler sur une **branche candidate temporaire explicitement nommée**, "
        "à condition que `main` reste intact jusqu’à acceptation du SHA candidat. Une telle branche "
        "candidate est un espace de validation, jamais une seconde autorité de publication. Le workflow "
        "peut utiliser un workspace runner et des artifacts éphémères ; il ne doit pas créer ou maintenir "
        "un workbench persistant implicite.\n"
    )
    text = replace_once(text, old_rebuild, new_rebuild, "reconstruction branch policy")

    old_labs = (
        "Règles :\n\n"
        "- chaque device est une preuve indépendante ;\n"
        "- la matrice de routes est dérivée du manifest courant, pas d’un nombre figé dans la documentation ;\n"
        "- `canonicalSupportedTypes` porte la sémantique, `supportedTypes` la surface de lancement testée ;\n"
        "- providers désactivés restent auditables ;\n"
        "- les Labs utilisent les bytes NiakVIO candidats exacts ;\n"
        "- **aucun Lab ne patch NuvioTV/NuvioMobile/NuvioDesktop pour contourner un bug upstream** ;\n"
        "- un bug de compilation, packaging, runtime, QuickJS ou player upstream reste une preuve externe rouge ;\n"
        "- le plumbing de test est autorisé uniquement s’il expose le chemin officiel sans changer le comportement production ni réparer le défaut observé.\n\n"
        "Le trigger commun est `.github/triggers/full-native-lab-validation.json`.\n"
    )
    new_labs = (
        "Règles :\n\n"
        "- chaque device est une preuve indépendante ;\n"
        "- le catalogue reste 96 Provider Objects, tandis que la campagne d’acceptation native physique courante utilise le scope explicite **Hub-46** de `automation/evidence/hub-lab-matrix-46.json` et son transport `native-hub46/manifest.json` ;\n"
        "- la matrice de routes est dérivée du scope/manifest courant et de ses `supportedTypes`, pas d’un nombre historique de routes figé ;\n"
        "- le corpus ordinaire possède exactement trois réserves globales récentes `movie` / `tv` / `anime` dans `.github/triggers/rotating-popular-corpus.json` ;\n"
        "- un Lab démarre avec **1 movie + 1 TV + 1 anime** ; les autres œuvres sont une réserve adaptative, pas un batch fixe ;\n"
        "- seul un résultat propre `0 streams` autorise le provider/lane à passer à une autre œuvre de la même réserve ; positif = arrêt, erreur/timeout/transport/player/identité = arrêt + preuve rouge ;\n"
        "- `canonicalSupportedTypes` porte la sémantique, `supportedTypes` la surface de lancement testée ;\n"
        "- providers désactivés restent auditables ;\n"
        "- les Labs utilisent les bytes NiakVIO candidats exacts ;\n"
        "- **aucun Lab ne patch NuvioTV/NuvioMobile/NuvioDesktop pour contourner un bug upstream** ;\n"
        "- un bug de compilation, packaging, runtime, QuickJS ou player upstream reste une preuve externe rouge ;\n"
        "- le plumbing de test est autorisé uniquement s’il expose le chemin officiel sans changer le comportement production ni réparer le défaut observé.\n\n"
        "Le trigger commun est `.github/triggers/full-native-lab-validation.json` ; sa référence de release doit être régénérée sur le SHA candidat gelé avant la certification finale.\n"
    )
    text = replace_once(text, old_labs, new_labs, "native labs contract")

    old_branch = (
        "- **`main` = production et unique cible d’écriture active pour le travail courant** ;\n"
        "- ne pas créer de nouvelle branche workbench/clean pour les corrections en cours ;\n"
    )
    new_branch = (
        "- **`main` = production et cible de publication** ; une branche candidate temporaire explicitement active peut porter les réparations/certifications tant qu’aucune mutation n’est publiée sur `main` avant acceptation ;\n"
        "- ne pas créer de branche workbench/clean persistante implicite ; une branche candidate explicite doit avoir un périmètre, un SHA gelé de certification et une fin de vie claire ;\n"
    )
    text = replace_once(text, old_branch, new_branch, "publication branch policy")

    PATH.write_text(text, encoding="utf-8")
    print(f"CANDIDATE_HUB46_ARCH_V1_OK changed={str(text != original).lower()} main_production=true candidate_branch_explicit=true hub46=true adaptive_1_1_1=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
