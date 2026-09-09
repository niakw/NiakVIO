# International provider discovery

Use **Actions → MANUAL - International Provider Discovery → Run workflow**.

The job is deliberately manual-only. It recompiles the curated international candidate pool, de-duplicates it against the current NiakVIO provider catalog, enforces country/market coverage and regenerates the research JSON/CSV/XLSX.

A candidate route must be an actual provider/site endpoint. Stable website hubs, status/domain pages and public Telegram/Telegraph address channels are valid address sources. GitHub/GitLab/Bitbucket repository URLs are evidence only and are rejected from route/hub fields.

The generated XLSX also includes NiakVIO providers that currently have no stable hub, so a later human discovery pass can target those gaps without overwriting known-good hubs.
