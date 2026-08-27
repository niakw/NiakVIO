## 5.21.0 — Audit technique, clients natifs et durcissement de la publication

- Intègre les corrections issues du croisement SonarQube / DeepSource / CodeScene sans réécriture aveugle des providers générés, snapshots LKG ou faux positifs de scanner.
- Corrige les contrats Brain/runtime confirmés, durcit les permissions GitHub Actions et impose les installations npm basées sur le lockfile.
- Empêche la persistance de JWT, cookies et credentials tiers dans les diagnostics committés tout en conservant les requêtes runtime réelles inchangées.
- Aligne le suivi officiel NuvioMobile / NuvioDesktop / NuvioTV sur leurs HEADs audités courants et maintient ces dépôts en référence read-only.
- Étend la vitrine README pour exposer explicitement la couverture TV, Mobile, Desktop macOS et Desktop Windows, même lorsqu'une plateforme n'a encore aucune preuve positive conservée.
- Synchronise désormais la version de release dans package.json, package-lock.json, sources.json, manifest.json, vf/manifest.json et provider_catalog.json.
- Préserve le versioning individuel des providers : un scraper ne change de version que lorsque son payload client-visible change réellement.
- Conserve les invariants ARCHI 2 : provider_catalog.json canonique, sync.yml orchestrateur unique, Quick/Deep séparés, LKG fail-closed, identité média prioritaire et preuves natives indépendantes par client.

## 5.20.50 — Quarantaine des durées contradictoires observées

- Met VIXSRC en quarantaine cache-safe après un HLS Interstellar annoncé à 169 min mais mesuré à 4 765,75 s (~79 min, ratio 0,470).
- Met Frenchstream en quarantaine cache-safe après un HLS Revenant S01E01 mesuré à 2 144,07 s (~35,7 min) contre 4 620 s attendues (ratio 0,464) sur TV, macOS et mobile.
- Conserve DVDPlay et TopCartoons inertes ; ces quatre providers ne peuvent plus renvoyer de média même si un client garde une ancienne activation locale.
- Lie toute baisse d’activation pour raison de sécurité au rapport distant, aux hashes des bundles testés et publiés, à la durée mesurée et au marqueur du bundle inerte ; un résultat CI inconclusif ou une qualité `Unknown` ne suffit pas.
- Ramène l’activation publiée à 59/91 providers généraux et 21/26 VF, en privilégiant l’absence de résultat à un contenu tronqué ou contradictoire.

## 5.20.49 — Contradictions bloquantes et quarantaine cache-safe

- Rend toute contradiction d’identité lisible bloquante dans le lab distant, indépendamment de l’objectif consultatif 10 providers / 3 VF et même si le provider est désactivé dans le manifest.
- Met DVDPlay en quarantaine avec un bundle inerte après les noms de fichiers incompatibles avec Revenant S01E01, afin de neutraliser aussi les anciennes activations conservées localement par Nuvio.
- Évite le faux positif MovieBlast en retirant le nom du provider et les marqueurs techniques de langue, qualité et codec avant de comparer un libellé à l’œuvre demandée.
- Ajoute une durée attendue aux six œuvres du lab : 169 min, 88 min, 58 min, 77 min, 24 min et 24 min ; une durée absente reste inconclusive, une durée manifestement incompatible est rejetée.

## 5.20.48 — Identité d’œuvre, durée et quarantaine fail-safe

- Corrige le faux positif qui classait un média HTTP lisible comme succès lorsque l’identité de l’œuvre restait inconnue.
- Ajoute un gate global bloquant pour les contradictions de titre, saison, épisode, nom de fichier média et durée ; l’absence de durée reste inconclusive et ne pénalise pas une œuvre récente.
- Distingue explicitement l’identité d’un contenu de la qualité UI `Unknown` / `Inconnue`, afin de préserver les sources valides telles que Purstream.
- Place le validateur direct-media StreamZo après toutes les récupérations catalogue : un proxy/iframe HTML est désormais résolu en HLS/DASH/conteneur ou rejeté, jamais envoyé brut à NuvioTV/Desktop.
- Enregistre la preuve live StreamZo pour `Mon ninja et moi 3` : titre du lecteur concordant, HLS final présent et durée de 5 262,615 s pour 88 minutes attendues.
- Met TopCartoons en quarantaine : manifest désactivé et bundle publié rendu inerte après les contenus croisés observés sur Breaking Bad et Revenant.
- Ramène l’activation générale de 69 à 61 providers selon la baseline d’activation validée ; les huit ajouts hors baseline restent publiés mais désactivés jusqu’à une nouvelle preuve avec les onze gates.
- Fait du seuil 10 providers / 3 VF un objectif strictement indicatif tout en excluant systématiquement des décomptes les contenus contradictoires, durées incohérentes et médias non vérifiés.

## 5.20.47 — Lab multi-œuvres et récupération catalogue globale

- Ajoute un lab reproductible couvrant films, séries et anime sur les contrats NuvioTV, Desktop et Mobile, avec rapports nettoyés par œuvre.
- Définit 10 providers jouables dont 3 VF comme objectif indicatif : le manque de couverture d'une œuvre récente ou rare reste non bloquant, contrairement aux erreurs runtime, contenus contradictoires et médias illisibles.
- Répare la récupération StreamZo et confirme sa lecture pour `Mon ninja et moi 3` sur les trois familles de clients.
- Applique la récupération catalogue bornée globalement et retire les correctifs V1 lorsqu'un correctif V2 équivalent est déjà publié.
- Isole les exécutions lentes, retente une fois les timeouts avec un profil réduit et borne la recherche PapaDuStream.
- Intègre le test unitaire du lab à `npm test`, élargit ses déclencheurs CI et vérifie l'intégrité de release après la suite locale puis avant la matrice distante.
- Restaure une provenance JSON valide, régénère les empreintes et élague les anciens bundles hachés devenus non référencés.
- Retire le déclencheur de branche temporaire du lab et place ses fixtures de test hors du dépôt pour éviter tout artefact résiduel après une interruption.

## 5.20.29 — NuvioTV media-output safety and bundle reconciliation

- Fix Coflix on NuvioTV: WordPress infrastructure endpoints (`admin-ajax`, `wp-json`, Ajax Search Lite) can no longer escape as streams.
- Resolve candidate Coflix embeds to direct media before applying the final strict all-URL HLS/DASH/container validator.
- Keep the 60-second short-VOD floor; update the synthetic VF recovery fixture instead of weakening preview rejection.
- Record that current NuvioTV parses `supportedPlatforms` / `disabledPlatforms` but does not enforce them in its PluginManager.
- Reconcile Flemmix, Frenchstream, HindMoviez, Movix, StreamZo and WookaFR with their already configured runtime-compatibility revision.
- Add a permanent published-override drift gate and include the complete NuvioTV target-media/sanitizer chain in release integrity hashes.

## 5.20.0

- Rebuilt the VF movie path around full catalogue recovery instead of domain-only validation.
- Added verified movie recovery adapters for Frenchstream, StreamZo, Movix, Coflix and Flemmix, tested with Interstellar and Guardians of the Galaxy Vol. 3 response structures.
- Kept Flemmix, Wooka, Nakios and ToFlix disabled until a current playable-stream proof exists; address discovery alone can no longer enable them.
- Removed the unsupported movie capability from Papadustream and preserved explicit anime-movie capabilities.
- Added strict hub-versus-terminal separation, catalogue-page markers and meaningful API probes for Purstream, Movix and Nakios. Generic HTTP 404 responses are no longer accepted as API validation.
- Rejects fstream.top, /troll/ and short preview playlists before they reach the player.
- Fixed domain-prefix replacement collisions such as flemmix.me -> flemmix.men and made coexisting recovery/sanitizer wrappers idempotent.
- Keeps Dahmermovies and Dahmermovies-TV excluded from manifests, providers and future upstream promotion.

## 5.19.2 — Deep harness integrity and repair rollback

## 5.19.4

- Rejected short/troll HLS previews, including the 18-second French-Manga/FStream false player.
- Refreshed Frenchstream from its official hub and preserved anime-film request types.
- Added automatic provider/release version invalidation so removed or changed providers cannot remain cached under an unchanged release.
- Kept Dahmermovies variants removed and explicitly excluded.


- Fixed provider invocation selection so incompatible object/positional signatures cannot generate `[object Object]` URLs.
- Preserved structured runtime exceptions for baseline, availability and repair rounds.
- Reclassified blocked, unavailable, unreachable and genuine empty-catalogue results separately.
- Required playable-stream proof before accepting any automatic source mutation.
- Disabled the generic metadata repair that generated repeated runtime errors and rolled back its four published artifacts to their exact upstream parents.
- Added a pre-publication deep-evidence integrity gate and blocked duplicate deterministic repair retests.

## 5.19.0

- Turn the complete provider hub registry into an active runtime source instead of documentation only.
- Resolve official hubs, public Telegram posts, redirects and curated candidates daily; use bounded Yandex/DuckDuckGo fallback only in deep mode.
- Require two consecutive validations before accepting a search-only domain and retain the last-known-good domain whenever discovery is inconclusive.
- Keep Frenchstream and Movix address resolution independent while filtering the unrelated `fstream.top` player output returned by either provider.
- Retain two content-addressed generations for each of the three upstream repositories and fall back to current published provider artifacts when an upstream is missing, truncated or corrupt.
- Add a focused daily domain-publication workflow while keeping full deep provider tests limited to Tuesday and Friday.
- Preserve the curated manifest order, expanded movie/anime types, stream-output validation and complete removal of Dahmermovies variants.

## 5.18.0

- Replace blind pre-build structural rewrites with a bounded baseline → diagnose → patch → exact deep retest → compare loop.
- Select repairs from generic runtime signatures and structural capabilities; the repair engine contains no provider IDs or domains.
- Add generic metadata-context recovery and DLE-like HTML search recovery as runtime-only profiles.
- Retain a generated JavaScript file only after a strict runtime improvement; runtime errors, neutral route-only changes and regressions keep the parent artifact.
- Revalidate the final staged tree after accepted repairs and publish `repair-report.json` with every accepted/rejected attempt.
- Keep URL/domain changes in simple durable overrides while behavioural adaptations remain shared profiles.
- Validate root and nested manifest paths, referenced provider files, and both `sources.json` version fields.
- Preserve 86 providers in the main manifest and 22 VF-capable providers, including disabled entries.

## 5.17.2

- Replace the provider-specific Frenchstream patch hook with a capability-driven, auto-applied HTML search-recovery profile.
- Apply the same recovery profile to every staged bundle exposing the same DLE-like search schema, regardless of provider ID.
- Keep provider-specific data limited to durable domain and wrapper compatibility overrides.
- Validate reusable patch-profile markers in staged and published provider files.
- Publish the Frenchstream final JS from the generic profile and keep manifests aligned.

## 5.17.1

- Finish the Frenchstream movie lookup patch on top of the locally verified `frenchstream.food` access.
- Parse current DLE search results across card, article, generic-link and data-id layouts.
- Remove obsolete `/films/.../` category fallbacks that currently return 404.
- Try multiple scored search matches before declaring the provider empty.
- Add a generic, versioned `patch_script` hook so complex provider fixes remain maintainable outside minified replacement strings.
- Update the Frenchstream manifest logo to the current domain.

## 5.17.0

- Restore trusted provider activation state and preserve enabled providers on inconclusive CI runs.
- Keep disabled French-capable providers in the VF manifest.
- Publish locally patched providers as deterministic `--nuvio--` JavaScript files.
- Persist Frenchstream domain, settings propagation and title fallback patches.

## 5.16.7

- Removed provider-specific origin probes and provider-specific deep-check fixtures.
- Added a global fixture-metadata fallback for TMDb title lookups when TMDb is unavailable or rejects the bundled key.
- Providers can now continue to their real site search routes, allowing genuine route observations instead of synthetic homepage probes.
- Mark synthetic TMDb fallback observations explicitly in health evidence.
- Apply the same diagnostic behavior to every provider without provider-specific blocking.

## 5.16.5

- Removed provider-specific strict route blocking from the global sync workflow.
- Route regressions and missing observations are now reported uniformly for every provider without failing unrelated providers.
- Kept `--strict` as a deprecated non-blocking compatibility flag.

## 5.16.2

## 5.16.4

- Added independent guarded origin probes for Frenchstream and StreamZo.
- Added provider-specific Tenet diagnostics for deep checks.
- Preserved network observations even when a provider crashes.
- Strict route validation now reports and blocks reachable origins with no observed lookup routes.
- Added regression tests for diagnostic fixtures and route-observation gaps.


- Make the promoted manifest version authoritative across `package.json`, `manifest.json`, `vf/manifest.json`, and `sources.json`.
- Add `scripts/sync_release_versions.py` so CI-generated manifest bumps cannot leave release metadata out of sync.
- Run release-integrity validation immediately before the manifest publication commit.
- Include all synchronized version files in the second publication phase.
- Add a regression test covering the synchronization workflow wiring.

## 5.16.1

- Align package, main manifest, VF manifest, and repository manifest versions.
- Pin all first-party GitHub Actions to immutable full commit SHAs.
- Add release-integrity checks for version alignment and immutable action references.
- Preserve the hardened provider, network, override, and route-regression controls from 5.16.0.

## 5.15.0

- Add a central `route_replacements` override namespace per provider, separate from domain replacements.
- Record sanitized HTTP method, request stage, host and path pattern for every provider request without publishing query values or tokens.
- Detect origin-reachable providers whose search/content routes mostly return 404/410 and publish `route-regressions.json`.
- Add an optional strict route gate for providers with validated route overrides.
- Preserve route diagnostics through the worker, health report and HTML/JSON diagnostics pipeline.
- Add regression tests for route-obsolescence detection and override schema validation.

## 5.14.4

- Persist the locally verified Frenchstream domain replacement: `french-stream.one` → `frenchstream.food`.
- Require the final published Frenchstream provider to contain `frenchstream.food`.
- Require the final published StreamZo provider to retain the verified `streamzo.fr` domain.
- Validate required domain values in both staging and final published provider files.
- Update Frenchstream logo URLs in the main and VF manifests.

# Changelog

## 5.17.4

- Fix the generic HTML-search patcher so it replaces complete top-level functions without deleting nested or adjacent helpers.
- Add syntax, load, and runtime smoke validation for every generated `--nuvio--` provider artifact.
- Reject invalid patched candidates before staging and revalidate the exact bytes before publication.
- Persist provider manifest metadata overrides, including the current Frenchstream favicon domain.
- Realign package, main manifest, VF manifest, and source manifest versions.

## 5.14.3

- Synchronize `manifest.json` and `vf/manifest.json` on version `5.14.2`.
- Treat `repository.manifest_version` as a version floor so unchanged runs cannot preserve an obsolete 5.13.x series.
- Add regression tests for manifest-series migration and normal patch increments.

## 5.14.1

- Added an end-to-end override pipeline gate that inspects the exact staged JavaScript later executed and promoted.
- Movix staging now fails if `api.movix.cash` survives or if a recorded replacement does not produce `api.movix.show`.
- Provenance now records `upstream_sha256`, `patched_sha256`, and `local_patches` for every selected provider.


## 5.14.0

- Added SSRF/DNS-rebinding protection for provider and media probes.
- Validate each redirect manually and reject private or metadata destinations.
- Added provider request, redirect and response-size quotas.
- Added durable, centrally tracked provider/domain overrides.
- Movix `api.movix.cash` is replaced with `api.movix.show` during staging.
- Preserve upstream SHA-256 separately from the locally patched SHA-256.
- Added stage-oriented JSON and HTML diagnostic reports.
- Added regression tests for the network guard and override pipeline.
- CI now runs the complete regression suite before upstream discovery.

## Current-proof pipeline correction

- Reordered the deep workflow around DNS/domain recovery, provider-specific access, then stream quality.
- Removed activation through historical SHA grace, inconclusive manifest preservation, and manual runtime evidence.
- Providers are enabled only when the current deep run proves DNS, successful provider-owned access, a playable stream, and all quality gates.
- Reset the historical LKG registry; future records require exact-SHA, fixture, category, timestamp, and positive stream-count evidence.
