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
import shutil
import subprocess
import time
from pathlib import Path

ENDPOINTS = (
    "https://checkip.amazonaws.com/",
    "https://api.ipify.org/",
    # Direct-IP HTTPS fallback avoids making route attestation depend entirely
    # on the runner's current DNS resolver after Tailscale route selection.
    "https://1.1.1.1/cdn-cgi/trace",
)
TAILSCALE_SET_TIMEOUT_SECONDS = 12
TAILSCALE_CLEAR_TIMEOUT_SECONDS = 8
PUBLIC_IP_COMMAND_TIMEOUT_SECONDS = 8
EGRESS_VERIFY_ATTEMPTS = 3
EGRESS_VERIFY_BACKOFF_SECONDS = (2, 4)


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


def _extract_public_ipv4(body: str) -> str:
    lines = [line.strip() for line in str(body or "").splitlines() if line.strip()]
    candidates = []
    for line in lines:
        if line.casefold().startswith("ip="):
            candidates.append(line.split("=", 1)[1].strip())
        elif "=" not in line:
            candidates.append(line)
    for value in candidates:
        try:
            parsed = ipaddress.IPv4Address(value[:64])
            # A private, loopback, documentation or CGNAT address cannot be
            # evidence of an independently observable public internet route.
            if parsed.is_global:
                return str(parsed)
        except ValueError:
            continue
    raise ValueError("response does not contain a public IPv4")


def observed_public_ipv4() -> str:
    """Return the first independently observed public IPv4 with hard deadlines.

    Exact equality across separate public-IP services is intentionally not required:
    GitHub-hosted runners can traverse rotating NAT egress. Route proof instead
    combines a changed public IPv4 with Tailscale's active ExitNodeStatus.
    """
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("public IPv4 probe unavailable")
    for index, url in enumerate(ENDPOINTS, start=1):
        try:
            proc = subprocess.run(
                [
                    curl,
                    "--ipv4",
                    "--fail",
                    "--noproxy", "*",
                    "--location",
                    "--max-redirs", "2",
                    "--connect-timeout", "3",
                    "--max-time", "6",
                    "--silent",
                    "--show-error",
                    "--user-agent", "NiakVIO-egress-attestation/3",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=PUBLIC_IP_COMMAND_TIMEOUT_SECONDS,
                check=False,
            )
            if proc.returncode != 0:
                failure = {
                    6: "dns",
                    7: "connect",
                    22: "http",
                    28: "timeout",
                    35: "tls",
                    60: "certificate",
                }.get(proc.returncode, "transport")
                print(f"FIELD_WAF_EXIT_ENDPOINT index={index} result={failure}")
                continue
            try:
                public_ip = _extract_public_ipv4(proc.stdout)
            except ValueError:
                print(f"FIELD_WAF_EXIT_ENDPOINT index={index} result=no_public_ipv4")
                continue
            print(f"FIELD_WAF_EXIT_ENDPOINT index={index} result=public_ipv4")
            return public_ip
        except subprocess.TimeoutExpired:
            print(f"FIELD_WAF_EXIT_ENDPOINT index={index} result=deadline")
        except (OSError, UnicodeError):
            print(f"FIELD_WAF_EXIT_ENDPOINT index={index} result=command_error")
    raise RuntimeError("public IPv4 cannot be independently established")


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


def exit_route_health(status: dict) -> tuple[bool, bool, bool]:
    selected = status.get("ExitNodeStatus")
    backend_running = status.get("BackendState") == "Running"
    exit_present = isinstance(selected, dict) and bool(selected.get("ID") or selected.get("TailscaleIPs"))
    exit_online = bool(exit_present and selected.get("Online") is not False)
    return backend_running, exit_present, exit_online


def attest(before: str, after: str, status: dict) -> None:
    if not ipaddress.IPv4Address(before).is_global or not ipaddress.IPv4Address(after).is_global:
        raise RuntimeError("public egress is not globally routable")
    backend_running, exit_present, exit_online = exit_route_health(status)
    if not backend_running or not exit_present:
        raise RuntimeError("selected Tailscale exit route absent")
    if not exit_online:
        raise RuntimeError("selected Tailscale exit route inactive")
    if before == after:
        raise RuntimeError("public egress is unchanged")


def verify_converged_exit(before: str, attempts: int = EGRESS_VERIFY_ATTEMPTS) -> str:
    """Wait briefly for selected exit dataplane convergence, never for control-plane only."""
    last_error = "selected exit route has no observable public internet"
    bounded_attempts = max(1, min(int(attempts), EGRESS_VERIFY_ATTEMPTS))
    for attempt in range(1, bounded_attempts + 1):
        status = exit_status()
        backend_running, exit_present, exit_online = exit_route_health(status)
        print(
            "FIELD_WAF_EXIT_STATUS "
            f"attempt={attempt} backend_running={str(backend_running).lower()} "
            f"exit_present={str(exit_present).lower()} exit_online={str(exit_online).lower()}"
        )
        if not backend_running or not exit_present:
            raise RuntimeError("selected Tailscale exit route absent")
        if not exit_online:
            raise RuntimeError("selected Tailscale exit route inactive")
        try:
            after = observed_public_ipv4()
        except RuntimeError:
            last_error = "selected exit route has no observable public internet"
            print(f"FIELD_WAF_EXIT_PUBLIC_PROBE attempt={attempt} reached=false")
        else:
            if after != before:
                attest(before, after, status)
                print(f"FIELD_WAF_EXIT_PUBLIC_PROBE attempt={attempt} reached=true changed=true")
                return after
            last_error = "public egress is unchanged"
            print(f"FIELD_WAF_EXIT_PUBLIC_PROBE attempt={attempt} reached=true changed=false")
        if attempt < bounded_attempts:
            time.sleep(EGRESS_VERIFY_BACKOFF_SECONDS[min(attempt - 1, len(EGRESS_VERIFY_BACKOFF_SECONDS) - 1)])
    raise RuntimeError(last_error)


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
            before = args.state.read_text(encoding="ascii").strip()
            verify_converged_exit(before, attempts=max(1, min(args.attempts, EGRESS_VERIFY_ATTEMPTS)))
            print("FIELD_WAF_EXIT_EGRESS phase=residential changed=true selected=true")
        else:
            clear_exit_node(); print("FIELD_WAF_EXIT_SELECTION cleared=true bounded=true")
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        message=str(error).casefold()
        if phase=="baseline": reason="baseline-public-ip-unavailable"
        elif phase=="select": reason="exit-selection-unavailable"
        elif "no observable public internet" in message: reason="exit-selected-public-internet-unavailable"
        elif "public ipv4" in message: reason="post-exit-public-ip-unavailable"
        elif "unchanged" in message: reason="egress-unchanged"
        elif "inactive" in message: reason="exit-node-offline"
        elif "status" in message or "exit route" in message: reason="exit-status-unavailable"
        else: reason="verification-unavailable"
        print(f"FIELD_WAF_EXIT_EGRESS attested=false phase={phase} reason={reason}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
