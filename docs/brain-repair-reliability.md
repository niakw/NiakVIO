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
- 321 tests Brain et audit de confidentialité réussis lors de la reprise du 31 octobre 2026.
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
des chemins et la confidentialité des références. Cette étape a utilisé le SHA
Brain réellement publié `91db65bdae83ce79b6185e5753bf19c2650a1025`.
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

Le [relevé 41217088557](https://github.com/niakw/NiakVIO/actions/runs/41217088557)
conserve ces faits après abstention. Chaque réponse Sendvid observée déclare une
seule balise `source`. La page d'épisode expose 54 options d'URL et trois
emplacements `div[data-src]`, sans preuve qu'il s'agisse d'autres lecteurs complets.

La projection Brain conservait seulement les huit premiers événements et ignorait
le nouveau schéma : les réponses répétées des lecteurs excluaient donc la page
d'épisode du prompt. Elle projette maintenant les types et compteurs reconnus,
réserve les étapes distinctes par fixture puis les formes distinctes avant les
doublons, en conservant la limite de huit observations sur douze événements
d'entrée. Le rejeu réel transmet désormais les 54 options et les trois champs
au prompt. Les tests couvrent aussi le filtrage de valeurs forgées et l'idempotence.

Le [run 41218371896](https://github.com/niakw/NiakVIO/actions/runs/41218371896)
n'appelle pourtant pas le modèle : le census classe maintenant ce provider
`candidate_replay_gap`, stratégie de rejeu sans mutation. L'ancien raffinement
du diagnostic courant ne remplaçait que le risque de variantes. Le raffinement
d'un classement de rejeu exige désormais le même contre-exemple média complet :
épisode long sans flux, MP4 court mesuré pour cette même fixture, HTTP réussi,
échantillon suffisant et lecture/annulation achevées. Un simple rejeu ou une preuve
incomplète restent inchangés. Les tests confirment aussi que les exigences de
preuve courante de la politique de mutation restent obligatoires. Aucun gain de
lecture n'est déduit d'une abstention préalable à l'appel au modèle.

## 1er novembre 2026 — Forme des adresses et origine

Le [run 41219789908](https://github.com/niakw/NiakVIO/actions/runs/41219789908)
confirme deux appels au modèle et deux propositions matérialisées/exécutées,
toutes deux refusées sans gain. La seconde élargit `playerRows` aux options et
aux `div[data-src]` ; aucun média n'est observé pour Jujutsu Kaisen avec ce candidat.
Les compteurs d'adresses absolues ne suffisent pas à distinguer les usages de ces
emplacements.

Le schéma conserve désormais, pour chaque attribut reconnu, une catégorie fondée
sur la syntaxe de l'URL : extension d'image, script, style, média, page ou route
de lecteur, avec une relation d'origine identique/différente/inconnue. La base
utilisée est l'URL effective de la réponse. La projection publique et le Brain
ne conservent que des énumérations fixes ; les URL et contenus décodés ne sont
pas archivés. Les formes distinctes ont des compteurs distincts et les attributs
de données restent prioritaires dans le relevé borné.

Ces indices syntaxiques ne prouvent ni le type réel de la réponse, ni une autre
source complète : les contrôles de média et d'identité restent obligatoires.
Les 322 tests Brain, l'audit de confidentialité et la vérification de bout en bout
producteur → préflight/archivage → prompt passent. Le workflow épingle le Brain
publié `88a520771f75acae7226d15978fa10d2c9e660c9` pour ce relevé réel.

## 1er novembre 2026 — Admission des lecteurs avant HTTP

Le [run 41255639071](https://github.com/niakw/NiakVIO/actions/runs/41255639071)
confirme deux appels au modèle et deux candidats exécutés, refusés sans gain :
Hell Mode reste lisible et Jujutsu Kaisen reste sans flux validé, avec un MP4
mesuré de cinq secondes. Le relevé révèle trois `div[data-src]` de forme
`embed_route`, de même origine, et des iframes étrangères de forme
`page_extension` dans les pages de lecteurs. La trace externe observée ne visite
que Sendvid. Ces formes décrivent la syntaxe des adresses, pas leur disponibilité.

Un rejeu hors ligne des fonctions exactes du bundle publié montre que le filtre
des graines peut refuser des adresses de pages de lecteurs avant toute requête
HTTP. Le Brain peut désormais proposer ce filtre nommé et ses helpers d'URL
après un échec mesuré et des essais de parsing exécutés sans gain, sur la même
fixture. Il ne modifie aucun provider à la main. Les contrôles de protocole,
d'assets, d'identité incomplète, de média et d'identité restent obligatoires.

La délimitation structurelle des fonctions évite aussi qu'une accolade littérale
dans une expression régulière exclue le filtre des unités d'édition. Les 325 tests
Brain et l'audit de confidentialité passent. Le rejeu des archives contre le SHA
exact du bundle propose uniquement `_crawlEligible`, `_playerLike` et
`_crawlUrlScore`. Le workflow épingle le Brain publié
`12d2d8f81b1dc22d252f7bfb0c2081798636a6be` pour tester cette hypothèse en réseau.
Aucune réparation de lecture n'est encore validée.

Le [run 41257855269](https://github.com/niakw/NiakVIO/actions/runs/41257855269)
matérialise et exécute un premier candidat qui admet les pages étrangères de
lecteurs : Sibnet apparaît dans la trace pour les deux épisodes et répond
HTTP 403. Aucun gain de flux n'est validé. La seconde tentative n'est pas
exécutée : le convertisseur rejette une fonction complète car il compte encore
une accolade littérale de regex comme une accolade de code. Les cinq appels au
modèle ne représentent donc qu'un seul candidat exécuté.

Le convertisseur utilise désormais le même délimiteur structurel JavaScript
que la sélection des unités. Les 327 tests couvrent la conversion complète avec
des accolades dans les regex, chaînes et commentaires, ainsi qu'un fragment
réellement incomplet masqué par une accolade littérale fermante. L'ancre exacte
`_crawlEligible` du bundle publié passe ce contrôle. Le workflow épingle le Brain
`9c80e6c271d09600e0ae85baefb1b2a17f5683ad` pour permettre un nouvel essai complet.
Le refus HTTP observé reste une preuve négative, jamais une réparation acceptée.

## 1er novembre 2026 — Diagnostic des réponses de lecteurs refusées

Le [run 41258465778](https://github.com/niakw/NiakVIO/actions/runs/41258465778)
exécute deux candidats sans gain : Hell Mode reste lisible, Jujutsu Kaisen reste
sans flux validé et les MP4 Sendvid mesurés durent cinq secondes. Les deux
candidats atteignent Sibnet, qui répond HTTP 403. Ce statut parvient bien au
prompt ; il ne suffit pas à conclure que la ressource a disparu. Le provider
jette sur les réponses HTTP d'erreur avant de les lire et la structure reste vide.

Le worker relève désormais le type de contenu et la relation entre URL demandée
et URL effective, sous forme d'énumérations fixes. Sur les seules erreurs HTTP
textuelles, un clone de réponse fournit un échantillon borné à 8192 octets et
250 ms. Seuls un indice de page (challenge, captcha, refus, absence, limitation
ou inconnu), l'état de lecture et le compteur sont conservés. Aucun texte,
en-tête ou URL n'est ajouté au relevé. Le corps original reste lisible et les
réponses réussies comme les médias ne sont pas échantillonnés par ce diagnostic.
Ces indices de syntaxe ne prouvent ni disponibilité ni réparation de lecture.

Le préflight, l'évaluation, le retour au Brain et l'archive publique projettent
ces champs indépendamment. Un reçu `-http-observation.json` conserve aussi le
préflight lorsqu'aucun candidat n'est produit. Les 328 tests Brain et l'audit de
confidentialité passent ; les tests Node/Python couvrent les streams réels,
l'original inchangé, le délai, l'annulation, la confidentialité et la transmission.
Le Brain publié est épinglé à `ba629acd73df78df06a771c0086b3d8fe6ef73cd`.

L'essai automatique sur push rejoue uniquement le candidat déjà exécuté du
run 41257855269 afin de diagnostiquer sa réponse HTTP, sans nouvelle inférence
ni publication de provider. Un lancement manuel sans archive conserve la
synthèse bornée habituelle. Aucune réparation de lecture n'est encore validée.

Le [rejeu 41300728008](https://github.com/niakw/NiakVIO/actions/runs/41300728008)
exécute et refuse le candidat sans nouvelle inférence. Il révèle un raccord
manquant : `health_check.mjs` supprimait encore le champ HTTP produit par le
worker. Le relevé vide ne permet donc aucune interprétation de la page 403.
La projection du contrôle de santé conserve désormais les mêmes énumérations
bornées. Le test de transmission exécute cette expression réelle de production
entre le sampler et le préflight, puis vérifie l'archive et le retour au Brain.

Le [rejeu 41302016139](https://github.com/niakw/NiakVIO/actions/runs/41302016139)
conserve enfin le diagnostic pour les deux épisodes : Sibnet répond HTTP 403,
HTML, URL inchangée, corps entièrement observé de 93 octets et indice textuel
de refus d'accès. Aucun flux supplémentaire n'est validé. Le rejeu hors ligne
du bundle exact confirme la présence de ces faits dans le prompt du Brain.
Ce signal ne suffit pas à affirmer l'absence de challenge ou la disparition
de la ressource. La synthèse bornée habituelle est rétablie par défaut ;
un rejeu sans inférence reste disponible par l'entrée explicite d'archive.

## 1er novembre 2026 — Comparaison contrôlée du profil User-Agent

Après le diagnostic qualifié, le [run 41302490957](https://github.com/niakw/NiakVIO/actions/runs/41302490957)
appelle effectivement le modèle, qui s'abstient : les fonctions d'admission
proposées ne peuvent réparer les lecteurs déjà atteints. Le code utilise un
profil Chrome pour les wrappers via `hdr()`, mais `_fetch` injecte `NiakVIO/3`
lorsque le crawler appelle le lecteur sans User-Agent explicite. Ce changement
de profil est une hypothèse à tester, pas une cause acquise du 403.

Le diagnostic optionnel `NIAKVIO_READER_UA_PROBE=1` compare la même requête GET
de lecteur refusée à un profil User-Agent observé sur une réponse HTML 2xx
antérieure de la même exécution. Tous les autres en-têtes et paramètres réseau
sont conservés ; seul le signal d'annulation est renouvelé pour borner le contrôle.
La requête est différée après l'exécution du provider, avec une limite d'un
contrôle et 2500 ms par worker. Le verdict, les flux et la durée d'exécution du
provider sont calculés avant ce contrôle. Une réponse HTTP réussie du contrôle
ne compte jamais comme un flux vidéo validé.
Le contrôle respecte aussi la méthode effective d'un objet `Request`. Son délai
est réduit au budget restant du worker, avec 500 ms réservées à la sortie ;
il est omis avec le résultat `budget_exhausted` si ce budget manque.

Les URL, valeurs d'en-têtes et profils restent en mémoire. L'archive conserve
seulement la provenance du profil, le nom du champ changé, un statut, un résultat
énuméré et le diagnostic HTTP borné. Les projections worker → santé → évaluation
→ archive sont testées ensemble. Le worker normal ne lance aucun contrôle sans
activation explicite. Le prochain push rejoue le candidat déjà exécuté du run
41257855269 avec ce diagnostic, sans inférence ni patch manuel du provider.

Le [run 41304513624](https://github.com/niakw/NiakVIO/actions/runs/41304513624)
exécute le contrôle pour les deux épisodes. Le profil antérieurement réussi
donne encore HTTP 403, URL inchangée et la même page HTML de 93 octets avec
indice de refus d'accès. Ce changement d'User-Agent seul ne rétablit donc pas
l'accès dans cet environnement. Hell Mode reste lisible et Jujutsu Kaisen
reste sans flux complet validé ; aucun gain du contrôle n'est compté comme vidéo.

Les 329 tests Brain et l'audit de confidentialité passent. Le Brain publié
`89560b995b2879ebd3ab0b8992c30c2c3dbe5d7b` conserve le contrôle dans le prompt,
avec un rejeu du bundle exact comme preuve de transmission. Les observations
absentes restent absentes. Le workflow retrouve la synthèse bornée par défaut ;
le contrôle supplémentaire nécessite désormais l'entrée manuelle explicite
`reader_user_agent_probe`, désactivée par défaut.

## 2 novembre 2026 — Correspondance entre lecteurs déclarés et requêtes

Le [run 41305337204](https://github.com/niakw/NiakVIO/actions/runs/41305337204)
confirme une abstention après appel réel au modèle : les sélecteurs d'admission
ne peuvent réparer les lecteurs déjà atteints. Les trois `div[data-src]`
observés ne prouvent pas que trois lecteurs différents ont été essayés, car
les anciennes traces fusionnaient les requêtes de même route qui ne différaient
que par leurs paramètres.

Une table privée au worker attribue désormais des références opaques aux URL
HTTP reconnues, dans un espace éphémère propre à l'exécution. Les paramètres
restent distincts ; seuls les fragments sont retirés. Les valeurs d'adresses
et la table restent en mémoire. Les groupes de markup conservés émettent les
références par attribut, puis les événements de requête/réponse et de Referer
les réutilisent. La déduplication du rapport inclut cet espace et la référence
de requête. Aucun octet ni requête réseau supplémentaire n'est nécessaire.

Les limites de la table, des attributs, des échantillons et des traces sont
signalées explicitement. Une référence absente d'une trace partielle ne prouve
pas qu'un lecteur a été ignoré. Les projections worker → santé → préflight →
évaluation → archive et Brain valident indépendamment ces champs. Les tests
couvrent trois wrappers de même route avec paramètres différents, les aliases,
les limites, les entrées forgées et la confidentialité. Les 337 tests Brain et
l'audit de confidentialité passent ; le workflow épingle
`b90234958c6111d8d284d3defa7f262a59269689`.

Le prochain push rejoue le candidat du run 41257855269, sans inférence ni
modification manuelle du provider, afin d'observer la couverture réelle des
lecteurs. Aucune réparation de lecture n'est déduite des seules références.
