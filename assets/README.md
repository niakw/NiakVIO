# Assets NiakVIO

Ce dossier contient les assets visuels et les feeds **StreamBadge** utilisés avec les clients Nuvio compatibles.

## Feeds StreamBadge

| Feed | Usage | URL brute |
| --- | --- | --- |
| **Fusion v2** | **Recommandé** pour un réglage unique, lisible sur fonds sombres et clairs | `https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v2.json` |
| Dark | Variante pour interfaces sombres | `https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-dark.json` |
| Light | Variante pour interfaces claires | `https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-light.json` |

Le feed historique `stream-badges-fusion.json` reste présent pour compatibilité. Pour un nouvel import, utilisez **Fusion v2**.

## Feed badges et manifest providers sont séparés

Le manifest NiakVIO charge les providers. Les règles StreamBadge sont une configuration distincte du client Nuvio.

Réinstaller ou rafraîchir le manifest **ne recharge donc pas automatiquement les règles de badges**.

## Cache / réimport NuvioTV

NuvioTV enregistre localement les règles d'un feed au moment de son import. Une URL déjà importée peut donc continuer à utiliser l'ancienne copie des filtres même si le JSON distant a été corrigé.

Symptôme typique :

- l'aperçu des badges/images fonctionne ;
- les streams réels n'affichent pourtant aucun badge ;
- le même feed fonctionne avec une URL différente ou sur un profil propre.

Dans ce cas :

1. supprimez l'ancien import StreamBadge ;
2. importez **Fusion v2** avec l'URL versionnée ci-dessus ;
3. vérifiez que Fusion v2 est l'import actif ;
4. revenez à l'écran des streams.

L'URL versionnée permet de forcer un import neuf et évite de dépendre de l'ancienne copie locale de `stream-badges-fusion.json`.

## Comment le matching fonctionne

NuvioTV compile directement le champ `pattern` de chaque filtre comme expression régulière. Le matcher cherche ces motifs dans plusieurs champs du stream, notamment :

- `filename` et `behaviorHints.filename` ;
- `name` ;
- `title` ;
- `description` ;
- les informations techniques parsées quand elles existent.

NiakVIO veille donc à faire survivre les faits utiles dans la présentation des streams : qualité, source, codec, HDR, audio, langue, etc. C'est ce qui permet aux règles de reconnaître des tokens comme `2160p`, `WEB-DL`, `HEVC`, `HDR10+`, `MULTI`, `VFF`, etc.

## Regex

Après décodage JSON, Nuvio attend **un seul antislash runtime** pour les séquences regex telles que `\b`.

Les tests NiakVIO interdisent désormais les patterns double-échappés qui rendaient les badges invisibles dans les streams réels.

## Sources et mapping

- `badge_catalog_v2_complete.json` : catalogue canonique ;
- `mapping_core_brain_ui_v2_complete.json` : mapping Core / Brain / UI ;
- `stream-badges-fusion-v2.json` : feed Fusion recommandé ;
- `stream-badges-dark.json` : feed Dark ;
- `stream-badges-light.json` : feed Light.

Les assets sont générés et validés de façon déterministe par les scripts/tests du dépôt. Évitez de modifier uniquement un feed généré à la main : la source canonique doit rester cohérente avec les trois variantes.
