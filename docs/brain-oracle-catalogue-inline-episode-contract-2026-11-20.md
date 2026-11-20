# Brain — Oracle de contrat des épisodes inline (20 novembre 2026)

## Sources et fiabilité

Le commit upstream [Anime-Sama FR — Site Redesign & Lib 16 du 13 novembre 2026](https://github.com/yuzono/anime-extensions/commit/414c9bc8c8c2b904232264f279d9b4e814c4bde9) décrit un changement de structure de l'extraction d'épisodes. Une implémentation indépendante actuelle extrait depuis les scripts HTML de la page des tableaux eps1/eps2, un epsJeton, une carte epsMeta, une carte de lecteurs et les langues disponibles. Les valeurs lien: sont des identifiants opaques, résolus par une API distincte du même site. Le choix de la saison/langue doit suivre le chemin publié par le catalogue plutôt qu'inventer systématiquement saison1.

Ce dépôt upstream constitue une **référence de contrat**, pas une preuve que le domaine ou le corps HTTP atteint depuis NuvioTV est identique. Les pages de présentation et hubs publics sont contradictoires au sujet des domaines ; ni une page auto-déclarée officielle ni un 200 ne suffisent à valider un domaine. Il est interdit de recopier un jeton, un HTML brut, une URL signée ou d'en tirer automatiquement une réparation de provider.

## Différence observée dans NiakVIO

Le Lego actuel dans scripts/provider_patches/anime_sama_runtime_v1.py recherche des fichiers externes episodes.js et des tableaux contenant directement des URL média. Les overrides actuels déclarent encore ce contrat et ne possèdent aucun resolver inline-token avec epsJeton + api/lien.php. Le diagnostic officiel **Anime-Sama** expose les enums exacts `script_http_missing` (HTTP 404/410) et `script_html_2xx` (HTTP 2xx qui contient du HTML à la place du JavaScript attendu). Ces deux signatures sont des observations, pas une preuve du nouveau schéma inline `catalogue_inline_token_episode` ni une autorisation de mutation.

Les preuves natives du [run 44781039914](https://github.com/niakw/NiakVIO/actions/runs/44781039914), source exacte e7c7c9206182f27df4537465e614b1c5dfacb408, montrent 404/410 ou 2xx HTML sur la ressource attendue puis zéro flux pour Mushoku Tensei S01E01. Le feedback [44784359819](https://github.com/niakw/NiakVIO/actions/runs/44784359819) a bien conservé ces signatures, mais la réponse HTML n'est pas encore attestée comme étant une page d'épisode au nouveau schéma. Ces observations établissent un **candidat de dérive de contrat**, pas une cause certifiée.

## Mécanisme familial et portes de validation

L'oracle générique scripts/brain_oracles/catalogue_inline_episode_source.py classe des réponses HTTP en source externe ancienne, contenu HTML sans source exécutable, ressource JS absente ou page d'épisode inline avec identifiant opaque + jeton. Il ne fait aucune requête réseau, n'exécute aucun code upstream, ne résout aucun média et ne conserve que des enums et booléens. tests/brain_oracles/catalogue_inline_episode_source_test.py couvre les faux positifs, les réponses 404, les limites de taille, la non-divulgation de secrets et l'absence d'autorité de mutation. La comparaison avec le Lego actuel est faite sur un HTML **synthétique**, non sur des bytes live.

La prochaine preuve causale demande : provenance du domaine du client réel ; route catalogue et identité exactes ; chemin de saison et voix réellement annoncé ; classification de la réponse HTML du client sur cette route ; résolution contrôlée des identifiants ; génération d'un Lego familial réutilisable ; compilation et rematérialisation isolée ; lecture de l'épisode correct sur NuvioTV officiel ; pistes audio et sous-titres ; test d'un sibling de signature causale compatible. Zéro réparation produit certifiée, aucun changement de provider, Core ou manifest.
