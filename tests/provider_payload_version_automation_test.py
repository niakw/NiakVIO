#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / ".github" / "workflows" / "provider-payload-version-sync.yml"
FORCED = ROOT / ".github" / "workflows" / "provider-v3-reconstruct-all.yml"
ROUTES = ROOT / ".github" / "workflows" / "provider-v3-reconstruct-routes.yml"
LEARN = ROOT / ".github" / "workflows" / "brain-learning-lab.yml"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> int:
    sync = SYNC.read_text(encoding="utf-8")
    forced = FORCED.read_text(encoding="utf-8")
    routes = ROUTES.read_text(encoding="utf-8")
    learn = LEARN.read_text(encoding="utf-8")

    # One cache-safety owner watches every published Provider v3 payload source.
    for watched in (
        "- 'manifest.json'",
        "- 'provider-overrides.json'",
        "- 'provider-bases/**'",
        "- 'providers/**'",
    ):
        require(sync, watched, "payload sync watched paths")
    if "branches:" in sync.split("permissions:", 1)[0]:
        raise AssertionError("payload version sync must cover every branch, including Brain/forced branches")

    # Branch synchronization is a workspace transaction. This must remain in
    # scope through release-integrity validation so pre-existing activation state
    # is validated as a baseline, not misread as a new publication shrink.
    require(sync, "NUVIO_PROVIDER_V3_CONTEXT: workspace", "workspace transaction scope")
    for command in (
        "python scripts/materialize_provider_v3_all.py",
        "python scripts/provider_release_versioning.py",
        "python scripts/generate_language_manifests.py",
        "python scripts/generate_release_hashes.py",
        "python scripts/validate_release_integrity.py",
    ):
        require(sync, command, "cache-safe publication pipeline")

    # Forced reconstruction may write only to a non-main branch. Its committed
    # Provider/DATA outputs are watched by the synchronization workflow above,
    # so an applied route/DATA fix cannot reach a PR without cache invalidation.
    require(forced, "Manual Provider v3 reconstruction may never commit directly to main", "forced main guard")
    require(forced, "providers/ provider-v3-materialization.json", "forced provider publication")
    require(forced, "automation/provider-v3-static-knowledge.json automation/provider-v3-recognition-seeds.json provider-overrides.json", "forced DATA publication")
    require(forced, 'git push origin "HEAD:${GITHUB_REF_NAME}"', "forced branch push")

    # Brain/Learn remains proposal-only, but concrete accepted repair DATA/Base
    # is pushed to brain-repair/proposal. Those exact paths are watched by the
    # synchronization workflow, which then materializes providers and bumps only
    # provider payloads whose content-addressed filename changed.
    require(learn, "BRANCH: brain-repair/proposal", "Learn repair branch")
    require(learn, "git add provider-overrides.json PROVENANCE.json provider-bases", "Learn applied repair paths")
    require(learn, 'git push --force-with-lease origin HEAD:"$BRANCH"', "Learn repair branch push")

    # Route reconstruction is evidence-only. It has no write permission and no
    # commit/push path, so merely recognizing candidate routes never bumps a
    # provider or the global manifest release.
    require(routes, "contents: read", "route-only permissions")
    require(routes, "reconstructed static routes are not", "route-only candidate policy")
    require(routes, "never committed from this job", "route-only no publication")
    if "git push" in routes or "git commit" in routes:
        raise AssertionError("route-only reconstruction must not publish candidate DATA")

    print("provider payload version automation contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
