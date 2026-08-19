#!/usr/bin/env python3
"""Inject passive HTTP evidence into official Nuvio repository loaders.

Requests are observed only when they belong to the NiakVIO repository under test:
- exact raw.githubusercontent.com/niakw/NiakVIO paths, or
- content-addressed loopback candidate paths used by isolated native repair labs.

The interceptor does not alter method, URL, headers, body, redirects, cache policy,
DNS, timeouts or response handling. Query strings/header values/bodies are never
persisted.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"repository HTTP instrumentation anchor {label!r} count={count}")
    return text.replace(old, new, 1)


def kotlin_interceptor(client: str, logger: str) -> str:
    emit = (
        'android.util.Log.i("NiakvioEvidence", message)'
        if logger == "android"
        else "println(message)"
    )
    return f'''.addInterceptor {{ chain ->
            val request = chain.request()
            val rawUrl = request.url
            val encodedPath = rawUrl.encodedPath
            val rawGithubEvidence = rawUrl.host.equals("raw.githubusercontent.com", ignoreCase = true) &&
                encodedPath.lowercase().contains("/niakw/niakvio/")
            val loopbackEvidence = rawUrl.host.lowercase() in setOf("127.0.0.1", "localhost", "10.0.2.2") &&
                Regex("/candidate-[0-9a-f]{{32}}/").containsMatchIn(encodedPath.lowercase())
            val repoEvidence = rawGithubEvidence || loopbackEvidence
            if (!repoEvidence) return@addInterceptor chain.proceed(request)
            val endpoint = rawUrl.toString().substringBefore('?').substringBefore('#')
                .replace(Regex("\\\\s+"), "%20")
            val kind = when {{
                endpoint.endsWith("/manifest.json", ignoreCase = true) -> "manifest"
                loopbackEvidence -> "provider"
                endpoint.contains("/providers/", ignoreCase = true) -> "provider"
                else -> "repository"
            }}
            val method = request.method.uppercase()
            val requestHeaderNames = request.headers.names().map {{ it.lowercase() }}.sorted().joinToString(",")
            val startedAt = System.nanoTime()
            val requestMessage = "FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client={client} kind=$kind method=$method endpoint=$endpoint request_header_names=$requestHeaderNames"
            {emit.replace('message', 'requestMessage')}
            try {{
                val response = chain.proceed(request)
                val responseHeaderNames = response.headers.names().map {{ it.lowercase() }}.sorted().joinToString(",")
                val cacheSource = when {{
                    response.cacheResponse != null && response.networkResponse != null -> "conditional_cache"
                    response.cacheResponse != null -> "cache"
                    response.networkResponse != null -> "network"
                    else -> "unknown"
                }}
                val durationMs = ((System.nanoTime() - startedAt) / 1_000_000L).coerceAtLeast(0L)
                val responseMessage = "FIELD_NATIVE_REPOSITORY_HTTP_RESPONSE client={client} kind=$kind method=$method endpoint=$endpoint status=${{response.code}} duration_ms=$durationMs response_header_names=$responseHeaderNames source=$cacheSource"
                {emit.replace('message', 'responseMessage')}
                response
            }} catch (error: Throwable) {{
                val durationMs = ((System.nanoTime() - startedAt) / 1_000_000L).coerceAtLeast(0L)
                val errorClass = error::class.qualifiedName.orEmpty().replace(Regex("\\\\s+"), "_")
                val errorMessage = "FIELD_NATIVE_REPOSITORY_HTTP_ERROR client={client} kind=$kind method=$method endpoint=$endpoint duration_ms=$durationMs error_class=$errorClass"
                {emit.replace('message', 'errorMessage')}
                throw error
            }}
        }}
        '''


def instrument_tv(repo: Path) -> None:
    path = repo / "app/src/full/java/com/nuvio/tv/core/plugin/PluginManager.kt"
    text = path.read_text(encoding="utf-8")
    if "FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client=tv" in text:
        print(f"FIELD_NATIVE_REPOSITORY_HTTP_INSTRUMENTED client=tv path={path}")
        return
    anchor = """        .proxy(java.net.Proxy.NO_PROXY)\n        .dispatcher(okhttp3.Dispatcher(\n"""
    replacement = """        .proxy(java.net.Proxy.NO_PROXY)\n        """ + kotlin_interceptor("tv", "android") + """.dispatcher(okhttp3.Dispatcher(\n"""
    text = replace_once(text, anchor, replacement, "tv PluginManager OkHttp")
    path.write_text(text, encoding="utf-8")
    print(f"FIELD_NATIVE_REPOSITORY_HTTP_INSTRUMENTED client=tv path={path}")


def instrument_mobile(repo: Path) -> None:
    path = repo / "composeApp/src/androidMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.android.kt"
    text = path.read_text(encoding="utf-8")
    if "FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client=mobile" in text:
        print(f"FIELD_NATIVE_REPOSITORY_HTTP_INSTRUMENTED client=mobile path={path}")
        return
    anchor = """        .addInterceptor(SentryNetworkBreadcrumbInterceptor())\n        .proxy(Proxy.NO_PROXY)\n"""
    replacement = """        .addInterceptor(SentryNetworkBreadcrumbInterceptor())\n        """ + kotlin_interceptor("mobile", "android") + """.proxy(Proxy.NO_PROXY)\n"""
    text = replace_once(text, anchor, replacement, "mobile AddonHttpClient")
    path.write_text(text, encoding="utf-8")
    print(f"FIELD_NATIVE_REPOSITORY_HTTP_INSTRUMENTED client=mobile path={path}")


def instrument_desktop(repo: Path) -> None:
    path = repo / "composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt"
    text = path.read_text(encoding="utf-8")
    if "FIELD_NATIVE_REPOSITORY_HTTP_REQUEST client=desktop" in text:
        print(f"FIELD_NATIVE_REPOSITORY_HTTP_INSTRUMENTED client=desktop path={path}")
        return
    anchor = """    .followRedirects(true)\n    .followSslRedirects(true)\n    .build()\n"""
    replacement = """    .followRedirects(true)\n    .followSslRedirects(true)\n    """ + kotlin_interceptor("desktop", "stdout") + """.build()\n"""
    text = replace_once(text, anchor, replacement, "desktop AddonHttpClient")
    path.write_text(text, encoding="utf-8")
    print(f"FIELD_NATIVE_REPOSITORY_HTTP_INSTRUMENTED client=desktop path={path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=("tv", "mobile", "desktop"))
    parser.add_argument("repo")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    if args.client == "tv":
        instrument_tv(repo)
    elif args.client == "mobile":
        instrument_mobile(repo)
    else:
        instrument_desktop(repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
