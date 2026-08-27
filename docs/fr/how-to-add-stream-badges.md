# Ajouter les règles StreamBadge NiakVIO dans Nuvio

[English](../how-to-add-stream-badges.md) · [Retour au README](../../README.fr.md)

NiakVIO fournit des règles StreamBadge au format Fusion pour enrichir les cartes de streams.

## Feed recommandé

Utilisez **Fusion v2** dans la configuration normale :

```text
https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion-v2.json
```

Des variantes spécifiques au thème existent également :

- Dark : `assets/stream-badges-dark.json`
- Light : `assets/stream-badges-light.json`

Pour la majorité des utilisateurs, **Fusion v2 est le bon choix**.

## Nuvio Mobile et Nuvio Desktop

Chemin actuel dans l'interface Nuvio :

1. Ouvrez **Settings**.
2. Ouvrez **Appearance**.
3. Ouvrez **Streams**.
4. Dans **FUSION STYLE**, ouvrez **Fusion badge URLs**.
5. Collez l'URL JSON Fusion v2 de NiakVIO.
6. Sélectionnez **Import**.
7. Vérifiez que l'URL apparaît dans la liste et qu'elle est **Active**.
8. Optionnel : utilisez **Preview** pour contrôler les badges importés.
9. Optionnel : choisissez **Top** ou **Bottom** dans **Badge position**.

Nuvio peut conserver plusieurs URLs de badges. Si plusieurs feeds sont installés, vérifiez que le feed NiakVIO souhaité est bien actif.

## NuvioTV

Chemin actuel dans NuvioTV :

1. Ouvrez **Settings**.
2. Ouvrez **Layout**.
3. Dépliez **Streams**.
4. Dans **Fusion Style**, ouvrez **Fusion badge URLs**.
5. NuvioTV démarre son interface locale de configuration et affiche un **QR code**.
6. Scannez le QR code avec votre téléphone, connecté au même réseau local que la TV.
7. Dans la page web ouverte sur votre téléphone, collez l'URL JSON Fusion v2 de NiakVIO.
8. Sélectionnez **Import**.
9. Vérifiez que le feed est indiqué **Active** et utilisez éventuellement **Preview**.
10. La position des badges peut également être réglée via **Badge position**.

La TV conserve localement les règles déjà importées. Si une ancienne version du feed Fusion NiakVIO avait déjà été importée et ne se met pas correctement à jour, supprimez l'ancien import puis ajoutez à nouveau l'URL **Fusion v2** actuelle.

## Vérifier le résultat

Ouvrez un contenu disposant de streams. Les cartes compatibles doivent afficher les badges Fusion lorsque les métadonnées du stream correspondent à une règle.

Si aucun badge n'apparaît :

- vérifiez que l'URL importée est active ;
- utilisez **Preview** pour confirmer que les badges ont été chargés ;
- réimportez l'URL Fusion v2 actuelle ;
- gardez en tête qu'un badge ne s'affiche que si les métadonnées du stream correspondent à sa règle.
