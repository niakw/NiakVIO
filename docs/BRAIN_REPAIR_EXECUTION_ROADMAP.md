# NiakVIO — feuille de route Brain-first vers les réparations réellement validées

> Baseline vérifiée le 19 novembre 2026. Ce document est une trajectoire avec portes de sortie mesurables, pas une déclaration de réparation ni une autorité de publication.

## Baseline et preuves

- Census le plus récent inspecté : `44609268223`, source SHA `0251d7dae8dd4b2e4d51ca2f2cb52862f64c09a9` : 111 providers, 5 `FULL OK`, 1 `PARTIAL OK`, 11 dans la `repairQueue`. Le census n'est **pas** une validation du HEAD plus récent.
- Fast Brain `44602295350` sur `20b9116e...` : 10 sélectionnés, 4 vagues sur 6, budget épuisé, 0 candidat/repair accepté, 0 validé, 5 progressions exploratoires précoces non promues. Le workflow vert atteste son exécution et la conservation des observations, pas des providers réparés.
- Family-frontier scheduler implémenté ultérieurement : un oracle par famille causale en absence de compétence trusted, puis fanout conditionné à une compétence validée (capability et failure family). Le test de 1000 providers prouve l'ordonnancement synthétique seulement.
- Native French-Manga `44567912230` : même master HLS signé observé d'abord 200 puis 403, résultat provider zéro et absence de lecture décodée prouvée. Le replay redacted `44600919814` récupère la signature. Le Brain route `llm_diagnose`, layer Core, mais `modelExecuted=false` et aucune mutation validée. Ce diagnostic est une hypothèse de causalité, pas une preuve que le Core en est la cause.
- `.github/workflows/brain-android-tv-emulator-feedback.yml` se limite explicitement à une route read-only diagnostic. `provider-fast-repair.yml` contraint le résultat aux mutations provider-locales : une observation attribuée au Core ne devient donc pas automatiquement une réparation du Core via ce chemin.
- Deuxième campagne family-frontier `44609250980` et replay TV `44610510286` étaient encore en cours au contrôle initial. Vérifier leurs verdicts par SHA exact avant mise à jour de ce document.

## Principes de planification

1. Un gate est acquis uniquement si la preuve et son SHA sont persistés. `FULL OK`, `CHAIN REACHED`, `CANDIDATE OK`, correction générée, bytes matérialisés et lecture décodée sont des états distincts.
2. Le choix de l'expérience dépend du **niveau causal** (Core, Brain, pipeline, provider, réseau, harness, client), non du seul nom du provider.
3. Dès qu'un profil exécuté n'apporte aucun gain de frontière vérifiable, il doit produire un négatif fingerprinté ; ne pas dépenser une nouvelle vague sur la même mutation/contexte sans hypothèse réellement nouvelle ou variation d'environnement démontrée.
4. Pas de fanout à 10, 60 ou 1000 providers sans un mécanisme représentatif prouvé ; chaque sibling reste soumis à ses propres gates current-byte, identité, terminal media et non-régression.
5. Les cases WAF, DNS, backend indisponible et environnement inconclusif restent hors mutation provider tant que la cause n'est pas prouvée.

## Priorités et portes de sortie

| Priorité | Livrable réel | Preuve de sortie obligatoire |
| --- | --- | --- |
| **P0 — arrêter la fausse progression** | Faire produire à chaque run un bilan unique par cause et famille : candidats générés/compilés/appliqués/rematérialisés/testés/validés, temps consommé, expériences nouvelles vs déjà négatives, statut exact du SHA et raison de non-progression. Empêcher l'amplification sans gain et conserver la dette hors de Learning si le sibling n'a pas été tenté. | Test de non-répétition sur mémoire négative réelle + run sur source actuelle ; une exécution avec 0 validé est enregistrée comme **0 réparation** et les frères non visités ne sont pas comptés comme échecs. |
| **P1 — fermer le circuit Brain ↔ Core/ProviderBase** | Prendre une observation native source-pinned, déterminer le propriétaire exact du doublon HLS (trace d'appel partagée), produire via Brain une proposition exécutable ciblant ce propriétaire, appliquer sur les vrais bytes, contrôler les fetch du master et les playlists enfants, puis retester avec le client officiel. Le routage `llm_diagnose` seul est insuffisant. | Une expérience Brain réellement générée, compilée, appliquée et matérialisée ; trace prouvant disparition de la cause observée **sans** désactiver la validation ; stream correct décodé (vidéo/audio/épisode) + non-régression. Si Core innocenté, réattribuer à la bonne couche avant correction. |
| **P2 — premier succès de réparation intégral** | Choisir l'oracle ayant le meilleur niveau de preuve parmi `french-manga`, `corsflix`, `nakios`, `sadisflix` (réévaluer après runs natifs). Corriger la vraie rupture, pas son symptôme ni un seul fixture. | Baseline cassée reproduite ; mutation Brain → compilation → sélection → application → rematérialisation SHA → media terminal décodé et identité correcte → non-régression → expérience positive durable + statut réconcilié au census sur la nouvelle source. |
| **P3 — couverture des familles** | Valider au moins un oracle pour terminal extraction, recherche/épisodes/identité, et mixed embed/transport seulement quand le transport est causalement provider-owned. Apprendre le nouveau Bloc/profil et la signature qui le déclenche. | Pour chaque famille : positif identifié, négatifs conservés, changement des bytes observé, test natif et régression d'un sibling distinct. Aucun transfert automatique par simple nom de domaine/statut. |
| **P4 — vague de cohortes** | Élargir à toute `repairQueue` courante, puis aux catalogues Global/VF avec rétention 10 JS et conservation des quatre manifests ; agents/workers isolés et fusion déterministe pour éviter des courses mémoire/publication. | Compteurs séparés `FULL OK`, `PARTIAL OK`, `CHAIN REACHED`, `blocked`, `disabled` par manifeste ; aucune promotion sans flux réel. La progression est le nombre de providers validés sur des nouveaux SHAs, pas les tentatives. |
| **P5 — échelle 600–1000+** | Généraliser l'ordonnancement des familles et Learning distribuée **après** P2/P3, avec coût/heure et taux de succès par famille, déclenchement incrémental par nouvelles signatures, barrières de persistance et contrôle de régression. | Test de charge du pipeline, conservation de la mémoire, absence de course et démonstration de réparation sur familles inconnues avec preuves jouables. Le test synthétique actuel de 1000 items ne suffit pas. |

## Cadence de décision

- Chaque campagne publie un **tableau de sortie** : `runId`, `sourceSha`, `currentMainSha`, `selected`, `processed`, `generated`, `compiled`, `applied`, `materialized`, `nativeValidated`, `accepted`, `newNegativeFingerprints`, `elapsedSeconds`, `owner`, `nextExperiment`. Si un compteur n'est pas instrumenté, indiquer `unavailable`, jamais zéro inventé.
- Quand 0 candidat est accepté, ne relancer le même profil que si la nouvelle observation ou le fingerprint montre une différence causale testable. Sinon : escalade Brain génération/Bloc, Core/harness ou transport selon le niveau responsable.
- Pendant l'exécution native et les CI, vérifier en parallèle code path, traces, artefacts, bytes et docs ; ne pas empiler de nouveaux jobs coûteux avec SHAs anciens.
- `MEMORY.md` et les banques Brain retiennent les causes et les expériences ; ce document reste le contrat de décision. Les nouveaux résultats doivent mettre à jour explicitement les gates P0–P5 sans réécrire l'histoire.

**Prochaine action déterminante :** faire aboutir **P1 et P2**. Tant que le pipeline ne sait pas transformer une preuve native en correction Brain appliquée et lue, augmenter de 10 à 1000 providers ne résout pas le problème.
