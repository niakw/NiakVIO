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

1. Ouvrez **Paramètres**.
2. Ouvrez **Apparence**.
3. Ouvrez **Streams** — ce libellé reste actuellement en anglais dans l'interface française Mobile/Desktop.
4. Dans **STYLE FUSION**, ouvrez **URL de badges Fusion**.
5. Collez l'URL JSON Fusion v2 de NiakVIO.
6. Sélectionnez **Importer**.
7. Vérifiez que l'URL apparaît dans la liste et qu'elle est **Active**.
8. Optionnel : utilisez **Aperçu** pour contrôler les badges importés.
9. Optionnel : choisissez **En haut** ou **En bas** dans **Position des badges**.

Nuvio peut conserver plusieurs URLs de badges. Si plusieurs feeds sont installés, vérifiez que le feed NiakVIO souhaité est bien actif.

## NuvioTV

Chemin actuel dans NuvioTV :

1. Ouvrez **Paramètres**.
2. Ouvrez **Disposition**.
3. Dépliez **Flux**.
4. Dans **Style Fusion**, ouvrez **URL de badges Fusion**.
5. NuvioTV démarre son interface locale de configuration et affiche un **QR code**.
6. Scannez le QR code avec votre téléphone, connecté au même réseau local que la TV.
7. Dans la page web ouverte sur votre téléphone, collez l'URL JSON Fusion v2 de NiakVIO.
8. Sélectionnez **Importer**.
9. Vérifiez que le feed est indiqué **Activé** et utilisez éventuellement **Aperçu**.
10. La position des badges peut également être réglée via **Position des badges** (**En haut** / **En bas**).

La TV conserve localement les règles déjà importées. Si une ancienne version du feed Fusion NiakVIO avait déjà été importée et ne se met pas correctement à jour, supprimez l'ancien import puis ajoutez à nouveau l'URL **Fusion v2** actuelle.

## Vérifier le résultat

Ouvrez un contenu disposant de streams. Les cartes compatibles doivent afficher les badges Fusion lorsque les métadonnées du stream correspondent à une règle.

Si aucun badge n'apparaît :

- vérifiez que l'URL importée est active ;
- utilisez **Preview** pour confirmer que les badges ont été chargés ;
- réimportez l'URL Fusion v2 actuelle ;
- gardez en tête qu'un badge ne s'affiche que si les métadonnées du stream correspondent à sa règle.
