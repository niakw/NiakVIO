# Nuvio Desktop — notes runtime

Ce document conserve les diagnostics et invariants spécifiques au runtime Nuvio Desktop sans alourdir le README principal du dépôt.

## Régression Unicode QuickJS/JVM — streams à zéro

### Symptôme

Un provider peut retourner un résultat réseau valide et un objet stream valide côté JavaScript, mais Nuvio Desktop finit avec **0 stream** lorsque le JSON final transmis de QuickJS vers la JVM contient directement certains caractères Unicode non ASCII, notamment des emojis.

Le cas de référence utilisé pour isoler la régression est **Purstream + Interstellar (TMDB 157336)** :

- la résolution TMDB fonctionne ;
- le endpoint Purstream `/sheet` renvoie bien un média ;
- l'URL HLS `https://free.finepulfe.xyz/movies/157336-unr8i/master.m3u8` est présente ;
- le résultat brut passe ;
- le résultat enrichi disparaissait lors du passage QuickJS → JVM.

Le problème n'était donc ni le provider, ni le réseau, ni HLS.

### Champs concernés

Le défaut n'était **pas limité à `description`**. Un caractère problématique pouvait faire disparaître le row lorsqu'il était présent dans n'importe quelle chaîne du payload stream, notamment :

- `title`
- `name`
- `description`
- `size`
- plus généralement toute valeur texte sérialisée dans le même payload.

Le bisect de référence a notamment confirmé :

- `title` avec texte ASCII : OK ;
- `title` avec emoji : row perdu ;
- `name` ASCII : OK ;
- `description` enrichie avec emoji : row perdu ;
- `size` enrichi avec emoji : row perdu ;
- URL / format / headers : OK.

### Cause

Le binding QuickJS/JVM utilisé par Nuvio Desktop corrompait le transport de chaînes JSON contenant des caractères Unicode supplémentaires/non ASCII. Le JSON brut avec emoji pouvait traverser le binding sous forme de mojibake puis échouer plus loin lors du décodage/conversion du résultat.

La reproduction minimale JVM avec `quickjs-kt 1.0.5` a confirmé la différence entre :

- JSON ASCII : transport correct ;
- JSON contenant directement des emojis : transport corrompu ;
- même JSON avec Unicode échappé en `\\uXXXX` : transport correct.

### Correctif Core V15

Le Core sérialise désormais les payloads de streams en JSON **ASCII-safe** avant leur passage dans le binding JVM.

Les caractères Unicode sont temporairement représentés avec leurs échappements JSON. Le parseur JSON du client restitue ensuite les caractères originaux.

Le correctif ne retire donc pas les emojis et n'appauvrit pas la présentation.

Exemple fonctionnel après décodage :

```text
firstTitle=💧 Purstream - 1080p
firstName=💧 Purstream
```

Les éléments visuels tels que `💧`, `🎬`, `🇫🇷`, `🔊` restent utilisables dans `title`, `name` et `description`.

### Validation native conservée

Le bundle Purstream publié avec le Core V15 a été exécuté sur le runtime officiel Nuvio Desktop macOS avec Interstellar :

```text
status=completed
count=1
firstUrl=https://free.finepulfe.xyz/movies/157336-unr8i/master.m3u8
firstTitle=💧 Purstream - 1080p
firstName=💧 Purstream
```

Cette preuve valide à la fois :

1. le retour effectif du stream sur Desktop ;
2. la conservation des emojis après le round-trip JSON ;
3. l'absence de patch spécifique à Purstream : la protection reste une règle Core globale.

### Invariant à préserver

Ne pas résoudre ce problème en supprimant les emojis des providers ou en ajoutant une réparation Desktop spécifique à Purstream.

La règle à conserver est :

> tout payload stream enrichi destiné au bridge QuickJS/JVM Desktop doit rester ASCII-safe pendant le transport JSON, puis être reconstruit normalement par le parseur du client.
