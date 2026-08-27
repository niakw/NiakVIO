# Disclaimer

This project is a technical manifest curator and compatibility monitor for
user-installed Nuvio provider modules.

It does not host, store, cache, index, upload, sell or distribute audiovisual content.
It does not provide user accounts, subscriptions, access credentials, decryption keys,
media files or a content catalogue. Public reports should omit complete playback URLs.

Automated checks establish only that a software module executed and that a limited
technical response was observed at a specific time from a GitHub-hosted runner.

## Test fixtures and work references

Names, titles, release years, seasons, episodes and similar identifiers of audiovisual works may appear in source files, fixture IDs, CI logs, artifact names and README evidence tables. They are used as deterministic test identifiers to verify software matching, media identity and wrong-content regressions.

A named fixture is **not** a content-catalogue entry and does not represent an offer, recommendation, endorsement, ownership claim, licence determination, authorization statement or representation that a work is lawfully available from any third-party service.

Repository fixtures and persisted public evidence should contain only the minimum metadata and sanitized technical observations needed for reproducible compatibility testing. They must not intentionally include or persist audiovisual files, clips, subtitles, decryption keys, access tokens, cookies, credentials or complete playback URLs.

Where a compatibility check can be performed using metadata, a lawful public preview or a trailer, those lower-exposure test inputs should be preferred. This does **not** mean that every native compatibility check is a trailer test.

A passing test establishes only a technical observation at a specific time. It does not establish the legal status of the work, source, provider, host, user access or downstream use.

See [`TESTING_NOTICE.md`](TESTING_NOTICE.md) for the repository-wide fixture policy.

## International and jurisdiction-specific rules

Copyright limitations and exceptions differ between jurisdictions. This project does not rely on, promise or represent that any particular doctrine — including fair use, fair dealing, research, testing, quotation, transient copying or interoperability — applies to a particular test or user.

Nothing in this repository grants a copyright licence, content-access right or permission to bypass paywalls, authentication, access controls, encryption or other technological protection measures. If applicable law or binding service terms do not permit a test or use, this notice does not authorize it.

The repository's minimization and sanitization rules are risk-reduction practices, not a substitute for jurisdiction-specific legal analysis.

They do not establish:

- ownership of any content;
- authorization to access any content;
- licensing status;
- territorial availability;
- accuracy of a title match;
- continued availability;
- legal compliance of any third-party service.

The software should be used only with content the user owns, controls, created,
licensed or is otherwise authorized to access.

Every user is solely responsible for complying with applicable law, contractual terms,
service rules and third-party rights. This statement describes the intended use of the
software and does not add restrictions to the GPL licence.

This repository is independent from Nuvio, all upstream projects and all third-party
services. Upstream maintainers are not responsible for this repository or for
downstream use.

Inclusion of a third-party provider does not imply endorsement, approval or validation
by its original author.

Content-related requests should be directed to the actual host or service controlling
the material. This repository cannot remove material it does not host.

Nothing in this notice authorizes unlawful use, overrides applicable law or excludes
responsibility that cannot legally be excluded.

The software is provided without warranty. See `LICENSE` for the GNU GPL v3 provisions
concerning absence of warranty and limitation of liability.

This document is informational and is not legal advice.


---

## Français — résumé

NiakVIO est un projet technique de compatibilité de providers. Il n'héberge, ne stocke, ne met en cache et ne distribue aucun contenu audiovisuel.

Des noms d'œuvres, années, saisons ou épisodes peuvent apparaître comme **fixtures de test déterministes** dans le code, les logs CI, les noms d'artefacts ou les tableaux de résultats. Ces références servent à vérifier le matching, l'identité du média et les régressions de type « mauvais contenu ». Elles ne constituent ni un catalogue, ni une offre de contenu, ni une recommandation, ni une affirmation de propriété, licence, disponibilité légale ou autorisation d'un service tiers.

Les preuves publiques doivent rester minimales et sanitizées : pas de fichier audiovisuel, extrait, sous-titre, clé de déchiffrement, identifiant secret, cookie, credential ou URL complète de lecture persistée intentionnellement. Quand un contrôle peut être réalisé avec des métadonnées, une preview publique licite ou une bande-annonce, ces entrées à exposition réduite sont à privilégier ; cela ne signifie pas que tous les tests natifs sont des tests de bandes-annonces.

Un test réussi prouve seulement une observation technique ponctuelle ; il ne prouve pas la situation juridique du contenu, du provider, de l'hébergeur ou de l'utilisation qui en est faite.

Les exceptions et limitations de droit d'auteur diffèrent selon les juridictions. NiakVIO ne présume pas qu'une exception particulière (recherche, test, citation, copie transitoire ou équivalent local) s'applique à un test ou à un utilisateur donné. Rien dans le dépôt n'accorde de licence ni n'autorise le contournement d'un paywall, d'une authentification, d'un contrôle d'accès, d'un chiffrement ou d'une mesure technique de protection.

L'utilisation du logiciel doit respecter la loi applicable, les conditions des services concernés et les droits des tiers. Les règles de minimisation/sanitization réduisent l'exposition technique mais ne remplacent pas une analyse juridique locale. Ce document est informatif et ne constitue pas un avis juridique. Voir [`TESTING_NOTICE.md`](TESTING_NOTICE.md).
