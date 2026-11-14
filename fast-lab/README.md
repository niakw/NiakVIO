# Fast Lab — nouveaux providers Global / France (14 novembre 2026)

> Statut: **catalogue expérimental uniquement**. Aucun des six providers ci-dessous n'a été validé en lecture terminale (décodage) sur TV/Mobile/Desktop NiakVIO à cette date. **Ne pas considérer un manifest chargé, un lien retourné, une route atteinte ou une disponibilité amont comme un flux réellement lisible.**

## Pourquoi cette voie

L'inventaire remis par l'utilisateur (classeur « NiakVIO-GLOBAL-FINAL-STRICT-TOP20-2026-09-11(2).xlsx », onglets **Global** 259 et **France** 81) date du 11 septembre 2026. Ses URL et rangs servent à découvrir des candidats, pas à certifier une lecture actuelle.

On privilégie les modules **déjà distribués au format Nuvio** par leurs mainteneurs amont plutôt que de repartir d'un reverse engineering, afin de tester vite sans retarder la réparation structurelle du Brain.

## Manifests de test, séparés sans recouvrement

| Projection | URL de test | Providers |
| --- | --- | --- |
| **Global** | [fast-lab/global/manifest.json](global/manifest.json) | KissKH, VidEasy, VidLink |
| **France uniquement** | [fast-lab/france/manifest.json](france/manifest.json) | Movix, Franime, Nakios |

**URLs publiques directes :**

- Global : `https://raw.githubusercontent.com/niakw/NiakVIO/main/fast-lab/global/manifest.json`
- France : `https://raw.githubusercontent.com/niakw/NiakVIO/main/fast-lab/france/manifest.json`

Les IDs des deux listes ne se recouvrent pas et aucun n'est déjà dans les 41 lignes du `manifest.json` de production. Dans ce **Fast Lab uniquement**, un provider français n'est pas ajouté à Global. Les scripts Nuvio de chaque candidat pointent vers un **commit amont exact** dans `filename`, jamais vers `main` mouvant.

## Sources et sélection

| Provider | Groupe | Score de sélection | Source du script épinglée | Architecture / risque | Statut réel |
| --- | --- | --- | --- | --- | --- |
| KissKH | Global | Rang 2 | `NuvioPlugin/All-in-One-Nuvio@3f09a6ff4360498895e622877af7a32212f75038` | Extraction Nuvio existante; TMDB/TVDB et backend spécifique; source obfusquée, correspondance domaine à confirmer | **Non testé terminalement** |
| VidEasy | Global | Inventaire Global | Même commit | Module Nuvio court, lecteur/serveur externe; risque de changement de domaine | **Non testé terminalement** |
| VidLink | Global | Inventaire Global | Même commit | Module Nuvio court, route lecteur externe; transport et headers à valider | **Non testé terminalement** |
| Movix | France | Rang 3 | `Gowaru/gowaru-nuvio-providers@66494c595865fd2e6d664876935d577389eb23b6` | Module de 309 Ko; logique anti-bot/captcha optionnelle; candidat prioritaire mais **pas** une intégration facile tant que parcours réel non prouvé | **Non testé terminalement** |
| Franime | France | Inventaire France | Même commit | Module d'environ 35 Ko; API `api.franime.fr`, anime francophone; le plus simple à sonder | **Non testé terminalement** |
| Nakios | France | Inventaire France | Même commit | Backend REST `api.nakios.store`; direct MP4 annoncé amont, qualités non prouvées | **Non testé terminalement** |

**Rejets temporaires du lot rapide :** ShowBox (souvent dépendant de cookie/token FebBox; anciennes sources déjà dans `providers/` mais absentes du manifest actif), VidSrc (version amont ciblant des domaines différents de l'inventaire), FrenchStream / Webflix (blocs anti-bot + gros modules), Coflix/Purstream/Anime-Sama (déjà au catalogue, aucun gain de couverture à les dupliquer).

## Politique de validation

Ne promouvoir sur les manifests de production qu'après :
1. Vérification du bundle JS et de ses dépendances, sans comportement non autorisé.
2. Chargement par le client Nuvio (TV ou Mobile + Desktop si applicable).
3. Épreuve **film + série avec identité TMDB et saison/épisode exacts** et **anime** lorsque la capacité est déclarée.
4. Résolution des médias terminaux, contrôle des redirects/headers et lecture réellement décodée; pour HLS, playlists/segments valides.
5. Capture de langue, qualité **réellement mesurée** (1080p/4K), doublons, faux positifs, sous-titres, badges et StreamScore.
6. Non-régression et transcription de la preuve sur le SHA exécuté; ensuite seulement activation côté utilisateurs et mise à jour census/registre.

**État production au moment du staging :** `manifest.json` 41 entrées, `vf/manifest.json` 21 entrées, même version `5.21.143`. La règle *Global et France totalement disjoints dans les manifests de production* **n'est pas encore migrée**. En effet `scripts/generate_language_manifests.py` fabrique la sélection VF depuis `manifest.json`; vider Global des Français sans découpler les sources effacerait tous les Français de `vf/manifest.json` au prochain rebuild. Le laboratoire préserve l'existant sans prétendre accomplir cette migration.

## Règles

- Ce Fast Lab **n'est pas** le manifest Hub-46 ni le feed officiel.
- Ne pas annoncer « 6 flux de plus » tant que le test de lecture réel n'a pas passé.
- Ne pas transformer un statut de source Nuvio tierce en preuve NiakVIO.
- Une future promotion doit matérialiser des scripts maîtrisés/qualifiés, avec provenance, code/identité et politique de sélection explicites.
