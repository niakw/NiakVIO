/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */
;(function(g,rules){
  if(!g||typeof g.fetch!=="function")return;
  var key="__nuvioDomainOverrideV1";
  var state=g[key];
  if(!state){
    state={native:g.fetch.bind(g),rules:Object.create(null)};
    g[key]=state;
    g.fetch=function(input,init){
      var next=input;
      try{
        var raw=(typeof Request!=="undefined"&&input instanceof Request)?input.url:String(input);
        var url=new URL(raw);
        var replacement=state.rules[String(url.hostname).toLowerCase()];
        if(replacement){
          url.hostname=replacement;
          next=(typeof Request!=="undefined"&&input instanceof Request)?new Request(url.toString(),input):url.toString();
        }
      }catch(_error){}
      return state.native(next,init);
    };
  }
  for(var i=0;i<rules.length;i++){
    try{state.rules[atob(rules[i][0])]=rules[i][1];}catch(_error){}
  }
})(typeof globalThis!=="undefined"?globalThis:this,[["NGtoZGh1Yi5jbGljaw==","new4.hdhub4u.cl"],["NGtoZGh1Yi5vbmU=","new4.hdhub4u.cl"],["bmV3My5oZGh1YjR1LmNs","new4.hdhub4u.cl"]]);
"use strict";
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
var BASE_URL = "https://new4.hdhub4u.cl";
var TMDB_API_KEY = "439c478a771f35c05022f9feabcca01c";
var USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36";
var DOMAINS_URL = "https://raw.githubusercontent.com/phisher98/TVVVV/refs/heads/main/domains.json";
var domainCache = { url: BASE_URL, ts: 0 };
function fetchLatestDomain() {
  return __async(this, null, function* () {
    const now = Date.now();
    if (now - domainCache.ts < 36e5)
      return domainCache.url;
    try {
      const response = yield fetch(DOMAINS_URL);
      const data = yield response.json();
      if (data && data["4khdhub"]) {
        domainCache.url = data["4khdhub"];
        domainCache.ts = now;
      }
    } catch (e) {
    }
    return domainCache.url;
  });
}
function fetchText(_0) {
  return __async(this, arguments, function* (url, options = {}) {
    const retries = options.retries !== void 0 ? options.retries : 2;
    const delay = options.delay !== void 0 ? options.delay : 1e3;
    for (let i = 0; i <= retries; i++) {
      try {
        const response = yield fetch(url, {
          headers: __spreadValues({
            "User-Agent": USER_AGENT
          }, options.headers)
        });
        return yield response.text();
      } catch (err) {
        console.log(`[4KHDHub] Request failed for ${url}: ${err.message}${i < retries ? `, retrying (${i + 1}/${retries})...` : ""}`);
      }
      if (i < retries) {
        yield new Promise((r) => setTimeout(r, delay * Math.pow(2, i)));
      }
    }
    return null;
  });
}
function getTmdbDetails(tmdbId, type) {
  return __async(this, null, function* () {
    const isSeries = type === "series" || type === "tv";
    const endpoint = isSeries ? "tv" : "movie";
    const url = `https://api.themoviedb.org/3/${endpoint}/${tmdbId}?api_key=${TMDB_API_KEY}`;
    console.log(`[4KHDHub] Fetching TMDB details from: ${url}`);
    try {
      const response = yield fetch(url);
      const data = yield response.json();
      if (isSeries) {
        return {
          title: data.name,
          year: data.first_air_date ? parseInt(data.first_air_date.split("-")[0]) : 0
        };
      } else {
        return {
          title: data.title,
          year: data.release_date ? parseInt(data.release_date.split("-")[0]) : 0
        };
      }
    } catch (error) {
      console.log(`[4KHDHub] TMDB request failed: ${error.message}`);
      return null;
    }
  });
}
function atob(input) {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
  let str = String(input).replace(/=+$/, "");
  if (str.length % 4 === 1) {
    throw new Error("'atob' failed: The string to be decoded is not correctly encoded.");
  }
  let output = "";
  for (let bc = 0, bs, buffer, i = 0; buffer = str.charAt(i++); ~buffer && (bs = bc % 4 ? bs * 64 + buffer : buffer, bc++ % 4) ? output += String.fromCharCode(255 & bs >> (-2 * bc & 6)) : 0) {
    buffer = chars.indexOf(buffer);
  }
  return output;
}
function rot13Cipher(str) {
  return str.replace(/[a-zA-Z]/g, function(c) {
    return String.fromCharCode((c <= "Z" ? 90 : 122) >= (c = c.charCodeAt(0) + 13) ? c : c - 26);
  });
}
function levenshteinDistance(s, t) {
  if (s === t)
    return 0;
  const n = s.length;
  const m = t.length;
  if (n === 0)
    return m;
  if (m === 0)
    return n;
  const d = [];
  for (let i = 0; i <= n; i++) {
    d[i] = [];
    d[i][0] = i;
  }
  for (let j = 0; j <= m; j++) {
    d[0][j] = j;
  }
  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      const cost = s.charAt(i - 1) === t.charAt(j - 1) ? 0 : 1;
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost);
    }
  }
  return d[n][m];
}
function parseBytes(val) {
  if (typeof val === "number")
    return val;
  if (!val)
    return 0;
  const match = val.match(/^([0-9.]+)\s*([a-zA-Z]+)$/);
  if (!match)
    return 0;
  const num = parseFloat(match[1]);
  const unit = match[2].toLowerCase();
  let multiplier = 1;
  if (unit.indexOf("k") === 0)
    multiplier = 1024;
  else if (unit.indexOf("m") === 0)
    multiplier = 1024 * 1024;
  else if (unit.indexOf("g") === 0)
    multiplier = 1024 * 1024 * 1024;
  else if (unit.indexOf("t") === 0)
    multiplier = 1024 * 1024 * 1024 * 1024;
  return num * multiplier;
}
function formatBytes(val) {
  if (val === 0)
    return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  let i = Math.floor(Math.log(val) / Math.log(k));
  if (i < 0)
    i = 0;
  return parseFloat((val / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}
var cheerio = require("cheerio-without-node-native");
function fetchPageUrl(name, year, isSeries) {
  return __async(this, null, function* () {
    const domain = yield fetchLatestDomain();
    const searchUrl = `${domain}/?s=${encodeURIComponent(name + " " + year)}`;
    console.log(`[4KHDHub] Search Request URL: ${searchUrl}`);
    const html = yield fetchText(searchUrl);
    if (!html) {
      console.log("[4KHDHub] Search failed: No HTML response");
      return null;
    }
    const $ = cheerio.load(html);
    const targetType = isSeries ? "Series" : "Movies";
    console.log(`[4KHDHub] Parsing search results for type: ${targetType}`);
    const matchingCards = $(".movie-card").filter((_, el) => {
      const hasFormat = $(el).find(`.movie-card-format:contains("${targetType}")`).length > 0;
      if (!hasFormat) {
      }
      return hasFormat;
    }).filter((_, el) => {
      const metaText = $(el).find(".movie-card-meta").text();
      const movieCardYear = parseInt(metaText);
      const yearMatch = !isNaN(movieCardYear) && Math.abs(movieCardYear - year) <= 1;
      if (!yearMatch) {
        console.log(`[4KHDHub] Skip: Year mismatch (${movieCardYear} vs ${year}) - ${$(el).find(".movie-card-title").text().trim()}`);
      }
      return yearMatch;
    }).filter((_, el) => {
      const movieCardTitle = $(el).find(".movie-card-title").text().replace(/\[.*?]/g, "").trim();
      const distance = levenshteinDistance(movieCardTitle.toLowerCase(), name.toLowerCase());
      const match = distance < 5;
      console.log(`[4KHDHub] Checking: "${movieCardTitle}" (Dist: ${distance}) vs "${name}"`);
      return match;
    }).map((_, el) => {
      let href = $(el).attr("href");
      if (href && !href.startsWith("http")) {
        href = domain + (href.startsWith("/") ? "" : "/") + href;
      }
      return href;
    }).get();
    if (matchingCards.length === 0) {
      console.log("[4KHDHub] No matching cards found after filtering");
    } else {
      console.log(`[4KHDHub] Found ${matchingCards.length} matching cards`);
    }
    return matchingCards.length > 0 ? matchingCards[0] : null;
  });
}
var cheerio2 = require("cheerio-without-node-native");
function resolveRedirectUrl(redirectUrl) {
  return __async(this, null, function* () {
    if (redirectUrl.includes("hubcloud.") || redirectUrl.includes("hubdrive.")) {
      return redirectUrl;
    }
    const redirectHtml = yield fetchText(redirectUrl);
    if (!redirectHtml)
      return redirectUrl;
    try {
      const redirectDataMatch = redirectHtml.match(/'o','(.*?)'/);
      if (!redirectDataMatch)
        return redirectUrl;
      const step1 = atob(redirectDataMatch[1]);
      const step2 = atob(step1);
      const step3 = rot13Cipher(step2);
      const step4 = atob(step3);
      const redirectData = JSON.parse(step4);
      if (redirectData && redirectData.o) {
        return atob(redirectData.o);
      }
    } catch (e) {
      console.log(`[4KHDHub] Error resolving redirect: ${e.message}`);
    }
    return redirectUrl;
  });
}
function extractSourceResults($, el) {
  return __async(this, null, function* () {
    const localHtml = $(el).html();
    const sizeMatch = localHtml.match(/([\d.]+ ?[GM]B)/);
    const heightMatch = localHtml.match(/\d{3,}p/);
    const title = $(el).find(".file-title, .episode-file-title").text().trim();
    let height = heightMatch ? parseInt(heightMatch[0]) : 0;
    if (height === 0 && (title.includes("4K") || title.includes("4k") || localHtml.includes("4K") || localHtml.includes("4k"))) {
      height = 2160;
    }
    const meta = {
      bytes: sizeMatch ? parseBytes(sizeMatch[1]) : 0,
      height,
      title
    };
    const hubCloudLink = $(el).find("a").filter((_, a) => {
      const text = $(a).text();
      const href = $(a).attr("href") || "";
      return text.includes("HubCloud") || href.includes("hubcloud.") || href.includes("hubcloud/");
    }).attr("href");
    if (hubCloudLink) {
      const resolved = yield resolveRedirectUrl(hubCloudLink);
      return { url: resolved, meta };
    }
    const hubDriveLink = $(el).find("a").filter((_, a) => {
      const text = $(a).text();
      const href = $(a).attr("href") || "";
      return text.includes("HubDrive") || href.includes("hubdrive.") || href.includes("hubdrive/");
    }).attr("href");
    if (hubDriveLink) {
      const resolvedDrive = yield resolveRedirectUrl(hubDriveLink);
      if (resolvedDrive) {
        const hubDriveHtml = yield fetchText(resolvedDrive);
        if (hubDriveHtml) {
          const $2 = cheerio2.load(hubDriveHtml);
          const innerCloudLink = $2('a:contains("HubCloud")').attr("href") || $2("a").filter((_, a) => {
            const text = $2(a).text();
            const href = $2(a).attr("href") || "";
            return text.includes("HubCloud") || href.includes("hubcloud.") || href.includes("hubcloud/");
          }).attr("href");
          if (innerCloudLink) {
            return { url: innerCloudLink, meta };
          }
        }
      }
    }
    return null;
  });
}
function extractHubCloud(hubCloudUrl, baseMeta) {
  return __async(this, null, function* () {
    if (!hubCloudUrl)
      return [];
    const redirectHtml = yield fetchText(hubCloudUrl, { headers: { Referer: hubCloudUrl } });
    if (!redirectHtml)
      return [];
    const redirectUrlMatch = redirectHtml.match(/var url ?= ?'(.*?)'/);
    if (!redirectUrlMatch)
      return [];
    const finalLinksUrl = redirectUrlMatch[1];
    const linksHtml = yield fetchText(finalLinksUrl, { headers: { Referer: hubCloudUrl } });
    if (!linksHtml)
      return [];
    const $ = cheerio2.load(linksHtml);
    const results = [];
    const sizeText = $("#size").text();
    const titleText = $("title").text().trim();
    const currentMeta = __spreadProps(__spreadValues({}, baseMeta), {
      bytes: parseBytes(sizeText) || baseMeta.bytes,
      title: titleText || baseMeta.title
    });
    $("a").each((_, el) => {
      const text = $(el).text().trim();
      const href = $(el).attr("href");
      if (!href)
        return;
      if (text.includes("10Gbps") || text.includes("PixelServer") || href.includes("hubcloud.cx")) {
        results.push({
          source: "HubCloud 10Gbps",
          url: href,
          meta: currentMeta
        });
      } else if (text.includes("Download File") || href.includes("r2.dev")) {
        results.push({
          source: "Direct R2",
          url: href,
          meta: currentMeta
        });
      } else if (text.includes("ZipDisk") || href.includes("workers.dev")) {
        results.push({
          source: "ZipDisk Server",
          url: href,
          meta: currentMeta
        });
      } else if (text.includes("FSL")) {
        results.push({
          source: "FSL",
          url: href,
          meta: currentMeta
        });
      }
    });
    return results;
  });
}
var cheerio3 = require("cheerio-without-node-native");
function getStreams(tmdbId, type, season, episode) {
  return __async(this, null, function* () {
    const tmdbDetails = yield getTmdbDetails(tmdbId, type);
    if (!tmdbDetails)
      return [];
    const { title, year } = tmdbDetails;
    console.log(`[4KHDHub] Search: ${title} (${year})`);
    const isSeries = type === "series" || type === "tv";
    const pageUrl = yield fetchPageUrl(title, year, isSeries);
    if (!pageUrl) {
      console.log("[4KHDHub] Page not found");
      return [];
    }
    console.log(`[4KHDHub] Found page: ${pageUrl}`);
    const html = yield fetchText(pageUrl);
    if (!html)
      return [];
    const $ = cheerio3.load(html);
    const itemsToProcess = [];
    if (isSeries && season && episode) {
      const seasonStr = "S" + String(season).padStart(2, "0");
      const episodeStr = "Episode-" + String(episode).padStart(2, "0");
      $(".episode-item").each((_, el) => {
        if ($(".episode-title", el).text().includes(seasonStr)) {
          const downloadItems = $(".episode-download-item", el).filter((_2, item) => $(item).text().includes(episodeStr));
          downloadItems.each((_2, item) => {
            itemsToProcess.push(item);
          });
        }
      });
    } else {
      $(".download-item").each((_, el) => {
        itemsToProcess.push(el);
      });
    }
    console.log(`[4KHDHub] Processing ${itemsToProcess.length} items`);
    const streamPromises = itemsToProcess.map((item) => __async(this, null, function* () {
      try {
        const sourceResult = yield extractSourceResults($, item);
        if (sourceResult && sourceResult.url) {
          console.log(`[4KHDHub] Extracting from HubCloud: ${sourceResult.url}`);
          const extractedLinks = yield extractHubCloud(sourceResult.url, sourceResult.meta);
          return extractedLinks.map((link) => ({
            name: `4KHDHub - ${link.source}${sourceResult.meta.height ? ` ${sourceResult.meta.height}p` : ""}`,
            title: `${link.meta.title}
${formatBytes(link.meta.bytes || 0)}`,
            url: link.url,
            quality: sourceResult.meta.height ? `${sourceResult.meta.height}p` : void 0,
            behaviorHints: {
              bingeGroup: `4khdhub-${link.source}`
            }
          }));
        }
        return [];
      } catch (err) {
        console.log(`[4KHDHub] Item processing error: ${err.message}`);
        return [];
      }
    }));
    const results = yield Promise.all(streamPromises);
    return results.reduce((acc, val) => acc.concat(val), []);
  });
}
module.exports = { getStreams };
/* NUVIO_STREAM_OUTPUT_SANITIZER_V3:2705513012b7 */
;(function(g,config){
  "use strict";
  function hostOf(raw){try{return new URL(String(raw)).hostname.toLowerCase()}catch(_e){return ""}}
  function blocked(raw){
    var host=hostOf(raw);
    if(!host)return true;
    for(var i=0;i<config.blockedHosts.length;i++){
      var rule=config.blockedHosts[i];
      if(host===rule||host.endsWith("."+rule))return true;
    }
    try{
      var path=new URL(String(raw)).pathname.toLowerCase();
      for(var j=0;j<config.blockedPathPatterns.length;j++){
        if(path.indexOf(config.blockedPathPatterns[j])>=0)return true;
      }
    }catch(_e){}
    return false;
  }
  function urlOf(stream){return stream&&typeof stream.url==="string"?stream.url.trim():""}
  function isDirect(stream,url){
    var hint=String((stream&&(stream.type||stream.format||stream.mimeType||stream.contentType))||"").toLowerCase();
    return /(?:\.m3u8|\.mp4|\.mkv|\.webm|\.mpd)(?:[?#]|$)/i.test(url)||/(?:hls|mpegurl|dash|mp4|video\/)/.test(hint);
  }
  function headersFor(stream){
    var output={"Accept":"application/vnd.apple.mpegurl,application/x-mpegURL,video/*,*/*;q=0.8","Range":"bytes=0-4095"};
    var source=stream&&stream.headers;
    if(source&&typeof source==="object"){
      try{Object.keys(source).forEach(function(key){if(source[key]!=null)output[key]=String(source[key])})}catch(_e){}
    }
    return output;
  }
  async function prefixBytes(response,controller){
    if(response.body&&typeof response.body.getReader==="function"){
      var reader=response.body.getReader();
      try{var chunk=await reader.read();return chunk&&chunk.value?chunk.value:new Uint8Array(0)}
      finally{try{await reader.cancel()}catch(_e){};try{controller.abort()}catch(_e){}}
    }
    var buffer=await response.arrayBuffer();
    try{controller.abort()}catch(_e){}
    return new Uint8Array(buffer.slice(0,4096));
  }
  function ascii(bytes){
    var end=Math.min(bytes.length,16384),out="";
    for(var i=0;i<end;i++)out+=String.fromCharCode(bytes[i]);
    return out;
  }
  function validHls(text){
    var value=String(text||"").replace(/^\uFEFF/,"").trimStart();
    if(value.indexOf("#EXTM3U")!==0)return false;
    var isVod=/#EXT-X-ENDLIST(?:\r?\n|$)/i.test(value);
    var durations=[],match,re=/#EXTINF:([0-9]+(?:\.[0-9]+)?)/gi;
    while((match=re.exec(value))!==null)durations.push(Number(match[1])||0);
    if(isVod&&durations.length&&config.minVodDurationSeconds>0){
      var total=durations.reduce(function(sum,item){return sum+item},0);
      if(total<config.minVodDurationSeconds)return false;
    }
    return true;
  }
  async function probe(stream,url){
    if(typeof g.fetch!=="function")return true;
    var controller=typeof AbortController!=="undefined"?new AbortController():{signal:void 0,abort:function(){}};
    var timer=setTimeout(function(){try{controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",headers:headersFor(stream),redirect:"follow",signal:controller.signal});
      if(!response||!response.ok||blocked(response.url||url))return false;
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      var bytes=await prefixBytes(response,controller),text=ascii(bytes);
      if(/(?:\.m3u8)(?:[?#]|$)/i.test(url)||/(?:mpegurl|vnd\.apple)/.test(contentType))return validHls(text);
      if(/(?:text\/html|application\/json|text\/plain)/.test(contentType)||/^\s*(?:<!doctype|<html|<body|\{|\[)/i.test(text))return false;
      if(/(?:\.mp4)(?:[?#]|$)/i.test(url)||/video\/mp4/.test(contentType))return /video\/mp4/.test(contentType)||(bytes.length>=8&&ascii(bytes.slice(4,8))==="ftyp");
      return bytes.length>0;
    }catch(_error){return false}
    finally{clearTimeout(timer);try{controller.abort()}catch(_e){}}
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__nuvioSanitized)return false;
    var original=container[key];
    var wrapped=async function(){
      var result=await original.apply(this,arguments);
      if(!Array.isArray(result))return result;
      var seen=Object.create(null),candidates=[],probeCount=0;
      for(var i=0;i<result.length;i++){
        var stream=result[i],url=urlOf(stream);
        if(!url||blocked(url)||seen[url])continue;
        seen[url]=true;
        candidates.push({stream:stream,url:url,probe:(config.probeAllUrls||(config.probeDirectMedia&&isDirect(stream,url)))&&probeCount++<config.maxProbes});
      }
      var checked=await Promise.all(candidates.map(async function(item){
        if(!item.probe)return item.stream;
        return await probe(item.stream,item.url)?item.stream:null;
      }));
      return checked.filter(Boolean);
    };
    wrapped.__nuvioSanitized=true;
    wrapped.__nuvioOriginal=original;
    container[key]=wrapped;
    return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){
    if(installed&&typeof module!=="undefined"&&module.exports&&module.exports.getStreams)g.getStreams=module.exports.getStreams;
    else install(g,"getStreams");
  }}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"blockedHosts":[],"probeDirectMedia":true,"probeAllUrls":true,"maxProbes":6,"timeoutMs":4500,"minVodDurationSeconds":60,"blockedPathPatterns":[]});
