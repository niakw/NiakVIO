/**
 * netmirror - Built from src/netmirror/
 * Generated: 2026-06-06T08:44:04.688Z
 */
var __defProp = Object.defineProperty;
var __defProps = Object.defineProperties;
var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __propIsEnum = Object.prototype.propertyIsEnumerable;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __spreadValues = (a, b) => {
  for (var prop in b || (b = {}))
    if (__hasOwnProp.call(b, prop))
      __defNormalProp(a, prop, b[prop]);
  if (__getOwnPropSymbols)
    for (var prop of __getOwnPropSymbols(b)) {
      if (__propIsEnum.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    }
  return a;
};
var __spreadProps = (a, b) => __defProps(a, __getOwnPropDescs(b));
var __async = (__this, __arguments, generator) => {
  return new Promise((resolve, reject) => {
    var fulfilled = (value) => {
      try {
        step(generator.next(value));
      } catch (e) {
        reject(e);
      }
    };
    var rejected = (value) => {
      try {
        step(generator.throw(value));
      } catch (e) {
        reject(e);
      }
    };
    var step = (x) => x.done ? resolve(x.value) : Promise.resolve(x.value).then(fulfilled, rejected);
    step((generator = generator.apply(__this, __arguments)).next());
  });
};

// src/netmirror/constants.js
var TMDB_API_KEY = "1865f43a0549ca50d341dd9ab8b29f49";
var PLATFORM_MAP = {
  netflix: {
    ott: "nf",
    search: "/mobile/search.php",
    post: "/mobile/post.php",
    episodes: "/mobile/episodes.php",
    playlist: "/mobile/playlist.php",
    img: "poster/v",
    epImg: "epimg/150"
  },
  primevideo: {
    ott: "pv",
    search: "/mobile/pv/search.php",
    post: "/mobile/pv/post.php",
    episodes: "/mobile/pv/episodes.php",
    playlist: "/mobile/pv/playlist.php",
    img: "pv/v",
    epImg: "pvepimg"
  },
  hotstar: {
    ott: "hs",
    search: "/mobile/hs/search.php",
    post: "/mobile/hs/post.php",
    episodes: "/mobile/hs/episodes.php",
    playlist: "/mobile/hs/playlist.php",
    img: "hs/v",
    epImg: "hsepimg"
  },
  disney: {
    ott: "hs",
    search: "/mobile/hs/search.php",
    post: "/mobile/hs/post.php",
    episodes: "/mobile/hs/episodes.php",
    playlist: "/mobile/hs/playlist.php",
    img: "hs/v",
    epImg: "hsepimg"
  }
};
var NEW_TV_BASE_HEADERS = {
  "Cache-Control": "no-cache, no-store, must-revalidate",
  "Pragma": "no-cache",
  "Expires": "0",
  "X-Requested-With": "NetmirrorNewTV v1.0",
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0 /OS.GatuNewTV v1.0",
  "Accept": "application/json, text/plain, */*"
};
var NEW_TV_DOMAINS = [
  "aHR0cHM6Ly9tb2JpbGVkZXRlY3RzLmNvbQ==",
  "aHR0cHM6Ly9tb2JpbGVkZXRlY3QuYXBw",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0LmFydA==",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0LmNj",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0LmNsaWNr",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0Lmluaw==",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0LmxpdmU=",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0LnBybw==",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0LnNob3A=",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0LnNpdGU=",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0LnNwYWNl",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0LnN0b3Jl",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0LnZpcA==",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0Lndpa2k=",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0Lnh5eg==",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0cy5hcnQ=",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0cy5jYw==",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0cy5pbmZv",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0cy5pbms=",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0cy5saXZl",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0cy5wcm8=",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0cy5zdG9yZQ==",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0cy50b3A=",
  "aHR0cHM6Ly9tb2JpZGV0ZWN0cy54eXo="
];

// src/netmirror/utils.js
var resolvedApiUrl = "";
function safeAtob(encoded) {
  if (typeof atob === "function") {
    return atob(encoded);
  }
  return Buffer.from(encoded, "base64").toString("binary");
}
function resolveApiUrl() {
  return __async(this, null, function* () {
    if (resolvedApiUrl)
      return resolvedApiUrl;
    for (const encoded of NEW_TV_DOMAINS) {
      const base = safeAtob(encoded).replace(/\/$/, "");
      try {
        const response = yield fetch(`${base}/checknewtv.php`, {
          headers: __spreadProps(__spreadValues({}, NEW_TV_BASE_HEADERS), { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" })
        });
        const data = yield response.json();
        const tokenHash = data.token_hash;
        if (tokenHash) {
          resolvedApiUrl = safeAtob(tokenHash).replace(/\/$/, "");
          return resolvedApiUrl;
        }
      } catch (error) {
      }
    }
    throw new Error("Failed to resolve NewTV API base URL");
  });
}
function buildNewTvHeaders(ott, extra = {}) {
  return __spreadValues(__spreadProps(__spreadValues({}, NEW_TV_BASE_HEADERS), {
    "Ott": ott
  }), extra);
}

// src/netmirror/index.js
function getStreams(tmdbId, mediaType, season, episode) {
  return __async(this, null, function* () {
    try {
      const tmdbType = mediaType === "tv" ? "tv" : "movie";
      const tmdbResp = yield fetch(`https://api.themoviedb.org/3/${tmdbType}/${tmdbId}?api_key=${TMDB_API_KEY}`, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
          "Accept": "application/json"
        }
      });
      const tmdbData = yield tmdbResp.json();
      const title = mediaType === "tv" ? tmdbData.name : tmdbData.title;
      if (!title)
        throw new Error("Could not fetch title from TMDB");
      const platforms = ["netflix", "primevideo", "hotstar", "disney"];
      for (const platformKey of platforms) {
        try {
          const streams = yield fetchFromPlatform(platformKey, title, mediaType, season, episode);
          if (streams && streams.length > 0)
            return streams;
        } catch (e) {
        }
      }
      return [];
    } catch (error) {
      return [];
    }
  });
}
function fetchFromPlatform(platformKey, title, mediaType, season, episode) {
  return __async(this, null, function* () {
    const platform = PLATFORM_MAP[platformKey];
    const apiBase = yield resolveApiUrl();
    const searchUrl = `${apiBase}/newtv/search.php?s=${encodeURIComponent(title)}`;
    const searchResp = yield fetch(searchUrl, {
      headers: buildNewTvHeaders(platform.ott)
    });
    const searchData = yield searchResp.json();
    if (!searchData.searchResult || searchData.searchResult.length === 0)
      return null;
    const result = searchData.searchResult[0];
    const contentId = result.id;
    const postUrl = `${apiBase}/newtv/post.php?id=${contentId}`;
    const postResp = yield fetch(postUrl, {
      headers: buildNewTvHeaders(platform.ott, { Lastep: "", Usertoken: "" })
    });
    const postData = yield postResp.json();
    let targetId = contentId;
    if (mediaType === "tv") {
      const episodes = yield getAllEpisodes(contentId, postData, platform, apiBase);
      const targetEp = episodes.find((ep) => ep && ep.s === season && ep.ep === episode);
      if (targetEp) {
        targetId = targetEp.id;
      } else {
        return null;
      }
    } else {
      const isSeries = postData.type === "t" || postData.episodes && postData.episodes.filter((e) => e !== null).length > 0;
      if (isSeries)
        return null;
      targetId = postData.main_id || contentId;
    }
    const playerUrl = `${apiBase}/newtv/player.php?id=${targetId}`;
    const playerResp = yield fetch(playerUrl, {
      headers: buildNewTvHeaders(platform.ott, { "Usertoken": "" })
    });
    const response = yield playerResp.json();
    if (response.status === "ok" && response.video_link) {
      return [{
        name: `NetMirror (${platformKey.charAt(0).toUpperCase() + platformKey.slice(1)})`,
        title: `${title}`,
        url: response.video_link,
        quality: "Auto",
        headers: {
          Referer: response.referer || apiBase
        }
      }];
    }
    return null;
  });
}
function getAllEpisodes(contentId, postData, platform, apiBase) {
  return __async(this, null, function* () {
    const episodes = [];
    const selectedSeasonIdx = postData.season ? postData.season.findIndex((s) => s.selected === true) : -1;
    const selectedSeasonId = selectedSeasonIdx >= 0 ? postData.season[selectedSeasonIdx].id : postData.nextPageSeason;
    const selectedSeasonNumber = selectedSeasonIdx >= 0 ? selectedSeasonIdx + 1 : null;
    if (postData.episodes) {
      postData.episodes.filter((e) => e !== null).forEach((ep) => {
        const epNum = ep.ep ? parseInt(ep.ep) : ep.epNum ? parseInt(ep.epNum.replace("E", "")) : null;
        const sNum = selectedSeasonNumber || (ep.sNum ? parseInt(ep.sNum.replace("S", "")) : null);
        episodes.push({
          id: ep.id,
          s: sNum,
          ep: epNum
        });
      });
    }
    if (postData.nextPageShow === 1 && selectedSeasonId) {
      const more = yield fetchEpisodesPage(contentId, selectedSeasonId, 2, selectedSeasonNumber, platform, apiBase);
      episodes.push(...more);
    }
    if (postData.season) {
      for (let index = 0; index < postData.season.length; index++) {
        const season = postData.season[index];
        if (season.id !== selectedSeasonId && season.id) {
          const more = yield fetchEpisodesPage(contentId, season.id, 1, index + 1, platform, apiBase);
          episodes.push(...more);
        }
      }
    }
    return episodes;
  });
}
function fetchEpisodesPage(contentId, seasonId, page, seasonNumber, platform, apiBase) {
  return __async(this, null, function* () {
    const episodes = [];
    let pg = page;
    while (true) {
      const url = `${apiBase}/newtv/episodes.php?id=${seasonId}&page=${pg}`;
      const resp = yield fetch(url, {
        headers: buildNewTvHeaders(platform.ott)
      });
      const data = yield resp.json();
      if (data.episodes) {
        data.episodes.filter((e) => e !== null).forEach((ep) => {
          const epNum = ep.ep ? parseInt(ep.ep) : ep.epNum ? parseInt(ep.epNum.replace("E", "")) : null;
          const sNum = seasonNumber || (ep.sNum ? parseInt(ep.sNum.replace("S", "")) : null);
          episodes.push({
            id: ep.id,
            s: sNum,
            ep: epNum
          });
        });
      }
      if (data.nextPageShow !== 1)
        break;
      pg++;
    }
    return episodes;
  });
}
module.exports = { getStreams };
