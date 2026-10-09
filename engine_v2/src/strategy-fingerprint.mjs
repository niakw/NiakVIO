/** Scoped implementation provenance for Brain Repair strategy Lego.
 * Adding a new sibling profile must NEVER make exhausted older profiles
 * look fresh. Common code still participates in every fingerprint.
 */
export function profileRuntimeFingerprintMaterial(source, profile) {
  const raw = String(source || "").replace(/\r\n/g, "\n");
  const wanted = String(profile || "").trim().toLowerCase();
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
