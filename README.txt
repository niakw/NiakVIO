Correctif ultime Movix 5.20.3

Copier tous les fichiers à la racine du dépôt en conservant l'arborescence.
Aucun fichier à supprimer.

Ce correctif :
- supprime la dernière preuve fixe /api/fstream/ du résolveur Movix ;
- découvre une route API depuis la page officielle et ses bundles JavaScript ;
- rejette les routes contenant fstream ou d'autres marqueurs obsolètes ;
- valide la route découverte avec le film témoin 157336 avant de conserver l'API ;
- aligne le test VF Interstellar/Gardiens 3 sur le même parcours réel ;
- conserve un retour vide propre si aucune route fiable n'est découverte.
