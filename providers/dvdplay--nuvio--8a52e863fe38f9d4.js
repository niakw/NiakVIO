// DVDPlay scraper for Nuvio
// Scrapes content from dvdplay.forum with HubCloud link extraction

// Constants
const TMDB_API_KEY = "439c478a771f35c05022f9feabcca01c"; // This will be replaced by Nuvio
const BASE_URL = 'https://dvdplay.cv';

// Temporarily disable URL validation for faster results
global.URL_VALIDATION_ENABLED = true;

// === HubCloud Extractor Functions (embedded) ===

// Utility functions
function getBaseUrl(url) {
    try {
        const urlObj = new URL(url);
        return `${urlObj.protocol}//${urlObj.host}`;
    } catch (e) {
        return '';
    }
}

// Base64 and encoding utilities (from 4KHDHub)
function base64Decode(str) {
    try {
        // Convert base64 -> binary string -> UTF-8
        // escape/unescape is deprecated but works in RN environments for this use case
        return decodeURIComponent(escape(atob(str)));
    } catch (e) {
        return '';
    }
}

function base64Encode(str) {
    try {
        return btoa(unescape(encodeURIComponent(str)));
    } catch (e) {
        return '';
    }
}

function rot13(str) {
    return (str || '').replace(/[A-Za-z]/g, function (char) {
        var start = char <= 'Z' ? 65 : 97;
        return String.fromCharCode(((char.charCodeAt(0) - start + 13) % 26) + start);
    });
}

// Advanced title normalization (from 4KHDHub)
function normalizeTitle(title) {
    return (title || '')
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

// String similarity calculation (from 4KHDHub)
function calculateSimilarity(str1, str2) {
    var s1 = normalizeTitle(str1);
    var s2 = normalizeTitle(str2);
    if (s1 === s2) return 1.0;
    var len1 = s1.length;
    var len2 = s2.length;
    if (len1 === 0) return len2 === 0 ? 1.0 : 0.0;
    if (len2 === 0) return 0.0;
    var matrix = Array(len1 + 1).fill(null).map(function () { return Array(len2 + 1).fill(0); });
    for (var i = 0; i <= len1; i++) matrix[i][0] = i;
    for (var j = 0; j <= len2; j++) matrix[0][j] = j;
    for (i = 1; i <= len1; i++) {
        for (j = 1; j <= len2; j++) {
            var cost = s1[i - 1] === s2[j - 1] ? 0 : 1;
            matrix[i][j] = Math.min(matrix[i - 1][j] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j - 1] + cost);
        }
    }
    var maxLen = Math.max(len1, len2);
    return (maxLen - matrix[len1][len2]) / maxLen;
}

function makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const fetchOptions = {
            method: options.method || 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                ...options.headers
            },
            timeout: 30000
        };

        fetch(url, fetchOptions)
            .then(response => {
                if (options.allowRedirects === false && (response.status === 301 || response.status === 302 || response.status === 303 || response.status === 307 || response.status === 308)) {
                    resolve({ statusCode: response.status, headers: Object.fromEntries(response.headers) });
                    return;
                }

                return response.text().then(data => {
                    if (options.parseHTML && data) {
                        const cheerio = require('cheerio-without-node-native');
                        const $ = cheerio.load(data);
                        resolve({ $: $, body: data, statusCode: response.status, headers: Object.fromEntries(response.headers) });
                    } else {
                        resolve({ body: data, statusCode: response.status, headers: Object.fromEntries(response.headers) });
                    }
                });
            })
            .catch(reject);
    });
}

function getIndexQuality(str) {
    const match = (str || '').match(/(\d{3,4})[pP]/);
    return match ? parseInt(match[1]) : null; // Don't assume quality if not found
}

function decodeFilename(filename) {
    if (!filename) return filename;

    try {
        let decoded = filename;

        if (decoded.startsWith('UTF-8')) {
            decoded = decoded.substring(5);
        }

        decoded = decodeURIComponent(decoded);

        return decoded;
    } catch (error) {
        return filename;
    }
}

function cleanTitle(title) {
    const decodedTitle = decodeFilename(title);
    const parts = decodedTitle.split(/[.\-_]/);

    const qualityTags = ['WEBRip', 'WEB-DL', 'WEB', 'BluRay', 'HDRip', 'DVDRip', 'HDTV', 'CAM', 'TS', 'R5', 'DVDScr', 'BRRip', 'BDRip', 'DVD', 'PDTV', 'HD'];
    const audioTags = ['AAC', 'AC3', 'DTS', 'MP3', 'FLAC', 'DD5', 'EAC3', 'Atmos'];
    const subTags = ['ESub', 'ESubs', 'Subs', 'MultiSub', 'NoSub', 'EnglishSub', 'HindiSub'];
    const codecTags = ['x264', 'x265', 'H264', 'HEVC', 'AVC'];

    const startIndex = parts.findIndex(part =>
        qualityTags.some(tag => part.toLowerCase().includes(tag.toLowerCase()))
    );

    const endIndex = parts.map((part, index) => {
        const hasTag = [...subTags, ...audioTags, ...codecTags].some(tag =>
            part.toLowerCase().includes(tag.toLowerCase())
        );
        return hasTag ? index : -1;
    }).filter(index => index !== -1).pop() || -1;

    if (startIndex !== -1 && endIndex !== -1 && endIndex >= startIndex) {
        return parts.slice(startIndex, endIndex + 1).join('.');
    } else if (startIndex !== -1) {
        return parts.slice(startIndex).join('.');
    } else {
        return parts.slice(-3).join('.');
    }
}

function getFilenameFromUrl(url) {
    return new Promise((resolve) => {
        try {
            fetch(url, { method: 'HEAD', timeout: 10000 })
                .then(response => {
                    const contentDisposition = response.headers.get('content-disposition');
                    let filename = null;

                    if (contentDisposition) {
                        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/i);
                        if (filenameMatch && filenameMatch[1]) {
                            filename = filenameMatch[1].replace(/["']/g, '');
                        }
                    }

                    if (!filename) {
                        const urlObj = new URL(url);
                        const pathParts = urlObj.pathname.split('/');
                        filename = pathParts[pathParts.length - 1];
                        if (filename && filename.includes('.')) {
                            filename = filename.replace(/\.[^.]+$/, '');
                        }
                    }

                    const decodedFilename = decodeFilename(filename);
                    resolve(decodedFilename || null);
                })
                .catch(() => resolve(null));
        } catch (error) {
            resolve(null);
        }
    });
}

function extractHubCloudLinks(url, referer = 'HubCloud') {
    var origin;
    try { origin = new URL(url).origin; } catch (e) { origin = ''; }

    // Helper function for absolute URL resolution
    function toAbsolute(href, base) {
        try {
            return new URL(href, base).href;
        } catch (e) {
            return href;
        }
    }

    return makeRequest(url, { parseHTML: true })
        .then(response => {
            const $ = response.$;

            var href;
            if (url.indexOf('hubcloud.php') !== -1) {
                href = url;
            } else {
                // Check for token-based HubCloud URLs (newer format)
                var tokenMatch = url.match(/\/video\/([^\/\?]+)(\?token=([^&\s]+))?/);
                if (tokenMatch) {
                    var videoId = tokenMatch[1];
                    var token = tokenMatch[3];
                    if (token) {
                        // Use the token-based URL format
                        href = origin + '/video/' + videoId + '?token=' + token;
                    } else {
                        // Try to find token in the page
                        var tokenFromPage = $.html().match(/token=([^"'\s&]+)/);
                        if (tokenFromPage) {
                            href = origin + '/video/' + videoId + '?token=' + tokenFromPage[1];
                        } else {
                            href = url; // Use original URL as fallback
                        }
                    }
                } else {
                    // Traditional approach for older HubCloud formats
                    var rawHref = $('#download').attr('href') || $('a[href*="hubcloud.php"]').attr('href') || $('.download-btn').attr('href') || $('a[href*="download"]').attr('href');
                    if (!rawHref) throw new Error('Download element not found');
                    href = toAbsolute(rawHref, origin);
                }
            }

            return makeRequest(href, { parseHTML: true }).then(function (secondResponse) {
                return { firstResponse: response, secondResponse: secondResponse, href: href };
            });
        })
        .then(response => {
            const $$ = response.secondResponse.$; // Use $$ for the second cheerio instance like 4KHDHub
            const href = response.href;

            // Helper function to resolve intermediate HubCloud URLs (.fans/?id= and .workers.dev/?id=)
            function resolveHubCloudUrl(url) {
                console.log(`[DVDPlay] Resolving HubCloud URL: ${url.substring(0, 50)}...`);

                // If it's already an R2 Cloudflare URL, it's already resolved
                if (url.includes('r2.cloudflarestorage.com')) {
                    console.log(`[DVDPlay] URL already resolved (R2): ${url.substring(0, 50)}...`);
                    return Promise.resolve(url);
                }

                // Extract the actual download URL from 360news4u.net/dl.php?link= URLs FIRST
                if (url.includes('360news4u.net/dl.php?link=')) {
                    console.log(`[DVDPlay] 🔍 Processing 360news4u.net URL: ${url.substring(0, 100)}...`);
                    const linkMatch = url.match(/360news4u\.net\/dl\.php\?link=([^&\s]+)/);
                    console.log(`[DVDPlay] 🔍 Regex match result:`, linkMatch);

                    if (linkMatch && linkMatch[1]) {
                        const actualUrl = decodeURIComponent(linkMatch[1]);
                        console.log(`[DVDPlay] ✅ Extracted Google Drive URL from 360news4u.net: ${actualUrl.substring(0, 80)}...`);
                        return Promise.resolve(actualUrl);
                    } else {
                        console.log(`[DVDPlay] ❌ Failed to extract URL from 360news4u.net link`);
                        console.log(`[DVDPlay] ❌ Full URL for debugging: ${url}`);
                    }
                }

                // Extract the actual download URL from gamerxyt.com/dl.php?link= URLs
                if (url.includes('gamerxyt.com/dl.php?link=')) {
                    console.log(`[DVDPlay] 🔍 Processing gamerxyt.com URL: ${url.substring(0, 100)}...`);
                    const linkMatch = url.match(/gamerxyt\.com\/dl\.php\?link=([^&\s]+)/);
                    console.log(`[DVDPlay] 🔍 Regex match result:`, linkMatch);

                    if (linkMatch && linkMatch[1]) {
                        const actualUrl = decodeURIComponent(linkMatch[1]);
                        console.log(`[DVDPlay] ✅ Extracted Google Drive URL from gamerxyt.com: ${actualUrl.substring(0, 80)}...`);
                        return Promise.resolve(actualUrl);
                    } else {
                        console.log(`[DVDPlay] ❌ Failed to extract URL from gamerxyt.com link`);
                        console.log(`[DVDPlay] ❌ Full URL for debugging: ${url}`);
                    }
                }

                // If it's a direct Google Drive download URL, it might be final
                if (url.includes('video-downloads.googleusercontent.com')) {
                    console.log(`[DVDPlay] Google Drive download URL found: ${url.substring(0, 50)}...`);
                    return Promise.resolve(url);
                }

                return fetch(url, {
                    method: 'GET',
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    },
                    redirect: 'manual' // Don't follow redirects automatically
                }).then(response => {
                    if (response.status >= 300 && response.status < 400) {
                        // Follow redirect manually
                        const location = response.headers.get('location');
                        if (location) {
                            console.log(`[DVDPlay] Following redirect to: ${location.substring(0, 50)}...`);
                            // Recursively resolve the redirect URL
                            return resolveHubCloudUrl(location);
                        }
                    }

                    // If no redirect, check if this is already a direct file URL
                    if (response.status === 200 && response.headers.get('content-type')?.includes('video/')) {
                        console.log(`[DVDPlay] Direct file URL found: ${url.substring(0, 50)}...`);
                        return url;
                    }

                    // Check if it's a direct S3/R2 URL in the response
                    if (response.status === 200) {
                        console.log(`[DVDPlay] Checking for direct URL in response...`);
                        return response.text().then(text => {
                            // Look for direct download URLs in the response
                            const directUrlMatch = text.match(/(https?:\/\/[^"'\s]+\.r2\.cloudflarestorage\.com[^"'\s]*)/);
                            if (directUrlMatch) {
                                console.log(`[DVDPlay] Found direct URL in response: ${directUrlMatch[1].substring(0, 50)}...`);
                                return directUrlMatch[1];
                            }

                            // Look for other direct download patterns
                            const otherDirectMatch = text.match(/(https?:\/\/[^"'\s]+\/[^"'\s]*\.(mkv|mp4|avi|m4v)[^"'\s]*)/i);
                            if (otherDirectMatch) {
                                console.log(`[DVDPlay] Found direct file URL: ${otherDirectMatch[1].substring(0, 50)}...`);
                                return otherDirectMatch[1];
                            }

                            // Return original URL if we can't find a direct URL
                            console.log(`[DVDPlay] No direct URL found, returning original`);
                            return url;
                        });
                    }

                    // Return original URL if we can't resolve it
                    console.log(`[DVDPlay] Could not resolve URL, returning original`);
                    return url;
                }).catch(error => {
                    console.log(`[DVDPlay] Error resolving URL: ${error.message}`);
                    return url;
                });
            }

            function buildTask(buttonText, buttonLink, headerDetails, size, quality) {
                const qualityLabel = quality ? (' - ' + quality + 'p') : ' - Unknown';

                // Pixeldrain normalization (from 4KHDHub)
                const pd = buttonLink.match(/pixeldrain\.(?:net|dev)\/u\/([a-zA-Z0-9]+)/);
                if (pd && pd[1]) buttonLink = 'https://pixeldrain.net/api/file/' + pd[1];

                // Handle intermediate HubCloud URLs (.fans/?id=, .workers.dev/?id=, and Google Drive redirects)
                if (buttonLink.includes('.fans/?id=') || buttonLink.includes('.workers.dev/?id=') || buttonLink.includes('360news4u.net/dl.php')) {
                    return resolveHubCloudUrl(buttonLink)
                        .then(resolvedUrl => {
                            // If resolution failed and we still have an intermediate URL, try one more time
                            if (resolvedUrl.includes('.workers.dev/?id=') &&
                                !resolvedUrl.includes('r2.cloudflarestorage.com') &&
                                !resolvedUrl.includes('video-downloads.googleusercontent.com') &&
                                !resolvedUrl.includes('360news4u.net/dl.php')) {
                                console.log(`[DVDPlay] Second attempt to resolve: ${resolvedUrl.substring(0, 50)}...`);
                                return resolveHubCloudUrl(resolvedUrl);
                            }
                            return resolvedUrl;
                        })
                        .then(resolvedUrl => {
                            return getFilenameFromUrl(resolvedUrl)
                                .then(actualFilename => {
                                    const displayFilename = actualFilename || headerDetails || 'Unknown';

                                    // Try to extract quality from filename if not already found
                                    let finalQuality = quality;
                                    if (!finalQuality) {
                                        finalQuality = getIndexQuality(displayFilename);
                                    }
                                    if (!finalQuality && headerDetails) {
                                        finalQuality = getIndexQuality(headerDetails);
                                    }

                                    const finalQualityLabel = finalQuality ? (' - ' + finalQuality + 'p') : ' - Unknown';

                                    const titleParts = [];
                                    if (displayFilename) titleParts.push(displayFilename);
                                    if (size) titleParts.push(size);
                                    const finalTitle = titleParts.join('\n');

                                    let name;
                                    if (buttonText.includes('FSL Server')) name = 'DVDPlay - FSL Server' + finalQualityLabel;
                                    else if (buttonText.includes('S3 Server')) name = 'DVDPlay - S3 Server' + finalQualityLabel;
                                    else if (/pixeldra/i.test(buttonText) || /pixeldra/i.test(buttonLink)) name = 'DVDPlay - Pixeldrain' + finalQualityLabel;
                                    else if (buttonText.includes('Download File')) name = 'DVDPlay - HubCloud' + finalQualityLabel;
                                    else name = 'DVDPlay - HubCloud' + finalQualityLabel;

                                    return {
                                        name: name,
                                        title: finalTitle,
                                        url: resolvedUrl,
                                        quality: finalQuality ? finalQuality + 'p' : 'Unknown',
                                        size: size || null,
                                        fileName: actualFilename || null,
                                        type: 'direct'
                                    };
                                })
                                .catch(() => {
                                    const displayFilename = headerDetails || 'Unknown';
                                    const titleParts = [];
                                    if (displayFilename) titleParts.push(displayFilename);
                                    if (size) titleParts.push(size);
                                    const finalTitle = titleParts.join('\n');

                                    const name = 'DVDPlay - HubCloud' + qualityLabel;
                                    return {
                                        name: name,
                                        title: finalTitle,
                                        url: resolvedUrl,
                                        quality: quality ? quality + 'p' : 'Unknown',
                                        size: size || null,
                                        fileName: null,
                                        type: 'direct'
                                    };
                                });
                        });
                }

                return getFilenameFromUrl(buttonLink)
                    .then(actualFilename => {
                        const displayFilename = actualFilename || headerDetails || 'Unknown';

                        // Try to extract quality from filename if not already found
                        let finalQuality = quality;
                        if (!finalQuality) {
                            finalQuality = getIndexQuality(displayFilename);
                        }
                        if (!finalQuality && headerDetails) {
                            finalQuality = getIndexQuality(headerDetails);
                        }

                        const finalQualityLabel = finalQuality ? (' - ' + finalQuality + 'p') : ' - Unknown';

                        const titleParts = [];
                        if (displayFilename) titleParts.push(displayFilename);
                        if (size) titleParts.push(size);
                        const finalTitle = titleParts.join('\n');

                        let name;
                        if (buttonText.includes('FSL Server')) name = 'DVDPlay - FSL Server' + finalQualityLabel;
                        else if (buttonText.includes('S3 Server')) name = 'DVDPlay - S3 Server' + finalQualityLabel;
                        else if (/pixeldra/i.test(buttonText) || /pixeldra/i.test(buttonLink)) name = 'DVDPlay - Pixeldrain' + finalQualityLabel;
                        else if (buttonText.includes('Download File')) name = 'DVDPlay - HubCloud' + finalQualityLabel;
                        else name = 'DVDPlay - HubCloud' + finalQualityLabel;

                        return {
                            name: name,
                            title: finalTitle,
                            url: buttonLink,
                            quality: finalQuality ? finalQuality + 'p' : 'Unknown',
                            size: size || null,
                            fileName: actualFilename || null,
                            type: 'direct'
                        };
                    })
                    .catch(() => {
                        const displayFilename = headerDetails || 'Unknown';
                        const titleParts = [];
                        if (displayFilename) titleParts.push(displayFilename);
                        if (size) titleParts.push(size);
                        const finalTitle = titleParts.join('\n');

                        const name = 'DVDPlay - HubCloud' + qualityLabel;
                        return {
                            name: name,
                            title: finalTitle,
                            url: buttonLink,
                            quality: quality ? quality + 'p' : 'Unknown',
                            size: size || null,
                            fileName: null,
                            type: 'direct'
                        };
                    });
            }

            // Iterate per card to capture per-quality sections (from 4KHDHub)
            const tasks = [];
            const cards = $$('.card');
            if (cards.length > 0) {
                cards.each(function (ci, card) {
                    const $card = $$(card);
                    const header = $card.find('div.card-header').text() || $$('div.card-header').first().text() || '';
                    const size = $card.find('i#size').text() || $$('i#size').first().text() || '';
                    const quality = getIndexQuality(header);
                    const headerDetails = cleanTitle(header);

                    let localBtns = $card.find('div.card-body h2 a.btn');
                    if (localBtns.length === 0) localBtns = $card.find('a.btn, .btn, a[href]');

                    localBtns.each(function (i, el) {
                        const $btn = $$(el);
                        const text = ($btn.text() || '').trim();
                        let link = $btn.attr('href');

                        if (!link) return;
                        link = toAbsolute(link, href);

                        // Only consider plausible buttons (from 4KHDHub)
                        const isPlausible = /(hubcloud|hubdrive|pixeldrain|buzz|10gbps|workers\.dev|r2\.dev|download|api\/file)/i.test(link) ||
                            text.toLowerCase().includes('download');

                        if (!isPlausible) return;

                        tasks.push(buildTask(text, link, headerDetails, size, quality));
                    });
                });
            }

            // Fallback: whole page buttons (from 4KHDHub)
            if (tasks.length === 0) {
                let buttons = $$.root().find('div.card-body h2 a.btn');
                if (buttons.length === 0) {
                    const altSelectors = ['a.btn', '.btn', 'a[href]'];
                    for (const selector of altSelectors) {
                        buttons = $$.root().find(selector);
                        if (buttons.length > 0) break;
                    }
                }

                const size = $$('i#size').first().text() || '';
                const header = $$('div.card-header').first().text() || '';
                const quality = getIndexQuality(header);
                const headerDetails = cleanTitle(header);

                buttons.each(function (i, el) {
                    const $btn = $$(el);
                    const text = ($btn.text() || '').trim();
                    let link = $btn.attr('href');

                    if (!link) return;
                    link = toAbsolute(link, href);

                    tasks.push(buildTask(text, link, headerDetails, size, quality));
                });
            }

            if (tasks.length === 0) return [];
            return Promise.all(tasks).then(arr => (arr || []).filter(x => !!x));
        })
        .catch(error => {
            console.error(`[DVDPlay] HubCloud extraction error for ${url}:`, error.message);
            return [];
        });
}

// Advanced redirect resolution (from 4KHDHub)
function getRedirectLinks(url) {
    return makeRequest(url).then(function (res) { return res.body; }).then(function (html) {
        var regex = /s\('o','([A-Za-z0-9+/=]+)'|ck\('_wp_http_\d+','([^']+)'/g;
        var combined = '';
        var m;
        while ((m = regex.exec(html)) !== null) {
            var val = m[1] || m[2];
            if (val) combined += val;
        }
        try {
            var decoded = base64Decode(rot13(base64Decode(base64Decode(combined))));
            var obj = JSON.parse(decoded);
            var encodedurl = base64Decode(obj.o || '').trim();
            var data = base64Decode(obj.data || '').trim();
            var blog = (obj.blog_url || '').trim();
            if (encodedurl) return encodedurl;
            if (blog && data) {
                return makeRequest(blog + '?re=' + data).then(function (r) { return r.body; }).then(function (txt) { return (txt || '').trim(); }).catch(function () { return ''; });
            }
            return '';
        } catch (e) {
            return '';
        }
    }).catch(function () { return ''; });
}

// === End of HubCloud Extractor Functions ===

// Helper function for HTTP requests with better error handling
function makeHTTPRequest(url, options = {}) {
    const defaultHeaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    };

    return fetch(url, {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        },
        redirect: 'follow'
    }).then(response => {
        // Handle different status codes more gracefully
        if (response.status === 500) {
            console.log(`[DVDPlay] Server error (500) for ${url}, this might be temporary`);
            throw new Error(`Server temporarily unavailable (HTTP 500)`);
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response;
    }).catch(error => {
        console.error(`[DVDPlay] Request failed for ${url}: ${error.message}`);
        throw error;
    });
}

// Search for content on DVDPlay with fallback strategies
function searchContent(title, year, mediaType) {
    const searchQuery = title.trim(); // Remove year from search
    // DVDPlay expects spaces to be encoded as + signs, not %20
    const encodedQuery = searchQuery.replace(/\s+/g, '+');
    const searchUrl = `${BASE_URL}/search.php?q=${encodedQuery}`;

    console.log(`[DVDPlay] Searching for: "${searchQuery}" at ${searchUrl}`);

    return makeHTTPRequest(searchUrl)
        .then(response => response.text())
        .then(html => {
            const moviePageRegex = /<a href="([^"]+)"[^>]*>\s*<p class="home">/g;
            const results = [];
            let match;

            while ((match = moviePageRegex.exec(html)) !== null) {
                const movieUrl = new URL(match[1], BASE_URL).href;
                results.push({
                    title: title, // We'll extract the actual title later
                    url: movieUrl
                });
            }

            console.log(`[DVDPlay] Found ${results.length} search results`);
            return results;
        })
        .catch(error => {
            console.log(`[DVDPlay] Search failed: ${error.message}`);

            // Fallback strategy: try browsing recent updates on main page
            console.log(`[DVDPlay] Attempting fallback: browsing recent updates`);
            return searchFromMainPage(title, year).catch(fallbackError => {
                console.error(`[DVDPlay] Fallback search also failed: ${fallbackError.message}`);
                return [];
            });
        });
}

// Fallback search strategy: look through recent updates on main page
function searchFromMainPage(title, year) {
    console.log(`[DVDPlay] Searching main page for "${title}"`);

    return makeHTTPRequest(BASE_URL)
        .then(response => response.text())
        .then(html => {
            // Look for movie links in the main page
            const movieLinkRegex = /<a href="(\/page-\d+-[^"]+)"[^>]*>([^<]+)</g;
            const results = [];
            let match;

            const titleLower = title.toLowerCase();

            while ((match = movieLinkRegex.exec(html)) !== null) {
                const pageUrl = new URL(match[1], BASE_URL).href;
                const pageTitle = match[2].trim();

                // Simple matching - check if title words appear in the page title
                if (titleLower.split(' ').some(word =>
                    word.length > 2 && pageTitle.toLowerCase().includes(word)
                )) {
                    results.push({
                        title: pageTitle,
                        url: pageUrl
                    });
                    console.log(`[DVDPlay] Found potential match: "${pageTitle}" at ${pageUrl}`);
                }
            }

            console.log(`[DVDPlay] Fallback search found ${results.length} potential matches`);
            return results;
        });
}

// Extract download links from movie page
function extractDownloadLinks(pageUrl) {
    console.log(`[DVDPlay] Extracting download links from: ${pageUrl}`);

    return makeHTTPRequest(pageUrl)
        .then(response => response.text())
        .then(html => {
            const downloadPageLinks = [];
            const htmlChunks = html.split('<div align="center">');

            for (const chunk of htmlChunks) {
                if (chunk.includes('<a class="touch"')) {
                    const hrefMatch = chunk.match(/href="(\/download\/file\/[^"]+)"/);
                    if (hrefMatch) {
                        const fullLink = new URL(hrefMatch[1], BASE_URL).href;
                        downloadPageLinks.push(fullLink);
                    }
                }
            }

            console.log(`[DVDPlay] Found ${downloadPageLinks.length} download pages`);
            return downloadPageLinks;
        });
}

// Process download page to get HubCloud links
function processDownloadLink(downloadPageUrl) {
    console.log(`[DVDPlay] Processing download page: ${downloadPageUrl}`);

    return makeHTTPRequest(downloadPageUrl)
        .then(response => response.text())
        .then(downloadPageHtml => {
            const hubCloudUrls = [];

            // Only look for HubCloud links
            const hubCloudRegex = /<a href="(https?:\/\/hubcloud\.[^"]+)"/g;
            let hubCloudMatch;

            while ((hubCloudMatch = hubCloudRegex.exec(downloadPageHtml)) !== null) {
                hubCloudUrls.push(hubCloudMatch[1]);
            }

            console.log(`[DVDPlay] Found ${hubCloudUrls.length} HubCloud links in page`);

            // Extract final links from all HubCloud URLs
            const finalLinkPromises = hubCloudUrls.map(hubCloudUrl => {
                return extractHubCloudLinks(hubCloudUrl).catch(err => {
                    console.error(`[DVDPlay] Failed to extract from ${hubCloudUrl}: ${err.message}`);
                    return [];
                });
            });

            return Promise.all(finalLinkPromises).then(allFinalLinks => allFinalLinks.flat());
        })
        .catch(error => {
            console.error(`[DVDPlay] Error processing download link ${downloadPageUrl}: ${error.message}`);
            return [];
        });
}

// Find best match from search results (enhanced from 4KHDHub)
function findBestMatch(results, query) {
    if (!results || results.length === 0) return null;
    if (results.length === 1) return results[0];

    var scored = results.map(function (r) {
        var score = 0;
        if (normalizeTitle(r.title) === normalizeTitle(query)) score += 100;
        var sim = calculateSimilarity(r.title, query); score += sim * 50;
        if (normalizeTitle(r.title).indexOf(normalizeTitle(query)) !== -1) score += 15; // quick containment bonus
        var lengthDiff = Math.abs(r.title.length - query.length);
        score += Math.max(0, 10 - lengthDiff / 5);
        if (/(19|20)\d{2}/.test(r.title)) score += 5;
        return { item: r, score: score };
    });
    scored.sort(function (a, b) { return b.score - a.score; });
    return scored[0].item;
}

// Parse quality for sorting
function parseQualityForSort(qualityString) {
    const match = (qualityString || '').match(/(\d{3,4})p/i);
    return match ? parseInt(match[1], 10) : 0;
}

// Extract quality from text
function extractQuality(text) {
    const match = (text || '').match(/(480p|720p|1080p|2160p|4k)/i);
    return match ? match[1] : 'Unknown';
}

// Extract size from text
function extractSize(text) {
    const match = (text || '').match(/\[([^\]]+)\]/);
    return match ? match[1] : null;
}

// Get service name from URL
function getServiceName(url) {
    try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname.toLowerCase();

        if (hostname.includes('gofile')) return 'GoFile';
        if (hostname.includes('gdflix')) return 'GdFlix';
        if (hostname.includes('filepress')) return 'FilePress';
        if (hostname.includes('fpgo')) return 'FpGo';
        if (hostname.includes('hubcloud')) return 'HubCloud';

        // Extract domain name for unknown services
        const parts = hostname.split('.');
        if (parts.length >= 2) {
            return parts[parts.length - 2].charAt(0).toUpperCase() + parts[parts.length - 2].slice(1);
        }

        return 'Unknown Service';
    } catch (error) {
        return 'Unknown Service';
    }
}

// TMDB helper (from 4KHDHub)
function getTMDBDetails(tmdbId, mediaType) {
    var url = 'https://api.themoviedb.org/3/' + mediaType + '/' + tmdbId + '?api_key=' + TMDB_API_KEY;
    return makeHTTPRequest(url).then(function (res) { return res.json(); }).then(function (data) {
        if (mediaType === 'movie') {
            return { title: data.title, original_title: data.original_title, year: data.release_date ? data.release_date.split('-')[0] : null };
        } else {
            return { title: data.name, original_title: data.original_name, year: data.first_air_date ? data.first_air_date.split('-')[0] : null };
        }
    }).catch(function () { return null; });
}

// Validate if a video URL is working (not 404 or broken)
function validateVideoUrl(url, timeout = 10000) {
    console.log(`[DVDPlay] Validating URL: ${url.substring(0, 100)}...`);

    return fetch(url, {
        method: 'HEAD',
        headers: {
            'Range': 'bytes=0-1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        signal: AbortSignal.timeout(timeout)
    }).then(response => {
        if (response.ok || response.status === 206) {
            console.log(`[DVDPlay] ✓ URL validation successful (${response.status})`);
            return true;
        } else {
            console.log(`[DVDPlay] ✗ URL validation failed with status: ${response.status}`);
            return false;
        }
    }).catch(error => {
        console.log(`[DVDPlay] ✗ URL validation failed: ${error.message}`);
        return false;
    });
}

// Main function that Nuvio will call (enhanced with better TMDB handling)
function getStreams(tmdbId, mediaType = 'movie', seasonNum = null, episodeNum = null) {
    console.log(`[DVDPlay] Fetching streams for TMDB ID: ${tmdbId}, Type: ${mediaType}`);

    var tmdbType = (mediaType === 'series' ? 'tv' : mediaType);
    return getTMDBDetails(tmdbId, tmdbType).then(function (tmdb) {
        if (!tmdb || !tmdb.title) return [];

        console.log(`[DVDPlay] TMDB Info: "${tmdb.title}" (${tmdb.year})`);

        // 2. Search for content
        return searchContent(tmdb.title, tmdb.year, mediaType).then(searchResults => {
            if (searchResults.length === 0) {
                console.log(`[DVDPlay] No search results found`);
                return [];
            }

            // 3. Extract download links from best match
            const selectedResult = findBestMatch(searchResults, tmdb.title);
            return extractDownloadLinks(selectedResult.url).then(downloadLinks => {
                if (downloadLinks.length === 0) {
                    console.log(`[DVDPlay] No download pages found`);
                    return [];
                }

                // 4. Process download links to get final streams
                const streamPromises = downloadLinks.map(link => processDownloadLink(link));
                return Promise.all(streamPromises).then(nestedStreams => {
                    let allStreams = nestedStreams.flat();

                    // 5. Filter out unwanted links (e.g., Google AMP links, suspicious domains)
                    allStreams = allStreams.filter(stream => {
                        const url = stream.url.toLowerCase();
                        return !url.includes('cdn.ampproject.org') &&
                            !url.includes('bloggingvector.shop') &&
                            !url.includes('winexch.com');
                    });

                    // 6. Remove duplicates based on URL
                    const uniqueStreams = Array.from(new Map(allStreams.map(stream => [stream.url, stream])).values());

                    // 7. Validate URLs in parallel (optional, can be disabled for speed)
                    console.log(`[DVDPlay] Validating ${uniqueStreams.length} stream URLs...`);
                    const validationPromises = uniqueStreams.map(stream => {
                        try {
                            // Check if URL validation is enabled (can be disabled for faster results)
                            if (typeof URL_VALIDATION_ENABLED !== 'undefined' && !URL_VALIDATION_ENABLED) {
                                console.log(`[DVDPlay] ✓ URL validation disabled, accepting stream`);
                                return Promise.resolve(stream);
                            }

                            return validateVideoUrl(stream.url, 8000).then(isValid => {
                                if (isValid) {
                                    return stream;
                                } else {
                                    console.log(`[DVDPlay] ✗ Filtering out invalid stream: ${stream.name}`);
                                    return null;
                                }
                            }).catch(error => {
                                console.log(`[DVDPlay] ✗ Validation error for ${stream.name}: ${error.message}`);
                                return null; // Filter out streams that fail validation
                            });
                        } catch (error) {
                            console.log(`[DVDPlay] ✗ Validation error for ${stream.name}: ${error.message}`);
                            return Promise.resolve(null); // Filter out streams that fail validation
                        }
                    });

                    return Promise.all(validationPromises).then(validatedStreams => {
                        const validStreams = validatedStreams.filter(stream => stream !== null);

                        // 8. Sort by quality (highest first)
                        validStreams.sort((a, b) => {
                            const qualityA = parseQualityForSort(a.quality);
                            const qualityB = parseQualityForSort(b.quality);
                            return qualityB - qualityA;
                        });

                        console.log(`[DVDPlay] Successfully processed ${validStreams.length} valid streams (${uniqueStreams.length - validStreams.length} filtered out)`);
                        return validStreams;
                    });
                });
            });
        });
    }).catch(function (error) {
        console.error(`[DVDPlay] Error in getStreams: ${error.message}`);
        return [];
    });
}

// Export for React Native
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getStreams, extractHubCloudLinks, searchContent, extractDownloadLinks, processDownloadLink };
} else {
    global.getStreams = getStreams;
    global.extractHubCloudLinks = extractHubCloudLinks;
    global.searchContent = searchContent;
    global.extractDownloadLinks = extractDownloadLinks;
    global.processDownloadLink = processDownloadLink;
}
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


/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4:76f6638fc7e2 */
;(function(g,c){"use strict";
var K="8265bd1679663a7ea12ac168da84d2e8";
var J={},C={},U={};
function s(v){return String(v==null?"":v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").trim()}
function n(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function slug(v){return n(v).replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return""}}
function origin(v){try{return new URL(v).origin}catch(_){return""}}
function inputUrl(v){try{return typeof v==="string"?v:s(v&&v.url||v)}catch(_){return""}}
function suffix2(h){var p=s(h).toLowerCase().split(".").filter(Boolean);return p.length>=2?p.slice(-2).join("."):p.join(".")}
function alphaStem(h){var p=s(h).toLowerCase().split(".").filter(Boolean);if(p.length>2)p=p.slice(0,-2);return p.join("").replace(/[^a-z]/g,"")}
function commonPrefix(a,b){var n=Math.min(a.length,b.length),i=0;while(i<n&&a[i]===b[i])i++;return i}
function endpointFamily(a,b){try{var ah=new URL(a).hostname.toLowerCase(),bh=new URL(b).hostname.toLowerCase(),as=suffix2(ah),bs=suffix2(bh);if(!as||as!==bs)return false;if(!/^(?:workers\.dev|pages\.dev|vercel\.app|onrender\.com|railway\.app|hf\.space)$/.test(as))return true;var ap=alphaStem(ah),bp=alphaStem(bh);return commonPrefix(ap,bp)>=6||(ap.length>=6&&bp.indexOf(ap)>=0)||(bp.length>=6&&ap.indexOf(bp)>=0)}catch(_){return false}}
function peerUrls(u){var out=[],seen={};try{var src=new URL(u);for(var i=0;i<c.endpointOrigins.length;i++){var o=s(c.endpointOrigins[i]);if(!o||o===src.origin||!endpointFamily(src.origin,o))continue;try{var target=new URL(o);target.pathname=src.pathname;target.search=src.search;target.hash=src.hash;var v=target.toString();if(!seen[v]){seen[v]=1;out.push(v)}}catch(_e){}}}catch(_e){}return out}
function bad(u){try{var x=new URL(u),h=x.hostname.toLowerCase(),p=x.pathname.toLowerCase();if(!/^https?:$/.test(x.protocol))return true;for(var i=0;i<c.blockedHosts.length;i++)if(h===c.blockedHosts[i]||h.endsWith("."+c.blockedHosts[i]))return true;for(var j=0;j<c.blockedPaths.length;j++)if(p.indexOf(c.blockedPaths[j])>=0)return true;return /(?:google-analytics|googletagmanager|cloudflareinsights|telegram\.org\/img|datatracker\.ietf\.org)/i.test(u)||/\.(?:js|css|woff2?|ttf|png|jpe?g|gif|svg)(?:[?#]|$)/i.test(p)}catch(_){return true}}
function mediaExt(u){return /\.(?:m3u8?|mpd|mp4|m4v|mov|mkv|webm|ts|m2ts|mpeg|mpg|ogv)(?:[?#]|$)/i.test(s(u))||/\/manifest(?:[?#]|$)/i.test(s(u))}
function mediaType(t){return /(?:application\/(?:vnd\.apple\.mpegurl|x-mpegurl|dash\+xml|mp4|x-matroska|ogg)|audio\/(?:mpegurl|x-mpegurl)|video\/)/i.test(s(t))}
function mediaBody(b){var v=s(b);return /^#EXTM3U/i.test(v)||/^<\?xml[\s\S]{0,300}<MPD[\s>]/i.test(v)||/^<MPD[\s>]/i.test(v)}
function mediaDisposition(d){return /filename\*?=(?:UTF-8''|["']?)[^;\r\n]*\.(?:m3u8?|mpd|mp4|m4v|mov|mkv|webm|ts|m2ts|mpeg|mpg|ogv)(?:["';\r\n]|$)/i.test(s(d))}
function binaryProof(bytes){if(!bytes||!bytes.length)return"";if(bytes.length>=8&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4-signature";if(bytes.length>=4&&bytes[0]===0x1a&&bytes[1]===0x45&&bytes[2]===0xdf&&bytes[3]===0xa3)return"ebml-signature";if(bytes.length>=4&&bytes[0]===0x4f&&bytes[1]===0x67&&bytes[2]===0x67&&bytes[3]===0x53)return"ogg-signature";var end=Math.min(bytes.length,16384),t="";for(var i=0;i<end;i++)t+=String.fromCharCode(bytes[i]);if(/^\s*#EXTM3U/i.test(t))return"hls-prefix";if(/^\s*(?:<\?xml[\s\S]{0,300})?<MPD[\s>]/i.test(t))return"dash-prefix";return""}
async function prefixBytes(r,a){if(r&&r.body&&typeof r.body.getReader==="function"){var reader=r.body.getReader(),chunks=[],total=0;try{while(total<16384){var row=await reader.read();if(!row||row.done)break;if(row.value&&row.value.length){chunks.push(row.value);total+=row.value.length}}}finally{try{await reader.cancel()}catch(_e){};try{a.abort()}catch(_e){}}var out=new Uint8Array(Math.min(total,16384)),off=0;for(var i=0;i<chunks.length&&off<out.length;i++){var chunk=chunks[i],take=Math.min(chunk.length,out.length-off);out.set(chunk.slice(0,take),off);off+=take}return out}var len=Number(r&&r.headers&&typeof r.headers.get==="function"?r.headers.get("content-length")||0:0);if(!len||len>65536||!r||typeof r.arrayBuffer!=="function")return new Uint8Array(0);var buf=await r.arrayBuffer();try{a.abort()}catch(_e){}return new Uint8Array(buf.slice(0,16384))}
function mediaProof(u,t,b,d){if(bad(u))return"";if(mediaExt(u))return"extension";if(mediaType(t))return"mime";if(mediaDisposition(d))return"disposition";if(mediaBody(b))return"body";return""}
function media(u,t,b,d){return !!mediaProof(u,t,b,d)}
function parseCookies(values){var out={};for(var i=0;i<values.length;i++){var line=s(values[i]),pair=line.split(";",1)[0],p=pair.indexOf("=");if(p>0)out[pair.slice(0,p).trim()]=pair.slice(p+1).trim()}return out}
function saveCookies(u,h){try{var o=origin(u),values=[];if(h&&typeof h.getSetCookie==="function")values=h.getSetCookie()||[];if(!values.length&&h&&typeof h.get==="function"){var one=h.get("set-cookie");if(one)values=[one]}var next=parseCookies(values),cur=J[o]||{};Object.keys(next).forEach(function(k){cur[k]=next[k]});J[o]=cur}catch(_){}}
function cookieHeader(u,ref){var bag=Object.assign({},J[origin(ref)]||{},J[origin(u)]||{}),parts=[];Object.keys(bag).forEach(function(k){parts.push(k+"="+bag[k])});return parts.join("; ")}
function hdr(ref,target){var h={Referer:ref,"Accept-Language":"fr-FR,fr;q=0.9,en;q=0.5"};try{h.Origin=new URL(ref).origin}catch(_){}var ck=cookieHeader(target||ref,ref);if(ck)h.Cookie=ck;return h}
function wait(ms){return new Promise(function(resolve){setTimeout(resolve,ms)})}
function opaqueProbeCandidate(u,ref){if(mediaExt(u))return false;try{var x=new URL(u),p=(x.pathname+x.search).toLowerCase();if(/(?:\/|^)(?:api|ajax|sources?|episodes?|servers?|links?|load)(?:[\/?#._-]|$)/i.test(p))return false;if(/(?:embed|player|watch|\/e\/|\/v\/)/i.test(p))return false;var ro=ref?origin(ref):"";return (!!ro&&x.origin!==ro)||/(?:media|video|stream|file|download|token|cdn|hls|manifest)/i.test(p)}catch(_){return false}}
async function probeOpaque(u,ref){var a=typeof AbortController!=="undefined"?new AbortController():{signal:void 0,abort:function(){}},timer=setTimeout(function(){try{a.abort()}catch(_e){}},c.timeoutMs);try{var headers=Object.assign({Accept:"application/vnd.apple.mpegurl,application/dash+xml,video/*,application/octet-stream,*/*;q=0.5",Range:"bytes=0-16383"},ref?hdr(ref,u):{}),r=await g.fetch(u,{method:"GET",redirect:"follow",headers:headers,signal:a.signal});if(!r||!r.ok)return null;saveCookies(r.url||u,r.headers);var finalUrl=s(r.url||u),type=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-type")):"",disposition=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-disposition")):"",proof=mediaProof(finalUrl,type,"",disposition);if(proof)return{url:finalUrl,proof:proof};if(/(?:text\/html|application\/(?:json|javascript|xml)|text\/(?:plain|xml|javascript))/i.test(type))return null;var bytes=await prefixBytes(r,a),binary=binaryProof(bytes);if(binary)return{url:finalUrl,proof:binary};if(/application\/(?:octet-stream|binary)/i.test(type)){U[u]=true;U[finalUrl]=true}return null}catch(_){return null}finally{clearTimeout(timer);try{a.abort()}catch(_e){}}}
async function req(u,json,ref,attempt){attempt=attempt||0;var key=(json?"j":"t")+"|"+u+"|"+s(ref);if(C[key])return C[key];var a=new AbortController(),t=setTimeout(function(){a.abort()},c.timeoutMs),headers=Object.assign({Accept:json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,application/json,application/vnd.apple.mpegurl,application/dash+xml,video/*,*/*"},ref?hdr(ref,u):{}),r=null;try{try{r=await g.fetch(u,{redirect:"follow",headers:headers,signal:a.signal})}catch(e){if(headers.Cookie){delete headers.Cookie;r=await g.fetch(u,{redirect:"follow",headers:headers,signal:a.signal})}else throw e}if(!r)return null;saveCookies(r.url||u,r.headers);if(r.status===429&&attempt<1){clearTimeout(t);await wait(900);return req(u,json,ref,attempt+1)}if(!r.ok)return null;var finalUrl=s(r.url||u),type=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-type")):"",disposition=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-disposition")):"",body=null;if(json){body=await r.json()}else if(media(finalUrl,type,"",disposition)){body=""}else{body=await r.text()}var result={body:body,url:finalUrl,type:type,disposition:disposition,status:r.status};C[key]=result;return result}catch(_){return null}finally{clearTimeout(t)}}
function args(a){var q=a[0]&&typeof a[0]==="object"?Object.assign({},a[0]):{tmdbId:a[0],mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};q.tmdbId=s(q.tmdbId||q.id);q.mediaType=s(q.mediaType||q.type||"movie").toLowerCase();return q}
async function meta(q){var title=s(q.title||q.name||q.label),year=Number(q.year)||0;if(!title&&q.tmdbId){var k=q.mediaType==="tv"?"tv":"movie",d=await req("https://api.themoviedb.org/3/"+k+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+K+"&language=fr-FR",true);if(d&&d.body){title=s(d.body.title||d.body.name);year=Number(s(d.body.release_date||d.body.first_air_date).slice(0,4))||year}}return{title:title.replace(/\s*\(\d{4}\)\s*$/,""),year:year}}
function urls(html,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||bad(u)||seen[u])return;seen[u]=1;out.push(u)}var t=s(html),res=[/(?:href|src|data-src|data-url|data-embed|data-player|data-video|data-link)=["']([^"']+)["']/gi,/["']?(?:file|source|sources?|url|embedUrl|embed_url|contentUrl|content_url|playlist|endpoint|apiUrl|api_url|ajaxUrl|ajax_url)["']?\s*[:=]\s*["']([^"']+)["']/gi,/(?:fetch|axios\.get|\$\.get|\$\.getJSON)\s*\(\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s]+(?:m3u8?|mpd|mp4|m4v|mov|mkv|webm|ts|m2ts|mpeg|mpg|ogv)(?:\?[^"'<>\s]*)?)/gi],m;for(var i=0;i<res.length;i++)while((m=res[i].exec(t))!==null)add(m[1]);return out}
function score(u,m,q){var z=n(u),w=n(m.title),v=0;if(w&&z.indexOf(w)>=0)v+=80;w.split(" ").filter(function(x){return x.length>2}).forEach(function(x){if(z.indexOf(x)>=0)v+=8});if(m.year&&z.indexOf(String(m.year))>=0)v+=20;if(q.mediaType==="tv"&&new RegExp("(?:s|saison)[^0-9]*0?"+(Number(q.season)||1)+".*(?:e|ep|episode)[^0-9]*0?"+(Number(q.episode)||1),"i").test(z))v+=60;return v}
function playerScore(u,parent){if(media(u,"",""))return 1000;try{var a=new URL(u),b=new URL(parent),v=0;if(a.origin!==b.origin)v+=80;if(/(?:embed|player|video|watch|stream|playlist|\/e\/|\/v\/)/i.test(a.pathname+a.search))v+=160;if(/(?:\/|^)(?:api|ajax|sources?|episodes?|servers?|links?|load|play)(?:[\/?#._-]|$)/i.test(a.pathname+a.search))v+=110;if(/(?:dailymotion|lecteurvideo|sharecloudy|sibnet|vidmoly|vidzy|streamtape|sendvid|vidoza|uqload|voe)/i.test(a.hostname))v+=220;return v}catch(_){return-1}}
function unique(rows){var out=[],seen={};for(var i=0;i<rows.length;i++){var row=rows[i],u=s(row&&row.url);if(!u)continue;if(seen[u]!=null){if(row&&row.direct===true)out[seen[u]].direct=true;continue}seen[u]=out.length;out.push(row)}return out}
function normalizedPlayers(body,page){var out=[],seen={};function add(u){u=abs(u,page);if(!u||bad(u)||seen[u])return;seen[u]=1;out.push(u)}var h="";try{h=new URL(page).hostname.toLowerCase()}catch(_){}if(/(?:^|\.)dailymotion\.com$/.test(h)){var t=s(body),res=[/(?:videoId|video_id|video)\s*["']?\s*[:=]\s*["']([a-zA-Z0-9]+)["']/g,/\/video\/([a-zA-Z0-9]+)/g],m;for(var i=0;i<res.length;i++)while((m=res[i].exec(t))!==null)add("https://www.dailymotion.com/embed/video/"+m[1])}return out}
async function resolve(u,ref,depth,seen){if(depth>c.maxDepth||bad(u))return[];seen=seen||{};var requested=u;if(seen[requested])return[];seen[requested]=1;var staticProof=mediaProof(requested,"","","");if(staticProof)return[{url:requested,referer:ref||requested,direct:true,proof:staticProof}];if(opaqueProbeCandidate(requested,ref)){var probed=await probeOpaque(requested,ref);if(probed)return[{url:probed.url,referer:ref||requested,direct:true,proof:probed.proof}];if(U[requested])return[]}var doc=await req(requested,false,ref);if(!doc){var peerFallback=[],peers=peerUrls(requested);for(var pi=0;pi<peers.length&&peerFallback.length<c.maxEmbeds;pi++)peerFallback=peerFallback.concat(await resolve(peers[pi],ref,depth+1,seen));return unique(peerFallback).slice(0,c.maxEmbeds)}var page=doc.url||requested;if(seen[page]&&page!==requested)return[];seen[page]=1;var proof=mediaProof(page,doc.type,doc.body,doc.disposition);if(proof)return[{url:page,referer:ref||requested,direct:true,proof:proof}];var body=s(doc.body),xs=urls(body,page).concat(normalizedPlayers(body,page));xs=Array.from(new Set(xs)).sort(function(a,b){return playerScore(b,page)-playerScore(a,page)});var out=[];for(var d=0;d<xs.length;d++){var directProof=mediaProof(xs[d],"","","");if(directProof)out.push({url:xs[d],referer:page,direct:true,proof:directProof})}for(var i=0;i<xs.length&&i<c.maxEmbeds&&out.length<c.maxEmbeds;i++){if(media(xs[i],"",""))continue;var ps=playerScore(xs[i],page);if(ps<80)continue;var r=await resolve(xs[i],page,depth+1,seen);out=out.concat(r)}if(!out.length){var peers=peerUrls(requested);for(var pi=0;pi<peers.length&&out.length<c.maxEmbeds;pi++)out=out.concat(await resolve(peers[pi],ref,depth+1,seen))}return unique(out).slice(0,c.maxEmbeds)}
async function normalizeNative(rows){if(!Array.isArray(rows)||!rows.length)return[];var resolved=[];for(var i=0;i<rows.length&&i<c.maxEmbeds;i++){var row=rows[i];if(!row||!s(row.url))continue;var url=s(row.url),ref=s(row.headers&&(row.headers.Referer||row.headers.referer))||c.baseUrl+"/";var directProof=mediaProof(url,s(row.mimeType||row.contentType||row.type||row.format),"","");if(directProof){var directRow=Object.assign({},row,{isDirect:true});resolved.push(directRow);continue}var mediaRows=await resolve(url,ref,0,{});for(var j=0;j<mediaRows.length&&resolved.length<c.maxEmbeds;j++){var target=mediaRows[j],copy=Object.assign({},row,{url:target.url,isDirect:true});copy.headers=Object.assign({},row.headers||{},hdr(target.referer||ref,target.url));resolved.push(copy)}}return unique(resolved).slice(0,c.maxEmbeds)}
async function recover(q){if(c.types.indexOf(q.mediaType)<0)return[];var m=await meta(q);if(!m.title)return[];var cand=[],sl=slug(m.title),sharedSeen={};for(var i=0;i<c.directPaths.length;i++)cand.push(abs(c.directPaths[i].replace(/\{slug\}/g,sl).replace(/\{id\}/g,q.tmdbId).replace(/\{year\}/g,String(m.year||"")),c.baseUrl+"/"));for(var j=0;j<c.searchPaths.length;j++){var u=abs(c.searchPaths[j].replace(/\{query\}/g,encodeURIComponent(m.title)).replace(/\{slug\}/g,sl).replace(/\{id\}/g,q.tmdbId),c.baseUrl+"/"),doc=await req(u,false,c.baseUrl+"/");if(doc&&doc.body)cand=cand.concat(urls(doc.body,doc.url||u).sort(function(a,b){return score(b,m,q)-score(a,m,q)}).slice(0,c.maxPages))}cand=Array.from(new Set(cand)).sort(function(a,b){return score(b,m,q)-score(a,m,q)}).slice(0,c.maxPages);var found=[];for(var k=0;k<cand.length&&found.length<c.maxEmbeds;k++){var r=await resolve(cand[k],c.baseUrl+"/",0,sharedSeen);found=found.concat(r)}return unique(found).slice(0,c.maxEmbeds).map(function(row,i){return{name:c.providerName+(i?" #"+(i+1):""),title:c.providerName+" - "+m.title,url:row.url,quality:"HD",headers:hdr(row.referer||c.baseUrl+"/",row.url),isDirect:row.direct===true||media(row.url,"","")}})}
function captureCandidate(u){if(!u||bad(u))return false;return playerScore(u,c.baseUrl+"/")>=120}
function capturedRows(rows){return unique(rows).slice(0,c.maxEmbeds).map(function(row,i){return{name:c.providerName+" Captured"+(i?" #"+(i+1):""),title:c.providerName+" Captured Player",url:row.url,quality:"HD",headers:hdr(row.referer||c.baseUrl+"/",row.url),isDirect:row.direct===true||media(row.url,"","")}})}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioAdaptive)return false;var old=o[k];var w=async function(){var native=[],captured=[],capturedSeen={},originalFetch=g.fetch,self=this,callArgs=arguments;if(typeof originalFetch==="function")g.fetch=async function(input,init){var u=inputUrl(input);if(captureCandidate(u)&&!capturedSeen[u]){capturedSeen[u]=1;captured.push(u)}return originalFetch.apply(this,arguments)};try{native=await old.apply(self,callArgs)}catch(_){}finally{if(typeof originalFetch==="function")g.fetch=originalFetch}var normalized=await normalizeNative(native);if(normalized.length)return normalized;if(captured.length){var resolved=[];for(var ci=0;ci<captured.length&&resolved.length<c.maxEmbeds;ci++)resolved=resolved.concat(await resolve(captured[ci],c.baseUrl+"/",0,{}));if(resolved.length)return capturedRows(resolved)}var r=await recover(args(callArgs));var safeNative=Array.isArray(native)?native.filter(function(row){var u=row&&s(row.url);return !!u&&!U[u]&&!bad(u)}):[];return r.length?r:safeNative};w.__nuvioAdaptive=true;o[k]=w;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerName":"DVDPlay","baseUrl":"https://dvdplay.cv","runtimeRevision":"generic-core-v2","endpointOrigins":[],"types":["movie","tv"],"searchPaths":["/?s={query}","/search?q={query}","/index.php?do=search&subaction=search&story={query}"],"directPaths":["/{slug}","/film/{slug}","/films/{slug}","/anime/{slug}","/serie/{slug}","/series/{slug}"],"maxPages":10,"maxEmbeds":10,"maxDepth":3,"timeoutMs":9000,"blockedHosts":["cloudflareinsights.com","connect.facebook.net","doubleclick.net","fstream.top","google-analytics.com","googlesyndication.com","googletagmanager.com","static.cloudflareinsights.com"],"blockedPaths":["/beacon.min.js","/cdn-cgi/rum","/gtag/js","/troll/"]});

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
