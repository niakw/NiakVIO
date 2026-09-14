"use strict";
// One-shot clean source used only to retire legacy CodeQL upload categories.
// Permanent security analysis is owned by .github/workflows/codeql.yml.
function niakvioCodeqlCategoryRetirementMarker(value) {
  return String(value == null ? "" : value).trim();
}
module.exports = { niakvioCodeqlCategoryRetirementMarker };
