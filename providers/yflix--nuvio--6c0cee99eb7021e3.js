// YFlix Scraper for Nuvio Local Scrapers
// React Native compatible version - Uses enc-dec.app database for accurate matching

// Headers for requests
const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
  'Connection': 'keep-alive'
};

const API = 'https://enc-dec.app/api';
const DB_API = 'https://enc-dec.app/db/flix';
const YFLIX_AJAX = 'https://1moviesz.to/ajax';

// Debug helpers
function createRequestId() {
  try {
    const rand = Math.random().toString(36).slice(2, 8);
    const ts = Date.now().toString(36).slice(-6);
    return `${rand}${ts}`;
  } catch (e) {
    return String(Date.now());
  }
}

function logRid(rid, msg, extra) {
  try {
    if (extra !== undefined) {
      console.log(`[YFlix][rid:${rid}] ${msg}`, extra);
    } else {
      console.log(`[YFlix][rid:${rid}] ${msg}`);
    }
  } catch (e) {
    // ignore logging errors
  }
}

// Helper functions for HTTP requests (React Native compatible)
function getText(url) {
  return fetch(url, { headers: HEADERS })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.text();
    });
}

function getJson(url) {
  return fetch(url, { headers: HEADERS })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    });
}

function postJson(url, jsonBody, extraHeaders) {
  const body = JSON.stringify(jsonBody);
  const headers = Object.assign(
    {},
    HEADERS,
    { 'Content-Type': 'application/json', 'Content-Length': body.length.toString() },
    extraHeaders || {}
  );

  return fetch(url, {
    method: 'POST',
    headers,
    body
  }).then(response => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  });
}

// Enc/Dec helpers
function encrypt(text) {
  return getJson(`${API}/enc-movies-flix?text=${encodeURIComponent(text)}`).then(j => j.result);
}

function decrypt(text) {
  return postJson(`${API}/dec-movies-flix`, { text: text }).then(j => j.result);
}

function parseHtml(html) {
  return postJson(`${API}/parse-html`, { text: html }).then(j => j.result);
}

function decryptRapidMedia(embedUrl) {
  const media = embedUrl.replace('/e/', '/media/').replace('/e2/', '/media/');
  return getJson(media)
    .then((mediaJson) => {
      const encrypted = mediaJson && mediaJson.result;
      if (!encrypted) throw new Error('No encrypted media result from RapidShare media endpoint');
      return postJson(`${API}/dec-rapid`, { text: encrypted, agent: HEADERS['User-Agent'] });
    })
    .then(j => j.result);
}

// Database lookup - replaces title matching
function findInDatabase(tmdbId, mediaType) {
  const type = mediaType === 'movie' ? 'movie' : 'tv';
  const url = `${DB_API}/find?tmdb_id=${tmdbId}&type=${type}`;

  return getJson(url)
    .then(results => {
      if (!results || results.length === 0) {
        return null;
      }
      return results[0]; // Return first match
    });
}

// HLS helpers (Promise-based)
function parseQualityFromM3u8(m3u8Text, baseUrl = '') {
  const streams = [];
  const lines = m3u8Text.split(/\r?\n/);
  let currentInfo = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith('#EXT-X-STREAM-INF')) {
      const bwMatch = line.match(/BANDWIDTH=\s*(\d+)/i);
      const resMatch = line.match(/RESOLUTION=\s*(\d+)x(\d+)/i);

      currentInfo = {
        bandwidth: bwMatch ? parseInt(bwMatch[1]) : null,
        width: resMatch ? parseInt(resMatch[1]) : null,
        height: resMatch ? parseInt(resMatch[2]) : null,
        quality: null
      };

      if (currentInfo.height) {
        currentInfo.quality = `${currentInfo.height}p`;
      } else if (currentInfo.bandwidth) {
        const bps = currentInfo.bandwidth;
        if (bps >= 6_000_000) currentInfo.quality = '2160p';
        else if (bps >= 4_000_000) currentInfo.quality = '1440p';
        else if (bps >= 2_500_000) currentInfo.quality = '1080p';
        else if (bps >= 1_500_000) currentInfo.quality = '720p';
        else if (bps >= 800_000) currentInfo.quality = '480p';
        else if (bps >= 400_000) currentInfo.quality = '360p';
        else currentInfo.quality = '240p';
      }
    } else if (line && !line.startsWith('#') && currentInfo) {
      let streamUrl = line;
      if (!streamUrl.startsWith('http') && baseUrl) {
        try {
          const url = new URL(streamUrl, baseUrl);
          streamUrl = url.href;
        } catch (e) {
          // Ignore URL parsing errors
        }
      }

      streams.push({
        url: streamUrl,
        quality: currentInfo.quality || 'unknown',
        bandwidth: currentInfo.bandwidth,
        width: currentInfo.width,
        height: currentInfo.height,
        type: 'hls'
      });

      currentInfo = null;
    }
  }

  return {
    isMaster: m3u8Text.includes('#EXT-X-STREAM-INF'),
    streams: streams.sort((a, b) => (b.height || 0) - (a.height || 0))
  };
}

function enhanceStreamsWithQuality(streams) {
  const enhancedStreams = [];

  const tasks = streams.map(s => {
    if (s && s.url && typeof s.url === 'string' && s.url.includes('.m3u8')) {
      return getText(s.url)
        .then(text => {
          const info = parseQualityFromM3u8(text, s.url);
          if (info.isMaster && info.streams.length > 0) {
            info.streams.forEach(qualityStream => {
              enhancedStreams.push({
                ...s,
                ...qualityStream,
                masterUrl: s.url
              });
            });
          } else {
            enhancedStreams.push({
              ...s,
              quality: s.quality || 'unknown'
            });
          }
        })
        .catch(() => {
          enhancedStreams.push({
            ...s,
            quality: s.quality || 'Adaptive'
          });
        });
    } else {
      enhancedStreams.push(s);
    }
    return Promise.resolve();
  });

  return Promise.all(tasks).then(() => enhancedStreams);
}

function formatStreamsData(rapidResult) {
  const streams = [];
  const subtitles = [];
  const thumbnails = [];
  if (rapidResult && typeof rapidResult === 'object') {
    (rapidResult.sources || []).forEach(src => {
      const fileUrl = src && src.file;
      if (fileUrl) {
        streams.push({
          url: fileUrl,
          quality: fileUrl.includes('.m3u8') ? 'Adaptive' : 'unknown',
          type: fileUrl.includes('.m3u8') ? 'hls' : 'file',
          provider: 'rapidshare',
        });
      }
    });
    (rapidResult.tracks || []).forEach(tr => {
      if (tr && tr.kind === 'thumbnails' && tr.file) {
        thumbnails.push({ url: tr.file, type: 'vtt' });
      } else if (tr && (tr.kind === 'captions' || tr.kind === 'subtitles') && tr.file) {
        subtitles.push({ url: tr.file, language: tr.label || '', default: !!tr.default });
      }
    });
  }
  return { streams, subtitles, thumbnails, totalStreams: streams.length };
}

function runStreamFetch(eid, title, year, mediaType, seasonNum, episodeNum, rid) {
  logRid(rid, `runStreamFetch: start eid=${eid}`);

  return encrypt(eid)
    .then(encEid => {
      logRid(rid, 'links/list: enc(eid) ready');
      return getJson(`${YFLIX_AJAX}/links/list?eid=${eid}&_=${encEid}`);
    })
    .then(serversResp => parseHtml(serversResp.result))
    .then(servers => {
      const serverTypes = Object.keys(servers || {});
      const byTypeCounts = serverTypes.map(stype => ({ type: stype, count: Object.keys(servers[stype] || {}).length }));
      logRid(rid, 'servers available', byTypeCounts);

      const allStreams = [];
      const allSubtitles = [];
      const allThumbnails = [];

      const serverPromises = [];
      const lids = [];
      Object.keys(servers).forEach(serverType => {
        Object.keys(servers[serverType]).forEach(serverKey => {
          const lid = servers[serverType][serverKey].lid;
          lids.push(lid);
          const p = encrypt(lid)
            .then(encLid => {
              logRid(rid, `links/view: enc(lid) ready`, { serverType, serverKey, lid });
              return getJson(`${YFLIX_AJAX}/links/view?id=${lid}&_=${encLid}`);
            })
            .then(embedResp => {
              logRid(rid, `decrypt(embed)`, { serverType, serverKey, lid });
              return decrypt(embedResp.result);
            })
            .then(decrypted => {
              if (decrypted && typeof decrypted === 'object' && decrypted.url && decrypted.url.includes('rapidshare.cc')) {
                logRid(rid, `rapid.media → dec-rapid`, { lid });
                return decryptRapidMedia(decrypted.url)
                  .then(rapidData => formatStreamsData(rapidData))
                  .then(formatted => enhanceStreamsWithQuality(formatted.streams)
                    .then(enhanced => {
                      enhanced.forEach(s => {
                        s.serverType = serverType;
                        s.serverKey = serverKey;
                        s.serverLid = lid;
                        allStreams.push(s);
                      });
                      allSubtitles.push(...formatted.subtitles);
                      allThumbnails.push(...formatted.thumbnails);
                    })
                  );
              }
              return null;
            })
            .catch(() => null);
          serverPromises.push(p);
        });
      });
      const uniqueLids = Array.from(new Set(lids));
      logRid(rid, `fan-out: lids`, { total: lids.length, unique: uniqueLids.length });

      return Promise.all(serverPromises).then(() => {
        // Deduplicate streams by URL
        const seen = new Set();
        let dedupedStreams = allStreams.filter(s => {
          if (!s || !s.url) return false;
          if (seen.has(s.url)) return false;
          seen.add(s.url);
          return true;
        });
        logRid(rid, `streams: deduped`, { count: dedupedStreams.length });

        // Convert to Nuvio format
        const nuvioStreams = dedupedStreams.map(stream => ({
          name: `YFlix ${stream.serverType || 'Server'} - ${stream.quality || 'Unknown'}`,
          title: `${title}${year ? ` (${year})` : ''}${mediaType === 'tv' && seasonNum && episodeNum ? ` S${seasonNum}E${episodeNum}` : ''}`,
          url: stream.url,
          quality: stream.quality || 'Unknown',
          size: 'Unknown',
          headers: HEADERS,
          provider: 'yflix'
        }));

        return nuvioStreams;
      });
    });
}

// Main getStreams function
function getStreams(tmdbId, mediaType, seasonNum, episodeNum) {
  return new Promise((resolve, reject) => {
    const rid = createRequestId();
    logRid(rid, `getStreams start tmdbId=${tmdbId} type=${mediaType} S=${seasonNum || ''} E=${episodeNum || ''}`);

    // Look up content in database by TMDB ID
    findInDatabase(tmdbId, mediaType)
      .then(dbResult => {
        if (!dbResult) {
          logRid(rid, 'no match found in database');
          resolve([]);
          return;
        }

        const info = dbResult.info;
        const episodes = dbResult.episodes;

        logRid(rid, `database match found`, {
          title: info.title_en,
          year: info.year,
          flixId: info.flix_id,
          episodeCount: info.episode_count
        });

        // Get the episode ID
        let eid = null;
        const selectedSeason = String(seasonNum || 1);
        const selectedEpisode = String(episodeNum || 1);

        if (episodes && episodes[selectedSeason] && episodes[selectedSeason][selectedEpisode]) {
          eid = episodes[selectedSeason][selectedEpisode].eid;
          logRid(rid, `found episode eid=${eid} for S${selectedSeason}E${selectedEpisode}`);
        } else {
          // Fallback: try to find any available episode
          const seasons = Object.keys(episodes || {});
          if (seasons.length > 0) {
            const firstSeason = seasons[0];
            const episodesInSeason = Object.keys(episodes[firstSeason] || {});
            if (episodesInSeason.length > 0) {
              const firstEp = episodesInSeason[0];
              eid = episodes[firstSeason][firstEp].eid;
              logRid(rid, `fallback: using S${firstSeason}E${firstEp}, eid=${eid}`);
            }
          }
        }

        if (!eid) {
          logRid(rid, 'no episode ID found');
          resolve([]);
          return;
        }

        // Fetch streams using the episode ID
        return runStreamFetch(eid, info.title_en, info.year, mediaType, seasonNum, episodeNum, rid);
      })
      .then(streams => {
        if (streams) {
          logRid(rid, `returning streams`, { count: streams.length });
          resolve(streams);
        } else {
          resolve([]);
        }
      })
      .catch(error => {
        logRid(rid, `ERROR ${error && error.message ? error.message : String(error)}`);
        resolve([]); // Return empty array on error, don't reject
      });
  });
}

// Export for React Native compatibility
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { getStreams };
} else {
  global.getStreams = getStreams;
}

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
