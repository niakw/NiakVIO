#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "scripts" / "probe_waf_browser_session.py"
JAVA = ROOT / "tools" / "waf-okhttp-probe" / "src" / "main" / "java" / "WafOkHttpProbe.java"
POM = ROOT / "tools" / "waf-okhttp-probe" / "pom.xml"
WORKFLOW = ROOT / ".github" / "workflows" / "provider-waf-browser-session.yml"

spec = importlib.util.spec_from_file_location("probe_waf_browser_session", PY)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

java = JAVA.read_text(encoding="utf-8")
pom = POM.read_text(encoding="utf-8")
workflow = WORKFLOW.read_text(encoding="utf-8")
source = PY.read_text(encoding="utf-8")

assert "<version>4.12.0</version>" in pom
assert "<artifactId>maven-resources-plugin</artifactId>" in pom
assert "<version>3.3.1</version>" in pom
assert "clientBuilder.proxy(Proxy.NO_PROXY)" in java
assert '"system".equals(proxyMode)' in java
assert "NIAKVIO_WAF_OKHTTP_PROFILE" in java
assert "NIAKVIO_WAF_PROXY_MODE" in java
assert ".dns(new IPv4FirstDns())" in java
assert ".followRedirects(true)" in java
assert ".followSslRedirects(true)" in java
assert "SAFE_REQUEST_HEADERS" in java
assert 'name.equals("accept-encoding")' in java
assert "requestBuilder.header(header.getKey(), header.getValue())" in java
assert "Math.min(profileMaxTimeout, Integer.parseInt(args[2]))" in java
assert "response.peekBody(262144)" in java
assert 'outcome = "okhttp_jvm_http_error";' in java
assert "script|style|noscript|template" in java
assert "instanceof Inet4Address ? 0 : 1" in java
assert "nuvio-tv-okhttp-jvm" in source
assert "okHttpJvmProfile" in source
assert "--okhttp-classpath" in source
assert "mvn -q -f tools/waf-okhttp-probe/pom.xml" in workflow
assert "--okhttp-classpath 'tools/waf-okhttp-probe/target/classes:tools/waf-okhttp-probe/target/dependency/*'" in workflow

for forbidden in (
    "cf_clearance",
    "undetected_chromedriver",
    "cloudscraper",
    "flaresolverr",
):
    assert forbidden not in java.casefold(), forbidden

target = {
    "provider": "synthetic",
    "lane": "movie",
    "url": "https://example.invalid/",
    "requestHeaders": {
        "Referer": "https://catalog.example/",
        "Origin": "https://catalog.example",
        "Accept-Language": "fr-FR,fr",
        "Authorization": "Bearer must-never-leave-python",
        "Cookie": "session=must-never-leave-python",
        "Accept-Encoding": "br",
    },
}
original_which = mod.shutil.which
original_run = mod.subprocess.run
commands = []
environments = []
try:
    mod.shutil.which = lambda name: "/usr/bin/java" if name == "java" else original_which(name)
    payload = (
        'NIAKVIO_WAF_OKHTTP={"profile":"nuvio-tv-okhttp-jvm",'
        '"outcome":"okhttp_jvm_content_reached","attemptCount":1,'
        '"attempts":[{"attempt":1,"outcome":"okhttp_jvm_content_reached","status":200}]}\n'
    )
    def fake_run(*args, **kwargs):
        commands.append(args[0])
        environments.append(kwargs.get("env") or {})
        return SimpleNamespace(returncode=0, stdout=payload, stderr="")
    mod.subprocess.run = fake_run
    row = mod.probe_tv_okhttp_jvm(
        target,
        timeout=5,
        attempts=2,
        classpath="classes:deps/*",
    )
finally:
    mod.subprocess.run = original_run
    mod.shutil.which = original_which

assert row["outcome"] == "okhttp_jvm_content_reached", row
assert row["profile"] == "nuvio-tv-okhttp-jvm", row
assert row["nativeContractApproximation"]["httpStack"] == "OkHttp 4.12.0", row
assert row["nativeContractApproximation"]["proxyPolicy"] == "Proxy.NO_PROXY", row
assert row["nativeContractApproximation"]["dnsPolicy"] == "IPv4FirstDns", row
assert row["requestHeaderNames"] == ["accept-language", "origin", "referer"], row
assert commands, commands
assert environments[0]["NIAKVIO_WAF_OKHTTP_PROFILE"] == "nuvio-tv-okhttp-jvm"
assert environments[0]["NIAKVIO_WAF_PROXY_MODE"] == "no-proxy"
assert environments[0]["NIAKVIO_WAF_MAX_TIMEOUT_SECONDS"] == "30"
joined = "\n".join(str(value) for value in commands[0])
assert "referer: https://catalog.example/" in joined
assert "origin: https://catalog.example" in joined
assert "accept-language: fr-FR,fr" in joined
for secret in ("Authorization", "Bearer must-never-leave-python", "Cookie", "session=must-never-leave-python", "Accept-Encoding"):
    assert secret not in joined, (secret, joined)

desktop_commands = []
desktop_envs = []
original_which = mod.shutil.which
original_run = mod.subprocess.run
try:
    mod.shutil.which = lambda name: "/usr/bin/java" if name == "java" else original_which(name)
    desktop_payload = (
        'NIAKVIO_WAF_OKHTTP={"profile":"nuvio-desktop-okhttp-jvm",'
        '"outcome":"okhttp_jvm_content_reached","attemptCount":1,'
        '"attempts":[{"attempt":1,"outcome":"okhttp_jvm_content_reached","status":200}],'
        '"nativeContractApproximation":{"proxyPolicy":"JVM/system default"}}\n'
    )
    def fake_desktop_run(*args, **kwargs):
        desktop_commands.append(args[0])
        desktop_envs.append(kwargs.get("env") or {})
        return SimpleNamespace(returncode=0, stdout=desktop_payload, stderr="")
    mod.subprocess.run = fake_desktop_run
    desktop = mod.probe_desktop_okhttp_jvm(
        target,
        timeout=55,
        attempts=1,
        classpath="classes:deps/*",
    )
finally:
    mod.subprocess.run = original_run
    mod.shutil.which = original_which

assert desktop["profile"] == "nuvio-desktop-okhttp-jvm", desktop
assert desktop["outcome"] == "okhttp_jvm_content_reached", desktop
assert desktop["nativeContractApproximation"]["proxyPolicy"] == "JVM/system default", desktop
assert desktop_envs[0]["NIAKVIO_WAF_PROXY_MODE"] == "system"
assert desktop_envs[0]["NIAKVIO_WAF_MAX_TIMEOUT_SECONDS"] == "60"
assert "55" in desktop_commands[0], desktop_commands

print("Nuvio TV/Desktop OkHttp WAF diagnostic contract passed")
