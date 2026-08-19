#!/usr/bin/env python3
"""Route native-corpus provider execution through the official Nuvio repository layer.

The device labs previously executed staged JS directly through PluginRuntime. That is
useful runtime evidence but it cannot prove the human path where Nuvio downloads a
manifest, downloads/caches each provider and reconstructs its provider model first.

This augmenter keeps the existing generated test/readers but changes the primary
provider source to the official client repository/manager:
  * NuvioTV: PluginManager.addRepository -> ScraperInfo -> executeScraper
  * Mobile/Desktop: PluginRepository.addRepository -> PluginScraper -> executeScraper

Manifest-disabled providers are deliberately still executed individually. Platform-
blocked providers are not forced through a client that Nuvio itself rejects; they are
recorded as explicit platform skips. Repository/provider load failures remain evidence,
not silent omissions.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_TYPES = {"movie", "tv", "anime"}


def kotlin_string(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    seen: set[str] = set()
    for raw in data.get("scrapers", []):
        if not isinstance(raw, dict):
            continue
        provider_id = str(raw.get("id") or "").strip()
        if not provider_id:
            raise SystemExit(f"{path}: provider without id")
        key = provider_id.casefold()
        if key in seen:
            raise SystemExit(f"{path}: duplicate provider id {provider_id}")
        seen.add(key)
        types = [str(v or "").strip().lower() for v in raw.get("supportedTypes", [])]
        if not types or any(v not in CANONICAL_TYPES for v in types):
            raise SystemExit(f"{path}: provider {provider_id} has invalid supportedTypes={types}")
        rows.append(raw)
    if not rows:
        raise SystemExit(f"{path}: no providers")
    return rows


def platform_tags(client: str, host_platform: str) -> set[str]:
    if client == "mobile":
        return {"android"}
    if client == "desktop":
        host = host_platform.lower().strip()
        if host not in {"macos", "windows"}:
            raise SystemExit(f"desktop native provider loading requires macos/windows, got {host_platform!r}")
        return {"desktop", "jvm", host}
    # NuvioTV's accepted PluginManager currently retains every manifest JS scraper;
    # it parses platform metadata but downloadJsScrapers does not filter it.
    return set()


def excluded_ids(rows: list[dict], client: str, host_platform: str) -> list[str]:
    tags = platform_tags(client, host_platform)
    if not tags:
        return []
    excluded: list[str] = []
    for row in rows:
        supported = {str(v).lower() for v in (row.get("supportedPlatforms") or [])}
        disabled = {str(v).lower() for v in (row.get("disabledPlatforms") or [])}
        if (supported and not (tags & supported)) or (tags & disabled):
            excluded.append(str(row["id"]).casefold())
    return excluded


def insert_imports(text: str, client: str) -> str:
    if client == "tv":
        anchor = "import androidx.test.platform.app.InstrumentationRegistry\n"
        addition = (
            anchor
            + "import dagger.hilt.EntryPoint\n"
            + "import dagger.hilt.InstallIn\n"
            + "import dagger.hilt.android.EntryPointAccessors\n"
            + "import dagger.hilt.components.SingletonComponent\n"
            + "import kotlinx.coroutines.flow.first\n"
        )
    elif client == "desktop":
        anchor = "import java.io.File\n"
        addition = anchor
    else:
        anchor = "import androidx.test.platform.app.InstrumentationRegistry\n"
        addition = anchor
    if text.count(anchor) != 1:
        raise SystemExit(f"provider-loading import anchor client={client} count={text.count(anchor)}")
    return text.replace(anchor, addition, 1)


def platform_set_literal(ids: list[str]) -> str:
    if not ids:
        return "emptySet()"
    return "setOf(" + ", ".join(kotlin_string(v) for v in ids) + ")"


def tv_helpers(manifest_url: str, blocked: list[str]) -> str:
    return f'''
    private val repositoryManifestUrl = {kotlin_string(manifest_url)}
    private val platformExcludedProviders = {platform_set_literal(blocked)}

    @EntryPoint
    @InstallIn(SingletonComponent::class)
    interface NiakvioPluginManagerEntryPoint {{
        fun pluginManager(): PluginManager
    }}

    private suspend fun loadProvidersThroughNuvio(): Pair<PluginManager, Map<String, com.nuvio.tv.domain.model.ScraperInfo>> {{
        val app = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext
        val manager = EntryPointAccessors.fromApplication(
            app,
            NiakvioPluginManagerEntryPoint::class.java,
        ).pluginManager()
        emit("FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=tv fixture=$fixtureSlugForLoad manifest_host=${{hostOnly(repositoryManifestUrl)}} expected=${{providers.size}}")
        val installed = manager.addRepository(repositoryManifestUrl)
        if (installed.isFailure) {{
            emit("FIELD_NATIVE_REPOSITORY_LOAD_ERROR client=tv fixture=$fixtureSlugForLoad error64=${{b64(installed.exceptionOrNull()?.message ?: \"repository install failed\")}}")
            throw installed.exceptionOrNull() ?: IllegalStateException("NuvioTV repository install failed")
        }}
        val repo = installed.getOrThrow()
        val loaded = manager.scrapers.first().filter {{ it.repositoryId == repo.id }}
        val byId = loaded.associateBy {{ it.id.substringAfterLast(':').lowercase() }}
        val expectedLoaded = providers.count {{ it.id.lowercase() !in platformExcludedProviders }}
        emit("FIELD_NATIVE_REPOSITORY_LOAD_RESULT client=tv fixture=$fixtureSlugForLoad repository64=${{b64(repo.name)}} expected=$expectedLoaded loaded=${{loaded.size}}")
        providers.forEach {{ provider ->
            val key = provider.id.lowercase()
            if (key in platformExcludedProviders) {{
                emit("FIELD_NATIVE_PROVIDER_LOAD_SKIPPED client=tv fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} reason=disabled_platform")
            }} else {{
                val scraper = byId[key]
                if (scraper == null) {{
                    emit("FIELD_NATIVE_PROVIDER_LOAD_ERROR client=tv fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} reason=missing_after_repository_install")
                }} else {{
                    val loadedTypes = scraper.supportedTypes.map {{ it.lowercase() }}.distinct().sorted()
                    val declaredTypes = declaredTypesByProvider[key].orEmpty().sorted()
                    val metadataMatch = scraper.manifestEnabled == provider.enabled && loadedTypes == declaredTypes
                    emit("FIELD_NATIVE_PROVIDER_LOAD_RESULT client=tv fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} manifest_enabled=${{scraper.manifestEnabled}} runtime_enabled=${{scraper.enabled}} supported_types64=${{b64(loadedTypes.joinToString(\",\"))}} metadata_match=$metadataMatch")
                    if (!metadataMatch) {{
                        emit("FIELD_NATIVE_PROVIDER_LOAD_ERROR client=tv fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} reason=metadata_mismatch")
                    }}
                }}
            }}
        }}
        return manager to byId
    }}
'''


def repository_helpers(client: str, manifest_url: str, blocked: list[str]) -> str:
    return f'''
    private val repositoryManifestUrl = {kotlin_string(manifest_url)}
    private val platformExcludedProviders = {platform_set_literal(blocked)}

    private suspend fun loadProvidersThroughNuvio(): Map<String, PluginScraper> {{
        PluginRepository.clearLocalState()
        emit("FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client={client} fixture=$fixtureSlugForLoad manifest_host=${{hostOnly(repositoryManifestUrl)}} expected=${{providers.size}}")
        val installed = PluginRepository.addRepository(repositoryManifestUrl)
        val repositoryUrl = when (installed) {{
            is AddPluginRepositoryResult.Success -> installed.repository.manifestUrl
            is AddPluginRepositoryResult.Error -> {{
                emit("FIELD_NATIVE_REPOSITORY_LOAD_ERROR client={client} fixture=$fixtureSlugForLoad error64=${{b64(installed.message)}}")
                throw IllegalStateException(installed.message)
            }}
        }}
        val loaded = PluginRepository.uiState.value.scrapers.filter {{ it.repositoryUrl == repositoryUrl }}
        val byId = loaded.associateBy {{ it.id.substringAfterLast(':').lowercase() }}
        val expectedLoaded = providers.count {{ it.id.lowercase() !in platformExcludedProviders }}
        emit("FIELD_NATIVE_REPOSITORY_LOAD_RESULT client={client} fixture=$fixtureSlugForLoad expected=$expectedLoaded loaded=${{loaded.size}}")
        providers.forEach {{ provider ->
            val key = provider.id.lowercase()
            if (key in platformExcludedProviders) {{
                emit("FIELD_NATIVE_PROVIDER_LOAD_SKIPPED client={client} fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} reason=disabled_platform")
            }} else {{
                val scraper = byId[key]
                if (scraper == null) {{
                    emit("FIELD_NATIVE_PROVIDER_LOAD_ERROR client={client} fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} reason=missing_after_repository_install")
                }} else {{
                    val loadedTypes = scraper.supportedTypes.map {{ it.lowercase() }}.distinct().sorted()
                    val declaredTypes = declaredTypesByProvider[key].orEmpty().sorted()
                    val metadataMatch = scraper.manifestEnabled == provider.enabled && loadedTypes == declaredTypes && scraper.code.isNotBlank()
                    emit("FIELD_NATIVE_PROVIDER_LOAD_RESULT client={client} fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} manifest_enabled=${{scraper.manifestEnabled}} runtime_enabled=${{scraper.enabled}} code_bytes=${{scraper.code.toByteArray(Charsets.UTF_8).size}} supported_types64=${{b64(loadedTypes.joinToString(\",\"))}} metadata_match=$metadataMatch")
                    if (!metadataMatch) {{
                        emit("FIELD_NATIVE_PROVIDER_LOAD_ERROR client={client} fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} reason=metadata_or_code_mismatch")
                    }}
                }}
            }}
        }}
        return byId
    }}
'''


def augment(source: Path, client: str, manifest: Path, manifest_url: str, host_platform: str) -> None:
    parsed = urlparse(manifest_url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise SystemExit("native provider loading manifest URL must be pinned raw.githubusercontent.com HTTPS")
    rows = load_manifest(manifest)
    blocked = excluded_ids(rows, client, host_platform)
    text = source.read_text(encoding="utf-8")
    if "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN" in text:
        print(f"FIELD_NATIVE_PROVIDER_LOADING already=true client={client} source={source}")
        return
    text = insert_imports(text, client)

    # Request-contract augmentation has already introduced declaredTypesByProvider.
    if "private val declaredTypesByProvider" not in text:
        raise SystemExit("provider loading requires request-contract augmentation first")

    # The helper needs the fixture slug outside the @Test local scope so load markers
    # remain attributable even if installation fails before corpus begin.
    slug_match = re.search(r"val fixtureSlug = (\"(?:[^\"\\]|\\.)*\")", text)
    if not slug_match:
        raise SystemExit("provider-loading fixture slug anchor missing")
    fixture_literal = slug_match.group(1)

    provider_list = re.search(r"(    private val providers = listOf\(\n.*?\n    \)\n)", text, flags=re.S)
    if not provider_list:
        raise SystemExit("provider-loading provider list anchor missing")
    helper = f"\n    private val fixtureSlugForLoad = {fixture_literal}\n"
    helper += tv_helpers(manifest_url, blocked) if client == "tv" else repository_helpers(client, manifest_url, blocked)
    text = text[: provider_list.end()] + helper + text[provider_list.end() :]

    # Install through the official client after the Android UI has actually launched;
    # Desktop has no launchClientUi helper, so installation precedes corpus begin there.
    begin_anchor = f'        emit("FIELD_NATIVE_CORPUS_BEGIN client={client} fixture=$fixtureSlug'
    begin_at = text.find(begin_anchor)
    if begin_at < 0:
        raise SystemExit("provider-loading corpus begin anchor missing")
    line_start = text.rfind("\n", 0, begin_at) + 1
    prefix = text[line_start:begin_at]
    if client == "tv":
        load_line = "        val (officialPluginManager, loadedProviders) = loadProvidersThroughNuvio()\n"
    else:
        load_line = "        val loadedProviders = loadProvidersThroughNuvio()\n"
    text = text[:line_start] + load_line + text[line_start:]

    # Before route selection, respect the platform decision made by Nuvio itself and
    # refuse to fall back silently to the staged JS if repository loading failed.
    loop_anchor = "        for (provider in providers) {\n            val requestTypes = requestTypesFor(provider.id, mediaType)"
    loop_replacement = f'''        for (provider in providers) {{
            val providerKey = provider.id.lowercase()
            if (providerKey in platformExcludedProviders) {{
                emit("FIELD_NATIVE_PROVIDER_SKIPPED client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} requested_type=$mediaType declared_types64=${{b64(declaredTypesByProvider[providerKey].orEmpty().sorted().joinToString(\",\"))}} reason=disabled_platform")
                continue
            }}
            val loadedScraper = loadedProviders[providerKey]
            if (loadedScraper == null) {{
                emit("FIELD_NATIVE_PROVIDER_SKIPPED client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} requested_type=$mediaType declared_types64=${{b64(declaredTypesByProvider[providerKey].orEmpty().sorted().joinToString(\",\"))}} reason=load_failure")
                continue
            }}
            val requestTypes = requestTypesFor(provider.id, mediaType)'''
    if text.count(loop_anchor) != 1:
        raise SystemExit(f"provider-loading route loop anchor count={text.count(loop_anchor)}")
    text = text.replace(loop_anchor, loop_replacement, 1)

    if client == "tv":
        pattern = re.compile(
            r"val rows = runtime\.executePlugin\(\s*"
            r"code = code\(provider\.asset\),\s*"
            r"tmdbId = tmdbId,\s*"
            r"mediaType = requestMediaType,\s*"
            r"season = season,\s*"
            r"episode = episode,\s*"
            r"scraperId = provider\.id,\s*"
            r"\)",
            flags=re.S,
        )
        replacement = "val rows = officialPluginManager.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode)"
    else:
        runtime_name = "PluginRuntime" if client in {"mobile", "desktop"} else "PluginRuntime"
        if client == "desktop":
            code_expr = r"File\(root, provider\.asset\)\.readText\(\)"
        else:
            code_expr = r"code\(provider\.asset\)"
        pattern = re.compile(
            rf"val rows = {runtime_name}\.executePlugin\(\s*"
            rf"code = {code_expr},\s*"
            r"tmdbId = tmdbId,\s*"
            r"mediaType = requestMediaType,\s*"
            r"season = season,\s*"
            r"episode = episode,\s*"
            r"scraperId = provider\.id,\s*"
            r"\)",
            flags=re.S,
        )
        replacement = "val rows = PluginRepository.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode).getOrThrow()"
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"provider-loading official execution rewrite client={client} count={count}")

    source.write_text(text, encoding="utf-8")
    print(
        f"FIELD_NATIVE_PROVIDER_LOADING client={client} providers={len(rows)} platform_blocked={len(blocked)} "
        f"manifest={manifest} manifest_host={parsed.hostname} source={source}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=("tv", "mobile", "desktop"))
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-url", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--platform", default="", help="desktop host: macos or windows")
    args = parser.parse_args()
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = (ROOT / manifest).resolve()
    augment(Path(args.source).resolve(), args.client, manifest, args.manifest_url, args.platform)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
