# Assets NiakVIO

Ce dossier contient les assets visuels et les feeds **StreamBadge** utilisés avec les clients Nuvio compatibles.

**Guide technique et cinéphile :** [comprendre les badges et les données média](../docs/fr/stream-badges-technical-guide.md)

## Feeds StreamBadge

| Feed | Usage | URL brute |
| --- | --- | --- |
| **Fusion v8** | **Recommandé** pour un réglage unique, lisible sur fonds sombres et clairs | `https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v8.json` |
| Dark v8 | Variante pour interfaces sombres | `https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-dark-v8.json` |
| Light v8 | Variante pour interfaces claires | `https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-light-v8.json` |
| Transparent v8 | Artwork transparent / intégrations dédiées | `https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-transparent-v8.json` |

Les fichiers sans numéro restent des alias mobiles `latest`. Pour tout nouvel import et toute documentation publique, utilisez une URL **v8** explicite.

## Feed badges et manifest providers sont séparés

Le manifest NiakVIO charge les providers. Les règles StreamBadge sont une configuration distincte du client Nuvio.

Actualiser ou réinstaller le manifest **ne recharge donc pas automatiquement les règles de badges**. Si le plugin est récent mais que les badges restent anciens, réimportez le feed StreamBadge versionné.

## Cache / réimport StreamBadge

Nuvio peut conserver localement les règles d'un feed au moment de son import. Une URL déjà importée peut donc continuer à utiliser une ancienne copie.

Symptôme typique :

- l'aperçu des badges/images fonctionne ;
- les streams réels n'affichent pourtant aucun badge ;
- le même feed fonctionne avec une URL versionnée différente ou sur un profil propre.

Dans ce cas :

1. supprimez l'ancien import StreamBadge ;
2. importez **Fusion v8** avec l'URL versionnée ci-dessus ;
3. vérifiez que Fusion v8 est l'import actif ;
4. revenez à l'écran des streams.

## Comment le matching fonctionne

Nuvio compile le champ `pattern` de chaque filtre comme expression régulière et cherche les faits dans plusieurs champs du stream, notamment :

- `filename` et `behaviorHints.filename` ;
- `name` et `title` ;
- `description` ;
- les informations techniques structurées lorsque le provider ou le Core les connaît.

NiakVIO fait survivre les faits utiles jusqu'à la présentation : qualité, source, livraison HLS/DASH, conteneur, codec, HDR, bit depth, framerate, bitrate, audio, langue, sous-titres et classification.

Un fait inconnu reste inconnu : le système ne doit pas fabriquer `1080p`, `HEVC`, `HDR` ou une langue à partir d'une simple supposition. Les placeholders `Unknown`, `Inconnue`, `N/A` ou `Auto` ne doivent pas devenir des badges ou des suffixes de titre.

## Regex

Après décodage JSON, Nuvio attend **un seul antislash runtime** pour les séquences regex telles que `\b`.

Les tests NiakVIO interdisent les patterns double-échappés qui rendraient les badges invisibles dans les streams réels.

## Sources et mapping

- `badge_catalog_v8_complete.json` : catalogue canonique courant ;
- `mapping_core_brain_ui_v8_complete.json` : mapping Core / Brain / UI courant ;
- `stream-badges-fusion-v8.json` : feed Fusion stable recommandé ;
- `stream-badges-dark-v8.json` : feed Dark stable ;
- `stream-badges-light-v8.json` : feed Light stable ;
- `stream-badges-transparent-v8.json` : feed Transparent stable.

Les assets sont générés et validés de façon déterministe. Ne modifiez pas uniquement un feed généré à la main : la source canonique doit rester cohérente avec les quatre variantes.

## Couverture technique v4

Le catalogue canonique v8 couvre **309 badges répartis dans 17 groupes**.

La surface comprend notamment :

- sources : CAM, TS/Telesync, TC/Telecine, WEBRip, WEB-DL, HDTV, DVD, Blu-ray, BDMV, BD REMUX, UHD Blu-ray, UHD REMUX ;
- résolutions : 240p, 360p, 480p, 576p, 720p, **1080i**, 1080p, 1440p, 2160p/4K et 4320p/8K ;
- livraison / conteneurs : **HLS**, **MPEG-DASH**, MKV, MP4, WebM, MPEG-TS, M2TS ;
- vidéo : AVC/H.264, HEVC/H.265, AV1, VP9, MPEG-2, VC-1, MPEG-4 Part 2, 8/10/12-bit, SDR/HDR/HDR10/HDR10+/Dolby Vision/HLG, IMAX et 3D ;
- framerate : 23.976, 24, 25, 29.97, 30, 50, 59.94 et 60 fps ;
- audio : AAC, AC-3, E-AC-3, TrueHD, Atmos, DTS/DTS-HD/DTS:X, FLAC, PCM/LPCM, Opus, MP3, ALAC, 1.0 à 7.1 et 44.1 à 192 kHz ;
- score global de flux : **8 grades compacts** `S+`, `S`, `A+`, `A`, `B`, `C`, `D`, `E` ;
- **47 langues**, **49 variantes de sous-titres** et **118 classifications d'âge**.

Le groupe `stream-score` est volontairement placé en premier dans l'ordre public. Quand un score global est suffisamment prouvé, son badge `S+`/…/`E` doit donc être le premier repère visible avant les badges techniques détaillés.

Les mesures continues restent exactes dans la description : par exemple `6.0 Mbps` reste la valeur affichée, tandis que le badge `BITRATE` signale que cette donnée est réellement connue.

## Politique de version des feeds publics

**Règle obligatoire : toute modification matérielle du système de badges impose un bump de version public.**

Cela inclut l'ajout, le retrait ou le renommage d'un badge, une modification de pattern, de groupe, de style, d'asset, de sémantique de langue/sous-titre/classification ou de chemin public.

À chaque bump `vN → vN+1`, les quatre snapshots immuables sont publiés ensemble :

- `stream-badges-fusion-vN.json`
- `stream-badges-dark-vN.json`
- `stream-badges-light-vN.json`
- `stream-badges-transparent-vN.json`

Les fichiers sans numéro sont uniquement des alias **latest**. Les README et guides publics doivent toujours pointer vers la nouvelle version numérotée.

Une version publiée est immuable. Cela vaut pour les **feeds, catalogues et mappings versionnés** : ne jamais modifier, renommer ni supprimer un `badge_catalog_vN_complete.json`, `mapping_core_brain_ui_vN_complete.json` ou `stream-badges-*-vN.json` déjà publié. Toute modification/ajout de badge crée un nouveau `vN+1`, puis les références courantes basculent vers celui-ci. Les anciennes références restent disponibles pour la compatibilité épinglée.

Le générateur refuse de réécrire un feed `vN` existant avec un contenu différent. Le workflow vérifie aussi qu'un catalogue/mapping/feed versionné déjà publié n'est pas modifié ou supprimé.

### Version publique actuelle : v8

| Variante | Fichier stable |
| --- | --- |
| Fusion | `stream-badges-fusion-v8.json` |
| Dark | `stream-badges-dark-v8.json` |
| Light | `stream-badges-light-v8.json` |
| Transparent | `stream-badges-transparent-v8.json` |

### Compatibilité historique

Les quatre snapshots **v6**, **v5**, **v4** et **v3** restent publiés et immuables pour les installations épinglées. `stream-badges-fusion-v2.json` reste également disponible pour les anciens utilisateurs, avec les anciens WebP qu'il référence.

Les anciens `badge_catalog_v2_complete.json` et `mapping_core_brain_ui_v2_complete.json` sont conservés **intacts** comme références historiques/compatibilité. Des snapshots v4 explicites existent désormais également ; le catalogue/mapping courant est v8. Aucun ancien chemin versionné ne doit être recyclé pour une nouvelle version.

## Langues et classifications

Les badges publics de langue utilisent des identifiants universels de type ISO/BCP-47 (`FR`, `FR-CA`, `EN`, `KO`, `JA`, `ES-419`, `PT-BR`, `ZH-TW`, etc.).

`VF`, `VFF`, `VFQ`, `VO`, `MULTI` et `VOSTFR` ne sont pas des IDs publics actuels. Ils peuvent rester reconnus comme **alias d'entrée historiques** afin de convertir les anciennes données vers des faits universels.

Les sous-titres suivent la même logique (`SUB FR`, `SUB KO`, `SUB JA`, etc.). Les classifications d'âge distinguent les systèmes régionaux lorsqu'ils sont explicites (`US PG-13`, `KR 19`, `FSK 16`, `IN UA 16+`, etc.) et utilisent un âge numérique générique uniquement lorsque seule une limite d'âge est connue.
