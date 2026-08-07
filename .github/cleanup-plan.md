# Workflow cleanup

Permanent workflows after cleanup:
- `sync.yml` — quick/deep validation, repair and strict publication
- `domain-refresh.yml` — daily official-domain discovery and validated migration
- `availability.yml` — low-cost published-provider availability diagnostics
- `validate-desktop-runtime-compat.yml` — pull-request guard for Desktop QuickJS compatibility

All campaign-specific diagnose/promote/recover/publish workflows and their trigger files are temporary and are removed after the 5.20.25 Desktop runtime publication.
