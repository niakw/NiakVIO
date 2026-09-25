# NiakVIO StreamBadges — technical media guide

[Français](fr/stream-badges-technical-guide.md) · [Install StreamBadges](how-to-add-stream-badges.md) · [Back to README](../README.md)

NiakVIO StreamBadges are not a quality score. They are a compact vocabulary for **facts about a stream**: source, resolution, delivery format, container, video codec, HDR, frame rate, bitrate, audio, languages, subtitles and content rating.

> **Rule:** show what is known, keep what is unknown unknown. A truthful `HLS` badge is better than inventing `1080p`, `HEVC` or `HDR`.

Current stable feed: `assets/stream-badges-fusion-v4.json` — **301 badges / 16 groups**.

## Quick visual ranking

The markers below are a **reading aid, not a universal quality score**. They only rank the dimension named by the table; they must not be combined blindly.

| Marker | Reading |
| --- | --- |
| 🏆 | Top / highest potential in this dimension |
| 🟢 | Strong / modern / high potential |
| 🟡 | Solid, variable or context-dependent |
| 🟠 | Limited, older or lower potential |
| 🔴 | Weak / heavily compromised |
| ⚪ | Neutral fact — not meaningfully rankable |

For actual picture quality, read several facts together: **source + codec + resolution + bitrate**.

## Read one stream like a media sheet

Example:

`AVC · 1920×1080 · 6.0 Mbps · 23.976 fps · AAC · Stereo · 48 kHz · Korean`

| Fact | What it means |
| --- | --- |
| AVC / H.264 | Very widely supported video codec. At similar visual quality it normally needs more bitrate than HEVC or AV1. |
| 1920×1080 | Full HD / 1080p frame size. It does **not** tell you whether the source is Blu-ray or WEB-DL. |
| 6.0 Mbps | Video bitrate. A plausible 1080p streaming bitrate, but not a quality grade by itself. |
| 23.976 fps | Extremely common film/anime cadence derived from 24 fps. |
| AAC | Lossy audio codec widely used by streaming services. |
| Stereo / 2.0 | Two audio channels. |
| 48 kHz | Standard sample rate for film, TV and anime delivery. |
| Korean | Audio-language fact, normalized to the universal `KO` badge. |

<img src="../assets/transparent/96x40/1080p-full-hd.webp" height="30" alt="1080p"> <img src="../assets/transparent/96x40/avc.webp" height="30" alt="AVC"> <img src="../assets/transparent/96x40/video-bitrate.webp" height="30" alt="Bitrate"> <img src="../assets/transparent/96x40/23.976fps.webp" height="30" alt="23.976 fps"> <img src="../assets/transparent/96x40/aac.webp" height="30" alt="AAC"> <img src="../assets/transparent/96x40/2.0.webp" height="30" alt="2.0"> <img src="../assets/transparent/96x40/48khz.webp" height="30" alt="48 kHz"> <img src="../assets/transparent/96x40/lang-ko.webp" height="30" alt="KO">

## Source ≠ resolution ≠ delivery ≠ container

These four families describe different things.

### Source / release provenance

| Badge family | Quality potential | Practical meaning |
| --- | --- | --- |
| BD REMUX / UHD REMUX | 🏆 Top | Disc tracks repackaged without re-encoding the encoded essence. Usually large files. |
| UHD Blu-ray | 🏆 Top | Ultra HD optical-disc source, commonly 2160p with HDR-capable video. |
| Blu-ray / BDMV | 🟢 Very high | Optical-disc-derived source/structure. |
| WEB-DL | 🟢 High | Direct web-service delivery, usually without a screen/video recapture step. |
| HDTV | 🟡 Variable | Broadcast-derived source; quality depends heavily on channel, generation and bitrate. |
| WEBRip | 🟡 Variable | Capture or re-encode from a web source; quality can vary widely. |
| DVD / DVD Rip | 🟠 Limited | Standard-definition optical-disc source. |
| CAM / TS / TC | 🔴 Low | Cinema capture provenance. Useful information, but usually heavily compromised versus direct digital sources. |

<img src="../assets/transparent/96x40/webdl.webp" height="30" alt="WEB-DL"> <img src="../assets/transparent/96x40/blu-ray-disc.webp" height="30" alt="Blu-ray"> <img src="../assets/transparent/96x40/bdmv.webp" height="30" alt="BDMV"> <img src="../assets/transparent/96x40/blu-ray-remux.webp" height="30" alt="BD REMUX"> <img src="../assets/transparent/96x40/uhd-remux.webp" height="30" alt="UHD REMUX">

### Resolution and scan mode

Common classes include 240p, 360p, 480p, 576p, 720p, **1080i**, 1080p, 1440p, 2160p/4K and 4320p/8K.

| Resolution class | Detail potential | Practical reading |
| --- | --- | --- |
| 4320p / 8K | 🏆 Top | Highest raster detail potential listed here; useful only when the source and encode actually preserve that detail. |
| 2160p / 4K | 🟢 Very high | Excellent large-screen detail potential; often paired with HEVC/AV1 and HDR. |
| 1440p | 🟢 High | Clear step above 1080p, less common for film/TV delivery. |
| 1080p | 🟢 Strong | Full HD baseline for high-quality modern streaming. |
| 1080i | 🟡 Contextual | Full HD raster but interlaced; deinterlacing quality matters. |
| 720p | 🟡 Good | Can look excellent with a strong source and bitrate, especially for animation. |
| 576p / 480p | 🟠 Limited | Standard definition; visibly softer on modern large displays. |
| 360p / 240p | 🔴 Low | Low-detail delivery, mainly useful when bandwidth is constrained. |

- **1080p** is progressive Full HD.
- **1080i** is interlaced Full HD, still encountered in broadcast-derived material.
- A cropped 1080p movie may not literally be 1920×1080 after black bars are removed; the delivery class can still be 1080p.
- Resolution alone says nothing about source quality, codec efficiency or compression artifacts.

<img src="../assets/transparent/96x40/720p-hd.webp" height="30" alt="720p"> <img src="../assets/transparent/96x40/1080i.webp" height="30" alt="1080i"> <img src="../assets/transparent/96x40/1080p-full-hd.webp" height="30" alt="1080p"> <img src="../assets/transparent/96x40/4k-ultra-hd.webp" height="30" alt="4K"> <img src="../assets/transparent/96x40/8k-ultra-hd.webp" height="30" alt="8K">

### Delivery format and container

**HLS** and **MPEG-DASH** describe adaptive HTTP delivery. **MKV, MP4, WebM, MPEG-TS and M2TS** are containers/file formats.

| Badge | Rank | Meaning |
| --- | --- | --- |
| HLS / M3U8 | ⚪ Context | Adaptive HTTP streaming. A master playlist may advertise several variants, codecs and language renditions. |
| MPEG-DASH / MPD | ⚪ Context | Adaptive HTTP delivery based on an MPD manifest. |
| MKV / Matroska | ⚪ Context | Flexible multi-track container common for Blu-ray/anime releases. |
| MP4 | ⚪ Context | Highly compatible container. |
| MPEG-TS / M2TS | ⚪ Context | Transport-stream families common in broadcast, HLS segments and Blu-ray structures. |

**No winner here:** delivery/container format does not determine picture quality by itself.

<img src="../assets/transparent/96x40/hls.webp" height="30" alt="HLS"> <img src="../assets/transparent/96x40/dash.webp" height="30" alt="DASH"> <img src="../assets/transparent/96x40/mkv.webp" height="30" alt="MKV"> <img src="../assets/transparent/96x40/mp4.webp" height="30" alt="MP4">

A provider can legitimately expose **only HLS** when the URL proves `.m3u8` delivery but no reliable quality/codec fact is available.

## Video codecs

| Codec | Compression efficiency | Typical context | What to know |
| --- | --- | --- | --- |
| AV1 | 🏆 Top | Modern streaming | Very high compression efficiency; hardware support is newer. |
| HEVC / H.265 | 🟢 Very high | UHD Blu-ray, 4K streaming, 10-bit anime encodes | High efficiency; common with HDR and 10-bit. |
| VP9 | 🟢 High | Web streaming | Strong web codec historically common on Google platforms. |
| AVC / H.264 | 🟡 Solid | Blu-ray and very broad streaming | Excellent compatibility; normally needs more bitrate than HEVC/AV1 for similar visual quality. |
| MPEG-2 / VC-1 / MPEG-4 Part 2 | 🟠 Legacy | Legacy broadcast/disc/encodes | Useful compatibility and provenance information; generally less efficient than modern codecs. |

These markers compare **compression efficiency in broad terms**, not the quality of every individual encode. A carefully encoded AVC stream can still beat a poor AV1/HEVC encode.

<img src="../assets/transparent/96x40/avc.webp" height="30" alt="AVC"> <img src="../assets/transparent/96x40/hevc.webp" height="30" alt="HEVC"> <img src="../assets/transparent/96x40/av1.webp" height="30" alt="AV1"> <img src="../assets/transparent/96x40/vp9.webp" height="30" alt="VP9">

**x264/x265 are encoders**, while AVC/H.264 and HEVC/H.265 are codec standards. NiakVIO normalizes common aliases to the codec fact.

## Bit depth, HDR and presentation formats

NiakVIO distinguishes 8-bit, 10-bit and 12-bit from dynamic range.

- **10-bit does not automatically mean HDR.** High-quality anime encodes are often 10-bit SDR.
- HDR families include SDR, generic HDR, HDR10, HDR10+, Dolby Vision and HLG.
- IMAX, IMAX Enhanced and 3D are separate presentation facts.

<img src="../assets/transparent/96x40/10bit.webp" height="30" alt="10-bit"> <img src="../assets/transparent/96x40/hdr10.webp" height="30" alt="HDR10"> <img src="../assets/transparent/96x40/hdr10-plus.webp" height="30" alt="HDR10+"> <img src="../assets/transparent/96x40/dolby-vision.webp" height="30" alt="Dolby Vision">

## Frame rate

Normalized values include 23.976, 24, 25, 29.97, 30, 50, 59.94 and 60 fps.

- 23.976/24 fps dominates cinema and much anime.
- 25/50 fps is common in PAL-derived broadcast environments.
- 29.97/59.94 derives from NTSC-era timing.
- A higher number is not automatically “better” or “more cinematic”; frame rate is a creative and delivery choice.

## Bitrate

NiakVIO keeps the **exact value** in the technical description and uses the generic BITRATE badge only to show that the measurement exists.

Rough orientation ranges:

| Delivery | Common ballpark | Raw bitrate headroom |
| --- | --- | --- |
| UHD Blu-ray | commonly tens of Mbps, sometimes much higher | 🏆 Very high |
| Blu-ray AVC | often ~15–35+ Mbps | 🟢 High |
| 4K HEVC streaming | often ~10–25 Mbps | 🟢 High |
| 1080p H.264 streaming | ~3–10 Mbps | 🟡 Contextual |
| 1080p HEVC streaming | ~1.5–6 Mbps | 🟡 Contextual |

**Headroom is not a quality score.** Higher Mbps usually means more encoded data, but resolution, codec efficiency, source quality, encoder settings, grain and motion determine how effectively those bits are used.

These are not quality thresholds. A 6 Mbps AVC encode and a 6 Mbps AV1 encode are not equivalent; source, codec, encoder settings, grain and motion matter.

## Audio: codec, technology, channels and sample rate

NiakVIO keeps these as separate facts.

- codecs: AAC, AC-3, E-AC-3, TrueHD, DTS/DTS-HD, FLAC, PCM/LPCM, Opus, MP3, ALAC;
- technologies: Dolby Atmos, DTS:X;
- channels: 1.0, 2.0, 2.1, 5.1, 7.1;
- sample rates: 44.1, 48, 88.2, 96 and 192 kHz.

<img src="../assets/transparent/96x40/aac.webp" height="30" alt="AAC"> <img src="../assets/transparent/96x40/dolby-atmos.webp" height="30" alt="Atmos"> <img src="../assets/transparent/96x40/truehd.webp" height="30" alt="TrueHD"> <img src="../assets/transparent/96x40/5.1.webp" height="30" alt="5.1"> <img src="../assets/transparent/96x40/48khz.webp" height="30" alt="48 kHz">

48 kHz is the normal baseline for film/TV/video. 96 or 192 kHz by itself is not proof of better audible quality.

## Languages and subtitles

Public badges use an ISO/BCP-47-style model such as `FR`, `FR-CA`, `EN`, `KO`, `JA`, `PT-BR`, `ES-419`, `ZH-HK` and `ZH-TW`.

Legacy words such as `VF`, `VFF`, `VFQ`, `VO`, `MULTI` and `VOSTFR` are **input aliases only**.

- VF/VFF can normalize to French audio when evidence supports it.
- VFQ can normalize to French (Canada).
- VOSTFR becomes original-language audio + French subtitles when original-language context is known.
- **VO does not become English automatically.**

## Content ratings are regional

Age systems are not globally interchangeable. NiakVIO keeps explicit regional systems when known: US MPA/TV, Korean ALL/12/15/19, German FSK, Japanese G/PG12/R15+/R18+, Indian CBFC, Brazilian, Québec, Spanish, French, Hong Kong, Finnish, Greek, Portuguese, Philippine, Indonesian, Russian, Polish, Swedish, Taiwanese and LATAM families.

A generic numeric badge is used when the only reliable fact is a minimum age.

## What appears in the stream title?

The title stays deliberately simple: **provider identity + strongest proven quality**.

Examples:

- proven 1080p → `Kehflix - 1080p`
- proven 1080i → `Kehflix - 1080i`
- proven 2160p → `Kehflix - 4K`
- proven 4320p → `Kehflix - 8K`
- `Unknown`, `Inconnue`, `N/A`, `Auto` → simply `Kehflix`

Other facts belong in badges/description. If a sparse Kehflix stream only proves a `.m3u8` URL, the truthful presentation is **Kehflix + HLS**, not “Kehflix - Inconnue” and not a guessed resolution.

## How NiakVIO decides to show a badge

1. provider returns raw stream facts;
2. Core preserves and normalizes the strongest evidence;
3. presentation emits structured `badgeIds` plus a readable technical description;
4. Nuvio StreamBadge rules match those facts;
5. missing evidence remains missing.

This distinction prevents “badge inflation” and makes the UI useful to users who actually care about media quality.

## Feed versioning

Every material badge/rule change creates a new immutable version of **all four** public feeds.

Current version:

- `assets/stream-badges-fusion-v4.json`
- `assets/stream-badges-dark-v4.json`
- `assets/stream-badges-light-v4.json`
- `assets/stream-badges-transparent-v4.json`

Older versioned feeds remain available for pinned installations.
