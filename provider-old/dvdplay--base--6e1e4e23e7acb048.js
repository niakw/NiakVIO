"use strict";

/*
 * NiakVIO ProviderBase: DVDPlay
 * Clean reconstruction seed. Upstream implementations are knowledge sources only;
 * no third-party provider JavaScript is embedded here.
 *
 * DVDPlay remains quarantined until Learning/Deep reconstructs and proves a current
 * provider-owned catalogue -> detail -> media route. Keeping an inert ProviderBase
 * is deliberate: a disabled/quarantined provider must fail closed, never expose
 * stale cross-title media.
 */
const PROVIDER_ID = "dvdplay";
const KNOWN_SITE = "https://dvdplay.cv";
const SUPPORTED_TYPES = Object.freeze(["movie", "tv"]);

async function getStreams(_tmdbId, _mediaType, _season, _episode) {
  return [];
}

module.exports = {
  getStreams,
  __niakvioProviderBase: Object.freeze({
    providerId: PROVIDER_ID,
    knownSite: KNOWN_SITE,
    supportedTypes: SUPPORTED_TYPES,
    reconstructionState: "needs-learning-repair"
  })
};
