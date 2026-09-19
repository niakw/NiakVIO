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