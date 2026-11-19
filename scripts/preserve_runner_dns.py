#!/usr/bin/env python3
"""Restore the hosted runner DNS policy after Tailscale Action mutation.

On macOS the pinned Tailscale GitHub Action may apply 100.100.100.100 even when
tailscaled receives --accept-dns=false. State is transient and must not be
uploaded as evidence.
"""
from __future__ import annotations
import argparse,json,os,platform,socket,subprocess,time
from pathlib import Path
from typing import Any
MAGIC_DNS="100.100.100.100"
PROBE_HOSTS=("checkip.amazonaws.com","ipv4.icanhazip.com")

def _run(args:list[str],timeout:int=12)->subprocess.CompletedProcess[str]:
    return subprocess.run(args,capture_output=True,text=True,timeout=timeout,check=False)

def _values(text:str)->list[str]:
    rows=[x.strip() for x in str(text or "").splitlines() if x.strip()]
    return [] if any("There aren't any " in x for x in rows) else rows

def _services()->list[str]:
    p=_run(["networksetup","-listallnetworkservices"])
    if p.returncode: raise RuntimeError("networksetup-services-unavailable")
    rows=[x.strip() for x in p.stdout.splitlines() if x.strip() and not x.startswith("An asterisk") and not x.startswith("*")]
    if not rows: raise RuntimeError("networksetup-services-empty")
    return rows

def _snapshot_macos()->dict[str,Any]:
    rows=[]
    for name in _services():
        d=_run(["networksetup","-getdnsservers",name]); s=_run(["networksetup","-getsearchdomains",name])
        if d.returncode or s.returncode: continue
        rows.append({"name":name,"dns":_values(d.stdout),"search":_values(s.stdout)})
    if not rows: raise RuntimeError("networksetup-readable-services-empty")
    return {"services":rows,"magicDnsPreexisting":any(MAGIC_DNS in r["dns"] for r in rows)}

def _set(kind:str,name:str,values:list[str])->None:
    flag="-setdnsservers" if kind=="dns" else "-setsearchdomains"
    p=_run(["sudo","networksetup",flag,name,*(values or ["Empty"])])
    if p.returncode: raise RuntimeError(f"networksetup-restore-{kind}-failed")

def _active_nameservers()->set[str]:
    p=_run(["scutil","--dns"])
    if p.returncode: raise RuntimeError("scutil-dns-unavailable")
    return {line.split(":",1)[1].strip() for line in p.stdout.splitlines() if "nameserver[" in line and ":" in line}

def _resolves()->bool:
    for host in PROBE_HOSTS:
        try: rows=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        except OSError: return False
        if not rows: return False
    return True

def snapshot(path:Path)->None:
    system=platform.system().lower(); data={"schemaVersion":1,"platform":system}
    if system=="darwin": data.update(_snapshot_macos())
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as h: json.dump(data,h,sort_keys=True); h.write("\n")
    os.chmod(path,0o600)
    print(f"FIELD_NATIVE_DNS_SNAPSHOT platform={system} services={len(data.get('services') or [])} transient=true")

def restore(path:Path)->None:
    data=json.loads(path.read_text(encoding="utf-8")); system=platform.system().lower()
    if data.get("platform")!=system: raise RuntimeError("dns-state-platform-mismatch")
    if system!="darwin":
        print(f"FIELD_NATIVE_DNS_RESTORE platform={system} changed=false supported=false"); return
    rows=data.get("services") or []
    if not isinstance(rows,list) or not rows: raise RuntimeError("dns-state-services-missing")
    for row in rows:
        name=str(row.get("name") or "").strip()
        if not name: raise RuntimeError("dns-state-service-invalid")
        _set("dns",name,[str(x) for x in row.get("dns") or []]); _set("search",name,[str(x) for x in row.get("search") or []])
    pre=bool(data.get("magicDnsPreexisting"))
    for attempt in range(1,6):
        if (pre or MAGIC_DNS not in _active_nameservers()) and _resolves():
            print("FIELD_NATIVE_DNS_RESTORE platform=darwin changed=true magicdns_override_removed=true resolver_ready=true"); return
        if attempt<5: time.sleep(attempt)
    raise RuntimeError("dns-restore-verification-failed")

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("phase",choices=("snapshot","restore")); ap.add_argument("--state",type=Path,required=True); a=ap.parse_args()
    try: snapshot(a.state) if a.phase=="snapshot" else restore(a.state)
    except (RuntimeError,OSError,ValueError,json.JSONDecodeError,subprocess.TimeoutExpired):
        print(f"FIELD_NATIVE_DNS_{a.phase.upper()} status=failed"); return 1
    return 0
if __name__=="__main__": raise SystemExit(main())
