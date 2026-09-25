# NiakVIO StreamBadges — guide technique et cinéphile

[English](../stream-badges-technical-guide.md) · [Installer les StreamBadges](how-to-add-stream-badges.md) · [Retour au README](../../README.fr.md)

Les StreamBadges NiakVIO ne sont pas une note de qualité. Ils constituent un vocabulaire compact de **faits techniques sur un flux** : source, résolution, mode de livraison, conteneur, codec vidéo, HDR, framerate, bitrate, audio, langues, sous-titres et classification.

> **Règle :** afficher ce qui est connu, laisser inconnu ce qui ne l'est pas. Un badge `HLS` vrai vaut mieux qu'un faux `1080p`, `HEVC` ou `HDR`.

Feed stable actuel : `assets/stream-badges-fusion-v8.json` — **309 badges / 17 groupes**.

## Repère visuel rapide

Les marqueurs ci-dessous sont une **aide de lecture, pas une note universelle de qualité**. Ils classent uniquement la dimension indiquée par le tableau ; il ne faut pas les additionner aveuglément.

| Marqueur | Lecture |
| --- | --- |
| 🏆 | Top / potentiel maximal dans cette dimension |
| 🟢 | Fort / moderne / potentiel élevé |
| 🟡 | Solide, variable ou dépendant du contexte |
| 🟠 | Limité, ancien ou potentiel plus faible |
| 🔴 | Faible / fortement compromis |
| ⚪ | Fait neutre — pas de classement pertinent |

Pour estimer la qualité d'image réelle, il faut lire plusieurs faits ensemble : **source + codec + résolution + bitrate**.

## Lire un flux comme une fiche média

Exemple :

`AVC · 1920×1080 · 6,0 Mbps · 23,976 fps · AAC · Stéréo · 48 kHz · Coréen`

| Donnée | Ce qu'elle signifie |
| --- | --- |
| AVC / H.264 | Codec vidéo extrêmement répandu. À qualité visuelle comparable, il demande généralement plus de bitrate que HEVC ou AV1. |
| 1920×1080 | Full HD / 1080p. Cela ne dit **pas** si la source est Blu-ray ou WEB-DL. |
| 6,0 Mbps | Débit vidéo plausible pour un encode streaming 1080p, mais pas une note de qualité. |
| 23,976 fps | Cadence cinéma/anime très courante dérivée du 24 fps. |
| AAC | Codec audio avec pertes très répandu en streaming. |
| Stéréo / 2.0 | Deux canaux audio. |
| 48 kHz | Fréquence d'échantillonnage standard en film, TV et anime. |
| Coréen | Langue audio normalisée vers le badge universel `KO`. |

<img src="../../assets/transparent/96x40/1080p-full-hd.webp" height="30" alt="1080p"> <img src="../../assets/transparent/96x40/avc.webp" height="30" alt="AVC"> <img src="../../assets/transparent/96x40/video-bitrate.webp" height="30" alt="Bitrate"> <img src="../../assets/transparent/96x40/23.976fps.webp" height="30" alt="23.976 fps"> <img src="../../assets/transparent/96x40/aac.webp" height="30" alt="AAC"> <img src="../../assets/transparent/96x40/2.0.webp" height="30" alt="2.0"> <img src="../../assets/transparent/96x40/48khz.webp" height="30" alt="48 kHz"> <img src="../../assets/transparent/96x40/lang-ko.webp" height="30" alt="KO">

## Source ≠ résolution ≠ livraison ≠ conteneur

Ces quatre familles décrivent des choses différentes.

### Source / provenance

| Famille | Potentiel qualité | Signification pratique |
| --- | --- | --- |
| BD REMUX / UHD REMUX | 🏆 Top | Pistes du disque repackagées sans réencoder l'essence vidéo/audio. Fichiers généralement volumineux. |
| UHD Blu-ray | 🏆 Top | Source disque Ultra HD, fréquemment 2160p avec vidéo compatible HDR. |
| Blu-ray / BDMV | 🟢 Très élevé | Source ou structure issue d'un disque Blu-ray. |
| WEB-DL | 🟢 Élevé | Livraison directe issue d'un service web, généralement sans étape de recapture vidéo. |
| HDTV | 🟡 Variable | Source issue d'une diffusion TV ; la qualité dépend fortement de la chaîne, de la génération et du bitrate. |
| WEBRip | 🟡 Variable | Capture ou réencodage depuis une source web ; qualité très variable. |
| DVD / DVD Rip | 🟠 Limité | Source optique SD. |
| CAM / TS / TC | 🔴 Faible | Provenance de capture cinéma ; généralement très compromise face aux sources numériques directes. |

<img src="../../assets/transparent/96x40/webdl.webp" height="30" alt="WEB-DL"> <img src="../../assets/transparent/96x40/blu-ray-disc.webp" height="30" alt="Blu-ray"> <img src="../../assets/transparent/96x40/bdmv.webp" height="30" alt="BDMV"> <img src="../../assets/transparent/96x40/blu-ray-remux.webp" height="30" alt="BD REMUX"> <img src="../../assets/transparent/96x40/uhd-remux.webp" height="30" alt="UHD REMUX">

### Résolution et mode de balayage

Les classes courantes vont de 240p à 8K/4320p et incluent **1080i**.

| Classe de résolution | Potentiel de détail | Lecture pratique |
| --- | --- | --- |
| 4320p / 8K | 🏆 Top | Potentiel de détail raster maximal de cette liste ; utile seulement si la source et l'encodage conservent réellement ce détail. |
| 2160p / 4K | 🟢 Très élevé | Excellent potentiel sur grand écran ; souvent associé à HEVC/AV1 et HDR. |
| 1440p | 🟢 Élevé | Gain net face au 1080p, mais moins courant pour les films/séries. |
| 1080p | 🟢 Fort | Référence Full HD du streaming moderne de bonne qualité. |
| 1080i | 🟡 Contextuel | Raster Full HD mais entrelacé ; la qualité du désentrelacement compte. |
| 720p | 🟡 Bon | Peut être excellent avec une bonne source et un bitrate généreux, notamment en animation. |
| 576p / 480p | 🟠 Limité | Définition standard ; nettement plus douce sur les grands écrans modernes. |
| 360p / 240p | 🔴 Faible | Faible niveau de détail, surtout utile quand la bande passante est contrainte. |

- **1080p** = Full HD progressif.
- **1080i** = Full HD entrelacé, encore rencontré dans des sources TV/broadcast.
- Un film recadré peut ne pas mesurer exactement 1920×1080 tout en appartenant à la classe 1080p.
- La résolution seule ne renseigne ni la source, ni l'efficacité du codec, ni les artefacts de compression.

<img src="../../assets/transparent/96x40/720p-hd.webp" height="30" alt="720p"> <img src="../../assets/transparent/96x40/1080i.webp" height="30" alt="1080i"> <img src="../../assets/transparent/96x40/1080p-full-hd.webp" height="30" alt="1080p"> <img src="../../assets/transparent/96x40/4k-ultra-hd.webp" height="30" alt="4K"> <img src="../../assets/transparent/96x40/8k-ultra-hd.webp" height="30" alt="8K">

### Livraison et conteneur

**HLS** et **MPEG-DASH** décrivent une livraison HTTP adaptative. **MKV, MP4, WebM, MPEG-TS et M2TS** sont des conteneurs/formats de fichier.

| Badge | Repère | Signification |
| --- | --- | --- |
| HLS / M3U8 | ⚪ Contexte | Streaming HTTP adaptatif. Un master peut annoncer plusieurs variantes, codecs et pistes de langue. |
| MPEG-DASH / MPD | ⚪ Contexte | Livraison HTTP adaptative fondée sur un manifest MPD. |
| MKV / Matroska | ⚪ Contexte | Conteneur souple très courant pour Blu-ray/anime et pistes multiples. |
| MP4 | ⚪ Contexte | Conteneur extrêmement compatible. |
| MPEG-TS / M2TS | ⚪ Contexte | Familles de transport streams courantes en broadcast, segments HLS et structures Blu-ray. |

**Pas de gagnant ici :** le mode de livraison ou le conteneur ne détermine pas à lui seul la qualité d'image.

<img src="../../assets/transparent/96x40/hls.webp" height="30" alt="HLS"> <img src="../../assets/transparent/96x40/dash.webp" height="30" alt="DASH"> <img src="../../assets/transparent/96x40/mkv.webp" height="30" alt="MKV"> <img src="../../assets/transparent/96x40/mp4.webp" height="30" alt="MP4">

Un provider peut légitimement n'afficher que **HLS** si l'URL `.m3u8` est prouvée mais qu'aucune qualité/codec fiable n'est disponible.

## Codecs vidéo

| Codec | Efficacité de compression | Usage courant | À retenir |
| --- | --- | --- | --- |
| AV1 | 🏆 Top | Streaming moderne | Très haute efficacité de compression ; support matériel plus récent. |
| HEVC / H.265 | 🟢 Très élevée | UHD Blu-ray, 4K streaming, anime 10-bit | Efficace ; très courant avec HDR et 10-bit. |
| VP9 | 🟢 Élevée | Streaming web | Codec web important, historiquement très utilisé par Google. |
| AVC / H.264 | 🟡 Solide | Blu-ray et streaming très répandu | Très compatible ; demande généralement plus de bitrate que HEVC/AV1 à qualité visuelle comparable. |
| MPEG-2 / VC-1 / MPEG-4 Part 2 | 🟠 Ancien | Diffusions/disques/encodes plus anciens | Information utile de compatibilité et de provenance ; généralement moins efficace que les codecs modernes. |

Ces marqueurs comparent **l'efficacité de compression de manière générale**, pas la qualité de chaque encode. Un excellent AVC peut toujours battre un mauvais encode AV1/HEVC.

<img src="../../assets/transparent/96x40/avc.webp" height="30" alt="AVC"> <img src="../../assets/transparent/96x40/hevc.webp" height="30" alt="HEVC"> <img src="../../assets/transparent/96x40/av1.webp" height="30" alt="AV1"> <img src="../../assets/transparent/96x40/vp9.webp" height="30" alt="VP9">

**x264/x265 sont des encodeurs** ; AVC/H.264 et HEVC/H.265 sont les standards de codec. NiakVIO normalise les alias vers le bon fait technique.

## Bit depth, HDR et formats de présentation

NiakVIO distingue 8-bit, 10-bit et 12-bit de la plage dynamique.

- **10-bit ne signifie pas automatiquement HDR.** Beaucoup d'encodes anime de qualité sont 10-bit SDR.
- La famille HDR couvre SDR, HDR générique, HDR10, HDR10+, Dolby Vision et HLG.
- IMAX, IMAX Enhanced et 3D sont des informations séparées.

<img src="../../assets/transparent/96x40/10bit.webp" height="30" alt="10-bit"> <img src="../../assets/transparent/96x40/hdr10.webp" height="30" alt="HDR10"> <img src="../../assets/transparent/96x40/hdr10-plus.webp" height="30" alt="HDR10+"> <img src="../../assets/transparent/96x40/dolby-vision.webp" height="30" alt="Dolby Vision">

## Framerate

Valeurs normalisées : 23,976, 24, 25, 29,97, 30, 50, 59,94 et 60 fps.

- 23,976/24 fps domine le cinéma et beaucoup d'anime.
- 25/50 fps est fréquent dans les environnements broadcast dérivés du PAL.
- 29,97/59,94 dérive du timing NTSC.
- Plus de fps ne signifie pas automatiquement « meilleur » ou « plus cinéma ».

## Bitrate

NiakVIO conserve **la valeur exacte** dans la description technique et utilise le badge générique BITRATE uniquement pour signaler que la mesure existe.

Ordres de grandeur indicatifs :

| Livraison | Valeurs souvent rencontrées | Marge brute de bitrate |
| --- | --- | --- |
| UHD Blu-ray | fréquemment plusieurs dizaines de Mbps, parfois davantage | 🏆 Très élevée |
| Blu-ray AVC | souvent ~15–35+ Mbps | 🟢 Élevée |
| 4K HEVC streaming | souvent ~10–25 Mbps | 🟢 Élevée |
| 1080p H.264 streaming | ~3–10 Mbps | 🟡 Contextuelle |
| 1080p HEVC streaming | ~1,5–6 Mbps | 🟡 Contextuelle |

**La marge de bitrate n'est pas une note de qualité.** Plus de Mbps signifie généralement davantage de données encodées, mais la résolution, l'efficacité du codec, la qualité de la source, les réglages de l'encodeur, le grain et le mouvement déterminent comment ces bits sont réellement utilisés.

Ce ne sont pas des seuils de qualité. 6 Mbps en AVC et 6 Mbps en AV1 ne sont pas équivalents : source, codec, réglages encodeur, grain et mouvement comptent.

## Support physique vs livraison numérique

« Numérique » recouvre plusieurs réalités très différentes : streaming par abonnement, achat numérique lié à une plateforme et fichier numérique local acquis légalement ne sont pas équivalents. De même, **le support physique n'est pas automatiquement meilleur**, mais le Blu-ray et surtout l'UHD Blu-ray disposent souvent d'avantages techniques et pratiques importants.

| Critère | Blu-ray / UHD Blu-ray | Streaming / plateforme | Fichier numérique local acquis légalement |
| --- | --- | --- | --- |
| Bitrate vidéo | 🏆 Généralement beaucoup plus de marge | 🟡 Généralement plus compressé pour limiter la bande passante | 🟢 à 🏆 Dépend entièrement du fichier et de sa source |
| Audio | 🏆 Souvent lossless ou à très haut débit (TrueHD, DTS-HD MA, LPCM) | 🟡 Souvent compressé avec pertes, même lorsque des métadonnées Atmos sont présentes | 🟢 à 🏆 Dépend des pistes incluses |
| Stabilité de l'image | 🏆 Encode fixe ; pas de baisse adaptative liée au réseau | 🟡 Le bitrate adaptatif peut varier selon connexion, appareil et politique du service | 🏆 Fichier local fixe |
| Dépendance au réseau | 🏆 Aucune pour une lecture normale du disque | 🔴 Dépend du service et de la connexion | 🏆 Aucune une fois le fichier autorisé disponible localement |
| Dépendance au catalogue/service | 🏆 L'exemplaire physique reste en possession de l'utilisateur | 🟠 L'accès peut dépendre du compte, du catalogue, du territoire et des conditions du service | 🟢 Dépend du DRM, de la licence et du format |
| Bonus / pistes alternatives | 🟢 Souvent riches : commentaires, pistes lossless, montages alternatifs, suppléments | 🟡 Très variable selon les services | 🟢 Dépend de l'édition et du fichier |
| Praticité | 🟡 Nécessite le disque et un matériel compatible | 🏆 Accès immédiat sur plusieurs appareils | 🟢 Très pratique une fois configuré |
| Contrôle pratique à long terme | 🏆 Fort : l'utilisateur conserve son exemplaire physique | 🟠 Généralement plus dépendant d'une plateforme tierce | 🟢 à 🏆 Fort pour un fichier autorisé sans DRM ; sinon dépendant de la licence |

### Pourquoi le physique peut être meilleur en image et en son

L'avantage principal n'est généralement **pas la résolution seule**. Un UHD Blu-ray et un service de streaming peuvent tous deux afficher `4K`, `HEVC`, `HDR10` ou `Dolby Vision`, alors que le disque peut conserver nettement plus de données vidéo et subir une compression moins agressive. Les éditions physiques proposent aussi fréquemment des pistes audio lossless que les services de streaming remplacent par des alternatives à débit plus faible.

C'est pourquoi un **Blu-ray 1080p bien masterisé peut parfois paraître plus propre qu'un flux 4K très compressé**, et pourquoi deux éditions possédant les mêmes badges de résolution/HDR peuvent malgré tout avoir un rendu différent.

Le support physique n'est pas infaillible : mauvais master, filtrage excessif, encode médiocre ou authoring raté peuvent rendre un disque inférieur à un meilleur master numérique. Les badges décrivent des faits techniques, pas un gagnant automatique.

### Propriété, possession et accès autorisé

Acheter un disque physique donne normalement à l'acheteur la possession et le contrôle pratique de **cet exemplaire** ; cela ne transfère pas les droits d'auteur ou autres droits de propriété intellectuelle sur l'œuvre elle-même. Un « achat » numérique, une location ou un abonnement peuvent donner des formes différentes d'accès sous licence, souvent dépendantes d'une plateforme, d'un compte, d'un territoire, d'un DRM et de conditions de service.

Pour une vidéothèque, le physique possède donc un avantage pratique important : l'exemplaire ne disparaît normalement pas parce qu'un catalogue de streaming change, qu'un compte ferme ou qu'un accord de licence entre une plateforme et un ayant droit expire. Les droits précis de revente, prêt, copie privée ou contournement de mesures techniques dépendent de la juridiction et sortent du cadre de ce guide technique.

### Un mot de soutien au support physique

NiakVIO est un outil numérique, mais ce guide **soutient clairement le support physique comme le moyen pratique le plus solide de conserver une vidéothèque personnelle durable et sous le contrôle de l'utilisateur**. Un disque peut rester disponible lorsqu'un catalogue tourne, qu'une plateforme disparaît, qu'une licence change, qu'un compte devient inaccessible ou qu'une œuvre est remplacée par un autre master.

Acheter une édition physique soutient aussi directement la continuité de cet écosystème : mastering, authoring, fabrication, restauration, bonus, éditions collector et signal commercial montrant qu'un public valorise encore des éditions permanentes de haute qualité. Cela ne signifie pas que chaque disque est techniquement supérieur, et cela ne change évidemment pas le droit d'auteur ; cela signifie simplement que le physique réunit particulièrement bien **pérennité, potentiel technique élevé et contrôle pratique à long terme**.

> [!TIP]
> Si une œuvre compte pour vous et qu'une bonne édition physique existe, **conserver un exemplaire physique légitime reste le moyen le plus robuste de préserver dans le temps votre propre accès à cette édition précise**. Le streaming reste excellent pour la praticité et la découverte ; le physique est le choix le plus orienté conservation.

> [!CAUTION]
> **NiakVIO ne transforme jamais une disponibilité technique en autorisation de regarder une œuvre.** Le projet n'héberge aucun contenu audiovisuel et n'accorde aucun droit sur les médias ou services tiers. NiakVIO doit être utilisé uniquement avec des contenus que l'utilisateur **possède, contrôle, a créés, pour lesquels il dispose d'une licence ou auxquels il est autrement autorisé à accéder**. Rien dans NiakVIO n'autorise le contournement d'une authentification, d'un paywall, d'un chiffrement, d'un DRM ou d'un autre contrôle d'accès. Chaque utilisateur reste responsable du respect de la loi applicable, des conditions des services et des droits des tiers. Voir [`DISCLAIMER.md`](../../DISCLAIMER.md) et [`TESTING_NOTICE.md`](../../TESTING_NOTICE.md).

## Audio : codec, technologie, canaux et fréquence

NiakVIO garde ces faits séparés.

- codecs : AAC, AC-3, E-AC-3, TrueHD, DTS/DTS-HD, FLAC, PCM/LPCM, Opus, MP3, ALAC ;
- technologies : Dolby Atmos, DTS:X ;
- canaux : 1.0, 2.0, 2.1, 5.1, 7.1 ;
- fréquences : 44,1, 48, 88,2, 96 et 192 kHz.

<img src="../../assets/transparent/96x40/aac.webp" height="30" alt="AAC"> <img src="../../assets/transparent/96x40/dolby-atmos.webp" height="30" alt="Atmos"> <img src="../../assets/transparent/96x40/truehd.webp" height="30" alt="TrueHD"> <img src="../../assets/transparent/96x40/5.1.webp" height="30" alt="5.1"> <img src="../../assets/transparent/96x40/48khz.webp" height="30" alt="48 kHz">

48 kHz est la base normale pour film/TV/vidéo. 96 ou 192 kHz ne prouve pas à lui seul une meilleure qualité audible.

## Langues et sous-titres

Les badges publics utilisent un modèle ISO/BCP-47 : `FR`, `FR-CA`, `EN`, `KO`, `JA`, `PT-BR`, `ES-419`, `ZH-HK`, `ZH-TW`, etc.

Les termes historiques `VF`, `VFF`, `VFQ`, `VO`, `MULTI` et `VOSTFR` restent uniquement des **alias d'entrée**.

- VF/VFF peuvent être normalisés vers un audio français lorsque la preuve le permet.
- VFQ peut être normalisé vers français Canada.
- VOSTFR devient audio original + sous-titres français lorsque la langue originale est connue.
- **VO ne devient jamais automatiquement anglais.**

## Classifications : les pays n'utilisent pas le même système

NiakVIO conserve le système régional lorsqu'il est connu : MPA/TV US, Corée ALL/12/15/19, FSK allemand, Japon G/PG12/R15+/R18+, CBFC indien, Brésil, Québec, Espagne, France, Hong Kong, Finlande, Grèce, Portugal, Philippines, Indonésie, Russie, Pologne, Suède, Taïwan et LATAM.

Un badge numérique générique est utilisé lorsque le seul fait fiable est un âge minimal.

## Que mettre dans le titre du flux ?

Le titre reste volontairement simple : **identité provider + meilleure qualité réellement prouvée**.

Exemples :

- 1080p prouvé → `Kehflix - 1080p`
- 1080i prouvé → `Kehflix - 1080i`
- 2160p prouvé → `Kehflix - 4K`
- 4320p prouvé → `Kehflix - 8K`
- `Unknown`, `Inconnue`, `N/A`, `Auto` → simplement `Kehflix`

Les autres informations vont dans les badges et la description. Si un flux Kehflix pauvre en métadonnées ne prouve qu'une URL `.m3u8`, la présentation correcte est **Kehflix + HLS**, jamais « Kehflix - Inconnue » et jamais une résolution devinée.

## Comment NiakVIO décide d'afficher un badge

1. le provider retourne les faits bruts disponibles ;
2. le Core conserve et normalise les preuves les plus fortes ;
3. la présentation émet des `badgeIds` structurés et une description technique lisible ;
4. les règles StreamBadge de Nuvio matchent ces faits ;
5. une information absente reste absente.

Cette séparation évite « l'inflation de badges » et rend réellement les données utiles aux utilisateurs qui s'intéressent à la qualité média.

## Score global de flux

La v6 expose le vocabulaire compact de score global : **`S+` · `S` · `A+` · `A` · `B` · `C` · `D` · `E`**. Le badge n'affiche volontairement que la lettre afin de ne pas multiplier les variantes ; la valeur numérique `0–100` reste dans le détail technique.

| Bloc | Poids cible |
| --- | ---: |
| Qualité vidéo | 45 % |
| Source / provenance | 10 % |
| Audio | 10 % |
| Lecture / réseau | 30 % |
| Fiabilité provider | 5 % |

Le score réseau n'utilise **pas** le Mbps brut comme verdict. Il mesure surtout la **marge de débit** (`throughput réseau / bitrate du média`), puis le temps de démarrage, les stalls/coupures et le taux de segments lus avec succès.

| Score | Grade |
| ---: | :---: |
| 95–100 | **S+** |
| 90–94 | **S** |
| 85–89 | **A+** |
| 80–84 | **A** |
| 70–79 | **B** |
| 60–69 | **C** |
| 40–59 | **D** |
| 0–39 | **E** |

**Règle de vérité :** aucun badge global ne doit être inventé sans preuve de lecture/réseau suffisante. La preuve réseau HLS provient d'échantillons bornés de segments média (jusqu'à deux segments), jamais du simple temps de réponse du manifeste `.m3u8`. Les métriques de stalls du player ne sont utilisées que si l'hôte les fournit réellement ; elles ne sont jamais inventées. Un flux faux, placeholder, mauvais média ou invalide est rejeté avant scoring. Un excellent fichier qui bufferise réellement doit être fortement pénalisé.

Le contrat de score v6 est isolé dans `scripts/stream_score.py` afin d'être testée sans modifier les providers ou un Repair en cours. L'intégration Core devra conserver cette frontière : **faits média + observation de lecture + confiance**.

## FAQ — comprendre rapidement la qualité d'un flux

### Un flux 720p peut-il paraître aussi bon, voire meilleur, qu'un 1080p ?

Oui. `1080p` décrit seulement les dimensions de l'image. Un bon encode 720p issu d'une bonne source, avec un codec efficace et un bitrate généreux, peut paraître aussi bon — voire plus propre — qu'un 1080p fortement compressé. C'est particulièrement fréquent en animation et sur les écrans disposant d'un bon upscale.

À bitrate identique, le 1080p possède environ **2,25× plus de pixels** que le 720p : les mêmes bits doivent donc être répartis sur beaucoup plus de pixels. La résolution n'est qu'une partie de l'équation.

### Le Mbps est-il le meilleur indicateur unique de qualité ?

C'est l'un des **indices techniques simples les plus utiles**, mais pas une note universelle de qualité. Plus de bitrate donne généralement davantage de marge pour préserver détails, grain et mouvements, mais `6 Mbps AVC`, `6 Mbps HEVC` et `6 Mbps AV1` ne sont pas équivalents.

Pour une lecture rapide, regarde plutôt : **source → codec → résolution → bitrate**. Si tout le reste est comparable, le bitrate le plus élevé est généralement le choix le plus rassurant.

### La 4K est-elle toujours meilleure que le 1080p ?

Non. Un très bon Blu-ray ou encode 1080p peut battre une 4K faible, très compressée ou simplement upscalée. `4K` décrit la taille raster, pas la qualité du master, le détail natif de la source ni la qualité de compression.

### HEVC/H.265 est-il automatiquement meilleur qu'AVC/H.264 ?

Non. HEVC est généralement plus efficace en compression et peut donc atteindre une qualité comparable avec moins de débit, mais la source et les réglages de l'encodeur restent déterminants. Un excellent AVC peut battre un mauvais HEVC.

### AV1 est-il automatiquement le codec avec la meilleure image ?

Non. AV1 offre une excellente efficacité de compression, mais efficacité du codec ne signifie pas qualité visuelle garantie. Source, implémentation de l'encodeur, réglages et bitrate comptent toujours.

### 10-bit signifie-t-il HDR ?

Non. Profondeur de couleur et plage dynamique sont deux informations différentes. Une vidéo peut être `10-bit SDR`, ce qui est courant dans les bons encodes anime. Le HDR demande une preuve distincte : HDR10, HDR10+, Dolby Vision, HLG, etc.

### Dolby Vision est-il automatiquement meilleur que HDR10 ?

Non. Dolby Vision peut apporter des métadonnées dynamiques et une chaîne de restitution plus riche, mais le résultat dépend du master, de l'écran, du lecteur et de l'implémentation. Un excellent HDR10 peut battre une mauvaise présentation Dolby Vision.

### 60 fps est-il meilleur que 24 fps ?

Pas en général. Le framerate est un choix de présentation. Le cinéma et beaucoup d'animations sont conçus autour de 23,976/24 fps. Un framerate supérieur peut améliorer la lisibilité du mouvement pour certains contenus, mais ce n'est pas une amélioration universelle.

### MKV est-il meilleur que MP4 ?

Non. Ce sont des conteneurs. MKV est très souple pour les multiples pistes audio/sous-titres et les releases complexes ; MP4 est extrêmement compatible. La qualité dépend des flux vidéo et audio contenus dedans.

### HLS signifie-t-il mauvaise qualité ?

Non. HLS décrit une livraison HTTP adaptative, pas la qualité d'image. Un master HLS peut contenir aussi bien de faibles résolutions que d'excellents flux 4K HDR. Si NiakVIO ne prouve que `HLS`, il n'invente volontairement ni résolution ni codec.

### Pourquoi un Blu-ray 1080p peut-il être meilleur qu'un streaming 4K ?

Parce que le disque peut utiliser beaucoup plus de bitrate, préserver davantage de détails fins et de grain, éviter les baisses adaptatives liées au réseau et proposer de meilleures pistes audio. Le flux 4K possède davantage de pixels, mais ceux-ci peuvent être beaucoup plus compressés.

### Le support physique est-il toujours le meilleur choix ?

Pour **le contrôle à long terme et la conservation d'une édition précise**, le physique est généralement le choix pratique le plus robuste. Pour la commodité, la mobilité et l'accès immédiat, le streaming ou un fichier numérique autorisé peuvent être plus pratiques. La qualité technique dépend toujours du master et de l'encode précis.

### Si NiakVIO trouve une source lisible, cela signifie-t-il que j'ai le droit de la regarder ?

Non. Une disponibilité technique n'est pas une autorisation. NiakVIO ne détermine ni la propriété des droits, ni la licence, ni la légalité d'une source tierce. Il doit être utilisé uniquement avec des contenus que vous possédez, contrôlez, avez créés, pour lesquels vous disposez d'une licence ou auxquels vous êtes autrement autorisé à accéder, dans le respect de la loi applicable et des conditions des services.

## Version des feeds

Toute modification matérielle crée une nouvelle version immuable des **quatre** feeds publics.

Version actuelle :

- `assets/stream-badges-fusion-v8.json`
- `assets/stream-badges-dark-v8.json`
- `assets/stream-badges-light-v8.json`
- `assets/stream-badges-transparent-v8.json`

Les anciennes versions restent disponibles pour les installations épinglées.
