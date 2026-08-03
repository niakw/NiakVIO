# Release 5.20.0 — VF movie recovery

This release is cumulative from the published 5.19.3 repository state. It does not require the intermediate 5.19.4 bundle.

## Mainstream VF movie providers

Enabled and wired for movie recovery:

- Purstream
- Frenchstream
- StreamZo
- Movix
- Coflix

Published but intentionally disabled pending a new current playable-stream proof:

- Flemmix
- Wooka
- Nakios
- ToFlix

Papadustream remains enabled for TV series only because its implementation does not expose a movie catalogue. Anime-specific providers keep their explicit anime/movie capabilities and are not counted as mainstream VF catalogues.

## Domain resolution

Address hubs, Telegram channels, terminal sites and APIs are separate roles. A hub can discover a candidate, but it can never become the provider base URL. Terminal catalogue markers are checked where the site is HTML-based. API-backed providers require a meaningful endpoint response; a generic 404 is not accepted as API proof. The last known good route is retained when discovery is inconclusive.

## Player validation

Known fake preview routes (`fstream.top`, `/troll/`) and short VOD playlists are rejected. External embed pages are preserved when the provider is declared compatible with an external player instead of being incorrectly reduced to a short or malformed HLS.

## Regression coverage

The release tests both Interstellar and Les Gardiens de la Galaxie : Volume 3 against the current response structures used by Frenchstream, StreamZo, Movix, Coflix and Flemmix. It also checks provider types, hub/terminal separation, API-validation policy, domain-prefix safety, wrapper idempotence and permanent Dahmermovies exclusion.
