# Mise en production rapide — Global et France (2026-11-14)

Ajout sur les **URLs de production existantes** sans changement de liens :
- Global `manifest.json` : KissKH, VidEasy, VidLink.
- France `vf/manifest.json` : Movix, Nakios, FrenchStream. Ces trois IDs ne figurent pas dans Global.

Scripts: provenance source maintenue dans `vf/production-source.json`, bundles amont épinglés et content-addressed sous `providers/`, projection no-anime synchronisée. Les autres providers existants n'ont pas été retirés, afin d'éviter une régression de l'installation Global actuellement utilisée.

Source code : `NuvioPlugin/All-in-One-Nuvio@3f09a6ff4360498895e622877af7a32212f75038` (Global) et `Gowaru/gowaru-nuvio-providers@66494c595865fd2e6d664876935d577389eb23b6` (France).

**Validation importante:** les modules sont des implémentations Nuvio amont, importées en production sur demande explicite, mais aucune lecture terminale, identité TMDB/épisodes, qualité HD/4K, headers, sous-titre ou décodage par l'application NiakVIO n'est prouvée par cet import. Ils doivent être soumis aux Labs, à la réconciliation Provider v3 et aux vérifications de sécurité ; le nombre de nouveaux flux fonctionnels demeure inconnu.

Si un automatisme regenerateur écrase un provider France-only, c'est une régression de pipeline et non un échec à masquer par une réinjection manuelle.
