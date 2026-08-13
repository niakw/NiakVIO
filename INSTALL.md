# Installation

## Utilisateurs Nuvio

Choisissez l'un des manifests stables :

- général (VF, VOSTFR, VO et autres langues) : `https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/manifest.json` ;
- francophone : `https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/vf/manifest.json`.

Dans un client Nuvio compatible, ouvrez la gestion des plugins/providers, ajoutez
l'URL voulue, puis actualisez le repository. Les URLs restent stables : les versions,
bundles et états d'activation évoluent derrière elles.

## Mainteneurs

1. Installer exactement le graphe verrouillé avec
   `npm ci --ignore-scripts --no-audit --no-fund`.
2. Exécuter `npm test` avant toute publication.
3. Pour une modification du manifest visible par les clients, incrémenter la release
   avec `python3 scripts/sync_release_versions.py --version X.Y.Z`.
4. Élaguer les anciens bundles hachés non référencés avec
   `python3 scripts/prune_unreferenced_providers.py`.
5. Régénérer les empreintes avec `python3 scripts/generate_release_hashes.py`, puis
   confirmer l'ensemble avec `python3 scripts/validate_release_integrity.py`.
6. Laisser les workflows de publication et le lab multi-œuvres valider `main`.

Le workflow **Check all manifests and publish Nuvio providers** reste l'entrée de la
validation distante complète. Le workflow **Nuvio client playback lab** vérifie une
matrice réelle sur NuvioTV, Desktop et Mobile ; sa cible 10 providers dont 3 VF est un
objectif de couverture non bloquant pour les œuvres récentes ou rares.
