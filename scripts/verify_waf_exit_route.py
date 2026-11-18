#!/usr/bin/env python3
"""Validate Tailscale route selection by independent public IPv4 comparison.

Only transient, restricted runner state contains the IP. Never persist public IP,
exit-node name, cookies, body or tokens to build artifacts or provider evidence.
A changed IP does not establish residential ownership or playable media.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import subprocess
import urllib.request
from pathlib import Path

ENDPOINTS = ("https://checkip.amazonaws.com/", "https://ipv4.icanhazip.com/")


def observed_public_ipv4() -> str:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    seen = []
    for url in ENDPOINTS:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "NiakVIO-egress-attestation/1"})
            with opener.open(request, timeout=8) as response:
                raw = response.read(64).decode("ascii").strip()
            ipaddress.IPv4Address(raw)
            seen.append(raw)
        except (OSError, ValueError, UnicodeError):
            continue
    if not seen or len(set(seen)) != 1:
        raise RuntimeError("public IPv4 cannot be independently established")
    return seen[0]


def exit_status() -> dict:
    proc = subprocess.run(
        ["tailscale", "status", "--json"], capture_output=True, text=True,
        timeout=10, check=False,
    )
    if proc.returncode:
        raise RuntimeError("Tailscale status unavailable")
    try:
        state = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("invalid Tailscale status") from error
    if not isinstance(state, dict):
        raise RuntimeError("invalid Tailscale status payload")
    return state


def attest(before: str, after: str, status: dict) -> None:
    ipaddress.IPv4Address(before)
    ipaddress.IPv4Address(after)
    selected = status.get("ExitNodeStatus")
    if status.get("BackendState") != "Running" or not isinstance(selected, dict):
        raise RuntimeError("selected Tailscale exit route absent")
    if not (selected.get("ID") or selected.get("TailscaleIPs")) or selected.get("Online") is False:
        raise RuntimeError("selected Tailscale exit route inactive")
    if before == after:
        raise RuntimeError("public egress is unchanged")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("baseline", "verify"))
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.phase == "baseline":
            current = observed_public_ipv4()
            fd = os.open(args.state, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="ascii") as handle:
                handle.write(current + "\n")
            os.chmod(args.state, 0o600)
            print("FIELD_WAF_EXIT_EGRESS phase=baseline observed=true")
        else:
            attest(args.state.read_text(encoding="ascii").strip(), observed_public_ipv4(), exit_status())
            print("FIELD_WAF_EXIT_EGRESS phase=residential changed=true selected=true")
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired):
        print("FIELD_WAF_EXIT_EGRESS attested=false reason=verification-unavailable")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
