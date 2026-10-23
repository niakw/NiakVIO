# Fiabilité des réparations NiakVIO / NiakVIO-Brain-LLM

## Cause confirmée : les corrections générées ne rejoignaient pas les bytes v3

Le pont déclarait un `provider_bloc` appliqué après avoir écrit son module dans
`patch_scripts`. Les providers v3 exécutent `provider_lego_scripts` : la mutation
était ignorée à la reconstruction. Le contrôle réseau pouvait donc comparer le
provider original à lui-même, puis apprendre un faux échec de la proposition.

Le cas a été reproduit hors ligne avec la proposition réelle AnimeVOSTFR du
[run 39858290849](https://github.com/niakw/NiakVIO/actions/runs/39858290849), à son
SHA source exact. Avant correction, la proposition disparaît du bundle. Après
correction du pont, elle est présente dans le fichier publié reconstruit et dans
le fichier du stage transmis au worker. Cela prouve la matérialisation de la
proposition, pas son efficacité en lecture.

Le pont inscrit maintenant le module dans le registre v3, respecte le propriétaire
`PROVIDER.<ID>.*` existant et modifie son rectangle en place sans blocs imbriqués.
Il retrouve l'ancre exacte publiée à travers la normalisation de sécurité et
préserve les modules précédents nécessaires à la reconstruction depuis un seed
vierge. Il ne promeut pas les anciens scripts archivés en code exécutable v3.

Avant le health check, le vérificateur contrôle les empreintes des fichiers
réellement stagés et la présence de la spécification générée dans leurs métadonnées
d'appartenance. Une proposition absente ou sans effet ne devient plus un échec
causal. L'acceptation exige toujours les preuves de lecture, d'identité et
d'amélioration existantes.

Les 27 anciens verdicts de Bloc sans preuve de matérialisation sont conservés
avec leurs compteurs, mais marqués `executionObserved=false`. Ils ne bloquent plus
une tentative et ne fournissent plus de prior positif. Les trois autres verdicts
historiques sont préservés. Les reçus et évaluations originaux restent consultables.

Le [premier essai après correctif](https://github.com/niakw/NiakVIO/actions/runs/40033310896)
confirme `materializedMutationObserved=true` et `executionObserved=true`, avec
des empreintes distinctes du bundle de référence et du candidat. Cette proposition
ne gagne aucun flux lisible : un avant, un après, acceptation refusée. Le verdict
est maintenant un véritable contre-exemple conservé automatiquement dans `main`.

Le filtre de capacités confondait aussi `function (…)` et `Function(…)`, car sa
comparaison ignorait la casse. Les callbacks JavaScript ordinaires sont désormais
admis ; `Function`, `eval`, `process` et les autres capacités interdites restent
rejetés dans le Brain et dans le récepteur NiakVIO.

## Boucle hosted et mémoire durable

Dans GitHub Actions du dépôt NiakVIO, lancer
`Brain - Hosted single-provider repair check` depuis `main`, puis choisir le
provider. La mise à jour de ce workflow sur `main` lance aussi une vérification.
Le backend utilise `NIAKVIO_OPENAI_API_KEY`, un SHA Brain exact et seulement le
contexte public. Aucun contenu de la mémoire privée n'est transmis à l'API.

La pré-observation relève les fonctions exécutées et la structure des réponses
JSON/HTML, sans leurs valeurs scalaires ni leur contenu brut. Chaque tentative
suivante reçoit le verdict et les mesures de la précédente. La boucle reste
limitée à trois propositions et dix minutes ; elle s'arrête sur acceptation,
absence de candidat exécutable ou épuisement du budget.

Un job distinct conserve les résultats dans `main`, une fois par run, même quand
la branche d'expérience a été supprimée. La collecte existante AnimeVOSTFR a été
[récupérée avec succès](https://github.com/niakw/NiakVIO/actions/runs/40032263921).
Les mutations de toutes les tentatives sont archivées pour les prochains essais.
La collecte ne publie pas de provider ; les gates canoniques gardent cette autorité.

Le secret a permis une vraie génération API dans le
[runner GitHub NiakVIO](https://github.com/niakw/NiakVIO/actions/runs/39853035153).
Le test de cette session cloud retourne encore HTTP 401 ; il ne remet pas en
cause le fonctionnement du secret GitHub. Aucun changement de mot de passe
supplémentaire n'est demandé.

## Autres corrections et vérifications

- Transport du gros payload de mémoire Node par fichier temporaire.
- Exclusion des essais non exécutés et conservation de toutes les clés historiques.
- Blocage des mutations réellement rejetées dans le même contexte de source.
- Revalidation des anciennes recettes positives et conservation de leur requête terminale.
- Priorité au parcours terminal réellement exécuté dans le choix des fonctions éditables.
- 307 tests Brain et audit de confidentialité réussis.
- Régressions NiakVIO : dispatch v3 réel, ancre durcie, propriété native,
  reconstruction successive, fichier stagé inchangé, spécification absente,
  mémoire historique non prouvée, feedback borné et isolation des secrets.

Un workflow vert et une proposition générée ne suffisent pas à déclarer un
provider réparé. Le résultat de lecture après le correctif doit être vérifié.

## Comparaison des réparations et changement de fonction après échec

Les essais AnimeVOSTFR précédents ne couvraient que Hell Mode : le mode
d'activation arrête l'échantillonnage après un premier titre et un flux HD sain.
Le sandbox de réparation utilise maintenant un profil de comparaison distinct :
deux titres primaires par catégorie et contrôle de tous les flux dans la limite
existante de trois. La référence et le candidat utilisent exactement le même
profil. Les résultats par titre sont transmis au Brain et conservés dans les preuves.

Sur ce provider, le contexte compact ne proposait que `text` et `resolve`.
Après une mutation matérialisée et exécutée sans gain vérifié, le Brain conserve
le dispatcher pour suivre ses appels mais propose les fonctions voisines à la
modification. Le rejeu du dernier échec expose désormais `playerRows`,
`externalPlayer` et `findAnime`. Cette rotation ne s'applique pas aux essais
non exécutés et ne constitue pas une interdiction permanente d'une fonction.

Le [premier relevé élargi](https://github.com/niakw/NiakVIO/actions/runs/40035356823)
observe désormais zéro flux sur cinq titres : les réponses HTTP ne contiennent
que des scripts obfusqués, sans catalogue ni lecteur exploitable. Un changement
de parser a été réellement essayé puis refusé ; aucun rétablissement n'est validé.

Quand cette absence de contenu est observée sur toutes les réponses du provider,
le parcours appelle le diagnostic navigateur ordinaire existant, sans conserver
DOM ni cookies. Le classifieur navigateur ne compte plus le texte des scripts
comme du contenu rendu. La synthèse est suspendue tant que ce prérequis manque,
sans appel API et sans transformer cette non-exécution en échec de code appris.
