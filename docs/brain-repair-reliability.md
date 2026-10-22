# Fiabilité des réparations NiakVIO / NiakVIO-Brain-LLM

Diagnostic local du 22 octobre 2026. Les changements concernent le planificateur,
la mémoire et son admission. Ils ne constituent pas une preuve de réparation
des providers ni un entraînement des poids du modèle.

## Blocages reproduits et corrections

| Blocage | Correction |
| --- | --- |
| Le planificateur Node échoue à lire un gros payload sur stdin, avant toute hypothèse. | Transmission complète par fichier temporaire via son contrat `NUVIO_BRAIN_PLANNER_INPUT_FILE`, avec nettoyage après succès ou erreur. |
| Un essai `executionObserved=false` ou un profil indisponible devient un échec bloquant. | Même distinction entre exécution et sélection dans le choix Brain, la publication de guidance, l'import NiakVIO et le scheduler. Les vrais échecs historiques restent exclus. |
| L'adaptateur garde les premières 32 lignes, puis le batch tronque encore la mémoire. | Conservation du registre sanitizé du provider pour les exclusions déterministes ; seul le contexte affiché au modèle est borné. Les réservations empêchent les doublons du batch sans oublier les anciens échecs. |
| Une expérience explicitement échouée impose une stratégie à forte confiance. | Les résultats négatifs ou inconclusifs ne peuvent plus fournir un prior positif. |
| Une proposition LLM répète une mutation déjà rejetée par le sandbox. | Contrôle de son empreinte avant admission, avec feedback de correction. Un nouveau candidat reste admissible ; les patches sont comparés dans leur contexte de source. |
| Un programme positif historique contourne le contrat actuel de preuve terminale. | Revalidation à la lecture ; conservation des recettes terminales à la compilation pour permettre le parcours compilation → mémoire → réutilisation. Les entrées rejetées sont signalées sans modifier l'historique source. |
| Le mode API ignore `NIAKVIO_OPENAI_API_KEY` et hérite du modèle local. | Résolution dédiée au backend hosted, avec la variable NiakVIO prioritaire et un modèle hosted par défaut. |

## Observations locales

- `automation/provider-brain-repair-latest.json` : 11 providers sélectionnés,
  aucune réparation acceptée, 11 différés à Learning.
- `automation/brain-repair-memory.json` : 1 154 entrées. L'ancien filtre d'import
  considérait 543 hypothèses échouées, dont 44 non exécutées.
- Le payload de mémoire réel de 690 Ko faisait échouer le transport stdin.
  Le même payload passe par fichier. Une reconstruction hors ligne des 11
  providers du census produit désormais 11 plans ; ce n'est pas un rejeu exact
  des résultats health ni une validation média.
- Les deux programmes positifs MalluMV historiques ne conservent aucune recette
  terminale avec `streamProof=true`. L'un contient des routes de vidéos marketing.
  La vue revalidée les exclut des routes et succès réutilisables.

## Vérification reproductible

Depuis NiakVIO :

```sh
python3 tests/brain_base_planner_large_input_test.py
python3 tests/brain_learning_guidance_negative_filter_test.py
python3 tests/brain_positive_program_memory_test.py
python3 tests/brain_accepted_program_v3_persistence_test.py
```

Depuis NiakVIO-Brain-LLM :

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/audit_public_repo_privacy.py
```

Le test de transport exécute réellement Node avec plus de 1 Mo de mémoire.
Les tests Brain couvrent les exclusions anciennes et récentes, les non-exécutions,
les réservations, les mutations répétées et les nouveaux candidats admissibles.

## Génération par API

Le mode `--backend hosted` utilise `NIAKVIO_OPENAI_API_KEY`, puis
`OPENAI_API_KEY` en secours. Les résultats restent soumis aux contrôles NiakVIO.
Le test réel de génération a retourné HTTP 401 avec le code `invalid_api_key` ;
la liste des modèles était accessible. Aucun résultat généré ni provider réparé
n'est donc revendiqué pour ce test. Il faut rendre le secret d'inférence valide
dans l'environnement pour effectuer la campagne réelle.
