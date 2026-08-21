import assert from "node:assert/strict";
import {
  catalogIdentity,
  compareManifest,
  interestFor,
  providerKey,
} from "../scripts/watch-upstream-providers.mjs";

assert.equal(providerKey("🐍 Anime-Sama"), "animesama");
assert.equal(providerKey("ANIME_SAMA"), "animesama");

const catalog = {
  providers: [
    {
      canonicalId: "cineby",
      scraper: { id: "CINEBY", name: "Cineby", filename: "providers/cineby--nuvio--abc.js" },
    },
    {
      canonicalId: "anime-sama",
      scraper: { id: "ANIME-SAMA", name: "🐍 Anime-Sama", filename: "providers/anime-sama--nuvio--def.js" },
    },
  ],
};
const identity = catalogIdentity(catalog);
assert(identity.ids.has("cineby"));
assert(identity.ids.has("animesama"));

const upstream = { id: "gowaru", repository: "Gowaru/gowaru-nuvio-providers" };
const manifest = {
  scrapers: [
    { id: "cineby", name: "Cineby", supportedTypes: ["movie", "tv"], formats: ["m3u8"] },
    {
      id: "new-vf-provider",
      name: "New VF Provider 4K",
      description: "Films et séries français 4K",
      supportedTypes: ["movie", "tv"],
      contentLanguage: ["fr"],
      formats: ["m3u8", "mp4"],
      enabled: true,
    },
    {
      id: "new-limited",
      name: "New Limited",
      supportedTypes: ["movie"],
      contentLanguage: ["en"],
      limited: true,
      enabled: false,
    },
  ],
};

const compared = compareManifest({ upstream, manifest, catalog });
assert.equal(compared.existingCount, 1);
assert.equal(compared.unseen.length, 2);
assert.equal(compared.unseen[0].id, "new-vf-provider");
assert.equal(compared.unseen[0].interesting, true);
assert(compared.unseen[0].reasons.includes("French/VF metadata"));
assert(compared.unseen[0].reasons.some((reason) => reason.startsWith("direct formats:")));
assert.equal(compared.unseen.at(-1).id, "new-limited");
assert.equal(compared.unseen.at(-1).interesting, false);

const noAutoMagic = interestFor({
  id: "plain",
  name: "Plain",
  supportedTypes: ["movie"],
  formats: [],
  contentLanguage: ["en"],
  enabled: false,
});
assert.equal(noAutoMagic.interesting, false);
assert(noAutoMagic.score < 4);

console.log("engine v2 upstream provider watch tests passed");
