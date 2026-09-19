#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from summarize_provider_v3_provenance_for_repair import summarize  # noqa: E402


def main() -> int:
    provenance = {
        "schema_version": 64,
        "generated_at": "2026-09-01T20:34:19+00:00",
        "providers": {
            "Example": {
                "source": "published-baseline",
                "source_name": "Last published local artifact",
                "checked_at": "2026-09-01T20:34:19+00:00",
                "check_mode": "deep",
                "check_status": "no_streams",
                "health_score": 82,
                "activation_eligible": False,
                "activation_blockers": ["route_identity", "content_identity"],
                "activation_gates": {
                    "00_dns_or_alternative_domain": {
                        "evidence": {"dns_status": "inconclusive"}
                    },
                    "00_provider_specific_access": {
                        "evidence": {
                            "provider_server_successful_response": True,
                            "provider_server_hosts": ["example.invalid", "api.example.invalid"],
                            "provider_server_http_statuses": [200, 403, 404],
                        }
                    },
                },
                # Deliberately route-looking historical fields: the summary must
                # never expose/promote them as executable route candidates.
                "historical_route": "/old-search?q=x",
                "historical_url": "https://example.invalid/old-search?q=x",
            },
            "Blocked": {
                "check_status": "blocked",
                "activation_gates": {
                    "00_provider_specific_access": {
                        "evidence": {
                            "provider_server_successful_response": False,
                            "provider_server_hosts": ["blocked.invalid"],
                            "provider_server_http_statuses": [403],
                        }
                    }
                },
            },
        },
    }

    summary = summarize(provenance)
    assert summary["role"] == "diagnostic-only-not-route-authority", summary
    assert summary["sourceSchemaVersion"] == 64, summary

    example = summary["providers"]["example"]
    assert example["routeAuthority"] is False, example
    assert example["providerServerSuccessfulResponse"] is True, example
    assert example["providerServerHosts"] == ["example.invalid", "api.example.invalid"], example
    assert example["providerServerHttpStatuses"] == [200, 403, 404], example
    assert example["failureFamilyHints"]["mixed403404Or522"] is True, example
    assert example["failureFamilyHints"]["routeMustNotBeInventedFromProvenance"] is True, example
    assert "historical_route" not in example, example
    assert "historical_url" not in example, example

    blocked = summary["providers"]["blocked"]
    assert blocked["failureFamilyHints"]["blockedOrPolicyHttpOnly"] is True, blocked
    assert blocked["failureFamilyHints"]["hasSuccessfulProviderHttp"] is False, blocked

    print("provider v3 provenance repair index tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
