#!/usr/bin/env python3
"""Route native-corpus execution through the official Nuvio repository layer.

The generated corpus still owns fixture traversal and reader evidence, but provider
code must first travel through the same repository/manager path used by the client:

* NuvioTV: PluginManager repository state -> ScraperInfo -> executeScraper
* Mobile/Desktop: PluginRepository profile state -> PluginScraper -> executeScraper

Manifest-disabled providers are still loaded and executed individually. Providers
that the official client rejects for the current platform are recorded as platform
skips. The request-contract postprocessor runs first and owns the declared media route;
this postprocessor preserves that route unchanged.

Normal evidence accepts only an exact 40-hex raw.githubusercontent.com revision.
Repair sandboxes may explicitly opt into a loopback-only HTTP repository so the
real client can install a locally generated candidate without publishing it first.

The lab deliberately preserves the Nuvio app/profile state between fixtures. It
reuses an already-installed repository and provider-code cache whenever the exact
manifest URL is already present, instead of clearing PluginRepository state. This
keeps repeated launches fast and mirrors a real user session more closely.

Repository installation failures are terminal observations, not harness crashes:
every selected provider receives a structured load failure and the corpus continues
to its normal end marker so the Brain can classify Core/manifest/repository faults
without ever turning them into provider-JS mutations.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_TYPES = {"movie", "tv", "anime"}
TRANSPORT_TYPES = CANONICAL_TYPES | {"series"}
LOCAL_LAB_HOSTS = {"127.0.0.1", "localhost", "10.0.2.2"}


def kotlin_string(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def validate_manifest_url(manifest_url: str, allow_local_lab_url: bool):
    parsed = urlparse(manifest_url)
    if parsed.username or parsed.password or parsed.fragment:
        raise SystemExit("native provider loading manifest URL must not contain credentials or fragments")
    if parsed.scheme == "https" and parsed.hostname == "raw.githubusercontent.com":
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 4 or re.fullmatch(r"[0-9a-fA-F]{40}", parts[2]) is None:
            raise SystemExit("raw GitHub native provider manifest must be pinned to an exact 40-hex commit SHA")
        return parsed, "pinned_github"
    if allow_local_lab_url and parsed.scheme == "http" and parsed.hostname in LOCAL_LAB_HOSTS:
        if parsed.port is None or parsed.port < 1 or parsed.port > 65535:
            raise SystemExit("local native provider lab manifest URL requires an explicit TCP port")
        return parsed, "local_candidate"
    raise SystemExit(
        "native provider loading manifest URL must be pinned raw.githubusercontent.com HTTPS; "
        "loopback HTTP is allowed only with --allow-local-lab-url"
    )


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
        supported = [str(value or "").strip().lower() for value in raw.get("supportedTypes", [])]
        canonical_raw = raw.get("canonicalSupportedTypes")
        canonical = (
            [str(value or "").strip().lower() for value in canonical_raw]
            if isinstance(canonical_raw, list) and canonical_raw
            else [value for value in supported if value in CANONICAL_TYPES]
        )
        if not supported or any(value not in TRANSPORT_TYPES for value in supported):
            raise SystemExit(f"{path}: provider {provider_id} has invalid supportedTypes={supported}")
        if not canonical or any(value not in CANONICAL_TYPES for value in canonical):
            raise SystemExit(f"{path}: provider {provider_id} has invalid canonicalSupportedTypes={canonical}")
        if "series" in canonical:
            raise SystemExit(f"{path}: provider {provider_id} leaked series into canonicalSupportedTypes")
        rows.append(raw)
    if not rows:
        raise SystemExit(f"{path}: no providers")
    return rows


def platform_tags(client: str, host_platform: str) -> set[str]:
    if client == "mobile":
        return {"android"}
    if client == "desktop":
        host = host_platform.strip().lower()
        if host not in {"macos", "windows"}:
            raise SystemExit(f"desktop native provider loading requires macos/windows, got {host_platform!r}")
        return {"desktop", "jvm", host}
    # Accepted NuvioTV parses platform metadata but its JS download path currently
    # does not filter on it. Reproduce the client instead of inventing a TV tag.
    return set()


def excluded_ids(rows: list[dict], client: str, host_platform: str) -> list[str]:
    tags = platform_tags(client, host_platform)
    if not tags:
        return []
    excluded: list[str] = []
    for row in rows:
        supported = {str(value).lower() for value in (row.get("supportedPlatforms") or [])}
        disabled = {str(value).lower() for value in (row.get("disabledPlatforms") or [])}
        if (supported and not (tags & supported)) or (tags & disabled):
            excluded.append(str(row["id"]).casefold())
    return excluded


def insert_imports(text: str, client: str) -> str:
    if client != "tv":
        return text
    anchor = "import androidx.test.platform.app.InstrumentationRegistry\n"
    shared_imports = (
        "import dagger.hilt.EntryPoint\n",
        "import dagger.hilt.InstallIn\n",
        "import dagger.hilt.android.EntryPointAccessors\n",
        "import dagger.hilt.components.SingletonComponent\n",
        "import kotlinx.coroutines.flow.first\n",
    )
    missing = [line for line in shared_imports if line not in text]
    if not missing:
        return text
    if text.count(anchor) != 1:
        raise SystemExit(f"provider-loading import anchor client=tv count={text.count(anchor)}")
    return text.replace(anchor, anchor + "".join(missing), 1)


def platform_set_literal(ids: list[str]) -> str:
    # Generated Kotlin is compiled by several different client/compiler stacks.
    # Empty generic constructors therefore carry their type explicitly instead of
    # relying on local inference (a real TV route run has failed here before).
    if not ids:
        return "emptySet<String>()"
    return "setOf<String>(" + ", ".join(kotlin_string(value) for value in ids) + ")"


def tv_helpers(manifest_url: str, blocked: list[str]) -> str:
    return f'''
    private val repositoryManifestUrl = {kotlin_string(manifest_url)}
    private val platformExcludedProviders: Set<String> = {platform_set_literal(blocked)}

    @EntryPoint
    @InstallIn(SingletonComponent::class)
    interface NiakvioPluginManagerEntryPoint {{
        fun pluginManager(): PluginManager
        fun pluginRuntime(): com.nuvio.tv.core.plugin.PluginRuntime
        fun pluginDataStore(): com.nuvio.tv.data.local.PluginDataStore
    }}

    // Test-owned synthetic runtime control. It never downloads/installs a
    // provider, supplies no real media and does not modify Nuvio production.
    // The official PluginRuntime must preserve both immediate and awaited
    // JS results before we attribute a provider's count=0 to its own code.
    private suspend fun probeOfficialTvPromiseBridge(
        runtime: com.nuvio.tv.core.plugin.PluginRuntime,
    ) {{
        val immediateCode = "module.exports.getStreams = function() {{ return [{{title:'control',url:'https://example.invalid/runtime-control.mp4'}}]; }};"
        val awaitedCode = "module.exports.getStreams = async function() {{ await Promise.resolve(1); return [{{title:'control',url:'https://example.invalid/runtime-control.mp4'}}]; }};"
        suspend fun runControl(code: String, label: String): Int {{
            return try {{
                runtime.executePlugin(
                    code = code,
                    tmdbId = "1",
                    mediaType = "movie",
                    season = null,
                    episode = null,
                    scraperId = "niakvio-test-only-$label",
                    scraperSettings = emptyMap(),
                ).size
            }} catch (error: Throwable) {{
                emit("FIELD_NATIVE_TV_PROMISE_CONTROL_ERROR client=tv kind=$label class64=${{b64(error.javaClass.simpleName)}}")
                -1
            }}
        }}
        val syncCount = runControl(immediateCode, "immediate")
        val asyncCount = runControl(awaitedCode, "awaited")
        emit("FIELD_NATIVE_TV_PROMISE_CONTROL client=tv sync_count=$syncCount async_count=$asyncCount expected=1 fixture=$fixtureSlugForLoad test_only=true provider_media=false proof_authority=false")
    }}

    private suspend fun loadProvidersThroughNuvio(): Pair<PluginManager, Map<String, com.nuvio.tv.domain.model.ScraperInfo>> {{
        val app = InstrumentationRegistry.getInstrumentation().targetContext.applicationContext
        val entryPoint = EntryPointAccessors.fromApplication(
            app,
            NiakvioPluginManagerEntryPoint::class.java,
        )
        val manager = entryPoint.pluginManager()
        probeOfficialTvPromiseBridge(entryPoint.pluginRuntime())
        emit("FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=tv fixture=$fixtureSlugForLoad manifest_host=${{hostOnly(repositoryManifestUrl)}} expected=${{providers.size}}")
        val canonicalTarget = repositoryManifestUrl.substringBefore("?").trimEnd('/')
        val existing = manager.repositories.first().firstOrNull {{ repo ->
            repo.url.substringBefore("?").trimEnd('/').equals(canonicalTarget, ignoreCase = true)
        }}
        val repo = if (existing != null) {{
            emit("FIELD_NATIVE_REPOSITORY_CACHE_HIT client=tv fixture=$fixtureSlugForLoad repository64=${{b64(existing.name)}}")
            existing
        }} else {{
            val installed = manager.addRepository(repositoryManifestUrl)
            if (installed.isFailure) {{
                val message = installed.exceptionOrNull()?.message ?: "repository install failed"
                emit("FIELD_NATIVE_REPOSITORY_LOAD_ERROR client=tv fixture=$fixtureSlugForLoad reason=install_failed error64=${{b64(message)}}")
                providers.forEach {{ provider ->
                    val key = provider.id.lowercase()
                    if (key in platformExcludedProviders) {{
                        emit("FIELD_NATIVE_PROVIDER_LOAD_SKIPPED client=tv fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} reason=disabled_platform")
                    }} else {{
                        emit("FIELD_NATIVE_PROVIDER_LOAD_ERROR client=tv fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} reason=repository_install_failed")
                    }}
                }}
                return manager to emptyMap<String, com.nuvio.tv.domain.model.ScraperInfo>()
            }}
            installed.getOrThrow()
        }}
        val selectedKeys = providers.map {{ it.id.lowercase() }}.toSet()
        val expectedLoaded = providers.count {{ it.id.lowercase() !in platformExcludedProviders }}
        var loaded = manager.scrapers.first().filter {{ it.repositoryId == repo.id }}
        var byId = loaded.associateBy {{ it.id.substringAfterLast(':').lowercase() }}
        var selectedLoaded = byId.keys.count {{ it in selectedKeys }}
        var waitedMs = 0L
        while (selectedLoaded < expectedLoaded && waitedMs < 30_000L) {{
            kotlinx.coroutines.delay(250L)
            waitedMs += 250L
            loaded = manager.scrapers.first().filter {{ it.repositoryId == repo.id }}
            byId = loaded.associateBy {{ it.id.substringAfterLast(':').lowercase() }}
            selectedLoaded = byId.keys.count {{ it in selectedKeys }}
        }}
        if (waitedMs > 0L) {{
            emit("FIELD_NATIVE_REPOSITORY_READY_WAIT client=tv fixture=$fixtureSlugForLoad waited_ms=$waitedMs expected=$expectedLoaded loaded=$selectedLoaded")
        }}
        emit("FIELD_NATIVE_REPOSITORY_LOAD_RESULT client=tv fixture=$fixtureSlugForLoad repository64=${{b64(repo.name)}} expected=$expectedLoaded loaded=$selectedLoaded")
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
                    val declaredTypes = transportTypesByProvider[key].orEmpty().sorted()
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
    desktop_before = '            captureDesktopPhase("repository-http-request", fixtureSlugForLoad)\n' if client == "desktop" else ""
    desktop_after = '                    captureDesktopPhase("repository-http-response", fixtureSlugForLoad)\n' if client == "desktop" else ""
    return f'''
    private val repositoryManifestUrl = {kotlin_string(manifest_url)}
    private val platformExcludedProviders: Set<String> = {platform_set_literal(blocked)}

    private suspend fun loadProvidersThroughNuvio(): Map<String, PluginScraper> {{
        // Preserve Nuvio's active profile/settings and previously downloaded plugin
        // cache. Reusing the exact repository makes subsequent fixture launches much
        // faster and mirrors a real user's persistent installation.
        PluginRepository.initialize()
        emit("FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client={client} fixture=$fixtureSlugForLoad manifest_host=${{hostOnly(repositoryManifestUrl)}} expected=${{providers.size}}")
        val existing = PluginRepository.uiState.value.repositories.firstOrNull {{ repo ->
            repo.manifestUrl == repositoryManifestUrl
        }}
        val repositoryUrl = if (existing != null) {{
            emit("FIELD_NATIVE_REPOSITORY_CACHE_HIT client={client} fixture=$fixtureSlugForLoad repository64=${{b64(existing.name)}}")
            existing.manifestUrl
        }} else {{
{desktop_before}            when (val installed = PluginRepository.addRepository(repositoryManifestUrl)) {{
                is AddPluginRepositoryResult.Success -> {{
{desktop_after}                    installed.repository.manifestUrl
                }}
                is AddPluginRepositoryResult.Error -> {{
{desktop_after}                    emit("FIELD_NATIVE_REPOSITORY_LOAD_ERROR client={client} fixture=$fixtureSlugForLoad reason=install_failed error64=${{b64(installed.message)}}")
                    providers.forEach {{ provider ->
                        val key = provider.id.lowercase()
                        if (key in platformExcludedProviders) {{
                            emit("FIELD_NATIVE_PROVIDER_LOAD_SKIPPED client={client} fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} reason=disabled_platform")
                        }} else {{
                            emit("FIELD_NATIVE_PROVIDER_LOAD_ERROR client={client} fixture=$fixtureSlugForLoad provider64=${{b64(provider.id)}} reason=repository_install_failed")
                        }}
                    }}
                    return emptyMap<String, PluginScraper>()
                }}
            }}
        }}
        val selectedKeys = providers.map {{ it.id.lowercase() }}.toSet()
        val expectedLoaded = providers.count {{ it.id.lowercase() !in platformExcludedProviders }}
        var loaded = PluginRepository.uiState.value.scrapers.filter {{ it.repositoryUrl == repositoryUrl }}
        var byId = loaded.associateBy {{ it.id.substringAfterLast(':').lowercase() }}
        var selectedLoaded = byId.keys.count {{ it in selectedKeys }}
        var waitedMs = 0L
        while (selectedLoaded < expectedLoaded && waitedMs < 30_000L) {{
            kotlinx.coroutines.delay(250L)
            waitedMs += 250L
            loaded = PluginRepository.uiState.value.scrapers.filter {{ it.repositoryUrl == repositoryUrl }}
            byId = loaded.associateBy {{ it.id.substringAfterLast(':').lowercase() }}
            selectedLoaded = byId.keys.count {{ it in selectedKeys }}
        }}
        if (waitedMs > 0L) {{
            emit("FIELD_NATIVE_REPOSITORY_READY_WAIT client={client} fixture=$fixtureSlugForLoad waited_ms=$waitedMs expected=$expectedLoaded loaded=$selectedLoaded")
        }}
        emit("FIELD_NATIVE_REPOSITORY_LOAD_RESULT client={client} fixture=$fixtureSlugForLoad expected=$expectedLoaded loaded=$selectedLoaded")
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
                    val declaredTypes = transportTypesByProvider[key].orEmpty().sorted()
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


def replace_official_execution(text: str, client: str, candidate_execution_sha256: str = "") -> str:
    # Replace only the provider invocation itself. The native corpus may wrap that
    # invocation in withTimeout(...); keeping the outer wrapper preserves the
    # per-provider runtime budget while still routing execution through the
    # official Nuvio repository layer.
    if client == "tv":
        pattern = re.compile(
            r"(?:runtime|PluginRuntime\(\))\.executePlugin\(\s*"
            r"code = code\(provider\.asset\),\s*"
            r"tmdbId = tmdbId,\s*"
            r"mediaType = requestMediaType,\s*"
            r"season = season,\s*"
            r"episode = episode,\s*"
            r"scraperId = provider\.id,\s*"
            r"\)",
            flags=re.S,
        )
        # The official app never invokes a scraper merely because its bytes
        # were installed. enabledScrapers combines the user's persisted enabled
        # flag and the global plugin switch; supportsType gates the request.
        # A direct executeScraper() test bypassed all three and could report
        # a TV success while the real stream list never selected that scraper.
        replacement = (
            "run {\n"
            "    val appPluginsEnabled = officialPluginManager.pluginsEnabled.first()\n"
            "    val appSupportedType = loadedScraper.supportsType(requestMediaType)\n"
            "    val appEligible = officialPluginManager.enabledScrapers.first().any { "
            "it.id == loadedScraper.id && it.supportsType(requestMediaType) }\n"
            "    if (!appEligible) {\n"
            "        val reason = when {\n"
            "            !appPluginsEnabled -> \"plugins_globally_disabled\"\n"
            "            !loadedScraper.enabled -> \"scraper_disabled_locally\"\n"
            "            !appSupportedType -> \"unsupported_media_type\"\n"
            "            else -> \"not_selected_by_app\"\n"
            "        }\n"
            "        emit(\"FIELD_NATIVE_PROVIDER_APP_SELECTION client=tv fixture=$fixtureSlug "
            "provider64=${b64(provider.id)} eligible=false plugins_enabled=$appPluginsEnabled "
            "runtime_enabled=${loadedScraper.enabled} "
            "manifest_enabled=${loadedScraper.manifestEnabled} supported_type=$appSupportedType "
            "request_type=$requestMediaType reason=$reason\")\n"
            "        emptyList<com.nuvio.tv.domain.model.LocalScraperResult>()\n"
            "    } else {\n"
            "        emit(\"FIELD_NATIVE_PROVIDER_APP_SELECTION client=tv fixture=$fixtureSlug "
            "provider64=${b64(provider.id)} eligible=true plugins_enabled=$appPluginsEnabled "
            "runtime_enabled=${loadedScraper.enabled} supported_type=$appSupportedType "
            "request_type=$requestMediaType\")\n"
            "        officialPluginManager.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode)\n"
            "    }\n"
            "}"
        )
        if candidate_execution_sha256:
            # Do not claim the published PluginManager invocation executed a
            # locally rematerialized candidate. It necessarily uses repository
            # code. This opt-in diagnostic branch preserves the real manager's
            # enable/type selection but exercises exact staged bytes via the
            # SAME official NuvioTV PluginRuntime. It is not playback authority.
            baseline_call = "officialPluginManager.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode)"
            candidate_call = """run {
                val candidateCode = code(provider.asset)
                val candidateSha = java.security.MessageDigest.getInstance("SHA-256")
                    .digest(candidateCode.toByteArray(Charsets.UTF_8))
                    .joinToString("") { "%02x".format(it.toInt() and 0xff) }
                val candidateExpectedSha = EXPECTED_SHA
                if (candidateSha != candidateExpectedSha) {
                    emit("FIELD_NATIVE_CANDIDATE_BYTE_MISMATCH client=tv provider64=${b64(provider.id)} expected=$candidateExpectedSha actual=$candidateSha")
                    throw IllegalStateException("candidate asset byte mismatch")
                }
                // Keep the official repository/manager *execution* path.
                // This is a test-only replacement of installed scraper code,
                // after the normal manifest, enable and supported-type checks.
                // PluginManager will load the candidate via PluginDataStore and
                // keep its genuine settings, media-type mapping and timeouts.
                val candidateStore = EntryPointAccessors.fromApplication(
                    InstrumentationRegistry.getInstrumentation().targetContext.applicationContext,
                    NiakvioPluginManagerEntryPoint::class.java,
                ).pluginDataStore()
                val previousCode = candidateStore.getScraperCode(loadedScraper.id)
                try {
                    candidateStore.saveScraperCode(loadedScraper.id, candidateCode)
                    val installedCode = candidateStore.getScraperCode(loadedScraper.id) ?: ""
                    val installedSha = java.security.MessageDigest.getInstance("SHA-256")
                        .digest(installedCode.toByteArray(Charsets.UTF_8))
                        .joinToString("") { "%02x".format(it.toInt() and 0xff) }
                    if (installedSha != candidateExpectedSha) {
                        emit("FIELD_NATIVE_CANDIDATE_BYTE_MISMATCH client=tv provider64=${b64(provider.id)} stage=installed expected=$candidateExpectedSha actual=$installedSha")
                        throw IllegalStateException("candidate installed code mismatch")
                    }
                    emit("FIELD_NATIVE_CANDIDATE_RUNTIME_BYTE_CHECK client=tv provider64=${b64(provider.id)} sha256=$installedSha matched=true runtime=official_plugin_manager production_playback_authority=false")
                    val candidateRows = officialPluginManager.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode)
                    val afterCode = candidateStore.getScraperCode(loadedScraper.id) ?: ""
                    val afterSha = java.security.MessageDigest.getInstance("SHA-256")
                        .digest(afterCode.toByteArray(Charsets.UTF_8))
                        .joinToString("") { "%02x".format(it.toInt() and 0xff) }
                    if (afterSha != candidateExpectedSha) {
                        emit("FIELD_NATIVE_CANDIDATE_BYTE_MISMATCH client=tv provider64=${b64(provider.id)} stage=after_execute expected=$candidateExpectedSha actual=$afterSha")
                        throw IllegalStateException("candidate changed during official manager invocation")
                    }
                    emit("FIELD_NATIVE_CANDIDATE_RUNTIME_RESULT client=tv provider64=${b64(provider.id)} sha256=$afterSha count=${candidateRows.size} runtime=official_plugin_manager authority=diagnostic_only")
                    candidateRows
                } finally {
                    // Isolated diagnostic, not a persistent override of the
                    // official installed provider. Cancellation cannot retain
                    // candidate bytes for the next fixture/client attempt.
                    kotlinx.coroutines.withContext(kotlinx.coroutines.NonCancellable) {
                        if (previousCode == null) {
                            candidateStore.deleteScraperCode(loadedScraper.id)
                        } else {
                            candidateStore.saveScraperCode(loadedScraper.id, previousCode)
                        }
                    }
                    emit("FIELD_NATIVE_CANDIDATE_RESTORED client=tv provider64=${b64(provider.id)} exact_previous_state=true diagnostic_only=true")
                }
            }""".replace("EXPECTED_SHA", kotlin_string(candidate_execution_sha256))
            if replacement.count(baseline_call) != 1:
                raise SystemExit("native candidate oracle cannot locate unique official TV invocation")
            replacement = replacement.replace(baseline_call, candidate_call, 1)
    else:
        code_expr = r"File\(root, provider\.asset\)\.readText\(\)" if client == "desktop" else r"code\(provider\.asset\)"
        pattern = re.compile(
            r"PluginRuntime\.executePlugin\(\s*"
            rf"code = {code_expr},\s*"
            r"tmdbId = tmdbId,\s*"
            r"mediaType = requestMediaType,\s*"
            r"season = season,\s*"
            r"episode = episode,\s*"
            r"scraperId = provider\.id,\s*"
            r"\)",
            flags=re.S,
        )
        replacement = "PluginRepository.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode).getOrThrow()"
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"provider-loading official execution rewrite client={client} count={count}")
    return text


def augment(
    source: Path,
    client: str,
    manifest: Path,
    manifest_url: str,
    host_platform: str,
    allow_local_lab_url: bool = False,
    candidate_execution_sha256: str = "",
) -> None:
    parsed, manifest_transport = validate_manifest_url(manifest_url, allow_local_lab_url)
    if candidate_execution_sha256 and (client != "tv" or re.fullmatch(r"[a-f0-9]{64}", candidate_execution_sha256) is None):
        raise SystemExit("native local candidate oracle requires TV and exact SHA256")
    rows = load_manifest(manifest)
    blocked = excluded_ids(rows, client, host_platform)
    text = source.read_text(encoding="utf-8")
    if "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN" in text:
        print(f"FIELD_NATIVE_PROVIDER_LOADING already=true client={client} source={source}")
        return
    text = insert_imports(text, client)
    if "private val declaredTypesByProvider" not in text or "requestRoutesFor(" not in text:
        raise SystemExit("provider loading requires the current request-contract augmentation first")

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

    begin_anchor = f'        emit("FIELD_NATIVE_CORPUS_BEGIN client={client} fixture=$fixtureSlug'
    begin_at = text.find(begin_anchor)
    if begin_at < 0:
        raise SystemExit("provider-loading corpus begin anchor missing")
    line_start = text.rfind("\n", 0, begin_at) + 1
    load_line = (
        "        val (officialPluginManager, loadedProviders) = loadProvidersThroughNuvio()\n"
        if client == "tv"
        else "        val loadedProviders = loadProvidersThroughNuvio()\n"
    )
    text = text[:line_start] + load_line + text[line_start:]

    # The request-contract owns requestRoutes/requestMediaType/routeMode. Insert
    # official loading checks before route construction and preserve the single
    # declared route unchanged.
    # Anchor on route construction rather than the loop opener so other
    # evidence layers (for example sanitized addon-logo diagnostics) may be
    # inserted between the provider loop and request routing without breaking
    # the official Nuvio loading transform.
    loop_anchor = "            val requestRoutes = requestRoutesFor(provider.id, mediaType)"
    loop_replacement = f'''            val providerKey = provider.id.lowercase()
            if (providerKey in platformExcludedProviders) {{
                emit("FIELD_NATIVE_PROVIDER_SKIPPED client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} requested_type=$mediaType declared_types64=${{b64(declaredTypesByProvider[providerKey].orEmpty().sorted().joinToString(\",\"))}} reason=disabled_platform")
                continue
            }}
            val loadedScraper = loadedProviders[providerKey]
            if (loadedScraper == null) {{
                emit("FIELD_NATIVE_PROVIDER_SKIPPED client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} enabled=${{provider.enabled}} requested_type=$mediaType declared_types64=${{b64(declaredTypesByProvider[providerKey].orEmpty().sorted().joinToString(\",\"))}} reason=load_failure")
                continue
            }}
            val requestRoutes = requestRoutesFor(provider.id, mediaType)'''
    if text.count(loop_anchor) != 1:
        raise SystemExit(f"provider-loading route loop anchor count={text.count(loop_anchor)}")
    text = text.replace(loop_anchor, loop_replacement, 1)
    text = replace_official_execution(text, client, candidate_execution_sha256)

    source.write_text(text, encoding="utf-8")
    print(
        f"FIELD_NATIVE_PROVIDER_LOADING client={client} providers={len(rows)} platform_blocked={len(blocked)} "
        f"manifest={manifest} manifest_host={parsed.hostname} manifest_transport={manifest_transport} source={source}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=("tv", "mobile", "desktop"))
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-url", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--platform", default="", help="desktop host: macos or windows")
    parser.add_argument("--candidate-execution-sha256", default="", help="diagnostic TV runtime oracle for exact staged asset bytes, never playback proof")
    parser.add_argument(
        "--allow-local-lab-url",
        action="store_true",
        help="allow only localhost/127.0.0.1/10.0.2.2 HTTP repository URLs for an isolated repair lab",
    )
    args = parser.parse_args()
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = (ROOT / manifest).resolve()
    augment(
        Path(args.source).resolve(),
        args.client,
        manifest,
        args.manifest_url,
        args.platform,
        allow_local_lab_url=args.allow_local_lab_url,
        candidate_execution_sha256=args.candidate_execution_sha256,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())