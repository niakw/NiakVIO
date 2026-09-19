# Testing Notice / Notice relative aux tests

## English

NiakVIO uses deterministic **test fixtures** to verify provider compatibility, media identity, client integration and regressions such as wrong-title, wrong-season or wrong-episode playback.

### References to audiovisual works

A work title, year, season or episode appearing in source code, test configuration, CI logs, artifact names or README evidence is a **test identifier**. It is not a catalogue entry, an offer of content, an endorsement, a statement of ownership, a licence determination or a representation that any third-party service is authorized to provide that work.

### Minimal public evidence

Repository-owned fixtures and persisted public evidence should contain only what is needed for reproducible technical verification:

- identifiers and minimal metadata;
- sanitized compatibility observations;
- provider/client/device status;
- bounded media characteristics needed for identity or playback checks.

They must not intentionally persist:

- audiovisual files or clips;
- subtitle payloads;
- decryption keys;
- credentials, cookies or access tokens;
- secret request headers;
- complete playback URLs or signed media URLs.

Transient CI/runtime data should be sanitized before it is persisted or published.

### Lower-exposure inputs first

When the same compatibility assertion can be made with metadata, a lawful public preview, a trailer or another lower-exposure input, that input should be preferred. This is a testing-minimization policy, **not a claim that every native Lab test uses trailers**.

### International and jurisdiction-specific use

Copyright exceptions and limitations vary by country. This repository does not assume that fair use, fair dealing, research/testing, quotation, transient-copying, interoperability or any other exception applies to a particular test.

This policy does not grant a licence or content-access right. It does not authorize bypassing authentication, paywalls, encryption, access controls or technological protection measures. If applicable law or binding service terms do not permit an action, the repository notice does not make that action permitted.

Contributors should keep test inputs and persisted evidence no broader than technically necessary and should prefer lower-exposure, lawfully public inputs whenever they can establish the same compatibility assertion.

### What a passing test means

A passing test means only that a specific software path produced a bounded technical observation at a specific time. It does not determine:

- copyright ownership;
- licensing or authorization;
- territorial availability;
- legality of a third-party source;
- legality of a user's access or downstream use.

Tests and downstream use must comply with applicable law, third-party rights and relevant service terms.

NiakVIO does not host or distribute audiovisual content. See [`DISCLAIMER.md`](DISCLAIMER.md) for the broader project disclaimer.

This notice documents intended repository/testing practice and is not legal advice.

---

## Français

NiakVIO utilise des **fixtures de test déterministes** afin de vérifier la compatibilité des providers, l'identité des médias, l'intégration aux clients et les régressions telles qu'une mauvaise œuvre, saison ou épisode.

### Références à des œuvres audiovisuelles

Un titre d'œuvre, une année, une saison ou un épisode visible dans le code source, la configuration de test, les logs CI, les noms d'artefacts ou les tableaux du README est un **identifiant de test**. Ce n'est ni une entrée de catalogue, ni une offre de contenu, ni une recommandation, ni une déclaration de propriété, de licence ou d'autorisation d'un service tiers.

### Preuves publiques minimales

Les fixtures appartenant au dépôt et les preuves publiques persistées doivent se limiter aux informations nécessaires à une vérification technique reproductible :

- identifiants et métadonnées minimales ;
- observations de compatibilité sanitizées ;
- état provider/client/device ;
- caractéristiques média strictement nécessaires aux contrôles d'identité ou de lecture.

Elles ne doivent pas persister intentionnellement :

- des fichiers ou extraits audiovisuels ;
- des payloads de sous-titres ;
- des clés de déchiffrement ;
- des identifiants, cookies ou jetons d'accès ;
- des headers secrets ;
- des URL complètes ou signées de lecture.

Les données transitoires de CI/runtime doivent être sanitizées avant toute persistance ou publication.

### Privilégier les entrées à exposition réduite

Lorsque la même assertion de compatibilité peut être vérifiée avec des métadonnées, une preview publique licite, une bande-annonce ou une autre entrée à exposition réduite, cette entrée doit être privilégiée. Il s'agit d'une politique de minimisation des tests, **pas d'une affirmation selon laquelle tous les Labs natifs utilisent des bandes-annonces**.

### Utilisation internationale et règles propres à chaque juridiction

Les exceptions et limitations au droit d'auteur varient selon les pays. Le dépôt ne présume pas que le fair use, fair dealing, la recherche, le test, la citation, la copie transitoire, l'interopérabilité ou une autre exception locale s'applique à un test donné.

Cette politique n'accorde aucune licence ni droit d'accès à un contenu. Elle n'autorise pas le contournement d'une authentification, d'un paywall, d'un chiffrement, d'un contrôle d'accès ou d'une mesure technique de protection. Si la loi applicable ou des conditions de service opposables n'autorisent pas une action, cette notice ne la rend pas autorisée.

Les contributeurs doivent limiter les entrées de test et les preuves persistées au strict nécessaire technique et privilégier les entrées publiques licites à exposition réduite lorsqu'elles permettent d'établir la même assertion de compatibilité.

### Signification d'un test réussi

Un test réussi signifie uniquement qu'un chemin logiciel précis a produit une observation technique bornée à un instant donné. Il ne détermine pas :

- la propriété des droits ;
- l'existence d'une licence ou autorisation ;
- la disponibilité territoriale ;
- la légalité d'une source tierce ;
- la légalité de l'accès d'un utilisateur ou de l'utilisation en aval.

Les tests et usages en aval doivent respecter la loi applicable, les droits des tiers et les conditions des services concernés.

NiakVIO n'héberge ni ne distribue de contenu audiovisuel. Voir [`DISCLAIMER.md`](DISCLAIMER.md) pour le disclaimer général du projet.

Cette notice décrit la pratique attendue du dépôt et des tests ; elle ne constitue pas un avis juridique.
