# NiakVIO — audit réel du 18 octobre 2026 : disponibilité, Domain Refresh, identité des épisodes et Brain-LLM

## Statut et preuves

Ce document sépare strictement **déclaré**, **reachable en CI**, **flux terminal confirmé**, **identité correcte** et **lecture effective dans les clients**. Ne pas promouvoir un provider sur la seule base de CI SUCCESS, HTTP 200, CHAIN REACHED, URL renvoyée, ancien fixture ou mutation de code.

| Élément | Observé | Source |
| --- | --- | --- |
| Manifests | `manifest.json`, `manifest-hub46.json`, `native-hub46/manifest.json` : **41 enabled** ; `vf/manifest.json` : **21** ; `no-anime/manifest.json` : **22** ; `vf-no-anime/manifest.json` : **7** | fichiers sur main, vérifiés au cours de l'audit |
| Cohorte census | **46 référencés, 22 FULL, 16 repairQueue, 5 DISABLED** ; les 25 « operational » des intitulés de commits = FULL + PARTIAL, pas FULL seuls | `automation/provider-census-status.json`, `runId=39127281651` |
| Présence/lecture sur le runner | **41 sondés : 6 healthy, 1 degraded, 11 no_streams, 14 provider_unreachable, 4 blocked, 5 unavailable** | `availability-report.json`, `generated_at=2026-10-18T12:41:37.155418+00:00` |
| Désactivations historisées | 5 archivés : `desiflix`, `fullanime`, `animetsu`, `showbox`, `videasy` ; pas de disabled actuel dans le manifest | `automation/provider-disabled-lifecycle.json` |

**Attention :** les statuts availability proviennent de GitHub Actions (réseau CI) ; `provider_unreachable` ou `blocked` ne prouve pas une panne reproduite sur TV/mobile/desktop (DNS/WAF/client peuvent différer). Un provider « healthy » CI ne garantit ni un épisode correct ni un flux lisible par le client. `manifest_changed=false` : le contrôle d'availability n'a pas réduit le manifest de 41 à 6.

## P0 — Domain Refresh : la tâche existe mais ses résultats peuvent rester inappliqués

- Workflow `.github/workflows/domain-refresh.yml` : cron `23 3 * * *` (UTC), `mode=quick` par défaut, `--include-disabled`. Le cron peut démarrer avec retard.
- Runs programmés **39015399987 (17/10)** et **39110367982 (18/10)** : **FAILURE** dans `tests/provider_domain_metadata_reconcile_test.py`, qui exigeait l'ancienne valeur littérale `hubs["4khdhub"]["direct"] == "https://4khdhub.one/"`. Ce contrat trop spécifique bloquait le pipeline après découverte de changements. Des corrections de validation cross-brand/HTTPS ont ensuite été apportées sur main par des commits indépendants.
- Runs **39127108430** et **39127704619** : GH SUCCESS mais étape de publication `FIELD_DOMAIN_PUBLICATION_SKIPPED reason=main_advanced` (course entre le SHA initial et les commits du Brain/Census). L'exécution a détecté `scope=41 resolved=20 unresolved=14 applied=3`, avec modifications sur `hindmoviez`, `uhdmovies`, `wookafr`, puis a **réenfilé un workflow** au lieu de publier ces trois modifications. `terminal_probe=false` dans le rapport : une adresse retenue n'est pas une preuve de média.
- Il manque un **point fixe de publication** : signaler séparément `domain candidates found`, `confirmed authority`, `data staged`, `manifest/published source SHA`, `remote published`, `replayed usable`. Un GH SUCCESS avec publication skipped doit être affiché comme `deferred`, et réessayé dans une fenêtre de mutation isolée jusqu'à SHA distant démontré ou blocage explicite. Préserver les garde-fous contre redirections inter-marques et HTTP downgrade.
- Vérifier ensuite les 14 non résolus par familles : origine durable, API backend, WAF, site supprimé ; ne jamais réécrire manuellement 14 domaines pour masquer un problème d'autorité ou de réseau.

## P0 — Saison/épisode : la preuve d'identité s'arrête trop tôt

- `scripts/provider_patches/global_stream_identity_v1.py` (**CORE.STREAM_IDENTITY.V1**) était partagé mais sa fonction `episode(text)` savait détecter `S03E02` / `Season 3 Episode 2`, **pas `3x02`**. Une contradiction explicite pouvait rester affichée.
- Correctif générique `5c8c2e17`, test `1c82ef63` dans `tests/episodic_identity_runtime_test.py` : `3x02`, `03x002`, `3 x 2` refusés pour requête S03E01 ; `3x01` conservé. Exact CORE Workflow Gate `39128756480`, Non-Regression `39128756537` et CodeQL `39128756477` ont validé le SHA testé. **Cela ne prouve pas encore la lecture réelle**.
- La politique actuelle conserve volontairement les flux **opaques** sans `tmdbId`, `imdbId`, titre, saison, numéro, provenance du lecteur ou information contradictoire. Elle rejette la contradiction observée, **mais ne prouve pas l'association de l'octet média à l'épisode**. Un lecteur peut afficher des métadonnées rassurantes mais servir un épisode incorrect.
- La matrice `automation/PLATFORM-RUNTIME-CONTRACTS.md` (dernier audit daté **16/09**, donc **à revalider**) signalait un écart client : `TMDB_API_KEY` et hydratation TMDB/IMDb côté TV, absents sur Android/iOS/Desktop. Tester sur les versions clients actuelles les mêmes requêtes TMDB + S/E, le passage object/positional, les données du contexte et les flux tardifs.
- Contrat à construire : `TMDB work id + season + episode -> provider catalogue entry id -> detail/player id -> source id -> terminal URL -> current-byte replay` ; comparer chaque transition, l'ordre absolu vs par saison, épisodes spéciaux S00, anime cour/cycle, `1x02`, `S01E02`, `EP02` et titres localisés. Classer `verified / opaque-unverified / contradicted`, et ne **jamais confondre un lien opaque avec un épisode vérifié**. Préserver les sources opaques dans une voie explicitement non vérifiée tant que le durcissement fail-closed n'a pas été testé contre les providers FULL (sinon risque de disparition supplémentaire).

## P0 — Brain/LLM : générer un vrai correctif avant d'étendre

- `NiakVIO-Brain-LLM`, workflow `niakvio-private-guidance.yml` : Qwen2.5-Coder-7B-Instruct Q4_K_M sur runner **CPU**, `-np 1`, jusqu'à 600 s de budget/provider. Les runs précédents ont enregistré des `TimeoutError`, `no_op` et prompts trop volumineux.
- Guidance republiée après les corrections de génération du 15/10, source `guidance/niakvio-force-mutations.json` au SHA modèle `52f28232` : **2 mutations candidates pour 2 providers**, mais principalement du **reformatage de code / variations syntaxiques**, et **aucune preuve de nouvelle réparation de média**. Les tests « schéma », « candidate generated » ou « published guidance » ne sont pas une mesure de réparation.
- Exiger une nouveauté sémantique (AST/bytecode + replay différentiel de comportements, pas simple diff texte), validation d'un patch exact, application dans les octets réellement exécutés, bonne identité et lecture terminale sur au moins un provider. Le Brain ne doit pas transformer des changements purement cosmétiques en « progrès ».
- Comparer trois backends interchangeables sur la **même suite de pannes documentées**, à budget et matériel indiqués : (1) Qwen local actuel = témoin, (2) API de raisonnement/code intermédiaire (ex. OpenAI `gpt-6.1-sol`), (3) modèle plus capable pour échec difficile (ex. `gpt-6-astra` ou Claude Opus 5.5), ou Qwen3-Coder-Next sur **GPU adapté** (pas sur le runner CPU/8 Go). Mesurer **accepted executable mutation**, **applied bytes**, **correct episode/title**, **playable media** et **régressions** par dollar et par minute, pas les fixtures de schéma. Toute API nécessite une clé en secret Actions, des plafonds de coût et un filtrage de contexte/PII. Ne pas envoyer cookies, secrets, URLs signées ou données privées.
- Aucun changement manuel définitif d'un provider pour contourner le Brain. Les correctifs d'infrastructure Core/Brain/harness restent légitimes.

## Ordre de validation bloquant

1. Relever `main` HEAD / SHA effectivement testé et inspecter publication des Domain Refresh (SHA final distant), sans relancer sans fin des runs qui se remplacent.
2. Isoler la perte de visibilité : 41 manifest contre filtres 21/22/7, présence dans le client, réseau CI vs cinq plateformes, listes de disable/archive.
3. Tester épisode S/E correct et faux de chaque famille sur les **octets publiés**, en traçant les identifiants source et leur rattachement à TMDB ; échantillon avec épisodes réellement lus, pas seulement HLS/URL.
4. Évaluer les moteurs Brain sur même fixture **réelle** ; première réparation intégrale sans oracle manuel, puis au moins un exemple par famille, puis cohorte de 16.
5. Publier chiffres fiables, non-régression, `MEMORY.md` et census basés sur l'exécution, puis seulement augmenter le catalogue vers 96/800.

## Liens de preuve

- [Census](https://github.com/niakw/NiakVIO/blob/main/PROVIDER_CENSUS_STATUS.md)
- [Domain schedule échec 17/10](https://github.com/niakw/NiakVIO/actions/runs/39015399987) ; [échec 18/10](https://github.com/niakw/NiakVIO/actions/runs/39110367982)
- [Domain recalcul sans publication 18/10](https://github.com/niakw/NiakVIO/actions/runs/39127704619)
- [Core gate épisode](https://github.com/niakw/NiakVIO/actions/runs/39128756480), [Non Regression](https://github.com/niakw/NiakVIO/actions/runs/39128756537)
- [OpenAI API modèles](https://developers.openai.com/api/docs/models), [Qwen3 Coder open weights](https://github.com/QwenLM/Qwen3-Coder)
