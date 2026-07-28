# Important correction — full three-manifest discovery

This version does **not** contain a preselected list of 38 providers.

At every publication run, the workflow:

1. downloads the complete manifests from Gowaru, All-in-One-Nuvio and yoruix;
2. downloads every declared non-P2P provider variant;
3. refuses publication if one of the three manifests could not be loaded;
4. checks every downloaded variant before changing the public manifest;
5. groups duplicate IDs only after those checks;
6. selects the best checked variant for each duplicate ID;
7. enables providers confirmed healthy;
8. keeps unconfirmed providers present but disabled instead of silently deleting
   them;
9. publishes content-addressed JavaScript files before the manifest.

The exact counts are generated on each run in `health-report.json`:

- `candidate_variants_checked`;
- `canonical_providers_discovered`;
- `published_providers`;
- `enabled_providers`.

The combined total is therefore never hardcoded in the documentation.
