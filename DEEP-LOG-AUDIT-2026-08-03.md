# Audit complet du deep du 3 août 2026

Cette synthèse est dérivée des rapports structurés produits par le job terminé. Les captures très compressées servent à confirmer l’ordre des étapes ; les JSON conservent les lignes et statuts exploitables sans perte.

## Résultat observé avant correction

- Variantes testées : **194**
- Statuts finaux : `healthy`=4, `reachable`=45, `blocked`=0, `degraded`=0, `no_streams`=143, `provider_unreachable`=0, `runtime_error`=2, `unavailable`=0, `excluded`=0
- Préflight DNS : `inconclusive`=164, `no_provider_domain_detected`=30
- Étapes diagnostiques : `content_not_found`=678, `content_not_found_or_parser_failed`=277, `provider_reachable_http_error`=188, `search_or_route_obsolete`=51, `provider_unreachable_or_runtime_error`=23, `stream_valid`=6

## Runtime errors visibles dans le job

- Résultat final : **Peachify** reste en `runtime_error` dans le deep ; **Peachify** et **Wookafr** apparaissent en `runtime_error` dans le contrôle d’availability.
- Repair round 1 : **8 runtime errors** — `gowaru:animesama-co`, `gowaru:flemmix`, `gowaru:french-manga`, `gowaru:voiranime-homes`, `gowaru:mugiwarastream`, `gowaru:sekai`, `gowaru:voiranime-rip`, `gowaru:streamzo`
- Repair round 2 : **8 runtime errors** — `gowaru:animesama-co`, `gowaru:flemmix`, `gowaru:french-manga`, `gowaru:voiranime-homes`, `gowaru:mugiwarastream`, `gowaru:sekai`, `gowaru:voiranime-rip`, `gowaru:streamzo`
- Les huit erreurs du repair round 1 ont été rejouées à l’identique au round 2, avec le même profil et le même SHA de réparation.
- L’ancien rapport ne stockait pas `name/code/message/stack` pour ces erreurs : la cause JavaScript exacte était donc perdue. La correction ajoute ces champs pour chaque fixture et chaque réparation.

## Réparations acceptées à tort

- `gowaru:anime-ultime` : `no_streams`/10 → `reachable`/75, **sans preuve de flux lisible**.
- `gowaru:animesultra` : `no_streams`/10 → `reachable`/75, **sans preuve de flux lisible**.
- `gowaru:coflix` : `no_streams`/10 → `reachable`/75, **sans preuve de flux lisible**.
- `gowaru:dulourd` : `no_streams`/10 → `no_streams`/10, **sans preuve de flux lisible**.
- `gowaru:frenchstream` : `no_streams`/10 → `reachable`/75, **sans preuve de flux lisible**.
- `gowaru:vostfree` : `no_streams`/10 → `reachable`/75, **sans preuve de flux lisible**.
- `gowaru:wookafr` : `no_streams`/10 → `reachable`/75, **sans preuve de flux lisible**.
- `gowaru:waveanime` : `no_streams`/10 → `no_streams`/10, **sans preuve de flux lisible**.

`dulourd` et `waveanime` ont même été acceptés sans changement de statut ni de score. La cause est double : le comparateur lisait `stream_count` alors que le rapport enregistrait `streams_returned`, et il considérait une simple réponse HTTP comme une amélioration suffisante.

## Requêtes et classifications fausses

- **292 requêtes** contenaient une forme de `/[object Object]/` : plusieurs signatures d’appel incompatibles étaient essayées dans le même processus.
- HTTP observés dans les diagnostics : `200`=2231, `403`=1595, `404`=480, sans statut=330, `429`=126, `401`=108, `400`=43.
- **104 variantes** n’avaient aucune observation de route provider, mais pouvaient encore être rangées dans `no_streams`.
- `no_streams (10)` affichait le score 10, pas dix essais. Le format du log est remplacé par des champs nommés.

## Correction finale appliquée

- Une signature d’appel qui retourne un tableau, même vide, arrête immédiatement les essais ; aucune seconde signature incompatible n’est appelée.
- Les arguments sérialisés en `[object Object]` sont bloqués avant le réseau et font remonter `invalid_request_arguments`.
- Les erreurs conservent `name`, `code`, `message`, `phase`, `invocation`, `settings_profile` et une stack filtrée.
- `no_streams` exige maintenant une recherche/fiche/épisode/lecteur ayant réellement répondu avec succès.
- 401/403/429/451 deviennent `blocked`, 404/410/5xx deviennent `unavailable`, absence de route devient `provider_unreachable`.
- Le proxy de `Response` utilise le bon receiver natif et lie les méthodes, ce qui évite les erreurs d’invocation Undici.
- Le repair lit enfin `streams_returned` et ne peut être accepté qu’après augmentation du nombre de flux **lisibles**.
- Le profil générique `metadata_context_recovery` est désactivé en automatique ; le profil DLE étroit reste testable mais doit prouver un flux lisible.
- Une réparation déterministe identique n’est jamais rejouée au round suivant.
- Un nouveau gate bloque toute publication si le harness contient une requête mal formée, une runtime error sans détail ou une réparation acceptée sans preuve lisible.
- Le deep teste au maximum quatre profils de settings et un seul fallback par catégorie afin de réduire les répétitions sans supprimer la couverture.

Le détail des 194 lignes agrégées est fourni dans `DEEP-LOG-LINES-2026-08-03.csv`.

## Lecture de chaque bloc visible dans les captures

| Bloc du workflow | Ce que les lignes montrent | Verdict après audit |
|---|---|---|
| Installation et tests du dépôt | Les contrôles statiques passent avant le réseau. | Le dépôt était syntaxiquement valide, mais cela ne validait pas le comportement du harness profond. |
| Résolution des hubs et découverte | Les trois sources et les providers publiés sont réunis dans la staging. | Étape structurelle correcte ; elle n'explique pas les faux `no_streams`. |
| Préflight DNS | 164 résultats `inconclusive` et 30 sans domaine détecté. | Le job ne disposait d'aucune preuve DNS positive pour la quasi-totalité des variantes. |
| Baseline deep | Les 194 lignes de providers sont reproduites dans `DEEP-LOG-LINES-2026-08-03.csv`. | Les statuts mélangeaient absence de route, blocage HTTP, catalogue vide et erreur d'invocation. |
| Repair round 1 | 21 candidats retestés ; 8 runtime errors ; 8 réparations acceptées. | Les 8 acceptations étaient fausses : aucun flux lisible supplémentaire. |
| Repair round 2 | 13 candidats retestés ; les mêmes 8 runtime errors reviennent avec les mêmes SHA. | Retest déterministe inutile ; désormais bloqué par empreinte. |
| Agrégation finale | 4 `healthy`, 45 `reachable`, 143 `no_streams`, 2 `runtime_error`. | Ce bilan ne pouvait pas servir à désactiver les providers ni à accepter des mutations. |
| Diagnostics et publication | Le job a publié malgré les erreurs de réparation et les preuves ambiguës. | Un nouveau gate interrompt désormais la publication avant promotion dans ce cas. |

Les **38 lignes de tentatives de réparation** sont reproduites séparément dans `DEEP-REPAIR-LINES-2026-08-03.csv`. L'ancien job ne conservait pas l'exception JavaScript exacte des 16 lignes `runtime_error` des repairs ; aucune analyse honnête ne peut la reconstruire après coup. Le nouveau format stocke désormais le nom, le code, le message, la phase, l'invocation, le profil de settings et la stack filtrée.

## Rollback des réparations déjà publiées

Le job fautif avait laissé quatre bundles contenant encore le profil générique accepté sans preuve : `anime-ultime`, `dulourd`, `waveanime` et `wookafr`. La version 5.19.2 les remplace par leurs **parents Gowaru exacts**, dont les SHA correspondent aux `parent_sha256` du rapport de réparation. Les quatre anciens bundles sont listés dans `DELETE_DEEP_FALSE_REPAIRS.txt` et ne sont plus référencés par les manifests.

Le nouveau validateur appliqué au rapport historique le refuse explicitement pour quatre motifs : réparations acceptées sans amélioration de flux lisible, raison d'acceptation non stricte, runtime errors de repair sans détails, et réparations identiques rejouées au round suivant.
