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
})(typeof globalThis!=="undefined"?globalThis:this,[["NGtoZGh1Yi5jbGljaw==","4khdhub.one"],["bmV3My5oZGh1YjR1LmNs","4khdhub.one"],["bmV3NC5oZGh1YjR1LmNs","4khdhub.one"]]);
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
var BASE_URL = "https://4khdhub.one";
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





/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:7a60b5a9b638 */
;(function(g,c){"use strict";
var ASSET=/\.(?:css|js|mjs|map|png|jpe?g|gif|svg|ico|woff2?|ttf|otf|eot|json|xml|vtt|srt)(?:[?#]|$)/i;
var BADHOST=/(?:^|\.)(?:youtube\.com|youtu\.be|twitter\.com|x\.com|twimg\.com|facebook\.com|instagram\.com|googletagmanager\.com|google-analytics\.com|doubleclick\.net)$/i;
function s(v){return String(v==null?"":v).replace(/\\\//g,"/").trim()}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return""}}
function host(v){try{return new URL(v).hostname.toLowerCase()}catch(_){return""}}
function rejected(v){var h=host(v);return !/^https?:\/\//i.test(v)||!h||BADHOST.test(h)||ASSET.test(v)||/(?:trailer|bande-annonce|big[_-]?buck[_-]?bunny|sample[-_]?video|\/troll\/master\.m3u8)/i.test(v)}
function directByName(v){return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/hls2?\//i.test(v)}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
function headers(row,referer,target){var out={},src=row&&row.headers&&typeof row.headers==="object"?row.headers:{};Object.keys(src).forEach(function(k){if(String(k).toLowerCase()!=="range")out[k]=s(src[k])});if(referer&&!out.Referer&&!out.referer)out.Referer=referer;try{var o=new URL(referer||target).origin;if(o&&!out.Origin&&!out.origin)out.Origin=o}catch(_){}if(!directByName(target)&&!out.Range&&!out.range)out.Range="bytes=0-262143";return out}
function kindBytes(bytes){if(!bytes||bytes.length<4)return null;if(bytes.length>=12&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4";if(bytes[0]===26&&bytes[1]===69&&bytes[2]===223&&bytes[3]===163)return"mkv";if(bytes[0]===71&&(bytes.length<189||bytes[188]===71))return"mpegts";return null}
function decode(bytes){try{return new TextDecoder("utf-8").decode(bytes)}catch(_){var x="";for(var i=0;i<Math.min(bytes.length,262144);i++)x+=String.fromCharCode(bytes[i]);return x}}
async function fetchResource(url,row,referer){try{var r=await g.fetch(url,{headers:headers(row,referer,url),redirect:"follow",signal:timeout()});if(!r)return null;var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",buf=await r.arrayBuffer(),bytes=new Uint8Array(buf),text=decode(bytes.slice(0,300000));return{ok:!!r.ok,status:r.status,url:s(r.url||url),type:type,bytes:bytes,text:text,headers:headers(row,referer,r.url||url)}}catch(_){return null}}
function proof(r){if(!r||!r.ok)return null;var t=s(r.text).trimStart();if(t.indexOf("#EXTM3U")===0)return"hls";if(/<MPD[\s>]/i.test(t.slice(0,4096))||/application\/dash\+xml/i.test(r.type))return"dash";var b=kindBytes(r.bytes);if(b)return b;if(/^video\//i.test(r.type)&&r.bytes&&r.bytes.length>12)return"video";return null}
function candidates(text,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||rejected(u)||seen[u])return;seen[u]=1;out.push(u)}var body=s(text),patterns=[/(?:src|href|data-src|data-url|data-embed|data-player|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+(?:m3u8|mpd|mp4|mkv|webm|embed|player|\/e\/|\/hls2?\/)[^"'<>\s\\]*)/gi],m;for(var i=0;i<patterns.length;i++){patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null){add(m[1]);if(out.length>=c.maxCandidates)return out}}return out}
async function resolve(url,row,referer,depth,seen){if(depth>c.maxDepth||rejected(url))return[];seen=seen||{};if(seen[url])return[];seen[url]=1;var r=await fetchResource(url,row,referer);if(!r)return[];var k=proof(r);if(k)return[{url:r.url||url,kind:k,headers:r.headers}];if(!/html|text|json|javascript|xml/i.test(r.type)&&!/[<>{}\[\]"']/.test(r.text||""))return[];var next=candidates(r.text,r.url||url),out=[];for(var i=0;i<next.length&&out.length<c.maxCandidates;i++){var found=await resolve(next[i],row,r.url||url,depth+1,seen);for(var j=0;j<found.length;j++)if(!out.some(function(x){return x.url===found[j].url}))out.push(found[j])}return out}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function clone(row,media){var out=Object.assign({},row,{url:media.url,headers:media.headers||row.headers||{},isDirect:true,type:media.kind});return out}
async function enrich(list){var out=[],seen={};function add(row){var u=s(row&&row.url);if(!u||seen[u])return;seen[u]=1;out.push(row)}for(var i=0;i<list.length;i++){var row=list[i];if(!row||typeof row!=="object"){continue}var u=s(row.url||row.streamUrl||row.stream||row.link||row.file);if(!u||rejected(u)){if(c.preserveOriginal)add(row);continue}if(i<c.maxRows&&!directByName(u)){var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||u),found=await resolve(u,row,ref,0,{});for(var j=0;j<found.length;j++)add(clone(row,found[j]))}add(row)}return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalMediaEnrichmentV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var list=await enrich(x.list);return rebuild(v,x,list)};wrap.__nuvioGlobalMediaEnrichmentV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"maxRows":6,"maxDepth":2,"maxCandidates":10,"timeoutMs":6500,"preserveOriginal":true});




/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:40ba2c55c9f9 */
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
      var parsed=new URL(String(raw)),path=parsed.pathname.toLowerCase();
      for(var j=0;j<config.blockedPathPatterns.length;j++){
        if(path.indexOf(config.blockedPathPatterns[j])>=0)return true;
      }
      // NUVIO_EMBED_HTML_ALLOWLIST_V1
      // External-player pages often legitimately end in .html. Preserve them
      // only when their path has an explicit player/embed/watch role.
      var embedLike=/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path);
      if(/\.(?:js|mjs|css|json|xml|txt|map|woff2?|ttf|otf|ico|jpe?g|png|gif|webp|svg)(?:$|[?#])/i.test(path))return true;
      if(/\.html?(?:$|[?#])/i.test(path)&&!embedLike)return true;
    }catch(_e){}
    return false;
  }
  function urlOf(stream){return stream&&typeof stream.url==="string"?stream.url.trim():""}
  function directExtension(url){return /(?:\.m3u8?|\.mpd|\.mp4|\.m4v|\.mov|\.mkv|\.webm|\.mpeg|\.mpg|\.ogv)(?:[?#]|$)/i.test(String(url||""))}
  function isDirect(stream,url){
    var hint=String((stream&&(stream.type||stream.format||stream.mimeType||stream.contentType))||"").toLowerCase();
    return directExtension(url)||/(?:hls|mpegurl|dash|mp4|matroska|webm|video\/)/.test(hint);
  }
  function markDirect(stream,url){
    if(!stream||typeof stream!=="object")return;
    if(url&&!blocked(url))stream.url=String(url);
    stream.isDirect=true;
  }
  function rank(stream,url){
    if(isDirect(stream,url))return 0;
    try{
      var path=new URL(String(url)).pathname.toLowerCase();
      if(/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))return 1;
    }catch(_e){}
    if(stream&&stream.headers&&typeof stream.headers==="object"&&Object.keys(stream.headers).length)return 2;
    return 3;
  }
  function headersFor(stream){
    var output={"Accept":"application/vnd.apple.mpegurl,application/x-mpegURL,application/dash+xml,video/*,*/*;q=0.8","Range":"bytes=0-4095"};
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
    var value=String(text||"").replace(/^(?:\uFEFF|\u00EF\u00BB\u00BF)/,"").trimStart();
    if(value.indexOf("#EXTM3U")!==0)return false;
    var lines=value.split(/\r?\n/),hasVariantTag=false,hasVariantUri=false;
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i].trim()))continue;
      hasVariantTag=true;
      for(var j=i+1;j<lines.length;j++){
        var child=String(lines[j]||"").trim();
        if(!child)continue;
        if(child.charAt(0)==="#")continue;
        hasVariantUri=true;break;
      }
      if(hasVariantUri)break;
    }
    if(hasVariantTag&&!hasVariantUri)return false;
    var hasMedia=/#EXTINF\s*:/i.test(value)||/#EXT-X-PART\s*:/i.test(value)||/#EXT-X-MAP\s*:/i.test(value);
    if(!hasMedia&&!hasVariantUri)return false;
    var isVod=/#EXT-X-ENDLIST(?:\r?\n|$)/i.test(value);
    var durations=[],match,re=/#EXTINF:([0-9]+(?:\.[0-9]+)?)/gi;
    while((match=re.exec(value))!==null)durations.push(Number(match[1])||0);
    if(isVod&&durations.length&&config.minVodDurationSeconds>0){
      var total=durations.reduce(function(sum,item){return sum+item},0);
      if(total<config.minVodDurationSeconds)return false;
    }
    return true;
  }
  function validDash(text){
    var value=String(text||"").trimStart();
    return /<MPD[\s>]/i.test(value)&&/<(?:Representation|AdaptationSet)\b/i.test(value);
  }
  function dispositionMedia(value){
    return /filename\*?=(?:UTF-8''|["']?)[^;\r\n]*\.(?:m3u8?|mpd|mp4|m4v|mov|mkv|webm|mpeg|mpg|ogv)(?:["';\r\n]|$)/i.test(String(value||""));
  }
  function isEbml(bytes){return bytes.length>=4&&bytes[0]===0x1a&&bytes[1]===0x45&&bytes[2]===0xdf&&bytes[3]===0xa3}
  async function probe(stream,url){
    if(typeof g.fetch!=="function")return true;
    var controller=typeof AbortController!=="undefined"?new AbortController():{signal:void 0,abort:function(){}};
    var timer=setTimeout(function(){try{controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",headers:headersFor(stream),redirect:"follow",signal:controller.signal});
      var finalUrl=response&&response.url?String(response.url):url;
      if(!response||!response.ok||blocked(finalUrl))return false;
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      var disposition=String(response.headers&&response.headers.get?response.headers.get("content-disposition")||"":"");
      var bytes=await prefixBytes(response,controller),text=ascii(bytes);
      if(/(?:\.m3u8?)(?:[?#]|$)/i.test(url)||/(?:\.m3u8?)(?:[?#]|$)/i.test(finalUrl)||/(?:mpegurl|vnd\.apple)/.test(contentType)||/^\s*#EXTM3U/i.test(text)){
        if(!validHls(text))return false;
        markDirect(stream,finalUrl);
        return true;
      }
      if(/(?:text\/html|application\/json|text\/plain)/.test(contentType)||/^\s*(?:<!doctype|<html|<body|\{|\[)/i.test(text))return false;
      if(/(?:\.mpd)(?:[?#]|$)/i.test(url)||/(?:\.mpd)(?:[?#]|$)/i.test(finalUrl)||/application\/dash\+xml/.test(contentType)||/^\s*(?:<\?xml[\s\S]{0,300})?<MPD[\s>]/i.test(text)){
        if(!validDash(text))return false;
        markDirect(stream,finalUrl);
        return true;
      }
      var hasFtyp=bytes.length>=8&&ascii(bytes.slice(4,8))==="ftyp";
      if(/(?:\.mp4|\.m4v|\.mov)(?:[?#]|$)/i.test(url)||/(?:\.mp4|\.m4v|\.mov)(?:[?#]|$)/i.test(finalUrl)||/video\/mp4/.test(contentType)||hasFtyp){
        if(!(/video\/mp4/.test(contentType)||hasFtyp||bytes.length>0))return false;
        markDirect(stream,finalUrl);
        return true;
      }
      if(/(?:video\/(?:webm|x-matroska|mpeg|ogg)|application\/(?:x-matroska|ogg))/.test(contentType)||isEbml(bytes)||dispositionMedia(disposition)){
        if(!bytes.length)return false;
        markDirect(stream,finalUrl);
        return true;
      }
      if(/^video\//.test(contentType)&&bytes.length){
        markDirect(stream,finalUrl);
        return true;
      }
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
        candidates.push({stream:stream,url:url,rank:rank(stream,url),index:i});
      }
      candidates.sort(function(a,b){return a.rank-b.rank||a.index-b.index});
      for(var c=0;c<candidates.length;c++){
        candidates[c].probe=(config.probeAllUrls||(config.probeDirectMedia&&isDirect(candidates[c].stream,candidates[c].url)))&&probeCount++<config.maxProbes;
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
})(typeof globalThis!=="undefined"?globalThis:this,{"blockedHosts":["analytics.google.com","api.themoviedb.org","arm.haglund.dev","cloudflareinsights.com","connect.facebook.net","doubleclick.net","google-analytics.com","googlesyndication.com","googletagmanager.com","graphql.anilist.co","kitsu.io","lodash.com","npms.io","openjsf.org","pagead2.googlesyndication.com","static.cloudflareinsights.com","underscorejs.org","v3-cinemeta.strem.io"],"probeDirectMedia":true,"probeAllUrls":true,"maxProbes":6,"timeoutMs":4500,"minVodDurationSeconds":60,"blockedPathPatterns":["/analytics","/beacon.min.js","/cdn-cgi/rum","/collect","/gtag/js"],"implementationVersion":7});
/* NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5 */


/* NUVIO_HLS_RUNTIME_INTEGRITY_V1:128b76741346 */
;(function(g,config){
  "use strict";
  function clean(v){return String(v==null?"":v).replace(/^\uFEFF/,"").replace(/^ï»¿/,"").trim()}
  function hlsHint(stream){
    if(!stream||typeof stream!=="object")return false;
    var u=String(stream.url||"").toLowerCase(),t=String(stream.type||stream.format||"").toLowerCase();
    return /\.m3u8(?:[?#]|$)/i.test(u)||u.indexOf("/hls/")>=0||u.indexOf("/hls2/")>=0||t==="hls"||t==="m3u8"||t.indexOf("mpegurl")>=0;
  }
  function absolute(raw,base){try{return new URL(clean(raw),base).toString()}catch(_e){return ""}}
  function headerValue(stream,name){
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    var wanted=String(name||"").toLowerCase(),keys=Object.keys(src);
    for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===wanted)return clean(src[keys[i]]);
    return "";
  }
  function requestHeaders(stream,referer,range){
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    var out={};Object.keys(src).forEach(function(k){out[k]=String(src[k])});
    if(referer){
      var refKey=Object.keys(out).find(function(k){return k.toLowerCase()==="referer"}),currentRef=refKey?clean(out[refKey]):"";
      if(!currentRef||currentRef!==clean(referer)){
        Object.keys(out).forEach(function(k){var lower=k.toLowerCase();if(lower==="referer"||lower==="origin")delete out[k]});
        out.Referer=referer;try{out.Origin=new URL(referer).origin}catch(_e){}
      }
    }
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-4095";
    if(!out.Accept)out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,application/dash+xml,video/*,text/plain,*/*";
    return out;
  }
  async function fetchBounded(url,stream,referer,range){
    if(!g||typeof g.fetch!=="function")return {state:"unknown",reason:"fetch_unavailable"};
    var controller=typeof AbortController!=="undefined"?new AbortController():null;
    var timer=setTimeout(function(){try{if(controller)controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",redirect:"follow",headers:requestHeaders(stream,referer,range),signal:controller?controller.signal:void 0});
      if(!response)return {state:"unknown",reason:"no_response"};
      if(response.status===404||response.status===410)return {state:"invalid",reason:"http_"+response.status};
      if(!response.ok)return {state:"unknown",reason:"http_"+response.status};
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      return {state:"ok",response:response,url:String(response.url||url),contentType:contentType};
    }catch(error){return {state:"unknown",reason:error&&error.name==="AbortError"?"timeout":"network_error"}}
    finally{clearTimeout(timer)}
  }
  async function responseText(result){
    var response=result&&result.response;if(!response)return "";
    try{if(typeof response.text==="function")return clean(await response.text())}catch(_e){}
    try{if(typeof response.arrayBuffer==="function"){var ab=await response.arrayBuffer();return clean(new TextDecoder("utf-8").decode(ab))}}catch(_e){}
    try{if(response.body&&typeof response.body.getReader==="function"){var reader=response.body.getReader(),chunks=[],total=0;while(total<131072){var part=await reader.read();if(part&&part.value){chunks.push(part.value);total+=part.value.byteLength||part.value.length||0}if(!part||part.done)break}try{if(typeof reader.cancel==="function")await reader.cancel()}catch(_e){}var merged=new Uint8Array(total),offset=0;for(var i=0;i<chunks.length;i++){var value=chunks[i],take=Math.min(value.byteLength||value.length||0,total-offset);merged.set(value.subarray?value.subarray(0,take):value,offset);offset+=take;if(offset>=total)break}return clean(new TextDecoder("utf-8").decode(merged))}}catch(_e){}
    return "";
  }
  function playlistKind(body){
    var text=clean(body);if(!/^#EXTM3U(?:\s|$)/i.test(text))return "invalid";
    if(/#EXT-X-STREAM-INF\s*:/i.test(text))return "master";
    if(/#EXTINF\s*:/i.test(text)||/#EXT-X-PART\s*:/i.test(text)||/#EXT-X-MAP\s*:/i.test(text)){
      var lines=text.split(/\r?\n/).map(function(v){return v.trim()}).filter(Boolean);
      if(lines.some(function(v){return v.charAt(0)!=="#"}))return "media";
    }
    return "header_only";
  }
  function variantUris(body,base){
    var lines=clean(body).split(/\r?\n/),out=[];
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i]))continue;
      for(var j=i+1;j<lines.length;j++){
        var candidate=clean(lines[j]);if(!candidate)continue;if(candidate.charAt(0)==="#")continue;
        var u=absolute(candidate,base);if(u&&out.indexOf(u)<0)out.push(u);break;
      }
      if(out.length>=config.maxChildren)break;
    }
    return out;
  }
  function audioUris(body,base){
    var out=[],lines=clean(body).split(/\r?\n/);
    lines.forEach(function(line){
      if(!/^#EXT-X-MEDIA\s*:/i.test(line)||!/TYPE\s*=\s*AUDIO/i.test(line))return;
      var m=line.match(/URI\s*=\s*"([^"]+)"/i)||line.match(/URI\s*=\s*([^,\s]+)/i);
      var u=m&&absolute(m[1],base);if(u&&out.indexOf(u)<0)out.push(u);
    });
    return out.slice(0,config.maxChildren);
  }
  async function validateChild(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,false);if(result.state!=="ok")return result.state;
    var body=await responseText(result),kind=playlistKind(body);return kind==="media"||kind==="master"?"valid":"invalid";
  }
  async function inspectHls(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,false);
    if(result.state!=="ok")return {state:result.state,reason:result.reason||"fetch_failed",result:result};
    var ct=result.contentType||"";
    if(/^video\//i.test(ct))return {state:"direct",format:ct.indexOf("webm")>=0?"webm":"mp4",url:result.url,result:result};
    var body=await responseText(result),kind=playlistKind(body);
    if(kind==="invalid"||kind==="header_only")return {state:"invalid",kind:kind,body:body,result:result};
    if(kind==="media")return {state:"valid",kind:kind,url:result.url,body:body,result:result};

    var variants=variantUris(body,result.url||url),audio=audioUris(body,result.url||url);
    if(!variants.length)return {state:"invalid",kind:"master_without_variants",body:body,result:result};
    var variantState="invalid";
    for(var i=0;i<variants.length;i++){
      var s=await validateChild(variants[i],stream,result.url||referer);if(s==="valid"){variantState="valid";break}if(s==="unknown")variantState="unknown";
    }
    if(variantState!=="valid")return {state:variantState,kind:"master_child_"+variantState,body:body,result:result};
    if(audio.length){
      var audioState="invalid";
      for(var j=0;j<audio.length;j++){
        var a=await validateChild(audio[j],stream,result.url||referer);if(a==="valid"){audioState="valid";break}if(a==="unknown")audioState="unknown";
      }
      if(audioState!=="valid")return {state:audioState,kind:"audio_child_"+audioState,body:body,result:result};
    }
    return {state:"valid",kind:"master",url:result.url,body:body,result:result};
  }
  function normalizedText(text){
    return clean(text).replace(/\\u002[fF]/g,"/").replace(/\\\//g,"/").replace(/&amp;/g,"&");
  }
  function candidateUrls(text,base){
    var body=normalizedText(text),out=[],seen={};
    function add(raw){
      var value=clean(raw).replace(/^['"]|['"]$/g,"");if(!value||/^javascript:|^data:/i.test(value))return;
      var u=absolute(value,base);if(!/^https?:\/\//i.test(u)||seen[u])return;seen[u]=1;out.push(u);
    }
    var patterns=[
      /(?:src|href|data-src|data-url|data-file|data-player|data-embed|file|source|url|playlist|hls|stream|embedUrl|embed_url)\s*[:=]\s*["']([^"']+)["']/gi,
      /(https?:\/\/[^"'<>\s\\]+)/gi,
      /["']([^"']+\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#][^"']*)?)["']/gi
    ],m;
    for(var i=0;i<patterns.length&&out.length<config.maxRecoveryCandidates;i++){
      patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null&&out.length<config.maxRecoveryCandidates)add(m[1]);
    }
    return out;
  }
  function mediaHint(url){return /\.m3u8(?:[?#]|$)|\/hls2?\//i.test(url)?"hls":/\.mpd(?:[?#]|$)/i.test(url)?"dash":/\.(?:mp4|mkv|webm)(?:[?#]|$)/i.test(url)?"direct":"page"}
  function cloneRecovered(stream,url,format,referer){
    var row=Object.assign({},stream,{url:url}),headers={};
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};Object.keys(src).forEach(function(k){headers[k]=String(src[k])});
    if(referer){
      var refKey=Object.keys(headers).find(function(k){return k.toLowerCase()==="referer"}),currentRef=refKey?clean(headers[refKey]):"";
      if(!currentRef||currentRef!==clean(referer)){
        Object.keys(headers).forEach(function(k){var lower=k.toLowerCase();if(lower==="referer"||lower==="origin")delete headers[k]});
        headers.Referer=referer;try{headers.Origin=new URL(referer).origin}catch(_e){}
      }
    }
    if(Object.keys(headers).length)row.headers=headers;
    if(format==="hls"){row.type="hls";if("format" in row)row.format="m3u8"}
    else if(format==="dash"){row.type="dash";if("format" in row)row.format="mpd"}
    else if(format){row.type=format;if("format" in row)row.format=format}
    return row;
  }
  async function probeDirect(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,true);if(result.state!=="ok")return null;
    var ct=result.contentType||"";
    if(/^video\//i.test(ct))return cloneRecovered(stream,result.url,ct.indexOf("webm")>=0?"webm":"mp4",referer);
    if(/(?:application\/dash\+xml|application\/xml|text\/xml)/i.test(ct)||/\.mpd(?:[?#]|$)/i.test(result.url)){
      var dash=await responseText(result);if(/<MPD(?:\s|>)/i.test(dash))return cloneRecovered(stream,result.url,"dash",referer);
    }
    if(/mpegurl/i.test(ct)||/\.m3u8(?:[?#]|$)/i.test(result.url)){
      var hls=await inspectHls(result.url,stream,referer);if(hls.state==="valid")return cloneRecovered(stream,hls.url||result.url,"hls",referer);
    }
    return null;
  }
  async function recover(stream,inspection){
    var queue=[],seen={},pages=0;
    function enqueue(url,referer){var u=absolute(url,referer||String(stream.url||""));if(!/^https?:\/\//i.test(u)||seen[u]||u===String(stream.url||""))return;seen[u]=1;queue.push({url:u,referer:referer||""})}
    var base=inspection&&inspection.result&&inspection.result.url||String(stream.url||"");
    candidateUrls(inspection&&inspection.body||"",base).forEach(function(u){enqueue(u,base)});
    var outerReferer=headerValue(stream,"referer");
    [stream&&stream.playerUrl,stream&&stream.embedUrl,stream&&stream.pageUrl,stream&&stream.sourceUrl,stream&&stream.referrer,stream&&stream.referer].forEach(function(u){if(u)enqueue(u,outerReferer||base)});
    if(outerReferer)enqueue(outerReferer,"");
    while(queue.length&&pages<config.maxRecoveryPages){
      var item=queue.shift(),kind=mediaHint(item.url);
      if(kind==="hls"){
        var hls=await inspectHls(item.url,stream,item.referer);if(hls.state==="valid")return cloneRecovered(stream,hls.url||item.url,"hls",item.referer);if(hls.state==="direct")return cloneRecovered(stream,hls.url||item.url,hls.format||"mp4",item.referer);
        candidateUrls(hls.body||"",hls.result&&hls.result.url||item.url).forEach(function(u){enqueue(u,hls.result&&hls.result.url||item.url)});continue;
      }
      if(kind==="direct"||kind==="dash"){
        var direct=await probeDirect(item.url,stream,item.referer);if(direct)return direct;continue;
      }
      pages++;
      var page=await fetchBounded(item.url,stream,item.referer,false);if(page.state!=="ok")continue;
      var ct=page.contentType||"";
      if(/^video\//i.test(ct))return cloneRecovered(stream,page.url,ct.indexOf("webm")>=0?"webm":"mp4",item.referer);
      var body=await responseText(page);
      if(/^#EXTM3U(?:\s|$)/i.test(body)){
        var pageHls=await inspectHls(page.url,stream,item.referer);if(pageHls.state==="valid")return cloneRecovered(stream,pageHls.url||page.url,"hls",item.referer);
      }
      if(/<MPD(?:\s|>)/i.test(body))return cloneRecovered(stream,page.url,"dash",item.referer);
      candidateUrls(body,page.url||item.url).forEach(function(u){enqueue(u,page.url||item.url)});
    }
    return null;
  }
  async function validateOrRecover(stream){
    var inspection=await inspectHls(String(stream.url||""),stream,headerValue(stream,"referer"));
    if(inspection.state==="valid"||inspection.state==="unknown")return stream;
    if(inspection.state==="direct")return cloneRecovered(stream,inspection.url||String(stream.url||""),inspection.format||"mp4",headerValue(stream,"referer"));
    var recovered=await recover(stream,inspection);if(recovered)return recovered;
    return null;
  }
  async function filterRows(value){
    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;
    if(!rows)return value;
    var checks=await Promise.all(rows.map(async function(stream){
      if(!hlsHint(stream))return stream;
      var output=await validateOrRecover(stream);
      if(!output){
        try{console.warn("[Nuvio HLS integrity] rejected malformed playlist after bounded recovery",String(stream&&stream.url||"").slice(0,180))}catch(_e){}
      }
      return output;
    }));
    var filtered=checks.filter(Boolean);
    if(Array.isArray(value))return filtered;
    var copy=Object.assign({},value);copy.streams=filtered;return copy;
  }
  function wrap(target,key){
    if(!target||typeof target[key]!=="function"||target[key].__nuvioHlsIntegrityV1)return false;
    var native=target[key];
    var wrapped=async function(){return filterRows(await native.apply(this,arguments))};
    try{Object.defineProperty(wrapped,"__nuvioHlsIntegrityV1",{value:true})}catch(_e){wrapped.__nuvioHlsIntegrityV1=true}
    target[key]=wrapped;return true;
  }
  function install(){
    var done=false;
    try{done=wrap(g,"getStreams")||done}catch(_e){}
    try{if(typeof module!=="undefined"&&module&&module.exports){done=wrap(module.exports,"getStreams")||done;done=wrap(module.exports,"streams")||done}}catch(_e){}
    try{if(typeof exports!=="undefined")done=wrap(exports,"getStreams")||done}catch(_e){}
    return done;
  }
  install();
})(typeof globalThis!=="undefined"?globalThis:this,{"timeoutMs":6500,"maxChildren":2,"maxRecoveryPages":4,"maxRecoveryCandidates":12,"implementationRevision":"recovery-first-v3"});
/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:1a320c9759f2 */
;(function(g,c){"use strict";
var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";
function s(v){return String(v==null?"":v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return""}}
function unique(values){var out=[],seen={};(values||[]).forEach(function(v){v=s(v).replace(/\s*\(\d{4}\)\s*$/,"");var k=norm(v);if(v&&k&&!seen[k]){seen[k]=1;out.push(v)}});return out}
function args(a){var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{id:first,mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};var raw=s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id||first),m;q.mediaType=s(q.mediaType||q.type||q.category||"movie").toLowerCase();q.season=Number(q.season)||0;q.episode=Number(q.episode)||0;q.tmdbId="";q.imdbId="";m=/^(?:imdb:)?(tt\d+)(?::(\d+):(?:(\d+)))?$/i.exec(raw);if(m){q.imdbId=m[1].toLowerCase();if(!q.season&&m[2])q.season=Number(m[2])||0;if(!q.episode&&m[3])q.episode=Number(m[3])||0}else{raw=raw.replace(/^tmdb:/i,"");m=/^(\d+)(?::(\d+):(?:(\d+)))?$/.exec(raw);if(m){q.tmdbId=m[1];if(!q.season&&m[2])q.season=Number(m[2])||0;if(!q.episode&&m[3])q.episode=Number(m[3])||0}}return q}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
async function request(url,json,referer){try{var h={Accept:json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"};if(referer){h.Referer=referer;try{h.Origin=new URL(referer).origin}catch(_){}}var r=await g.fetch(url,{headers:h,redirect:"follow",signal:timeout()});if(!r||!r.ok)return null;return{url:s(r.url||url),body:json?await r.json():await r.text(),type:r.headers&&r.headers.get?r.headers.get("content-type"):""}}catch(_){return null}}
function kindFor(q){if(q.mediaType==="tv")return"tv";if(q.mediaType==="anime"&&q.season&&q.episode)return"tv";return"movie"}
async function resolveIdentity(q,kind){if(/^\d+$/.test(q.tmdbId||""))return{tmdbId:q.tmdbId,imdbId:q.imdbId||"",seed:null};if(!/^tt\d+$/i.test(q.imdbId||""))return{tmdbId:"",imdbId:q.imdbId||"",seed:null};var r=await request("https://api.themoviedb.org/3/find/"+encodeURIComponent(q.imdbId)+"?api_key="+TMDB_KEY+"&external_source=imdb_id",true);if(!r||!r.body)return{tmdbId:"",imdbId:q.imdbId,seed:null};var preferred=kind==="tv"?(r.body.tv_results||[]):(r.body.movie_results||[]),other=kind==="tv"?(r.body.movie_results||[]):(r.body.tv_results||[]),seed=(preferred[0]||other[0]||null);return{tmdbId:seed&&seed.id?String(seed.id):"",imdbId:q.imdbId,seed:seed}}
async function meta(q){var titles=unique([q.title,q.name,q.label,q.settings&&q.settings.title]),year=Number(q.year||q.settings&&q.settings.year)||0,kind=kindFor(q),identity=await resolveIdentity(q,kind);if(identity.seed){var sd=identity.seed;titles=unique(titles.concat([sd.title,sd.name,sd.original_title,sd.original_name]));var seedDate=s(sd.release_date||sd.first_air_date);year=year||Number(seedDate.slice(0,4))||0}if(identity.tmdbId){var urls=["https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"?api_key="+TMDB_KEY+"&language=fr-FR","https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"?api_key="+TMDB_KEY+"&language=en-US"];for(var i=0;i<urls.length;i++){var r=await request(urls[i],true);if(r&&r.body){var d=r.body;titles=unique(titles.concat([d.title,d.name,d.original_title,d.original_name]));var date=s(d.release_date||d.first_air_date);year=year||Number(date.slice(0,4))||0}}var alt=await request("https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"/alternative_titles?api_key="+TMDB_KEY,true);if(alt&&alt.body){var rows=alt.body.titles||alt.body.results||[],priority={FR:100,US:90,GB:80,CA:70,DK:60};rows=rows.slice().sort(function(a,b){return(priority[String(b&&b.iso_3166_1||"").toUpperCase()]||0)-(priority[String(a&&a.iso_3166_1||"").toUpperCase()]||0)});rows.slice(0,50).forEach(function(x){if(x&&x.title)titles.push(x.title)});titles=unique(titles)}}return{titles:titles.slice(0,c.maxAliases),year:year,tmdbId:identity.tmdbId,imdbId:identity.imdbId}}
function tokens(v){var noise={the:1,a:1,an:1,le:1,la:1,les:1,un:1,une:1,de:1,des:1,du:1,and:1,et:1,film:1,movie:1,streaming:1,watch:1,voir:1,regarder:1};return norm(v).split(" ").filter(function(x){return x.length>1&&!noise[x]&&!/^\d{4}$/.test(x)})}
function aliasScore(text,m){var n=norm(text),best=-1;(m.titles||[]).forEach(function(t){var nt=norm(t),want=tokens(t);if(!want.length)return;var score=n.indexOf(nt)>=0?120:0;if(!score&&want.every(function(x){return n.indexOf(x)>=0}))score=90;if(score>best)best=score});if(best<0)return-1;var years=n.match(/\b(?:19|20)\d{2}\b/g)||[];if(m.year&&years.length&&years.indexOf(String(m.year))<0)return-1;if(m.year&&n.indexOf(String(m.year))>=0)best+=15;return best}
function links(html,base,m){var rows=[],seen={},re=/<a\b([^>]*)href=["']([^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi,x;while((x=re.exec(String(html||"")))!==null){var u=abs(x[2],base),label=s(x[1])+" "+s(x[3])+" "+s(x[4]).replace(/<[^>]+>/g," ");if(!u||seen[u])continue;seen[u]=1;var score=aliasScore(label+" "+u,m);if(score>=90)rows.push({url:u,score:score})}return rows.sort(function(a,b){return b.score-a.score}).slice(0,c.maxCandidates)}
function mediaish(u){return/(?:\.m3u8|\.mpd|\.mp4|\.mkv|\.webm)(?:[?#]|$)|\/(?:embed|player|watch|stream|video)(?:[/?#.-]|$)|\/e\//i.test(u)}
function extractPlayers(html,base,q){var text=String(html||"").replace(/\\\//g,"/"),out=[],seen={};function add(v){var u=abs(v,base);if(!u||seen[u]||!/^https?:\/\//i.test(u)||!mediaish(u))return;seen[u]=1;out.push(u)}var scoped=text;if((q.mediaType==="tv"||q.mediaType==="anime")&&q.season&&q.episode){var patterns=[new RegExp("s(?:aison|eason)?[ ._-]*0?"+q.season+"[ ._-]*e(?:p(?:isode)?)?[ ._-]*0?"+q.episode,"i"),new RegExp("(?:episode|ep)[ ._-]*0?"+q.episode,"i")],chunks=text.split(/(?=<[^>]+(?:episode|season|saison|data-ep))/i).filter(function(x){return patterns.some(function(p){return p.test(x)})});if(chunks.length)scoped=chunks.join("\n");else return[]}var patterns2=[/(?:src|href|data-src|data-url|data-embed|data-player|data-video|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi],m;for(var i=0;i<patterns2.length;i++){patterns2[i].lastIndex=0;while((m=patterns2[i].exec(scoped))!==null){add(m[1]);if(out.length>=c.maxPlayers)return out}}return out}
function rows(urls,m,page){return urls.slice(0,c.maxPlayers).map(function(u,i){var out={name:c.providerName+(urls.length>1?" #"+(i+1):""),title:c.providerName+" - "+(m.titles[0]||"Media"),url:u,quality:"Unknown",headers:{Referer:page,Origin:(function(){try{return new URL(page).origin}catch(_){return c.baseUrl}})()}};if(c.languageHint)out.language=c.languageHint;if(/\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)/i.test(u))out.isDirect=true;return out})}
function idEvidence(body,m){var text=String(body||"");if(m.tmdbId&&new RegExp("tmdb[^0-9]{0,24}"+String(m.tmdbId),"i").test(text))return true;if(m.imdbId&&new RegExp("imdb[^a-z0-9]{0,24}"+String(m.imdbId),"i").test(text))return true;return false}
async function recover(q,knownMeta,deadline){if(["movie","tv","anime"].indexOf(q.mediaType)<0||Date.now()>=deadline)return[];var m=knownMeta||await meta(q);if(!m.titles.length||Date.now()>=deadline)return[];var guessed=[],found=[],searches=[];m.titles.forEach(function(t){guessed.push(c.baseUrl+"/"+slug(t));searches.push(c.baseUrl+"/?s="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?q="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?query="+encodeURIComponent(t))});for(var i=0;i<searches.length&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){var sr=await request(searches[i],false,c.baseUrl+"/");if(sr)found=found.concat(links(sr.body,sr.url,m).map(function(x){return x.url}))}var candidates=unique(found.concat(guessed)).slice(0,c.maxCandidates);for(var j=0;j<candidates.length&&Date.now()<deadline;j++){var page=await request(candidates[j],false,c.baseUrl+"/");if(!page)continue;var identity=aliasScore(page.url+" "+String(page.body||"").slice(0,180000),m);if(identity<90&&!idEvidence(page.body,m))continue;var p=extractPlayers(page.body,page.url,q);if(p.length)return rows(p,m,page.url)}return[]}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function identityLabel(row){return s(row&&((row.title||row.description||row.filename||row.name)||""))}
function nativeIdentityReject(row,q,m){var label=identityLabel(row);if(!label)return false;var se=/(?:^|\D)s(?:eason|aison)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?:\D|$)/i.exec(label)||/(?:season|saison)\s*0*(\d{1,3})[^\d]{0,12}(?:episode|ep)\s*0*(\d{1,4})/i.exec(label);if(q.mediaType==="movie"&&se)return true;if(se&&(q.mediaType==="tv"||q.mediaType==="anime")){var ss=Number(se[1])||0,ee=Number(se[2])||0;if((q.season&&ss&&ss!==q.season)||(q.episode&&ee&&ee!==q.episode))return true}if(aliasScore(label,m)>=90)return false;var tech={server:1,serveur:1,stream:1,streaming:1,source:1,mirror:1,direct:1,download:1,telecharger:1,play:1,player:1,vcloud:1,hubcloud:1,file:1,video:1,quality:1,web:1,dl:1,webrip:1,webdl:1,bluray:1,remux:1,hdr:1,dv:1,dolby:1,atmos:1,aac:1,ac3:1,eac3:1,ddp:1,x264:1,x265:1,h264:1,h265:1,hevc:1,av1:1,multi:1,vf:1,vff:1,vostfr:1,vo:1,french:1,english:1,truefrench:1,hd:1,uhd:1,fhd:1,sd:1};var providerTokens=tokens(c.providerName),expected={};(m.titles||[]).forEach(function(t){tokens(t).forEach(function(x){expected[x]=1})});var words=tokens(label).filter(function(x){return !tech[x]&&providerTokens.indexOf(x)<0&&!/^\d{3,4}p$/.test(x)});if(words.length<2)return false;for(var i=0;i<words.length;i++)if(expected[words[i]])return false;return true}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalCatalogueAliasV2)return false;var native=o[k];var wrap=async function(){var q=args(arguments),v,deadline=Date.now()+c.budgetMs;try{v=await native.apply(this,arguments)}catch(_){v=[]}var x=slot(v),m=null;if(x&&x.list.length){try{m=await meta(q)}catch(_){m=null}if(!m||!m.titles||!m.titles.length)return v;var kept=x.list.filter(function(row){return !nativeIdentityReject(row,q,m)});if(kept.length)return rebuild(v,x,kept)}var recovered=await recover(q,m,deadline);if(!recovered.length)return x?rebuild(v,x,[]):v;return x?rebuild(v,x,recovered):recovered};wrap.__nuvioGlobalCatalogueAliasV2=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"baseUrl":"https://4khdhub.one","providerName":"4khdhub","maxAliases":8,"maxCandidates":8,"maxPlayers":8,"timeoutMs":7000,"budgetMs":45000,"languageHint":"","implementationRevision":"native-identity-budget-v2"});
/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:35bdb2c4cf66 */
;(function(g,c){"use strict";
var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";
function s(v){return String(v==null?"":v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return""}}
function unique(values){var out=[],seen={};(values||[]).forEach(function(v){v=s(v).replace(/\s*\(\d{4}\)\s*$/,"");var k=norm(v);if(v&&k&&!seen[k]){seen[k]=1;out.push(v)}});return out}
function args(a){var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{id:first,mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};var raw=s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id||first),m;q.mediaType=s(q.mediaType||q.type||q.category||"movie").toLowerCase();q.season=Number(q.season)||0;q.episode=Number(q.episode)||0;q.tmdbId="";q.imdbId="";m=/^(?:imdb:)?(tt\d+)(?::(\d+):(?:(\d+)))?$/i.exec(raw);if(m){q.imdbId=m[1].toLowerCase();if(!q.season&&m[2])q.season=Number(m[2])||0;if(!q.episode&&m[3])q.episode=Number(m[3])||0}else{raw=raw.replace(/^tmdb:/i,"");m=/^(\d+)(?::(\d+):(?:(\d+)))?$/.exec(raw);if(m){q.tmdbId=m[1];if(!q.season&&m[2])q.season=Number(m[2])||0;if(!q.episode&&m[3])q.episode=Number(m[3])||0}}return q}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
async function request(url,json,referer){try{var h={Accept:json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"};if(referer){h.Referer=referer;try{h.Origin=new URL(referer).origin}catch(_){}}var r=await g.fetch(url,{headers:h,redirect:"follow",signal:timeout()});if(!r||!r.ok)return null;return{url:s(r.url||url),body:json?await r.json():await r.text(),type:r.headers&&r.headers.get?r.headers.get("content-type"):""}}catch(_){return null}}
function kindFor(q){if(q.mediaType==="tv")return"tv";if(q.mediaType==="anime"&&q.season&&q.episode)return"tv";return"movie"}
async function resolveIdentity(q,kind){if(/^\d+$/.test(q.tmdbId||""))return{tmdbId:q.tmdbId,imdbId:q.imdbId||"",seed:null};if(!/^tt\d+$/i.test(q.imdbId||""))return{tmdbId:"",imdbId:q.imdbId||"",seed:null};var r=await request("https://api.themoviedb.org/3/find/"+encodeURIComponent(q.imdbId)+"?api_key="+TMDB_KEY+"&external_source=imdb_id",true);if(!r||!r.body)return{tmdbId:"",imdbId:q.imdbId,seed:null};var preferred=kind==="tv"?(r.body.tv_results||[]):(r.body.movie_results||[]),other=kind==="tv"?(r.body.movie_results||[]):(r.body.tv_results||[]),seed=(preferred[0]||other[0]||null);return{tmdbId:seed&&seed.id?String(seed.id):"",imdbId:q.imdbId,seed:seed}}
async function meta(q){var titles=unique([q.title,q.name,q.label,q.settings&&q.settings.title]),year=Number(q.year||q.settings&&q.settings.year)||0,kind=kindFor(q),identity=await resolveIdentity(q,kind);if(identity.seed){var sd=identity.seed;titles=unique(titles.concat([sd.title,sd.name,sd.original_title,sd.original_name]));var seedDate=s(sd.release_date||sd.first_air_date);year=year||Number(seedDate.slice(0,4))||0}if(identity.tmdbId){var urls=["https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"?api_key="+TMDB_KEY+"&language=fr-FR","https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"?api_key="+TMDB_KEY+"&language=en-US"];for(var i=0;i<urls.length;i++){var r=await request(urls[i],true);if(r&&r.body){var d=r.body;titles=unique(titles.concat([d.title,d.name,d.original_title,d.original_name]));var date=s(d.release_date||d.first_air_date);year=year||Number(date.slice(0,4))||0}}var alt=await request("https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"/alternative_titles?api_key="+TMDB_KEY,true);if(alt&&alt.body){var rows=alt.body.titles||alt.body.results||[],priority={FR:100,US:90,GB:80,CA:70,DK:60};rows=rows.slice().sort(function(a,b){return(priority[String(b&&b.iso_3166_1||"").toUpperCase()]||0)-(priority[String(a&&a.iso_3166_1||"").toUpperCase()]||0)});rows.slice(0,50).forEach(function(x){if(x&&x.title)titles.push(x.title)});titles=unique(titles)}}return{titles:titles.slice(0,c.maxAliases),year:year,tmdbId:identity.tmdbId,imdbId:identity.imdbId}}
function tokens(v){var noise={the:1,a:1,an:1,le:1,la:1,les:1,un:1,une:1,de:1,des:1,du:1,and:1,et:1,film:1,movie:1,streaming:1,watch:1,voir:1,regarder:1};return norm(v).split(" ").filter(function(x){return x.length>1&&!noise[x]&&!/^\d{4}$/.test(x)})}
function aliasScore(text,m){var n=norm(text),best=-1;(m.titles||[]).forEach(function(t){var nt=norm(t),want=tokens(t);if(!want.length)return;var score=n.indexOf(nt)>=0?120:0;if(!score&&want.every(function(x){return n.indexOf(x)>=0}))score=90;if(score>best)best=score});if(best<0)return-1;var years=n.match(/\b(?:19|20)\d{2}\b/g)||[];if(m.year&&years.length&&years.indexOf(String(m.year))<0)return-1;if(m.year&&n.indexOf(String(m.year))>=0)best+=15;return best}
function links(html,base,m){var rows=[],seen={},re=/<a\b([^>]*)href=["']([^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi,x;while((x=re.exec(String(html||"")))!==null){var u=abs(x[2],base),label=s(x[1])+" "+s(x[3])+" "+s(x[4]).replace(/<[^>]+>/g," ");if(!u||seen[u])continue;seen[u]=1;var score=aliasScore(label+" "+u,m);if(score>=90)rows.push({url:u,score:score})}return rows.sort(function(a,b){return b.score-a.score}).slice(0,c.maxCandidates)}
function mediaish(u){return/(?:\.m3u8|\.mpd|\.mp4|\.mkv|\.webm)(?:[?#]|$)|\/(?:embed|player|watch|stream|video)(?:[/?#.-]|$)|\/e\//i.test(u)}
function extractPlayers(html,base,q){var text=String(html||"").replace(/\\\//g,"/"),out=[],seen={};function add(v){var u=abs(v,base);if(!u||seen[u]||!/^https?:\/\//i.test(u)||!mediaish(u))return;seen[u]=1;out.push(u)}var scoped=text;if((q.mediaType==="tv"||q.mediaType==="anime")&&q.season&&q.episode){var patterns=[new RegExp("s(?:aison|eason)?[ ._-]*0?"+q.season+"[ ._-]*e(?:p(?:isode)?)?[ ._-]*0?"+q.episode,"i"),new RegExp("(?:episode|ep)[ ._-]*0?"+q.episode,"i")],chunks=text.split(/(?=<[^>]+(?:episode|season|saison|data-ep))/i).filter(function(x){return patterns.some(function(p){return p.test(x)})});if(chunks.length)scoped=chunks.join("\n");else return[]}var patterns2=[/(?:src|href|data-src|data-url|data-embed|data-player|data-video|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi],m;for(var i=0;i<patterns2.length;i++){patterns2[i].lastIndex=0;while((m=patterns2[i].exec(scoped))!==null){add(m[1]);if(out.length>=c.maxPlayers)return out}}return out}
function rows(urls,m,page){return urls.slice(0,c.maxPlayers).map(function(u,i){var out={name:c.providerName+(urls.length>1?" #"+(i+1):""),title:c.providerName+" - "+(m.titles[0]||"Media"),url:u,quality:"Unknown",headers:{Referer:page,Origin:(function(){try{return new URL(page).origin}catch(_){return c.baseUrl}})()}};if(c.languageHint)out.language=c.languageHint;if(/\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)/i.test(u))out.isDirect=true;return out})}
function idEvidence(body,m){var text=String(body||"");if(m.tmdbId&&new RegExp("tmdb[^0-9]{0,24}"+String(m.tmdbId),"i").test(text))return true;if(m.imdbId&&new RegExp("imdb[^a-z0-9]{0,24}"+String(m.imdbId),"i").test(text))return true;return false}
async function recover(q,knownMeta,deadline){if(["movie","tv","anime"].indexOf(q.mediaType)<0||Date.now()>=deadline)return[];var m=knownMeta||await meta(q);if(!m.titles.length||Date.now()>=deadline)return[];var guessed=[],found=[],searches=[];m.titles.forEach(function(t){guessed.push(c.baseUrl+"/"+slug(t));searches.push(c.baseUrl+"/?s="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?q="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?query="+encodeURIComponent(t))});for(var i=0;i<searches.length&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){var sr=await request(searches[i],false,c.baseUrl+"/");if(sr)found=found.concat(links(sr.body,sr.url,m).map(function(x){return x.url}))}var candidates=unique(found.concat(guessed)).slice(0,c.maxCandidates);for(var j=0;j<candidates.length&&Date.now()<deadline;j++){var page=await request(candidates[j],false,c.baseUrl+"/");if(!page)continue;var identity=aliasScore(page.url+" "+String(page.body||"").slice(0,180000),m);if(identity<90&&!idEvidence(page.body,m))continue;var p=extractPlayers(page.body,page.url,q);if(p.length)return rows(p,m,page.url)}return[]}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function identityLabel(row){var label=s(row&&((row.title||row.description||row.filename||row.name)||"")),base="";try{base=decodeURIComponent(new URL(s(row&&row.url)).pathname.split("/").filter(Boolean).pop()||"").replace(/\.(?:m3u8|mpd|mp4|mkv|webm|m4v|ts)$/i,"")}catch(_){}var human=tokens(base).filter(function(x){return/^[a-z]{3,}$/i.test(x)});return label+(human.length>=2?" "+base:"")}
function nativeIdentityReject(row,q,m){var label=identityLabel(row);if(!label)return false;var se=/(?:^|\D)s(?:eason|aison)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?:\D|$)/i.exec(label)||/(?:season|saison)\s*0*(\d{1,3})[^\d]{0,12}(?:episode|ep)\s*0*(\d{1,4})/i.exec(label);if(q.mediaType==="movie"&&se)return true;if(se&&(q.mediaType==="tv"||q.mediaType==="anime")){var ss=Number(se[1])||0,ee=Number(se[2])||0;if((q.season&&ss&&ss!==q.season)||(q.episode&&ee&&ee!==q.episode))return true}if(aliasScore(label,m)>=90)return false;var tech={server:1,serveur:1,stream:1,streaming:1,source:1,mirror:1,direct:1,download:1,telecharger:1,play:1,player:1,vcloud:1,hubcloud:1,file:1,video:1,quality:1,web:1,dl:1,webrip:1,webdl:1,bluray:1,remux:1,hdr:1,dv:1,dolby:1,atmos:1,aac:1,ac3:1,eac3:1,ddp:1,x264:1,x265:1,h264:1,h265:1,hevc:1,av1:1,multi:1,vf:1,vff:1,vostfr:1,vo:1,french:1,english:1,truefrench:1,hd:1,uhd:1,fhd:1,sd:1};var providerTokens=tokens(c.providerName),expected={};(m.titles||[]).forEach(function(t){tokens(t).forEach(function(x){expected[x]=1})});var words=tokens(label).filter(function(x){return !tech[x]&&providerTokens.indexOf(x)<0&&!/^\d{3,4}p$/.test(x)});if(words.length<2)return false;for(var i=0;i<words.length;i++)if(expected[words[i]])return false;return true}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalCatalogueAliasV2)return false;var native=o[k];var wrap=async function(){var q=args(arguments),v,deadline=Date.now()+c.budgetMs;try{v=await native.apply(this,arguments)}catch(_){v=[]}var x=slot(v),m=null;if(x&&x.list.length){try{m=await meta(q)}catch(_){m=null}if(!m||!m.titles||!m.titles.length)return v;var kept=x.list.filter(function(row){return !nativeIdentityReject(row,q,m)});if(kept.length)return rebuild(v,x,kept)}var recovered=await recover(q,m,deadline);if(!recovered.length)return x?rebuild(v,x,[]):v;return x?rebuild(v,x,recovered):recovered};wrap.__nuvioGlobalCatalogueAliasV2=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"baseUrl":"https://4khdhub.one","providerName":"4khdhub","maxAliases":8,"maxCandidates":8,"maxPlayers":8,"timeoutMs":7000,"budgetMs":45000,"languageHint":"","implementationRevision":"native-media-filename-identity-v3"});
