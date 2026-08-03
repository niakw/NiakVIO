Correctif publication 5.20.3

Remplacer ces fichiers à la racine du dépôt.
Ne pas relancer le deep.
Après push, lancer le workflow manuel "Resume a validated Nuvio publication" avec source_run_number=56.

Cause corrigée : le nettoyage de 4khdhub utilisait un préfixe trop large et supprimait le provider distinct 4khdhubnew.
