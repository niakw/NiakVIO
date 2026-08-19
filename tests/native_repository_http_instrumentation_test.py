#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/instrument_native_repository_http_evidence.py"
spec = importlib.util.spec_from_file_location("repository_http_evidence", MODULE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write(root: Path, relative: str, content: str) -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


with tempfile.TemporaryDirectory() as tmp_raw:
    tmp = Path(tmp_raw)

    tv = tmp / "tv"
    tv_path = write(
        tv,
        "app/src/full/java/com/nuvio/tv/core/plugin/PluginManager.kt",
        "private val httpClient = OkHttpClient.Builder()\n"
        "        .dns(com.nuvio.tv.core.network.IPv4FirstDns())\n"
        "        .connectTimeout(30, TimeUnit.SECONDS)\n"
        "        .readTimeout(30, TimeUnit.SECONDS)\n"
        "        .build()\n",
    )
    mod.instrument_tv(tv)
    tv_out = tv_path.read_text(encoding="utf-8")
    assert "FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client=tv" in tv_out
    assert ".connectTimeout(30, TimeUnit.SECONDS)" in tv_out
    assert ".readTimeout(30, TimeUnit.SECONDS)" in tv_out

    mobile = tmp / "mobile"
    mobile_path = write(
        mobile,
        "composeApp/src/androidMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.android.kt",
        "private fun client() = OkHttpClient.Builder()\n"
        "        .addInterceptor(SentryNetworkBreadcrumbInterceptor())\n"
        "        .proxy(Proxy.NO_PROXY)\n"
        "        .build()\n",
    )
    mod.instrument_mobile(mobile)
    mobile_out = mobile_path.read_text(encoding="utf-8")
    assert "FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client=mobile" in mobile_out
    assert ".proxy(Proxy.NO_PROXY)" in mobile_out

    desktop = tmp / "desktop"
    desktop_path = write(
        desktop,
        "composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt",
        "private val desktopHttpClient = OkHttpClient.Builder()\n"
        "    .followRedirects(true)\n"
        "    .followSslRedirects(true)\n"
        "    .build()\n",
    )
    mod.instrument_desktop(desktop)
    desktop_out = desktop_path.read_text(encoding="utf-8")
    assert "FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client=desktop" in desktop_out

    for client_out in (tv_out, mobile_out, desktop_out):
        for required in (
            "rawGithubEvidence",
            "loopbackEvidence",
            'setOf("127.0.0.1", "localhost", "10.0.2.2")',
            'Regex("/candidate-[0-9a-f]{32}/")',
            "FIELD_NATIVE_REPOSITORY_HTTP_RESPONSE",
            "FIELD_NATIVE_REPOSITORY_HTTP_ERROR",
            "request_header_names=$requestHeaderNames",
            "response_header_names=$responseHeaderNames",
            "source=$cacheSource",
        ):
            assert required in client_out, required
        # Evidence must not persist query strings, request/response bodies or
        # credential/header values. Only endpoint sans query and header names exist.
        assert "authorization=" not in client_out.lower()
        assert "cookie=" not in client_out.lower()
        assert "query=" not in client_out.lower()

print("native repository HTTP instrumentation tests passed")
