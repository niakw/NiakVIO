# Assets NiakVIO

Ce dossier contient les assets visuels et les feeds **StreamBadge** utilisés avec les clients Nuvio compatibles.

## Feeds StreamBadge

| Feed | Usage | URL brute |
| --- | --- | --- |
| **Fusion v2** | **Recommandé** pour un réglage unique, lisible sur fonds sombres et clairs | `https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v3.json` |
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
- `stream-badges-fusion-v3.json` : feed Fusion recommandé ;
- `stream-badges-dark.json` : feed Dark ;
- `stream-badges-light.json` : feed Light.

Les assets sont générés et validés de façon déterministe par les scripts/tests du dépôt. Évitez de modifier uniquement un feed généré à la main : la source canonique doit rester cohérente avec les trois variantes.

## Couverture technique v2.2

Le catalogue canonique couvre désormais 122 badges répartis dans 15 groupes. Il inclut les sources vidéo usuelles, les résolutions de 240p à 8K/4320p, les conteneurs courants, codecs vidéo, HDR/bit depth, fréquences d'image usuelles, débit vidéo, technologies/codecs/canaux audio, fréquences d'échantillonnage, langues normalisées du Core, sous-titres et classifications d'âge.

Les mesures continues restent exactes dans la ligne technique : par exemple `6.0 Mbps` reste la valeur affichée, tandis que le badge `BITRATE` indique la présence fiable de cette donnée. Les fréquences d'image et d'échantillonnage utilisent des badges pour les valeurs usuelles normalisées.

`stream-badges-fusion-v3.json`, le feed recommandé, est désormais régénéré et validé depuis la même source canonique que Dark, Light et Fusion afin d'empêcher toute dérive.

## Politique de version des feeds publics

**Règle obligatoire : toute modification matérielle du système de badges impose un bump de version public.** Cela inclut l'ajout, le retrait ou le renommage d'un badge, une modification de pattern, de groupe, de style, d'asset, de sémantique de langue/sous-titre/classification ou de chemin public.

À chaque bump `vN → vN+1`, les quatre snapshots immuables doivent être publiés ensemble :

- `stream-badges-fusion-vN.json`
- `stream-badges-dark-vN.json`
- `stream-badges-light-vN.json`
- `stream-badges-transparent-vN.json`

Les fichiers sans numéro (`stream-badges-fusion.json`, `stream-badges-dark.json`, `stream-badges-light.json`, `stream-badges-transparent.json`) sont uniquement des alias **latest**. Les README et guides publics doivent toujours pointer vers la nouvelle version numérotée, jamais vers `latest`.

Une version publiée est immuable. Le générateur refuse désormais de réécrire un `vN` existant avec un contenu différent : il faut d'abord incrémenter `PUBLIC_FEED_VERSION`. Les anciennes versions et leurs anciens assets restent disponibles pour les utilisateurs qui les ont épinglés.

### Version publique actuelle : v3

| Variante | Fichier stable |
| --- | --- |
| Fusion | `stream-badges-fusion-v3.json` |
| Dark | `stream-badges-dark-v3.json` |
| Light | `stream-badges-light-v3.json` |
| Transparent | `stream-badges-transparent-v3.json` |

### Compatibilité historique

`stream-badges-fusion-v2.json` reste publié tel quel pour les installations existantes. Les anciens WebP qu'il référence sont volontairement conservés même lorsqu'ils ne font plus partie du catalogue v3.

## Langues et classifications v3

Les badges publics de langue utilisent désormais des identifiants universels de type ISO/BCP-47 (`FR`, `FR-CA`, `EN`, `KO`, `JA`, `ES-419`, `PT-BR`, `ZH-TW`, etc.). `VF`, `VFF`, `VFQ`, `VO`, `MULTI` et `VOSTFR` ne sont plus des IDs publics v3. Ils peuvent rester reconnus dans les patterns comme alias d'entrée historiques afin de convertir les données anciennes vers le badge universel correspondant.

Les sous-titres suivent exactement la même logique (`SUB FR`, `SUB KO`, `SUB JA`, etc.). Les classifications d'âge distinguent les systèmes régionaux lorsqu'ils sont explicites (`US PG-13`, `KR 19`, `FSK 16`, `IN UA 16+`, etc.) et utilisent des âges numériques universels lorsque seule une limite d'âge est disponible.
