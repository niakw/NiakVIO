#!/usr/bin/env python3
"""Validate Tailscale route selection by independent public IPv4 comparison.

Capture the baseline before tailnet connection so Tailscale DNS/routing side
effects cannot contaminate the GitHub-network reference point. Only transient,
restricted runner state contains the IP; never persist IP or exit-node identity.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

ENDPOINTS = ("https://checkip.amazonaws.com/", "https://ipv4.icanhazip.com/")
TAILSCALE_SET_TIMEOUT_SECONDS = 12
TAILSCALE_CLEAR_TIMEOUT_SECONDS = 8


def _set_exit_route(*args: str, timeout: int) -> bool:
    try:
        proc = subprocess.run(
            ["sudo", "tailscale", "set", *args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False
    return proc.returncode == 0


def select_exit_node(exit_node: str, attempts: int = 3) -> None:
    node = str(exit_node or "").strip()
    if not node:
        raise RuntimeError("exit node is not configured")
    for attempt in range(1, max(1, attempts) + 1):
        if _set_exit_route(
            f"--exit-node={node}",
            "--exit-node-allow-lan-access=false",
            timeout=TAILSCALE_SET_TIMEOUT_SECONDS,
        ):
            return
        if attempt < attempts:
            time.sleep(min(attempt * 2, 4))
    raise RuntimeError("Tailscale exit route selection unavailable")


def clear_exit_node() -> None:
    if not _set_exit_route("--exit-node=", timeout=TAILSCALE_CLEAR_TIMEOUT_SECONDS):
        raise RuntimeError("Tailscale exit route cleanup unavailable")


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
    parser.add_argument("phase", choices=("baseline", "select", "verify", "clear"))
    parser.add_argument("--state", type=Path)
    parser.add_argument("--exit-node", default="")
    parser.add_argument("--attempts", type=int, default=3)
    args = parser.parse_args()
    phase = args.phase
    try:
        if phase == "baseline":
            if args.state is None: raise RuntimeError("baseline state path missing")
            current = observed_public_ipv4()
            fd = os.open(args.state, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="ascii") as handle: handle.write(current + "\n")
            os.chmod(args.state, 0o600)
            print("FIELD_WAF_EXIT_EGRESS phase=baseline observed=true pre_tailnet=true")
        elif phase == "select":
            select_exit_node(args.exit_node, attempts=max(1, min(args.attempts, 5)))
            print("FIELD_WAF_EXIT_SELECTION selected=true bounded=true")
        elif phase == "verify":
            if args.state is None: raise RuntimeError("verify state path missing")
            before=args.state.read_text(encoding="ascii").strip(); after=observed_public_ipv4()
            attest(before, after, exit_status())
            print("FIELD_WAF_EXIT_EGRESS phase=residential changed=true selected=true")
        else:
            clear_exit_node(); print("FIELD_WAF_EXIT_SELECTION cleared=true bounded=true")
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        message=str(error).casefold()
        if phase=="baseline": reason="baseline-public-ip-unavailable"
        elif phase=="select": reason="exit-selection-unavailable"
        elif "public ipv4" in message: reason="post-exit-public-ip-unavailable"
        elif "unchanged" in message: reason="egress-unchanged"
        elif "status" in message or "exit route" in message: reason="exit-status-unavailable"
        else: reason="verification-unavailable"
        print(f"FIELD_WAF_EXIT_EGRESS attested=false phase={phase} reason={reason}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
