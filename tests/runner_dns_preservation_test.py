#!/usr/bin/env python3
import importlib.util
from pathlib import Path
root=Path(__file__).resolve().parents[1]; script=root/"scripts/preserve_runner_dns.py"
spec=importlib.util.spec_from_file_location("runner_dns",script); assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
assert mod.MAGIC_DNS=="100.100.100.100"
assert mod._values("There aren't any DNS Servers set on Wi-Fi.\n")==[]
assert mod._values("9.9.9.9\n149.112.112.112\n")==["9.9.9.9","149.112.112.112"]
src=script.read_text()
for x in ("-getdnsservers","-getsearchdomains","-setdnsservers","-setsearchdomains","scutil","magicdns_override_removed=true","resolver_ready=true"): assert x in src,x
assert "print(data" not in src and "print(nameservers" not in src
print("pre-Tailscale DNS preservation contract passed")
