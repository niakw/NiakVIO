#!/usr/bin/env python3
"""Cross-repo exact SHA runtime with authorized metadata but no source publishing."""
from pathlib import Path
path=Path(".github/workflows/brain-authenticated-source-challenger.yml")
s=path.read_text(encoding="utf-8")
sha="8fa2f120c11936bcd085d61f8faf2fedcb7c29be"
assert "workflow_dispatch:" in s
assert "source-model-challenger-cpu.yml@" + sha in s
assert "brain_ref: " + sha in s
assert "niakvio_ref: ${{ github.sha }}" in s
assert "TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}" in s
assert "TMDB_ACCESS_TOKEN: ${{ secrets.TMDB_ACCESS_TOKEN }}" in s
assert "contents: read" in s
assert "needs: validate-caller" in s
for forbidden in (
    "secrets: inherit", "write-all", "contents: write", "git push",
    "GITHUB_TOKEN:", "gh api", "publish_niakvio_force_mutations.py",
    "api.github.com/models", "models.github.ai", "NIAKVIO_ALLOW_PAID_API",
):
    assert forbidden not in s, forbidden
print("BRAIN_AUTHENTICATED_SOURCE_CHALLENGER_OK SHA-pinned and TMDB-only secrets")
