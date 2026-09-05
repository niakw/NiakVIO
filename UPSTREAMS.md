# Sources amont et provenance

NiakVIO observe trois sources communautaires principales. Elles servent de **connaissance, comparaison et provenance** ; elles ne sont jamais une seed JavaScript exécutable pour reconstruire Provider v3.

## Gowaru

- Dépôt : `https://github.com/Gowaru/gowaru-nuvio-providers`
- Manifest : `https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/refs/heads/main/manifest.json`
- Apport historique : providers VF, VOSTFR et anime francophone.

## All-in-One-Nuvio

- Dépôt canonique : `https://github.com/NuvioPlugin/All-in-One-Nuvio`
- Manifest principal : `https://raw.githubusercontent.com/NuvioPlugin/All-in-One-Nuvio/refs/heads/main/manifest.json`
- Ancien miroir de connaissance : `https://raw.githubusercontent.com/D3adlyRocket/All-in-One-Nuvio/refs/heads/main/manifest.json`
- Apport historique : providers internationaux et correctifs récents.

## Yoru

- Dépôt : `https://github.com/yoruix/nuvio-providers`
- Manifest : `https://raw.githubusercontent.com/yoruix/nuvio-providers/refs/heads/main/manifest.json`
- Apport historique : providers exclusifs et variantes complémentaires.

## Contrat actuel

`.github/workflows/weekly-upstream-provider-discovery.yml` observe les trois sources en lecture seule :

1. résout les hubs/manifests accessibles ;
2. stage temporairement les entrées non-P2P pour comparaison ;
3. signale les providers absents du catalogue NiakVIO ;
4. publie uniquement des artifacts/rapports de découverte ;
5. vérifie par `git diff --exit-code` qu'aucun catalogue, manifest, override ou Provider JS n'a été muté.

Les répertoires `upstream-lkg/manifests/` et `upstream-lkg/providers/` conservent des snapshots historiques/provenance. Ils ne sont **pas** rafraîchis par CORE Deep aujourd'hui et ne constituent ni ProviderBase v3, ni une seed de reconstruction.

## Relation avec Provider v3

La reconstruction exécutable part exclusivement de :

- `provider-bases/` propres et marqués `NIAKVIO_PROVIDER_BASE_OWNED_V3` ;
- DATA/CONFIG structurées ;
- Lego `PROVIDER.*` ;
- Lego `CORE.*`.

Une observation upstream peut inspirer Learning ou une modification reviewable de DATA/Lego, mais son JavaScript n'est jamais copié comme base canonique.

## Règles

1. Ne jamais activer deux copies du même provider.
2. Ne jamais remplacer une génération publiée par une variante non prouvée.
3. Exclure les protocoles/providers P2P du flux d'onboarding standard.
4. Conserver les snapshots upstream comme provenance bornée, pas comme code de production.
5. Un snapshot LKG ou upstream ne contourne jamais les contrats d'identité, sécurité, HLS ou reverse reconstruction.
6. Les Provider JS publiés sont générés depuis Provider v3 et adressés par contenu avant toute projection qui les référence.
