# Architecture NiakVIO — Provider v3

> Source de vérité technique humaine. Les états de run, branches temporaires et métriques de disponibilité ne sont pas des invariants d’architecture et ne doivent pas être figés ici.

## 1. Modèle

NiakVIO sépare trois responsabilités :

- **Provider Object** : identité, capacité canonique, DATA, routes/protocole, stratégie, preuves et provenance ;
- **NiakVIO** : reconnaissance, composition, vérification, Learning et publication ;
- **clients Nuvio officiels** : surfaces d’exécution et de preuve par plateforme.

Le catalogue exécutable couvre **46 Provider Objects Hub**. Les providers hors Hub ne sont plus des lignes OFF : seuls leurs ProviderBase historiques restent archivés sous `provider-old/`. Un zéro flux, une route inconnue ou un stream cassé ne suffit jamais à déclarer un provider mort.

## 2. Source de vérité Provider v3

Un bundle publié est reconstruit depuis :

1. ProviderBase v3 propre ;
2. DATA structurée appartenant au provider ;
3. Lego `PROVIDER.*` ;
4. Lego `CORE.*` ;
5. minimizer NiakVIO conservateur avant hash.

Sources principales :

- `provider_catalog.json` ;
- `provider-bases/` ;
- `provider-overrides.json` ;
- `provider-type-policy.json` ;
- `automation/provider-v3-static-knowledge.json` ;
- `scripts/provider_patches/**` ;
- `scripts/provider_v3_minimizer.py`.

`providers/*.js` est une **sortie runtime adressée par contenu**, jamais une seed de reconstruction. Les bundles historiques/upstream servent uniquement de connaissance et de provenance.

Le ProviderBase canonique porte `NIAKVIO_PROVIDER_BASE_OWNED_V3`.

## 3. Envelope et ownership

Forme attendue :

```text
/* BEGIN NIAKVIO_PROVIDER */
/* NIAKVIO_PROVIDER_ID:<id> */
/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */
<ProviderBase v3>

/* STARTFIX:PROVIDER.<ID>.CONFIG.V1 */
/* FIXDATA:PROVIDER.<ID>.CONFIG.V1:<payload> */
<DATA>
/* CLOSEFIX:PROVIDER.<ID>.CONFIG.V1 */

<Lego PROVIDER.*>
/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
<Lego CORE.*>
/* END NIAKVIO_PROVIDER */
```

Les marqueurs canoniques sont `STARTFIX:<ID>` et `CLOSEFIX:<ID>`, avec `FIXDATA:<ID>` lorsque nécessaire. La frontière Core `NUVIO_GLOBAL_CORE_START_BOUNDARY_V1` est unique.

## 4. Routes et protocoles

La route durable appartient au Provider Object :

```text
provider.model.routeData
```

`provider.model.routes` et `provider.knowledge.recognizedContract.requests` sont des projections dérivées, pas de nouvelles sources de preuve.

La reconnaissance doit conserver quand ils sont connus : méthode HTTP, rôle, body/encodage, champs, `Referer`/`Origin`, type de réponse, placeholders, provenance et confiance. Elle peut analyser statiquement concaténations, variables et templates, sans exécuter le JavaScript provider.

Le workflow route-only est `.github/workflows/provider-v3-reconstruct-routes.yml`. Il ne doit ni exécuter le provider JS ni reconstruire les 46 bundles courants. Une absence de route reconnue reste un état **unknown**, pas une quarantaine automatique.

Les métriques d’un census précis restent dans les artifacts/rapports et dans `automation/provider-v3-architecture.json` lorsqu’une référence vérifiée est utile ; elles ne sont pas un invariant documentaire.

## 5. Type canonique ≠ transport Nuvio

C’est un contrat central.

### Capacité canonique

`canonicalSupportedTypes` décrit **ce que le catalogue du provider sert réellement** :

- `movie` ;
- `tv` ;
- `anime`.

Un provider anime-only reste donc :

```json
{"canonicalSupportedTypes":["anime"]}
```

### Compatibilité de lancement

`supportedTypes` décrit les voies par lesquelles Nuvio peut lancer ce provider.

Un provider anime-only peut exposer les alias de lancement épisodiques sans inventer de capacité movie :

```json
{"supportedTypes":["anime","tv"]}
```

Cela permet :

- anime épisodique via transport `tv` ;
- namespace `anime` lorsqu’il est exposé par le client ;
- transport `movie` **uniquement** pour un provider qui déclare réellement une capacité canonique `movie` ; il ne doit jamais être ajouté artificiellement à un provider anime-only.

**Cela n’ajoute jamais une capacité canonique `movie` ou `tv`.** Le Core doit rejeter une œuvre non-anime sur un provider anime-only après classification autoritative, avant le réseau provider lorsque l’information nécessaire est déjà disponible.

Inversement, un provider canonique `movie + tv` ne devient pas anime-compatible par simple alias de transport.

`tv` est l’unique alias de transport synthétique ajouté à un provider anime-only. `series`, `show` et `movie` ne sont jamais ajoutés comme aliases synthétiques.

## 6. Contrat runtime

Signature conceptuelle :

```text
getStreams(tmdbId, mediaType, season, episode)
```

Ordre logique :

```text
BEGIN PROVIDER
  gate launch/capacité
  résoudre l'identité/TMDB uniquement si le plan en a besoin
  exécuter le protocole provider
  si streams > 0
    appliquer identité, présentation, branding et sanitizer
  endif
END PROVIDER
```

Règles :

- gate capacité avant réseau provider ;
- pas d’appel TMDB gratuit quand le plan n’en a pas besoin ;
- cache TMDB scoped par œuvre/type ;
- saison/épisode conservés ;
- zéro flux ne fabrique rien ;
- mauvais média > zéro résultat en gravité ;
- erreur d’un stream ≠ désactivation globale du provider.

## 7. Reconstruction complète

La reconstruction courante **46/46** appartient à `.github/workflows/provider-v3-reconstruct-all.yml`. Elle travaille sur le SHA sélectionné et, lorsqu’un commit de reconstruction est demandé, **refuse toute écriture directe sur `main`** : la cible doit être une branche non-main explicite. Les 50 providers historiques restent des connaissances archivées, jamais des sorties de la reconstruction courante.

Interdictions :

- seed depuis `providers/*.js` ;
- seed depuis un bundle upstream ;
- création automatique d’une branche workbench persistante ;
- reconstruction cachée dans Quick, Deep ou un Native Lab.

La preuve finale doit inclure la reconstruction reverse byte-identical via `scripts/verify_provider_v3_reverse_rebuild.py`.

Les anciens comptes de plans/quarantaines restent des **snapshots historiques**, jamais une vérité opérationnelle courante.

## 8. CORE — Verify & Publish

Le workflow routine est `.github/workflows/sync.yml` : **CORE - Verify & Publish**.

### Quick

Quick vérifie rapidement :

- structure Provider v3/Core ;
- bytes publiés exacts ;
- sécurité ;
- minimizer ;
- contrats média/type ;
- cohérence des cinq Labs.

### Deep

Deep ajoute :

- observations réseau/hubs en lecture seule ;
- health des bytes publiés exacts ;
- diagnostics ;
- projections de manifests ;
- hashes et intégrité de release.

**Quick/Deep ne réparent ni ne reconstruisent les providers et ne réalisent pas le bump release de routine.**

### Finalisation d’une release acceptée

`.github/workflows/release-finalize.yml` est la transaction explicite de finalisation après acceptation de la pile de validation.

Contrat :

- en lancement manuel, l’entrée obligatoire est `expected_sha` ; sur push de son trigger permanent, le SHA d’événement joue le même rôle ;
- le checkout doit correspondre exactement au SHA accepté et une baseline de génération de release est exportée avant toute mutation ;
- les patches providers durables sont réappliqués sur les **46 providers courants**, puis le minimizer NiakVIO est amené à son fixed-point et vérifié ; les projections de manifests sont reconstruites et les générations non référencées sont prunées ;
- les versions provider/manifest/cache/release ne sont synchronisées qu’après stabilisation de cette génération exacte ;
- le transport Hub-46 épinglé, les hashes et l’intégrité de release sont ensuite reconstruits et validés ;
- les commits de génération et de pinning sont préparés localement, puis publiés atomiquement uniquement si `origin/main` pointe toujours sur le SHA de base accepté ; tout mouvement concurrent de `main` fait échouer la transaction ;
- une génération déjà finalisée peut rester un no-op ; aucune version provider/cache ne doit être inventée lorsque les bytes publiés n’ont pas changé.

Le finalizer n’est ni une autorité de découverte, ni un moteur Learning, ni une reconstruction complète : sa rematérialisation éventuelle est strictement bornée aux patches durables et à la génération courante acceptée, dans la transaction atomique de release.

## 9. Learning

`.github/workflows/brain-learning-lab.yml` est le seul espace de Learning/réparation expérimentale :

- providers actifs et désactivés peuvent être observés ;
- les essais restent sandboxés ;
- les preuves doivent être sanitizées ;
- les mutations deviennent des propositions reviewables ;
- `brain-learning/proposals` n’est pas une autorité de publication ;
- aucune mutation ne contourne les gates d’identité, sécurité, reconstruction et release.

Un échec appartenant au client Nuvio/OS ne doit jamais devenir une réparation Provider v3.

## 10. Domain Refresh

`.github/workflows/domain-refresh.yml` est une exception de maintenance d’adresse très bornée. Son autorité transactionnelle est `scripts/domain_refresh_transaction_v2.py` :

- les hubs/channels/redirects officiels servent à découvrir le terminal courant ; un hub reste une source d’adresse et ne devient jamais un backend d’exécution provider ;
- `official_site`, le registre `provider-hubs.json` et l’historique de domaines sont synchronisés avec la nouvelle autorité ;
- seules les substitutions/remplacements de domaine connectés à l’ancien terminal peuvent suivre la rotation ; une route/API métier indépendante reste inchangée ;
- le **CONFIG Provider complet** est reconstruit depuis la DATA structurée pour les providers modifiés ; l’ancien updater partiel `officialSite`-only n’est pas une autorité de publication ;
- ProviderBase, Lego `PROVIDER.*` hors CONFIG et Lego `CORE.*` doivent rester byte-identical ;
- le filename garde son namespace source-qualified et tourne uniquement par content hash lorsque les bytes CONFIG changent ;
- activation, projections, versions cache-safe, hashes et release integrity sont resynchronisés ;
- DNS/HTTP terminal est une observation postérieure à la résolution autoritative : un 403, anti-bot ou timeout CI ne rétablit pas silencieusement l’ancien domaine ;
- publication directe sur `main` n’est autorisée que pour cette transaction bornée, après CAS sur le SHA de base, puis Quick est relancé.

Le contrat est fail-closed sur rollback/cycle, terminal social/template, dérive d’activation et toute mutation hors CONFIG. Les preuves synthétiques A→B et d’ownership sont portées notamment par `tests/domain_refresh_workflow_test.py`, `tests/domain_refresh_transaction_guard_test.py` et `tests/provider_v3_workflow_ownership_test.py`.

## 11. Cinq Native Labs

Surface exacte :

1. `TVAndroid` — NuvioTV ;
2. `MobileAndroid` — NuvioMobile ;
3. `MobileIOS` — NuvioMobile ;
4. `DesktopMACOS` — NuvioDesktop ;
5. `DesktopWindows` — NuvioDesktop.

Règles :

- chaque device est une preuve indépendante ;
- la matrice de routes est dérivée du manifest courant, pas d’un nombre figé dans la documentation ;
- `canonicalSupportedTypes` porte la sémantique, `supportedTypes` la surface de lancement testée ;
- providers désactivés restent auditables ;
- les Labs utilisent les bytes NiakVIO candidats exacts ;
- **aucun Lab ne patch NuvioTV/NuvioMobile/NuvioDesktop pour contourner un bug upstream** ;
- un bug de compilation, packaging, runtime, QuickJS ou player upstream reste une preuve externe rouge ;
- le plumbing de test est autorisé uniquement s’il expose le chemin officiel sans changer le comportement production ni réparer le défaut observé.

Le trigger commun est `.github/triggers/full-native-lab-validation.json`.

## 12. Minimizer NiakVIO

Terser est interdit.

`scripts/provider_v3_minimizer.py` est conservateur et pré-hash. Il doit préserver :

- enveloppe BEGIN/END ;
- `STARTFIX/CLOSEFIX/FIXDATA` ;
- frontière Core ;
- retours ligne nécessaires à l’ASI ;
- littéraux, regexp et templates sensibles ;
- identifiants et ordre d’exécution.

Pas de renommage, reorder, folding ou remplacement textuel global. Les providers à état lexical risqué peuvent rester byte-stables.

Gates :

- `tests/provider_v3_minimizer_contract_test.py` ;
- `tests/provider_v3_minimizer_preview_test.py` ;
- `tests/provider_v3_minimizer_published_test.py` ;
- `scripts/verify_provider_v3_reverse_rebuild.py`.

## 13. Sécurité

Provider JS est de l’entrée non fiable : sandbox, budgets mémoire/temps/réseau, SSRF/redirect guards, protocoles P2P interdits, sanitization des artifacts et fail-closed publication.

Le stripping HTML générique par regexp est interdit. Les findings CodeQL sur code NiakVIO doivent être corrigés ou justifiés ; les snapshots/bundles générés restent traités comme code non fiable même lorsqu’un finding est classé vendored/generated.

`.github/workflows/codeql.yml` produit une preuve locale `security-extended` au SHA exact, conserve le SARIF en artifact et gate les findings High/Critical. Le même workflow audite les dépendances production au niveau High/Critical. Cette preuve complète le CodeQL Default Setup GitHub ; elle ne doit pas être désactivée pour masquer des alertes historiques.

## 14. Branches et publication

- **`main` = production et unique cible d’écriture active pour le travail courant** ;
- ne pas créer de nouvelle branche workbench/clean pour les corrections en cours ;
- `brain-learning/proposals` reste un store passif de propositions Learning, sans autorité de publication directe et sans servir de branche d’implémentation ;
- aucune branche workbench historique ne doit être documentée comme active après sa suppression ;
- avant de supprimer un ancien ref, vérifier qu’aucun artifact/code/doc utile n’y reste unique ;
- la finalisation release s’effectue uniquement après acceptation de la pile de validation, via `release-finalize.yml` sur le SHA exact accepté ;
- documentation/workflow/harness seuls n’imposent pas de bump provider/cache tant que les bytes providers publiés restent identiques.

## 15. Invariants non négociables

1. Les 96 Provider Objects restent dans le census.
2. ProviderBase v3 + DATA + Lego recréent les bundles sans seed JS publiée/upstream.
3. `provider.model.routeData` est la source route canonique.
4. Reconnaissance vide ≠ quarantaine.
5. `canonicalSupportedTypes` ≠ `supportedTypes`.
6. Anime canonique peut être lancé via `anime/tv` sans devenir movie/tv canonique ; aucun alias synthétique `series` ou `movie` n’est publié.
7. Gate capacité avant réseau provider.
8. Quick/Deep ne réparent ni ne reconstruisent et ne finalisent pas une release en routine.
9. `release-finalize.yml` ne modifie que la transaction release de bytes déjà acceptés.
10. Learning ne publie pas directement.
11. Domain Refresh ne modifie que l’autorité d’adresse et ses dérivées de domaine, puis reconstruit le CONFIG complet sans changer ProviderBase/Core ni les routes/API métier indépendantes.
12. Les cinq Labs restent séparés et observationnels.
13. Aucun Lab ne corrige un bug du repo Nuvio pour obtenir un vert.
14. Mauvais média jouable = échec.
15. Stream cassé ≠ provider globalement désactivé.
16. Terser interdit ; minimizer conservateur uniquement.
17. HTML stripping générique par regexp interdit.
18. Les métriques/run IDs historiques restent dans les rapports, pas dans les invariants.

## Références

- `automation/provider-v3-architecture.json`
- `automation/provider-v3-static-knowledge.json`
- `provider-v3-materialization.json`
- `PROVENANCE.json`
- `provider-overrides.json`
- `.github/workflows/release-finalize.yml`
- `scripts/release_version_baseline.py`
- `scripts/materialize_provider_v3_all.py`
- `scripts/verify_provider_v3_reverse_rebuild.py`
- `scripts/provider_v3_minimizer.py`
- `tests/provider_v3_documentation_contract_test.py`
- `tests/native_five_lab_coverage_test.py`
- `tests/native_lab_observational_purity_test.py`
