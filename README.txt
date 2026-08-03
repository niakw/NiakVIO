Correctif de publication 5.19.3 — aucun nouveau deep nécessaire

Cause exacte
------------
Le validateur traitait les noms de providers par préfixe. En validant "4khdhub",
il pouvait supprimer le bundle valide du provider distinct "4khdhubnew".
Le job deep "Discover and validate all upstream providers" du run #52 est déjà vert.

Procédure
---------
1. Copier ces fichiers dans le dépôt, puis commit/push.
2. Dans GitHub Actions, lancer manuellement le workflow :
   "Resume a validated Nuvio publication".
3. Saisir 52 comme source_run_number.

Le workflow vérifie que le job de validation du run #52 a réussi, télécharge son
artefact existant et ne rejoue que la phase de publication.

Important
---------
Ne pas cliquer sur "Re-run failed jobs" du run #52 après le nouveau commit :
un rerun classique utilise l'ancien commit et ne verrait pas le correctif.
Ne pas lancer un nouveau deep tant que l'artefact du run #52 est encore disponible
(rétention configurée : 2 jours).
