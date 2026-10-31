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
la mise sur une ligne. L'alignement par tokens retrouve les bytes lisibles du
seed ; une seconde normalisation vérifie le span sélectionné avant remplacement.
La métadonnée de restauration conserve les bytes originaux, commentaires compris.
Le [run 40037611469](https://github.com/niakw/NiakVIO/actions/runs/40037611469)
a généré un extracteur terminal Sendvid mais ne l'a pas exécuté à cause de cette
différence de format. Il ne constitue donc pas un échec causal du candidat.
Le workflow permet maintenant de rejouer une proposition archivée sans nouvel
appel API, en conservant son SHA et ses empreintes d'origine. Les vérifications
de dérive de source et les gates de lecture/identité restent obligatoires.

Le pont
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
limitée à deux propositions et dix minutes dans ce workflow ; elle s'arrête sur acceptation,
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
- 317 tests Brain et audit de confidentialité réussis lors de la reprise du 31 octobre 2026.
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
Le [rejeu 40038408753](https://github.com/niakw/NiakVIO/actions/runs/40038408753)
rencontre ce cas et un timeout du navigateur ; zéro candidat est exécuté.
Un seul nouveau relevé HTTP est désormais autorisé après cette observation pour
détecter le retour du contenu. Le timeout navigateur reste conservé comme tel.

L'accès varie entre les relevés. Le [run suivant](https://github.com/niakw/NiakVIO/actions/runs/40036152081)
retrouve Hell Mode lisible et Jujutsu Kaisen sans flux. Pour ce dernier, Sendvid
répond HTTP 200 avec des balises `video`/`source`, mais le worker final
ne retourne aucun flux. La préférence pour le bloc natif
cachait ce helper effectivement exécuté au modèle.

Le [rejeu 40038688593](https://github.com/niakw/NiakVIO/actions/runs/40038688593)
confirme ensuite la matérialisation et l'exécution du candidat Sendvid, sans gain :
Hell Mode reste à un flux lisible et Jujutsu Kaisen à zéro. Le candidat est refusé
et son échec causal est conservé. Même la référence reçoit déjà un HTTP 206 du
CDN média ; le statut seul ne permet pas de conclure à un défaut d'extraction.
Le worker relève désormais uniquement les faits dérivés du préfixe déjà lu par
le probe terminal : signature, durée MP4 si disponible, taille plafonnée à 64 Kio,
états de lecture et d'annulation. Aucune requête supplémentaire n'est émise et
aucun octet brut n'est conservé. Ces faits rejoignent le contexte et le feedback
du Brain ; ils ne remplacent pas les preuves de lecture et d'identité.
Le test exécute aussi la projection réelle worker → Deep afin qu'une nouvelle
mesure ne disparaisse pas entre les deux rapports. Les fonctions du Core restent
visibles dans les traces, mais les helpers du provider gardent la priorité dans
le choix des fonctions éditables.

Le [relevé 40039605264](https://github.com/niakw/NiakVIO/actions/runs/40039605264)
confirme un MP4 de **cinq secondes** sur Sendvid, référence comme candidat, pour
Jujutsu Kaisen S01E01 attendu à 24 minutes. Lecture et annulation du préfixe
s'achèvent sans erreur. Ce n'est pas une panne d'extraction ni un prétexte pour
relâcher le filtre : cette source courte est légitimement refusée. Le Brain reçoit
maintenant la durée attendue de la fixture et doit chercher un autre lecteur
corrélé au même épisode, ou s'abstenir si les observations n'en montrent aucun.

Le [run 40039908628](https://github.com/niakw/NiakVIO/actions/runs/40039908628)
génère ensuite deux propositions avec ce contexte. La première est matérialisée
et exécutée sans gain ; la seconde n'est pas exécutée car une fenêtre de corps
de fonction conserve un espace de séparation à sa bordure. La validation
canonique compare désormais les spans sans cet espace extérieur, en maintenant
l'unicité et la vérification du contenu entier. Le cas réel est reproduit sur le
seed lisible, sans changement manuel du provider ni assouplissement des gates.

Le choix des fonctions éditables exploite aussi ce contre-exemple : pour un
long épisode sans flux, un MP4 de moins d'une minute effectivement lu identifie
une source trop courte. Si les traces désignent son helper terminal, le Brain
remonte ses appelants observés et réserve trois unités aux sélecteurs locaux
qu'ils appellent directement. Le helper terminal garde son rôle dans les traces,
mais ses décodeurs et limites de parcours ne monopolisent plus les unités.
Le rejeu hors ligne du run ci-dessus expose désormais `playerRows`,
`externalPlayer` et `findEpisode`, dans la limite de quatre unités distinctes.
Les preuves d'une autre fixture, une durée inconnue, une lecture interrompue ou
un appelant non observé n'activent pas cette sélection. Le Core demeure exclu.
Cela valide le contexte proposé au modèle ; seul un nouvel essai réseau peut
valider une amélioration de lecture.

Le préflight privilégie maintenant le titre en échec et ses dernières requêtes
terminales, avant les wrappers de transport et la branche déjà saine. Les faits
actuels peuvent remplacer un ancien diagnostic de perte de variantes. Si le
helper appartient au préfixe du provider mais dépasse la limite d'une fonction
éditable, le Brain reçoit son code comme contexte en lecture seule et au plus
deux séquences d'instructions exactes à modifier. Le Core reste exclu de cette
surface. Deux edits exécutés récents sont conservés pour éviter l'alternance
immédiate entre le dispatcher et le dernier helper testé.

## Reprise du 31 octobre 2026

Les deltas du 24 octobre ont été réappliqués aux versions actuelles des deux
dépôts, en conservant les correctifs ultérieurs du Brain, notamment le confinement
des chemins et la confidentialité des références. Le workflow utilise le SHA
Brain réellement publié `40bb2cd321d0c1a23b22c77f45d762997556b1c7`.
Les tests du pont de mutation et des observations média passent également.
Ces vérifications locales ne valident pas encore une réparation de lecture.

Le [run 41209946518](https://github.com/niakw/NiakVIO/actions/runs/41209946518)
a matérialisé et exécuté deux propositions : `playerRows`, puis `externalPlayer`.
Elles sont refusées sans gain : Hell Mode garde un flux lisible, Jujutsu Kaisen
reste sans flux et sa source Sendvid mesure toujours cinq secondes. Les deux
contre-exemples sont conservés dans la mémoire durable.

Le rejeu avec ces contre-exemples révèle une limite de la rotation du contexte :
les fonctions rejetées occupaient encore les racines du parcours des appels,
avant leur retrait final. `findEpisode` restait visible mais ses propres parseurs
disparaissaient au profit de `abs`, `text` et `s`. Pour une source courte mesurée,
le parcours réserve désormais les sélecteurs restants avant de suivre leurs appels.
Le même rejeu expose `findEpisode`, `text`, `episodeRows` et `episodeScore`, soit
quatre unités exactes distinctes. La régression échoue avant correction et passe
après. Aucune modification manuelle du provider ni des gates de lecture/identité
n'est incluse ; un nouvel essai réseau doit encore mesurer le résultat.

Le [run 41214293334](https://github.com/niakw/NiakVIO/actions/runs/41214293334)
s'abstient après cette correction : seule la source de cinq secondes est prouvée,
sans autre source complète observée. Aucune proposition n'est exécutée ni apprise
comme échec causal.

Pour compléter ce diagnostic, l'observateur distingue maintenant les emplacements
d'adresses dans le markup (`iframe`, options, attributs de lecteurs) et leurs
types : absolu, relatif, fragment, markup inline ou encodé. Il conserve des types
et compteurs plafonnés, dont le nombre de valeurs distinctes, avec un indicateur
de troncature et des échantillons séparés du début et de la fin de page. Aucun
texte de réponse, URL complète ni contenu décodé n'est archivé. Ces déclarations
ne prouvent ni une autre source complète, ni une lecture réussie.

Le collecteur projette indépendamment ces faits vers
`automation/hosted-repair-evidence/<run>-player-markup.json`, en vérifiant le SHA
du relevé, même après une abstention. Les tests suivent la production du schéma,
son passage par le préflight et sa projection publique ; ils vérifient aussi la
confidentialité, les plafonds et le rejet d'un SHA différent.
