/** Scoped implementation provenance for Brain Repair strategy Bloc.
 * Adding a new sibling profile must NEVER make exhausted older profiles
 * look fresh. Common code still participates in every fingerprint.
 */
export function profileRuntimeFingerprintMaterial(source, profile) {
  const original = String(source || "").replace(/\r\n/g, "\n");
  const wanted = String(profile || "").trim().toLowerCase();
  const keepsScriptedRequestComposition = new Set([
    "document_request_contract_mining_v2",
    "provider_session_bootstrap_replay_v1",
  ]).has(wanted);
  let raw = original;
  if (!keepsScriptedRequestComposition) {
    const lines = raw.split("\n");
    const compositionStart = lines.indexOf("    session_bootstrap_media_followup = (");
    const compositionEnd = lines.findIndex(
      (line, index) => index > compositionStart && line.startsWith("    session_bootstrap = "),
    );
    if (compositionStart >= 0 && compositionEnd > compositionStart) {
      lines.splice(
        compositionStart,
        compositionEnd - compositionStart,
        '    document_request_mining = new_strategy_id == "document_request_contract_mining_v1" or llm_experiment.get("documentRequestMining") is True',
      );
    }
    raw = lines.join("\n").replace(
      /^        "scripted_request_mining":\s*scripted_request_mining,\n/m,
      "",
    );
  }
  if (!keepsScriptedRequestComposition) {
    const lines = raw.split("\n");
    const resolverStart = lines.indexOf(
      "    resolver_records: list[dict[str, Any]] = []",
    );
    const resolverEnd = lines.findIndex(
      (line, index) => index > resolverStart
        && line === "    native_source = _strip_generated_adaptive_wrapper(source_text)",
    );
    if (resolverStart >= 0 && resolverEnd > resolverStart) {
      lines.splice(
        resolverStart,
        resolverEnd - resolverStart,
        "    if resolver_contract:",
        "        return _apply_inline_token_resolver_contract(parent_data, resolver_contract)",
      );
    }

    const adaptiveStart = lines.indexOf("    adaptive_record = {");
    const adaptiveEnd = lines.findIndex(
      (line, index) => index > adaptiveStart
        && line === "    return patched, [*resolver_records, adaptive_record]",
    );
    if (adaptiveStart >= 0 && adaptiveEnd > adaptiveStart) {
      lines.splice(
        adaptiveStart,
        adaptiveEnd - adaptiveStart + 1,
        "    return patched, [{",
        '        "type": "patch_profile",',
        '        "profile": profile_name,',
        '        "strategy": expected or "adaptive_runtime_recovery",',
        '        "engine": "adaptive_runtime_recovery",',
        '        "phase": "runtime",',
        '        "revision": 5,',
        '        "options": options,',
        "    }]",
      );
    }
    raw = lines.join("\n");
  }
  const registryStart = raw.indexOf("POST_EXHAUSTION_STRATEGY_PROFILES = {");
  const registryEnd = registryStart < 0 ? -1 : raw.indexOf("\n}", registryStart);
  const trimmed = registryStart >= 0 && registryEnd >= 0
    ? raw.slice(0, registryStart)
      + "POST_EXHAUSTION_STRATEGY_PROFILES = {<selector-registry>}"
      + raw.slice(registryEnd + 2)
    : raw;
  const lines = trimmed.split("\n");
  const guard = /^    (?:if|elif) new_strategy_id == "([a-z][a-z0-9_]*)":\s*$/;
  const first = lines.findIndex((line) => guard.test(line));
  if (first < 0) return `common:${trimmed}\nprofile:${wanted}\nbranch:missing`;
  let end = -1;
  for (let i = first + 1; i < lines.length; i += 1) {
    // A new 4-space statement after the selector chain returns to common
    // runtime code. Nested 8+-space statements belong to the selected branch.
    if (/^    [^\s#]/.test(lines[i]) && !guard.test(lines[i])) {
      end = i;
      break;
    }
  }
  if (end < 0) end = lines.length;
  const common = [...lines.slice(0, first), ...lines.slice(end)].join("\n");
  const selected = [];
  let within = false;
  let owns = false;
  for (let i = first; i < end; i += 1) {
    const line = lines[i];
    const match = guard.exec(line);
    if (match) {
      within = true;
      owns = match[1] === wanted;
      if (owns) selected.push('    if new_strategy_id == "<selected>":');
    } else if (within && owns) {
      selected.push(line);
    }
  }
  return `common:${common}\nprofile:${wanted}\nbranch:${selected.length ? selected.join("\n") : "missing"}`;
}


/**
 * Read the installed post-exhaustion strategy registry from the Python Brain
 * runtime. This is intentionally parser-only: the Python registry remains the
 * authority, while Node consumers derive their view instead of duplicating it.
 */
export function postExhaustionStrategyProfiles(source) {
  const raw = String(source || "").replace(/\r\n/g, "\n");
  const marker = "POST_EXHAUSTION_STRATEGY_PROFILES = {";
  const start = raw.indexOf(marker);
  const end = start < 0 ? -1 : raw.indexOf("\n}", start);
  if (start < 0 || end < 0) return new Set();
  const block = raw.slice(start + marker.length, end);
  const profiles = new Set();
  for (const match of block.matchAll(/^\s*"([a-z][a-z0-9_]*_v[0-9]+)",\s*$/gm)) {
    profiles.add(match[1]);
  }
  return profiles;
}


/**
 * Keep scripted request-contract V2 provenance isolated from older adaptive
 * profiles. The V2 parser lives in the shared generator for byte reuse, but
 * dormant V2 code must not make unrelated executed/not-generated strategies
 * appear fresh.
 */
export function profileGeneratorFingerprintMaterial(source, profile) {
  const raw = String(source || "").replace(/\r\n/g, "\n");
  const wanted = String(profile || "").trim().toLowerCase();
  if (["document_request_contract_mining_v2", "provider_session_bootstrap_replay_v1"].includes(wanted)) return raw;

  let trimmed = raw.replace(
    /^\s*"scriptedRequestMining": bool\(cfg\.get\("scripted_request_mining", False\)\),\n/m,
    "",
  );

  const helperStart = trimmed.indexOf("function jsCallArgs(");
  const helperEnd = helperStart < 0
    ? -1
    : trimmed.indexOf("function explicitPlayerPayloadUrls(", helperStart);
  if (helperStart >= 0 && helperEnd >= 0) {
    trimmed = trimmed.slice(0, helperStart) + trimmed.slice(helperEnd);
  }

  const scriptedStart = trimmed.indexOf("if(c.scriptedRequestMining&&!out.length){");
  const legacyStart = scriptedStart < 0
    ? -1
    : trimmed.indexOf(
      "if(c.documentRequestMining&&!out.length){var mined=documentForms(body,page);",
      scriptedStart,
    );
  if (scriptedStart >= 0 && legacyStart >= 0) {
    trimmed = trimmed.slice(0, scriptedStart) + trimmed.slice(legacyStart);
  }
  return trimmed;
}
