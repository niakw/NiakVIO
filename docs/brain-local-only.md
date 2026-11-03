# Brain sans frais d'API OpenAI

La génération automatique utilise uniquement un modèle local. Les workflows
`brain-multi-provider-repair`, `brain-hosted-repair-check` et `hosted-api-check`
sont désactivés et ne reçoivent plus de clé OpenAI. Un échec du modèle local
ne provoque aucune bascule vers une API distante.

Le pipeline local existant `brain-learning-lab.yml` utilise llama.cpp et
Qwen2.5-Coder sur `http://127.0.0.1:8080`. La boucle de réparation exige aussi
une adresse de loopback et retire les clés OpenAI de tous ses sous-processus.
Si aucun serveur local n'est disponible, elle échoue sans appel payant.

Les frais d'API déjà engagés ne sont pas annulés. Le quota de la conversation
ChatGPT et les éventuels coûts de calcul ou de GitHub Actions sont distincts
de la facturation de l'API OpenAI.
