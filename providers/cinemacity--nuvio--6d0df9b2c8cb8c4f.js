/**
 * cinemacity - Built from src/cinemacity/
 * Generated: 2026-06-01T14:20:20.706Z
 */
var __create = Object.create;
var __defProp = Object.defineProperty;
var __defProps = Object.defineProperties;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getOwnPropSymbols = Object.getOwnPropertySymbols;
var __getProtoOf = Object.getPrototypeOf;
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
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
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

// src/cinemacity/index.js
var import_cheerio_without_node_native = __toESM(require("cheerio-without-node-native"));

// src/cinemacity/constants.js
var MAIN_URL = "https://cinemacity.cc";
var HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
  "Cookie": "dle_user_id=32729; dle_password=894171c6a8dab18ee594d5c652009a35;",
  "Referer": "https://cinemacity.cc/"
};
var TMDB_API_KEY = "1865f43a0549ca50d341dd9ab8b29f49";

// src/cinemacity/utils.js
var atobPolyfill = (str) => {
  try {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
    let output = "";
    str = String(str).replace(/[=]+$/, "");
    if (str.length % 4 === 1)
      return "";
    for (let bc = 0, bs = 0, buffer, i = 0; buffer = str.charAt(i++); ~buffer && (bs = bc % 4 ? bs * 64 + buffer : buffer, bc++ % 4) ? output += String.fromCharCode(255 & bs >> (-2 * bc & 6)) : 0) {
      buffer = chars.indexOf(buffer);
    }
    return output;
  } catch (e) {
    return "";
  }
};
function fetchText(_0) {
  return __async(this, arguments, function* (url, options = {}) {
    const response = yield fetch(url, __spreadValues({
      headers: options.headers || HEADERS,
      skipSizeCheck: true
    }, options));
    return yield response.text();
  });
}
function extractQuality(url) {
  const low = (url || "").toLowerCase();
  if (low.includes("2160p") || low.includes("4k"))
    return "4K";
  if (low.includes("1080p"))
    return "1080p";
  if (low.includes("720p"))
    return "720p";
  if (low.includes("480p"))
    return "480p";
  if (low.includes("360p"))
    return "360p";
  return "HD";
}

// src/cinemacity/index.js
function getStreams(tmdbId, mediaType, season, episode) {
  return __async(this, null, function* () {
    var _a;
    const streams = [];
    try {
      const tmdbUrl = `https://api.themoviedb.org/3/${mediaType === "tv" ? "tv" : "movie"}/${tmdbId}?api_key=${TMDB_API_KEY}&append_to_response=external_ids`;
      const tmdbRes = yield fetch(tmdbUrl, { skipSizeCheck: true });
      const tmdbData = yield tmdbRes.json();
      const imdbId = ((_a = tmdbData.external_ids) == null ? void 0 : _a.imdb_id) || tmdbData.imdb_id;
      const animeTitle = mediaType === "movie" ? tmdbData.title : tmdbData.name;
      if (!animeTitle && !imdbId)
        return [];
      const searchQuery = imdbId || animeTitle;
      const searchUrl = `${MAIN_URL}/?do=search&subaction=search&search_start=0&full_search=0&story=${encodeURIComponent(searchQuery)}`;
      console.log(`[CinemaCity] Searching for: ${searchQuery}`);
      const searchHtml = yield fetchText(searchUrl);
      const $search = import_cheerio_without_node_native.default.load(searchHtml);
      let mediaUrl = null;
      $search("div.dar-short_item").each((i, el) => {
        if (mediaUrl)
          return;
        const anchor = $search(el).find("a").filter((idx, a) => ($search(a).attr("href") || "").includes(".html")).first();
        if (!anchor.length)
          return;
        const href = anchor.attr("href");
        const foundTitle = anchor.text().toLowerCase();
        if (imdbId && searchHtml.includes(imdbId)) {
          mediaUrl = href;
        } else if (foundTitle.includes(animeTitle.toLowerCase()) || animeTitle.toLowerCase().includes(foundTitle)) {
          mediaUrl = href;
        }
      });
      if (!mediaUrl && imdbId && searchQuery !== animeTitle) {
        console.log(`[CinemaCity] IMDB search failed, falling back to title search: ${animeTitle}`);
        const titleSearchUrl = `${MAIN_URL}/?do=search&subaction=search&search_start=0&full_search=0&story=${encodeURIComponent(animeTitle)}`;
        const titleSearchHtml = yield fetchText(titleSearchUrl);
        const $titleSearch = import_cheerio_without_node_native.default.load(titleSearchHtml);
        $titleSearch("div.dar-short_item").each((i, el) => {
          if (mediaUrl)
            return;
          const anchor = $titleSearch(el).find("a").filter((idx, a) => ($titleSearch(a).attr("href") || "").includes(".html")).first();
          if (anchor.length)
            mediaUrl = anchor.attr("href");
        });
      }
      if (!mediaUrl) {
        console.log(`[CinemaCity] No media found for ${animeTitle}`);
        return [];
      }
      console.log(`[CinemaCity] Loading media page: ${mediaUrl}`);
      const pageHtml = yield fetchText(mediaUrl);
      const $page = import_cheerio_without_node_native.default.load(pageHtml);
      let fileData = null;
      let globalSubtitleData = null;
      $page("script").each((i, el) => {
        if (fileData)
          return;
        const html = $page(el).html();
        if (html && html.includes("atob")) {
          const regex = /atob\s*\(\s*(['"])(.*?)\1\s*\)/g;
          let match;
          while ((match = regex.exec(html)) !== null) {
            try {
              const decoded = atobPolyfill(match[2]);
              const fileMatch = decoded.match(new RegExp(`file\\s*:\\s*(['"])(.*?)\\1`, "s")) || decoded.match(new RegExp("file\\s*:\\s*(\\[.*?\\])", "s")) || decoded.match(new RegExp("file\\s*:\\s*(\\{.*?\\})", "s"));
              const subMatch = decoded.match(new RegExp(`subtitle\\s*:\\s*(['"])(.*?)\\1`, "s"));
              if (fileMatch) {
                let rawFile = fileMatch[2] || fileMatch[1];
                if (rawFile && rawFile.length > 5) {
                  if (rawFile.startsWith("[") || rawFile.startsWith("{")) {
                    try {
                      const unescaped = rawFile.replace(/\\(.)/g, "$1");
                      fileData = JSON.parse(unescaped);
                    } catch (e) {
                      try {
                        fileData = JSON.parse(rawFile);
                      } catch (e2) {
                        fileData = rawFile;
                      }
                    }
                  } else {
                    fileData = rawFile;
                  }
                }
              }
              if (subMatch) {
                globalSubtitleData = subMatch[2];
              }
              if (fileData)
                break;
            } catch (err) {
            }
          }
        }
      });
      if (!fileData) {
        console.log(`[CinemaCity] Failed to extract player data`);
        return [];
      }
      const parseSubtitles = (raw) => {
        const subtitles = [];
        if (!raw || typeof raw !== "string")
          return subtitles;
        raw.split(",").forEach((entry) => {
          const match = entry.trim().match(/\[(.+?)\](https?:\/\/.+)/);
          if (match) {
            subtitles.push({
              url: match[2],
              language: match[1],
              name: match[1],
              headers: { Referer: "https://cinemacity.cc/" }
            });
          }
        });
        return subtitles;
      };
      const addStream = (url, title, quality, subtitles) => {
        if (!url || !url.startsWith("http") || url.length < 15)
          return;
        streams.push({
          name: "CinemaCity",
          title,
          url,
          quality: quality || extractQuality(url),
          headers: __spreadProps(__spreadValues({}, HEADERS), {
            Referer: "https://cinemacity.cc/"
          }),
          subtitles: subtitles || []
        });
      };
      const processStr = (str, title, subtitles) => {
        if (str.includes(".urlset/master.m3u8")) {
          addStream(str, title, "Auto", subtitles);
        } else {
          const urls = str.includes("[") ? str.split(",") : [str];
          urls.forEach((u) => {
            const m = u.match(/\[(.*?)\](.*)/);
            if (m)
              addStream(m[2], title, m[1], subtitles);
            else
              addStream(u, title, extractQuality(u), subtitles);
          });
        }
      };
      if (mediaType === "movie") {
        if (Array.isArray(fileData)) {
          const obj = fileData.find((f) => !f.folder && f.file) || fileData[0];
          if (obj && obj.file) {
            const subs = parseSubtitles(obj.subtitle || globalSubtitleData);
            processStr(obj.file, animeTitle, subs);
          }
        } else if (typeof fileData === "string") {
          const subs = parseSubtitles(globalSubtitleData);
          processStr(fileData, animeTitle, subs);
        }
      } else {
        if (Array.isArray(fileData)) {
          const sLabel = `Season ${season}`;
          const sObj = fileData.find((s) => (s.title || "").includes(sLabel) || (s.title || "").includes(`S${season}`));
          if (sObj && sObj.folder) {
            const eLabel = `Episode ${episode}`;
            const eObj = sObj.folder.find((e) => (e.title || "").includes(eLabel) || (e.title || "").includes(`E${episode}`));
            if (eObj && eObj.file) {
              const subs = parseSubtitles(eObj.subtitle || sObj.subtitle || globalSubtitleData);
              processStr(eObj.file, `${animeTitle} S${season}E${episode}`, subs);
            }
          }
        }
      }
      console.log(`[CinemaCity] Successfully processed ${streams.length} streams`);
      return streams;
    } catch (error) {
      console.error(`[CinemaCity] Error in getStreams: ${error.message}`);
      return [];
    }
  });
}
module.exports = { getStreams };

/* NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V3 */
;(function(g,policy){
  function text(v){return v==null?"":String(v)}
  function inferQuality(stream){
    var hay=(text(stream.quality)+" "+text(stream.name)+" "+text(stream.title)+" "+text(stream.size)).toLowerCase();
    var m=hay.match(/(?:^|\D)(2160|1440|1080|720|576|540|480|360)(?:p|\D|$)/);
    if(m)return m[1]+"p";
    if(/\b(?:4k|uhd)\b/.test(hay))return"2160p";
    if(/\bfhd\b|full[ -]?hd/.test(hay))return"1080p";
    if(/\bhd\b/.test(hay))return"720p";
    return text(stream.quality)||"HD";
  }
  function inferLanguage(stream){
    var current=text(stream.language).trim();
    if(current)return current;
    var hay=(text(stream.name)+" "+text(stream.title)+" "+text(stream.size)).toUpperCase();
    if(/VOSTFR|VOST[ -]?FR|SUB(?:BED)?[ -]?FR/.test(hay))return"VOSTFR";
    if(/DUAL[ -]?AUDIO|MULTI(?:LANG)?|VFQ\s*[+\/]|VFF\s*[+\/]/.test(hay))return"MULTI";
    if(/\bVFQ\b/.test(hay))return"VFQ";
    if(/\bVFF\b|\bVF\b|FRENCH/.test(hay))return"VF";
    if(/\bVO\b|ENGLISH|ORIGINAL/.test(hay))return"VO";
    return null;
  }
  function hostOf(url){try{return new URL(url).hostname.toLowerCase()}catch(_e){return""}}
  function normalizeHeaders(stream){
    var out={};
    var source=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    Object.keys(source).forEach(function(k){if(source[k]!=null)out[k]=String(source[k])});
    var lower={};Object.keys(out).forEach(function(k){lower[k.toLowerCase()]=k});
    if(!lower["user-agent"])out["User-Agent"]=policy.user_agent;
    if(policy.add_accept&&!lower.accept)out.Accept="*/*";
    if(policy.add_range&&!lower.range)out.Range="bytes=0-";
    var host=hostOf(stream.url),rule=policy.host_rules&&policy.host_rules[host];
    if(rule&&typeof rule==="object"){
      if(rule.referer&&!lower.referer)out.Referer=String(rule.referer);
      if(rule.origin&&!lower.origin)out.Origin=String(rule.origin);
      if(rule.headers&&typeof rule.headers==="object")Object.keys(rule.headers).forEach(function(k){out[k]=String(rule.headers[k])});
    }
    return out;
  }
  function unsupported(url){
    var value=text(url).toLowerCase().split("?")[0].split("#")[0];
    return (policy.reject_extensions||[]).some(function(ext){return value.endsWith(String(ext).toLowerCase())});
  }
  function normalize(result){
    var list=Array.isArray(result)?result:[];
    var seen=Object.create(null),clean=[];
    for(var i=0;i<list.length;i++){
      var stream=list[i];
      if(!stream||typeof stream!=="object"||typeof stream.url!=="string")continue;
      var url=stream.url.trim();
      if(!/^https?:\/\//i.test(url)||unsupported(url)||seen[url])continue;
      seen[url]=1;
      var normalized=Object.assign({},stream,{url:url});
      normalized.quality=inferQuality(normalized);
      normalized.language=inferLanguage(normalized);
      normalized.headers=normalizeHeaders(normalized);
      clean.push(normalized);
    }
    return clean;
  }
  function wrapFunction(fn){
    if(typeof fn!=="function"||fn.__nuvioGlobalStreamGuardV3)return fn;
    var wrapped=function(){
      var self=this,args=arguments;
      try{return Promise.resolve(fn.apply(self,args)).then(normalize)}
      catch(error){return Promise.reject(error)}
    };
    try{Object.keys(fn).forEach(function(k){wrapped[k]=fn[k]})}catch(_e){}
    try{Object.defineProperty(wrapped,"__nuvioGlobalStreamGuardV3",{value:true})}catch(_e){wrapped.__nuvioGlobalStreamGuardV3=true}
    return wrapped;
  }
  function wrapTarget(target){
    if(!target)return target;
    if(typeof target==="function")return wrapFunction(target);
    if(typeof target==="object"&&typeof target.getStreams==="function")target.getStreams=wrapFunction(target.getStreams);
    return target;
  }
  try{
    if(typeof module!=="undefined"&&module&&module.exports)module.exports=wrapTarget(module.exports);
  }catch(_e){}
  try{
    if(g&&typeof g.getStreams==="function")g.getStreams=wrapFunction(g.getStreams);
  }catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"user_agent":"Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36","add_accept":true,"add_range":true,"reject_extensions":[".avi",".wmv",".flv"],"host_rules":{}});
