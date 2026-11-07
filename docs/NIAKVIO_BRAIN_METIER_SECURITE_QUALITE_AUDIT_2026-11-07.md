# Audit indépendant — cohérence métier, Brain, sécurité et qualité GitHub

**Date : 7 novembre 2026.** **Périmètre :** `niakw/NiakVIO` et `niakw/NiakVIO-Brain-LLM`. Les fichiers cités sont des snapshots de décision : comparer les SHA testés au `main` réellement exécuté avant toute promotion. Le présent audit n'affirme pas une application totalement optimisée, ni une réparation provider validée.

## 1. État réel et contrats métier

- 46 providers dans l'inventaire, 17 dans `repairQueue`, 21 `FULL OK` et 3 `PARTIAL OK` **retenus historiquement**, mais **0/21 FULL et 0/3 PARTIAL retestés** dans le census autoritaire de référence. **0 réparation de provider validée de bout en bout par le Brain.**
- NiakVIO est l'autorité des manifests, de l'exécution, du Core, du sandbox, des octets matérialisés, de la validation TMDB/épisodes/média et de la publication. Brain-LLM ne peut que proposer des changements et mémoriser les observations, sans droit autonome de publier un provider.
- Succès strict : panne actuelle reproduite → cause au bon niveau (Core, provider, Brain, harness, runtime, réseau) → code *généré* par le Brain → compilation → application → rematérialisation → hash du bundle réellement exécuté → médias terminaux **décodés** → bon identifiant TMDB et saison/épisode/S00/durée/langue/qualité/headers → non-régression → apprentissage durable → projection/publi vérifiée.
- Un HTTP 200, une route atteinte, un URL dit playable, une proposition JSON, un commit ou une CI verte ne constituent pas une réparation.

## 2. Faiblesses génériques reproduites et changements

| Couche | Erreur observée | Correction / état | Validation restante |
| --- | --- | --- | --- |
| Brain sandbox | Contrat anime 24 minutes appliqué aux films | `f751cc7` et `09b9c10` : sélection stricte par catégorie du manifeste et durée du vrai contenu | Couverture plus large films/TV et lecture terminale réelle |
| Brain strict | URL déjà « playable », encore non décodée : nouvel effet décodeur ignoré | `43f9e36` + `06ea768` : comparer les contrôles médias effectivement décodés | Au moins un vrai flux positif |
| Brain feedback | Compteurs de lecteurs réellement visités supprimés avant le prochain prompt | `80e328f`, `5402f16`, Brain-LLM `057d8d0`/`1f7096b` : transmettre les compteurs sans URLs | Rejeu d'un correctif causal, sans refaire le même no-op |
| Préflight | Films et séries observés sur un corpus différent de celui du validateur strict | `972b079` : activer `NIAKVIO_REQUIRE_DECODE_PROOF=1` dès observation et recheck | Vérifier l'effet en run réel, sans présumer une réparation |
| Identité RAG | Identifiants TMDB film/TV effacés parce que seuls deux anime étaient reconnus | `d9c2d5d`, `049c918`, `351148f` : identité catalogue pour tous les types, y compris avant décodage | Rejouer les vrais cas |
| Oracle de fixture | Le Brain pouvait voir un titre ou une durée annoncés sans lien exact avec le catalogue autoritaire | `9fed39c` : exige ID + saison/épisode + titre + durée du catalogue avant d'exposer l'identité/durée/proof, tests contre falsification | Code `9fed39c` a été suivi de `b5f86d`, Core exact-SHA en cours |
| S00 / mini-série | Spartacus S00E01 peut être confondu avec S01E01/S02E01/S201 | Core V17 et `tests/special_season_zero_identity_test.py` rejettent les coordonnées explicitement contraires ; les URLs opaques restent non vérifiées | Crosswalk seulement avec source, titre et identité prouvés ; TV/Mobile/Desktop et flux décodés non validés |
| Générateur | Qwen 3B produit suppressions/no-op (ex. `vidfast`), parfois après un HTTP bloqué | Rejet sûr ; `fbca89a` évite l'inférence lors d'un `blocked` réel, `b5f86d` évite de bloquer abusivement `provider_unreachable` | Essai complet généré, appliqué, réellement décodé ; comparaison modèle API |
| Learning | Mêmes mutations exécutées et refusées pouvaient être reproposées sans prendre en compte le progrès des lecteurs | Rotation générique conservant la preuve de fan-out, pas de blacklist à partir d'un simple timeout | Validation A/B sur le même SHA et la même famille |

**Limite représentativité :** les oracles positifs stricts à durée vérifiée restent petits (dans `health-config.json` : 1 film `Interstellar`, 1 épisode TV `Breaking Bad S01E01`, 2 épisodes anime de 24 minutes, plus plusieurs films anime). Les autres fixtures de découverte ne disposent pas toutes d'une durée autoritaire. Ne jamais inventer de durées pour les faire entrer dans la validation ; obtenir des preuves et élargir le corpus (film court/long, TV, anime, S00, mini-série, multi-lecteurs, HLS, épisodes tardifs) avant un verdict de couverture générale.

**Cas diagnostique :** Brain `42361093507` et `42361530133` : `vidfast`, génération locale non causale, **0 réparation**. Une classification `provider_http_blocked` n'est pas une preuve de parser JS cassé. En sens inverse, `provider_unreachable` sans preuve réseau externe ne doit pas empêcher d'examiner le code.

## 3. Sécurité : inventaire serveur vérifié, pas de « clean » fictif

### NiakVIO — inventaire #42364289118 (sur source de triage `57424210`)

**377 alertes CodeQL ouvertes de niveau High** :

| Portée déterminée par manifests et PROVENANCE | High ouvertes | Action |
| --- | ---: | --- |
| Snapshots `providers/` non référencés par les manifests courants | **376** | Préserver la compatibilité des anciennes URLs avant suppression ; classifier par règle et génération, revoir la politique de rétention/retirement puis demander une clôture justifiée si applicable |
| Fichier maintenu `tests/response_structure_test.cjs` | **1**, #2531 | `js/incomplete-url-substring-sanitization`, ligne 166 ; corrigé par `d5325feb` : oracle compare toutes les origines à l'origine de base attendue, au lieu d'un seul domaine exclu ; **attendre l'analyse CodeQL post-correctif pour confirmer la clôture** |
| Fichiers providers actuellement référencés | **0 dans cet inventaire** | Ne présume pas qu'un ancien client utilisant une URL historique est protégé |
| Archives lifecycle classées | **0 dans cet inventaire** | Ne supprime pas les preuves historiques |

**Répartition des 377 par règle :** `js/double-escaping` 204 ; `js/insecure-randomness` 148 ; `js/regex/missing-regexp-anchor` 21 ; `js/bad-tag-filter` 3 ; `js/incomplete-url-substring-sanitization` 1. Les diagnostics sont des constats du scanner, **pas** une démonstration de compromission. Une suppression groupée des anciens bundles peut casser les manifests cachés ; un dismissal sans preuve peut masquer des vulnérabilités encore accessibles.

### Brain-LLM

L'inventaire initial `42363757788` trouvait **1 alerte High**, `py/incomplete-url-substring-sanitization`, dans `private_chat_memory.py`. `68267973`/`b3031d36` remplacent le test par sous-chaîne par l'analyse du schéma, hostname exact, identifiants/port et chemin ; `e03334b1` ajoute des tests d'URL ressemblant à GitHub. **Nouvel inventaire `42364586403` : 0 alerte CodeQL ouverte**, et CI Brain `42364094964` validée. Ne pas en déduire que tous les scanners tiers sont verts.

**Dependabot et Secret scanning :** API du workflow renvoie `unavailable_not_clean` sur les deux repos. Statut = **non vérifié** (droits ou fonctionnalité), jamais 0. Le Final Gate NiakVIO reste distinct et souvent `skipped` quand le SHA analysé n'est pas `main` actuel.

## 4. Nettoyage et qualité du dépôt

- **Exécuté :** retrait de `noop.tmp` (contenu inertiel `temp`, aucune référence), commit `a1662cc`. Pas de suppression massive.
- **Brain supply chain :** 11 workflows passent d'actions mutables `@v4/@v5` à des SHA complets vérifiés dans NiakVIO, et `persist-credentials: false` aux checkouts nécessaires (`9e322dc`, `ee40901`). Test de contrat automatique ; Brain CI verte.
- **Docs :** `SECURITY.md` Brain corrigé (anciennes « versions supportées » 4.x/5.x fictives), README, coût et modèle économique publiés. Le dépôt Brain n'avait pas de description GitHub ; le connecteur présent ne permet pas de modifier cette métadonnée.
- **Conserver :** `provider-old/`, evidence `automation/`, expériences négatives, releases historiques et liens d'anciens manifests sans preuve que leurs consommateurs ont expiré. L'espace Git et les alertes ne doivent pas être optimisés en cassant le replay ou les clients.
- **Branches :** NiakVIO `main` et `brain-learning/proposals` ; Brain-LLM `main`, `niakvio-guidance` et `fix/brain-observed-media-bridge-contract`. Pas de suppression non vérifiée des branches de mémoire/guidance ; aucune PR ouverte lors de l'audit.
- **Reste à mesurer :** temps CPU, coût des runs, poids du clone/CI, I/O et taux de succès exact par couche. `CI green` ≠ app « totalement optimisée ».

## 5. Modèle d'IA et dépenses (VPS faible)

Architecture : orchestrateur déterministe et RAG → générateur économique API interchangeable → escalade forte si nouvelles preuves → validation indépendante NiakVIO → Learning réutilisable. Pas besoin de plusieurs gros modèles en RAM sur VPS.

Le backend OpenAI Responses Brain existait déjà, désactivé sauf opt-in explicite `NIAKVIO_ALLOW_PAID_API=1` + clé. L'allowlist autorise désormais `gpt-6-luna`, `gpt-6.1-terra`, `gpt-6.1-sol`, `gpt-6-astra`. Aucun appel API payant n'a été lancé, aucun routage automatique ni garde-fou de facturation réel n'est encore installé. Gemini/Groq/OpenRouter : alternatives gratuites ou peu chères **sous quotas**, adaptateurs non intégrés. Tarifs et exemple de 10 000 requêtes dans [Brain-LLM, coûts API](https://github.com/niakw/NiakVIO-Brain-LLM/blob/main/docs/MODEL_ROUTING_COST_2026-11-07.md).

**Ne pas limiter arbitrairement les tentatives utiles.** Dédupliquer les mêmes échecs et fingerprints, réutiliser les observations au même SHA, router les pannes externes correctement, puis escalader un **nouveau** raisonnement causal. Le quota per-job évite seulement qu'un runner tourne indéfiniment ; il ne doit pas représenter un plafond total des expériences par provider. Budget monétaire global explicite avec mesure du coût par réparation décodée est un chantier à implémenter, pas un contrôle déjà actif.

## 6. Priorités et décisions restantes

| Priorité | État | Fermeture vérifiable |
| --- | --- | --- |
| P0 Rejouer toutes les CI sur le code final | Non clôturé | Core, non-régression, Brain preflight, CodeQL, Final Gate : SHA exact et logs inspectés |
| P0 Première réparation par Brain | **0/17** | Correctif du LLM appliqué, bytes exécutés, vidéo réellement décodée, identité/durée correcte, Learning persisté |
| P0 Corpus représentatif | Partiel | Au moins un vrai oracle représentatif par type et famille, incl. S00, mini-série, alt-catalogue et tests négatifs |
| P1 Sécurité NiakVIO | 376 snapshots + #2531 à suivre | Nouveau scan constate #2531 close ; politique historique vérifie consommateurs cache/release avant triage/dismissal |
| P1 Dépendances/secrets | Non vérifiable via token actuel | Inventaire accessible, triage exploitabilité, correctifs/fixes avec CI |
| P1 Benchmark générateurs | Pas exécuté | Mêmes fixtures/sha, coût réel, compilabilité, décodage, absence de régression Luna vs Terra/Sol vs gratuit |
| P1 Scalabilité 800 hubs | Bloqué par 0 succès | 1 provider réellement réparé, puis 1 famille de panne pertinente, ensuite sweep 17 et nouveaux hubs |
| P2 Coût/temps/stockage CI | Non mesuré | Mesurer performance sur workflow exact avant optimisation, sans fragiliser provenance |

**Documents canoniques :** [Brain Repair Roadmap](../BRAIN_REPAIR_ROADMAP.md), [Brain Repair Architecture](../BRAIN_REPAIR_ARCHITECTURE.md), [Security Policy](../SECURITY.md), [Memory](../MEMORY.md). Tout nouveau run supersédant ce checkpoint doit y noter son SHA, son artifact, ce qui a réellement été testé et ce qui reste bloqué.


### Checkpoint complémentaire : transparence replay, sécurité, publication

- Deux CANDIDATE OK historiques référencent le run 34309729426 ; ni l'arbre GitHub consulté ni l'API d'artefacts utilisée ne livrent le programme exact. Nouveau diagnostic Brain `f2a620b`, CI 42367960593 SUCCESS, consommé en lecture seule par hosted ; aucun faux replay/promotion.
- CodeQL #2531 : le run retirement 42367868331 est SUCCESS technique mais **deferred**, car un shard census ajouté avançait HEAD. L'allowlist couvre désormais ces shards seulement **ajoutés**, pas modifiés ; nouvelle preuve exacte et fermeture toujours à vérifier.
- Domain Refresh 42366117014 a publié `ae9e931` ; la race précédente est corrigée en fail-closed sans rebases de code provider, qualification Core/non-regression sur `e11f6cc` verte.
- Budget API Brain testable : pas de dépenses automatiques, plafond monétaire local optionnel et persistant ; pas encore de plafond global multi-runner. Aucune prétention « totalement optimisé » ni « 17 réparés ».


### Checkpoint causal 2026-11-07 — parsing CSS, oracle Brain et publication

- Échec réel du préflight full current bytes : [run 42371665355](https://github.com/niakw/NiakVIO/actions/runs/42371665355), SHA `ad76b284`, `tests/provider_4khdhub_runtime_behavior_test.py` renvoie `movie=[]` ; la trace ne contient que les recherches The Colony / Breaking Bad, **aucune page détail visitée**.
- Cause locale prouvée : dans le runtime réellement publié `providers/4khdhub--nuvio--14b3b921a0d71897.js`, `classBlocks(html, "movie-card")` utilise `\\b` comme fin de token CSS et accepte incorrectement `movie-card-content`. Le bloc parent possède le lien mais perd le format, le bloc enfant possède le format mais perd le lien. Le parcours se termine avant le hub/terminal.
- Le Brain avait déjà produit un candidat générique pour **exact-class-token-boundary** : `automation/hosted-repair-evidence/42358985990-mutations.json`. Le profil `html_class_token_exact_v1` existe dans `scripts/adaptive_runtime/runtime_repair.py`, mais les anciennes assertions du profil étaient trop synthétiques.
- Nouveau test réaliste `tests/adaptive_html_class_token_profile_test.py` (commit `2c30f59`) : rejoue, sans la modifier, la fixture du runtime publié en appliquant le profil générique **en mémoire**. CI [42372664707](https://github.com/niakw/NiakVIO/actions/runs/42372664707), SHA `25f9e61`, produit **avant 0 film / 0 épisode, après 1 film / 1 épisode**, avec URL, qualité et titre d'épisode attendus. Le test courant du provider publié **échoue toujours**, conformément à la réalité. Ceci prouve un gain de parsing local, pas un stream réseau lisible.
- [Fast Brain Repair 42370960740](https://github.com/niakw/NiakVIO/actions/runs/42370960740) a fini `accepted=0` sur 12 providers. Son plan `published:4khdhub` indique `action=collect-more-evidence`, `allowedProfiles=[]`, `experimentExhausted=true`, bien que `postExhaustionCandidateProfiles` contienne `html_class_token_exact_v1`. Des essais passés ont été rejetés faute de `required_category_playable_proof`; ne pas les transformer en victoire.
- **Responsable à approfondir :** transition Brain Learning → nouvelle preuve causale structurelle → éligibilité profil → création de bytes → replay média réel → persistance/pub ; distinguer une hypothèse qui compile d'une correction effective. Aucun provider n'a été modifié directement. L'orchestreur doit incorporer la nouvelle preuve hors ligne sans lui donner l'autorité de publication.
- Le registre de statut a été clarifié : FULL/PARTIAL hérités explicitement qualifiés de **carried** ; `0/21` FULL et `0/3` PARTIAL fraîchement retestés dans le census précédent. Les problèmes de sécurité, CodeQL exact-SHA, nettoyage global et performance restent ouverts.
