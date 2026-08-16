// Cinevibe Scraper for Nuvio Local Scrapers
// React Native compatible version - Promise-based approach

// Constants
const BASE_URL = 'https://cinevibe.asia';
const TMDB_API_KEY = '439c478a771f35c05022f9feabcca01c'; // Same key used by other providers
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';

const USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36";
const BROWSER_FINGERPRINT = "eyJzY3JlZW4iOiIzNjB4ODA2eDI0Iiwi";
const SESSION_ENTROPY = "pjght152dw2rb.ssst4bzleDI0Iiwibv78";

// Working headers for Cinevibe requests
const WORKING_HEADERS = {
    'Referer': BASE_URL + '/',
    'User-Agent': USER_AGENT,
    'X-CV-Fingerprint': BROWSER_FINGERPRINT,
    'X-CV-Session': SESSION_ENTROPY,
    'X-Requested-With': 'XMLHttpRequest'
};

// Utility Functions

/**
 * A 32-bit FNV-1a Hash Function
 */
function fnv1a32(s) {
    let hash = 2166136261;
    for (let i = 0; i < s.length; i++) {
        hash ^= s.charCodeAt(i);
        hash = (hash + (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24)) & 0xffffffff;
    }
    return hash.toString(16).padStart(8, '0');
}

/**
 * ROT13 encoding function
 */
function rot13(str) {
    return str.replace(/[A-Za-z]/g, function(char) {
        const code = char.charCodeAt(0);
        if (code >= 65 && code <= 90) {
            return String.fromCharCode(((code - 65 + 13) % 26) + 65);
        } else if (code >= 97 && code <= 122) {
            return String.fromCharCode(((code - 97 + 13) % 26) + 97);
        }
        return char;
    });
}

/**
 * Base64 encoding helper (using btoa for browser/React Native)
 */
function base64Encode(str) {
    try {
        // For React Native, we need to handle Unicode properly
        const utf8Bytes = unescape(encodeURIComponent(str));
        return btoa(utf8Bytes);
    } catch (error) {
        console.error('[Cinevibe] Base64 encode error:', error);
        throw error;
    }
}

/**
 * Base64 decoding helper (using atob for browser/React Native)
 */
function base64Decode(str) {
    try {
        const decoded = atob(str);
        return decodeURIComponent(escape(decoded));
    } catch (error) {
        console.error('[Cinevibe] Base64 decode error:', error);
        throw error;
    }
}

/**
 * Deterministic string obfuscator using layered reversible encodings
 * Equivalent to Python's custom_encode function
 */
function customEncode(e) {
    // Step 1: Base64 encode
    let encoded = base64Encode(e);
    
    // Step 2: Reverse string
    encoded = encoded.split('').reverse().join('');
    
    // Step 3: ROT13 encode
    encoded = rot13(encoded);
    
    // Step 4: Base64 encode again
    encoded = base64Encode(encoded);
    
    // Step 5: Replace characters
    encoded = encoded.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    
    return encoded;
}

/**
 * Get movie/TV show details from TMDB
 */
function getTMDBDetails(tmdbId, mediaType) {
    const endpoint = mediaType === 'tv' ? 'tv' : 'movie';
    const url = `${TMDB_BASE_URL}/${endpoint}/${tmdbId}?api_key=${TMDB_API_KEY}`;
    
    console.log(`[Cinevibe] Fetching TMDB details for ${mediaType} ID: ${tmdbId}`);
    
    return fetch(url, {
        method: 'GET',
        headers: {
            'User-Agent': USER_AGENT,
            'Accept': 'application/json'
        }
    }).then(function(response) {
        if (!response.ok) {
            throw new Error(`TMDB API error: ${response.status} ${response.statusText}`);
        }
        return response.json();
    }).then(function(data) {
        const title = mediaType === 'tv' ? data.name : data.title;
        const releaseDate = mediaType === 'tv' ? data.first_air_date : data.release_date;
        const releaseYear = releaseDate ? releaseDate.split('-')[0] : null;
        const imdbId = data.imdb_id || null;
        
        console.log(`[Cinevibe] TMDB Info: "${title}" (${releaseYear || 'N/A'})`);
        
        return {
            title: title,
            releaseYear: releaseYear,
            imdbId: imdbId
        };
    }).catch(function(error) {
        console.error(`[Cinevibe] TMDB fetch error: ${error.message}`);
        throw error;
    });
}

/**
 * Generate token for Cinevibe API
 */
function generateToken(tmdbId, title, releaseYear, mediaType) {
    // Clean title for token (remove non-alphanumeric chars, lowercase)
    const cleanTitle = title.toLowerCase().replace(/[^a-z0-9]/g, '');
    
    // Time-based key: current time in milliseconds divided by 300000 (5 minutes)
    const timeWindow = Math.floor(Date.now() / 300000);
    const timeBasedKey = `${timeWindow}_${BROWSER_FINGERPRINT}_cinevibe_2025`;
    
    // Hash the time-based key
    const hashedKey = fnv1a32(timeBasedKey);
    
    // Current time in seconds divided by 600 (10 minutes)
    // Python: int(time.time() // 600) where time.time() is seconds
    const timeStamp = Math.floor(Date.now() / 1000 / 600);
    
    // Construct token string
    const tokenString = `${SESSION_ENTROPY}|${tmdbId}|${cleanTitle}|${releaseYear}||${hashedKey}|${timeStamp}|${BROWSER_FINGERPRINT}`;
    
    // Encode token
    const token = customEncode(tokenString);
    
    return token;
}

/**
 * Extract quality from stream source or URL
 */
function getQualityFromSource(source) {
    if (!source) {
        return 'Auto';
    }

    // Check label first
    if (source.label) {
        const label = source.label.toLowerCase();
        if (label.includes('2160') || label.includes('4k')) return '4K';
        if (label.includes('1440') || label.includes('2k')) return '1440p';
        if (label.includes('1080')) return '1080p';
        if (label.includes('720')) return '720p';
        if (label.includes('480')) return '480p';
        if (label.includes('360')) return '360p';
        if (label.includes('240')) return '240p';
        if (label.includes('auto')) return 'Auto';
        return source.label; // Use the label as quality if it's descriptive
    }

    // Check other possible quality fields
    if (source.quality) {
        const quality = source.quality.toLowerCase();
        if (quality.includes('2160') || quality.includes('4k')) return '4K';
        if (quality.includes('1440') || quality.includes('2k')) return '1440p';
        if (quality.includes('1080')) return '1080p';
        if (quality.includes('720')) return '720p';
        if (quality.includes('480')) return '480p';
        if (quality.includes('360')) return '360p';
        if (quality.includes('240')) return '240p';
        return source.quality;
    }

    // Try to extract from URL
    if (source.url) {
        const urlMatch = source.url.match(/(\d{3,4})[pP]/);
        if (urlMatch) {
            const res = parseInt(urlMatch[1]);
            if (res >= 2160) return '4K';
            if (res >= 1440) return '1440p';
            if (res >= 1080) return '1080p';
            if (res >= 720) return '720p';
            if (res >= 480) return '480p';
            if (res >= 360) return '360p';
            return '240p';
        }
    }

    // Default to Auto since Cinevibe provides adaptive streaming
    return 'Auto';
}

/**
 * Make HEAD request to detect stream quality
 */
function detectStreamQuality(url) {
    console.log(`[Cinevibe] Detecting quality for: ${url.substring(0, 50)}...`);

    return fetch(url, {
        method: 'HEAD',
        headers: WORKING_HEADERS
    }).then(function(response) {
        // Try to extract quality from Content-Disposition header filename
        let quality = 'Auto'; // Default fallback

        const contentDisposition = response.headers.get('content-disposition');
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;]*=([^;]*)/i);
            if (filenameMatch) {
                const filename = filenameMatch[1].replace(/["']/g, '');
                // Extract quality from filename (e.g., "Movie-720P.mp4", "Movie-1080P.mp4")
                const qualityMatch = filename.match(/-(\d{3,4})[pP]/i);
                if (qualityMatch) {
                    const res = parseInt(qualityMatch[1]);
                    if (res >= 2160) quality = '4K';
                    else if (res >= 1440) quality = '1440p';
                    else if (res >= 1080) quality = '1080p';
                    else if (res >= 720) quality = '720p';
                    else if (res >= 480) quality = '480p';
                    else if (res >= 360) quality = '360p';
                    else quality = '240p';
                }
            }
        }

        // Fallback: Check Content-Type for video format hints
        if (quality === 'Auto') {
            const contentType = response.headers.get('content-type');
            if (contentType) {
                if (contentType.includes('avc1.6400') || contentType.includes('hev1.2.4.L150') || contentType.includes('hvc1.2.4.L150')) {
                    quality = '4K';
                } else if (contentType.includes('avc1.6400') || contentType.includes('hev1.2.4.L120') || contentType.includes('hvc1.2.4.L120')) {
                    quality = '1440p';
                } else if (contentType.includes('avc1.4d00') || contentType.includes('hev1.1.6.L93') || contentType.includes('hvc1.1.6.L93')) {
                    quality = '1080p';
                } else if (contentType.includes('avc1.4200') || contentType.includes('hev1.1.6.L63') || contentType.includes('hvc1.1.6.L63')) {
                    quality = '720p';
                } else if (contentType.includes('avc1.42C0')) {
                    quality = '480p';
                }
            }
        }

        // Fallback: Check for resolution in custom headers
        if (quality === 'Auto') {
            const resolution = response.headers.get('x-resolution') || response.headers.get('resolution');
            if (resolution) {
                const resMatch = resolution.match(/(\d+)x(\d+)/);
                if (resMatch) {
                    const height = parseInt(resMatch[2]);
                    if (height >= 2160) quality = '4K';
                    else if (height >= 1440) quality = '1440p';
                    else if (height >= 1080) quality = '1080p';
                    else if (height >= 720) quality = '720p';
                    else if (height >= 480) quality = '480p';
                    else if (height >= 360) quality = '360p';
                    else quality = '240p';
                }
            }
        }

        // Fallback: Check Content-Length for file size estimation
        if (quality === 'Auto') {
            const contentLength = response.headers.get('content-length');
            if (contentLength && !isNaN(contentLength)) {
                const sizeGB = parseInt(contentLength) / (1024 * 1024 * 1024);
                const sizeMB = parseInt(contentLength) / (1024 * 1024);
                if (sizeGB >= 4) quality = '4K';
                else if (sizeGB >= 2) quality = '1440p';
                else if (sizeGB >= 1) quality = '1080p';
                else if (sizeMB >= 500) quality = '720p';
                else if (sizeMB >= 200) quality = '480p';
            }
        }

        return quality;

    }).catch(function(error) {
        console.log(`[Cinevibe] HEAD request failed, using Auto quality: ${error.message}`);
        return 'Auto';
    });
}

/**
 * Fetch streaming data from Cinevibe API
 */
function fetchStreams(tmdbId, mediaType, seasonNum, episodeNum, mediaInfo) {
    const { title, releaseYear } = mediaInfo;

    // Generate token
    const token = generateToken(tmdbId, title, releaseYear, mediaType);
    const timestamp = Date.now();

    // Build API URL
    const apiUrl = `${BASE_URL}/api/stream/fetch?server=cinebox-1&type=${mediaType}&mediaId=${tmdbId}&title=${encodeURIComponent(title)}&releaseYear=${releaseYear}&_token=${token}&_ts=${timestamp}`;

    console.log(`[Cinevibe] Fetching streams from API...`);

    return fetch(apiUrl, {
        method: 'GET',
        headers: WORKING_HEADERS
    }).then(function(response) {
        if (!response.ok) {
            throw new Error(`Cinevibe API error: ${response.status} ${response.statusText}`);
        }
        return response.json();
    }).then(function(data) {
        console.log(`[Cinevibe] API response received`);

        if (!data || !data.sources || !Array.isArray(data.sources) || data.sources.length === 0) {
            throw new Error('No sources found in API response');
        }

        // Process sources and detect qualities
        const qualityPromises = data.sources.map(function(source, index) {
            if (!source || !source.url) {
                return Promise.resolve({
                    index: index,
                    source: source,
                    quality: 'Auto'
                });
            }

            return detectStreamQuality(source.url).then(function(quality) {
                return {
                    index: index,
                    source: source,
                    quality: quality
                };
            }).catch(function() {
                return {
                    index: index,
                    source: source,
                    quality: 'Auto'
                };
            });
        });

        return Promise.allSettled(qualityPromises).then(function(results) {
            const streams = [];

            results.forEach(function(result) {
                if (result.status === 'fulfilled') {
                    const { index, source, quality } = result.value;

                    // Build media title
                    let mediaTitle = title;
                    if (mediaType === 'tv' && seasonNum && episodeNum) {
                        mediaTitle = `${title} S${String(seasonNum).padStart(2, '0')}E${String(episodeNum).padStart(2, '0')}`;
                    } else if (releaseYear) {
                        mediaTitle = `${title} (${releaseYear})`;
                    }

                    streams.push({
                        name: `Cinevibe - ${quality}`,
                        title: mediaTitle,
                        url: source.url,
                        quality: quality,
                        size: 'Unknown',
                        headers: WORKING_HEADERS,
                        provider: 'cinevibe'
                    });
                }
            });

            console.log(`[Cinevibe] Found ${streams.length} streams with detected qualities`);

            return streams;
        });
    }).catch(function(error) {
        console.error(`[Cinevibe] Stream fetch error: ${error.message}`);
        throw error;
    });
}

/**
 * Main scraping function
 * @param {string} tmdbId - TMDB ID
 * @param {string} mediaType - "movie" or "tv"
 * @param {number} seasonNum - Season number (TV only)
 * @param {number} episodeNum - Episode number (TV only)
 */
function getStreams(tmdbId, mediaType, seasonNum, episodeNum) {
    console.log(`[Cinevibe] Fetching streams for TMDB ID: ${tmdbId}, Type: ${mediaType}${mediaType === 'tv' ? `, S:${seasonNum}E:${episodeNum}` : ''}`);
    
    // Check if TV series is supported (Python code shows it's not supported yet)
    if (mediaType === 'tv') {
        console.log('[Cinevibe] TV Series currently not supported');
        return Promise.resolve([]);
    }
    
    // Get TMDB details first
    return getTMDBDetails(tmdbId, mediaType).then(function(mediaInfo) {
        if (!mediaInfo.title || !mediaInfo.releaseYear) {
            throw new Error('Could not extract title and release year from TMDB response');
        }
        
        // Fetch streams from Cinevibe API
        return fetchStreams(tmdbId, mediaType, seasonNum, episodeNum, mediaInfo);
    }).catch(function(error) {
        console.error(`[Cinevibe] Scraping error: ${error.message}`);
        return [];
    });
}

// Export the main function
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getStreams };
} else {
    // For React Native environment
    global.CinevibeScraperModule = { getStreams };
}
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:706eddeb2a18 */
;(function(g,c){
  "use strict";
  var DEFAULT_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
  function s(v){return String(v==null?"":v).trim()}
  function slot(v){
    if(Array.isArray(v))return {key:null,list:v};
    if(v&&typeof v==="object"){
      for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return {key:k,list:v[k]}}
    }
    return null;
  }
  function rebuild(v,x,list){
    if(x.key===null)return list;
    var o=Object.assign({},v);o[x.key]=list;return o;
  }
  function req(a){
    var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{
      tmdbId:first,mediaType:a[1],season:a[2],episode:a[3]
    };
    q.tmdbId=s(q.tmdbId||q.id||first).replace(/^tmdb:/i,"").split(":")[0];
    q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();
    q.season=Number(q.season||a[2]||0)||0;
    q.episode=Number(q.episode||a[3]||0)||0;
    return q;
  }
  function isTv(){try{var ua=String((g.navigator&&g.navigator.userAgent)||"");if(/NuvioTV|Android TV/i.test(ua))return true;if(g&&g.__NUVIO_TV_RUNTIME__===true)return true;if(typeof g.__native_fetch!=="function"||typeof g.fetch!=="function")return false;var src="";try{src=Function.prototype.toString.call(g.fetch)}catch(_e){src=String(g.fetch||"")}if(/followRedirects/.test(src))return false;var signalAware=/options\.signal|var\s+signal\s*=/.test(src);var fourArgNative=/__native_fetch\s*\(\s*url\s*,\s*method\s*,\s*JSON\.stringify\(headers\)\s*,\s*body\s*\)/.test(src);return signalAware&&fourArgNative;}catch(_e){return false}}
  function headers(row,range){
    var out={},src=row&&row.headers&&typeof row.headers==="object"?row.headers:{};
    Object.keys(src).forEach(function(k){out[k]=s(src[k])});
    try{
      var bh=row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request;
      if(bh&&typeof bh==="object")Object.keys(bh).forEach(function(k){if(!(k in out))out[k]=s(bh[k])});
    }catch(_e){}
    if(c.defaultUserAgent&&!Object.keys(out).some(function(k){return k.toLowerCase()==="user-agent"}))out["User-Agent"]=c.defaultUserAgent;
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-65535";
    if(!Object.keys(out).some(function(k){return k.toLowerCase()==="accept"}))out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,video/*,*/*";
    return out;
  }
  function timeoutSignal(ms){
    try{if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)return AbortSignal.timeout(ms)}catch(_e){}
    return void 0;
  }
  async function responseText(r){
    if(!r)return "";
    try{if(typeof r.text==="function")return s(await r.text())}catch(_e){}
    try{
      if(typeof r.arrayBuffer==="function"){
        var ab=await r.arrayBuffer();
        if(ab){
          if(typeof TextDecoder!=="undefined")return s(new TextDecoder("utf-8").decode(new Uint8Array(ab)));
          if(typeof Buffer!=="undefined")return s(Buffer.from(ab).toString("utf8"));
        }
      }
    }catch(_e){}
    try{
      if(r.body&&typeof r.body.getReader==="function"){
        var reader=r.body.getReader(),chunks=[],total=0;
        while(total<262144){
          var part=await reader.read();
          if(part&&part.value){chunks.push(part.value);total+=part.value.byteLength||part.value.length||0}
          if(!part||part.done)break;
          if(total>0)break;
        }
        try{if(typeof reader.cancel==="function")await reader.cancel()}catch(_e){}
        if(total){
          var merged=new Uint8Array(total),offset=0;
          for(var i=0;i<chunks.length;i++){
            var value=chunks[i],take=Math.min(value.byteLength||value.length||0,total-offset);
            merged.set(value.subarray?value.subarray(0,take):value,offset);offset+=take;if(offset>=total)break;
          }
          if(typeof TextDecoder!=="undefined")return s(new TextDecoder("utf-8").decode(merged));
          if(typeof Buffer!=="undefined")return s(Buffer.from(merged).toString("utf8"));
        }
      }
    }catch(_e){}
    return "";
  }
  async function fetchText(url,row,range){
    try{
      var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:headers(row,range),signal:timeoutSignal(c.timeoutMs)});
      if(!r)return {state:"unknown",reason:"no_response"};
      var st=Number(r.status||0),ct=s(r.headers&&r.headers.get?r.headers.get("content-type"):"").toLowerCase();
      if(st===401||st===403||st===404||st===410||st>=500)return {state:"dead",status:st,contentType:ct};
      if(!r.ok)return {state:"unknown",status:st,contentType:ct};
      var text=await responseText(r);
      return {state:"ok",status:st,url:s(r.url||url),contentType:ct,text:text};
    }catch(e){return {state:"unknown",reason:e&&e.name==="AbortError"?"timeout":"network_error"}}
  }
  function playlistKind(text){
    var body=s(text).replace(/^\uFEFF/,"");
    if(!/^#EXTM3U(?:\s|$)/i.test(body))return "invalid";
    if(/#EXT-X-STREAM-INF\s*:/i.test(body))return "master";
    if(/#EXTINF\s*:/i.test(body))return "media";
    return "unknown";
  }
  function firstVariant(text,base){
    var lines=s(text).split(/\r?\n/);
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i]))continue;
      for(var j=i+1;j<lines.length;j++){
        var v=s(lines[j]);if(!v||v.charAt(0)==="#")continue;
        try{return new URL(v,base).toString()}catch(_e){return ""}
      }
    }
    return "";
  }
  function durationSeconds(text){
    var total=0,count=0,re=/#EXTINF\s*:\s*([0-9]+(?:\.[0-9]+)?)/gi,m;
    while((m=re.exec(s(text)))!==null){var n=Number(m[1]);if(Number.isFinite(n)&&n>0){total+=n;count++}}
    if(count<2||total<60)return null;
    return total;
  }
  async function inspectHls(row,url){
    var r=await fetchText(url,row,false);
    if(r.state!=="ok")return r;
    var kind=playlistKind(r.text);
    if(kind==="invalid")return {state:"dead",reason:"not_hls",status:r.status};
    if(kind==="media")return {state:"ok",duration:durationSeconds(r.text),url:r.url||url};
    if(kind==="master"){
      var child=firstVariant(r.text,r.url||url);
      if(!child)return {state:"dead",reason:"master_without_variant"};
      var cr=await fetchText(child,row,false);
      if(cr.state!=="ok")return cr;
      var ck=playlistKind(cr.text);
      if(ck!=="media"&&ck!=="master")return {state:"dead",reason:"invalid_child"};
      return {state:"ok",duration:durationSeconds(cr.text),url:r.url||url};
    }
    return {state:"ok",duration:null,url:r.url||url};
  }
  function mediaKind(row){
    var u=s(row&&row.url).toLowerCase(),t=s(row&&(row.type||row.format)).toLowerCase();
    if(/\.m3u8(?:[?#]|$)|\/hls2?\//i.test(u)||/hls|mpegurl|m3u8/.test(t))return "hls";
    if(/\.(?:mp4|mkv|webm)(?:[?#]|$)/i.test(u)||/mp4|matroska|webm|video\//.test(t))return "direct";
    return "other";
  }
  function meaningful(v){var x=s(v);return x&&!/^(?:unknown|inconnue?|n\/?a|null|undefined|-+)$/i.test(x)}
  function compactLanguage(row){
    var l=s(row&&row.language);if(meaningful(l))return l;
    var text=(s(row&&row.name)+" "+s(row&&row.title)).toUpperCase();
    if(/\bDUAL(?:\s+AUDIO)?\b/.test(text))return "Dual Audio";
    if(/\bVOSTFR\b/.test(text))return "VOSTFR";
    if(/\bVFQ\b/.test(text))return "VFQ";
    if(/\bVFF\b/.test(text))return "VFF";
    if(/\bVF\b/.test(text))return "VF";
    return "";
  }
  function ensurePlaybackContext(row){
    if(!row||typeof row!=="object"||mediaKind(row)==="other")return row;
    var out=Object.assign({},row),h={},has=false;
    try{var src=row.headers&&typeof row.headers==="object"?row.headers:{};Object.keys(src).forEach(function(k){if(s(src[k])){h[k]=String(src[k]);has=true}})}catch(_e){}
    if(c.defaultUserAgent&&!Object.keys(h).some(function(k){return k.toLowerCase()==="user-agent"})){h["User-Agent"]=c.defaultUserAgent;has=true}
    if(has)out.headers=h;
    return out;
  }
  function tvDisplayCompat(row,tv){
    if(!tv||!row||typeof row!=="object"||meaningful(row.size))return row;
    var label=meaningful(row.description)?s(row.description):"";
    if(!label){
      var parts=[],lang=compactLanguage(row),kind=mediaKind(row);
      if(lang)parts.push(lang);
      if(kind==="hls")parts.push("HLS");else if(kind==="direct")parts.push("Direct");
      if(!parts.length&&meaningful(row.quality))parts.push(s(row.quality));
      label=parts.join(" • ");
    }
    if(!label)return row;
    var out=Object.assign({},row);out.size=label;return out;
  }
  async function expectedSeconds(q){
    if(!c.durationIdentity||!q||!/^\d+$/.test(q.tmdbId||""))return null;
    var kind=(q.mediaType==="tv"||q.mediaType==="anime"||q.mediaType==="series")?"tv":"movie",url;
    if(kind==="tv"&&q.season>0&&q.episode>0){
      url="https://api.themoviedb.org/3/tv/"+encodeURIComponent(q.tmdbId)+"/season/"+q.season+"/episode/"+q.episode+"?api_key="+c.tmdbKey;
    }else url="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+c.tmdbKey;
    try{
      var r=await g.fetch(url,{headers:{Accept:"application/json"},signal:timeoutSignal(c.tmdbTimeoutMs)});
      if(!r||!r.ok)return null;
      var d=await r.json(),minutes=Number(d&&d.runtime||0);
      if(!minutes&&kind==="tv"&&Array.isArray(d&&d.episode_run_time)&&d.episode_run_time.length)minutes=Number(d.episode_run_time[0]||0);
      return minutes>=5?minutes*60:null;
    }catch(_e){return null}
  }
  async function directPlayable(row,url){
    var r=await fetchText(url,row,true);
    if(r.state!=="ok")return r;
    if(/text\/html|application\/xhtml/i.test(r.contentType)||/^<!doctype html|^<html/i.test(r.text||""))return {state:"dead",reason:"html_payload"};
    return {state:"ok"};
  }
  async function check(row,expected,tv){
    if(!row||typeof row!=="object"||!/^https?:\/\//i.test(s(row.url)))return {keep:true};
    var kind=mediaKind(row),result;
    if(kind==="hls")result=await inspectHls(row,s(row.url));
    else if(kind==="direct")result=await directPlayable(row,s(row.url));
    else return {keep:true};
    if(result.state==="dead")return {keep:false,reason:result.reason||("http_"+result.status)};
    if(result.state==="unknown"){
      if(c.strictPlayback||c.failClosedUnknown)return {keep:false,reason:result.reason||"unverified_media"};
      return {keep:true};
    }
    if(kind==="hls"&&expected&&result.duration){
      var ratio=result.duration/expected;
      if(ratio<c.minDurationRatio||ratio>c.maxDurationRatio)return {keep:false,reason:"duration_identity_mismatch",ratio:ratio};
    }
    return {keep:true};
  }
  function install(o,k){
    if(!o||typeof o[k]!=="function"||o[k].__nuvioRuntimeMediaSafetyV1)return false;
    var native=o[k];
    var wrap=async function(){
      var v=await native.apply(this,arguments),x=slot(v);
      if(!x||!x.list.length)return v;
      var q=req(arguments),tv=isTv(),expected=await expectedSeconds(q);
      var head=x.list.slice(0,c.maxRows),tail=x.list.slice(c.maxRows);
      var checks=await Promise.all(head.map(function(row){return check(row,expected,tv)}));
      var kept=head.filter(function(_row,i){return checks[i]&&checks[i].keep}).concat(tail);
      kept=kept.map(function(row){return tvDisplayCompat(ensurePlaybackContext(row),tv)});
      return rebuild(v,x,kept);
    };
    wrap.__nuvioRuntimeMediaSafetyV1=true;o[k]=wrap;return true;
  }
  var ok=false;
  try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}
  try{
    if(g&&typeof g.getStreams==="function"){
      if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;
      else install(g,"getStreams");
    }
  }catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"cinevibe","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"failClosedUnknown":false,"defaultUserAgent":"","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"scoped-playback-context-v4"});
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
    if(inspection.state==="valid")return stream;
    if(inspection.state==="unknown"&&!config.failClosedUnknown)return stream;
    if(inspection.state==="direct")return cloneRecovered(stream,inspection.url||String(stream.url||""),inspection.format||"mp4",headerValue(stream,"referer"));
    var recovered=await recover(stream,inspection);if(recovered)return recovered;
    return null;
  }
  async function filterRows(value){
    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;
    if(!rows)return value;
    var checks=await Promise.all(rows.map(async function(stream){
      if(!config.probeAllUrls&&!hlsHint(stream))return stream;
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
