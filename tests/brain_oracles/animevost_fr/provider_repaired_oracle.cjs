'use strict';
// Offline reference ONLY. Never import into a published provider or production
// override. This is a reverse-engineering oracle for a failed animevost-fr lane.
// It deliberately rejects ambiguous season/episode/title identity and keeps
// external subtitles coupled to the selected episode.
const ORACLE_PROVIDER_ID = 'animevost-fr';

function str(value) { return String(value ?? '').trim(); }
function normalized(value) {
  return str(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()
    .replace(/[^a-z0-9]+/g,' ').trim();
}
function rows(value) {
  if (Array.isArray(value)) return value;
  for (const key of ['results','data','items','animes']) {
    if (Array.isArray(value?.[key])) return value[key];
    if (Array.isArray(value?.[key]?.results)) return value[key].results;
  }
  return [];
}
function coordinate(obj, key, otherKey) {
  const raw = obj?.[key] ?? obj?.[otherKey];
  return /^\d{1,4}$/.test(str(raw)) ? Number(raw) : null;
}
function episodeMatch(value, season, episode) {
  if (!value || typeof value !== 'object') return false;
  const s = coordinate(value,'season_number','seasonNumber') ?? coordinate(value,'season','s');
  const e = coordinate(value,'episode_number','episodeNumber') ?? coordinate(value,'episode','e');
  return (s === null || s === season) && (e === null || e === episode);
}
function subtitleBelongs(subtitle, season, episode) {
  if (!subtitle || typeof subtitle !== 'object' || !str(subtitle.url)) return false;
  // Only a positive attachment to this episode can be accepted. A filename
  // containing another coordinate also contradicts the requested episode.
  const source = [subtitle.filename, subtitle.title,subtitle.name,subtitle.url].map(str).join(' ');
  const marker = /(?:^|\W)s(?:eason)?\s*0*(\d{1,3})[\s._-]*e(?:pisode)?\s*0*(\d{1,4})(?:\W|$)/i.exec(source);
  if (marker && (Number(marker[1]) !== season || Number(marker[2]) !== episode)) return false;
  return episodeMatch(subtitle, season, episode);
}
async function getStreams(request, _type, positionalSeason, positionalEpisode) {
  const q = request && typeof request === 'object'
    ? request : {tmdbId:request, mediaType:_type, season:positionalSeason, episode:positionalEpisode};
  const s = coordinate(q,'season','season_number');
  const e = coordinate(q,'episode','episode_number');
  if (!['anime','tv','series'].includes(str(q.mediaType || q.type).toLowerCase()) || s === null || !e) return [];
  const metadata = q.tmdbMetadata ?? globalThis.__nuvioMediaContext?.tmdbMetadata ?? {};
  const titles = [metadata.title,metadata.name,metadata.original_name,metadata.original_title,
    ...(metadata.alternative_titles?.results || []).map(x=>x?.title || x?.name)]
    .map(normalized).filter(Boolean);
  if (!titles.length) return [];
  const base = 'https://animevost.fr';
  let best = null;
  for (const title of titles.slice(0,4)) {
    const response = await fetch(base+'/api/animes/search?q='+encodeURIComponent(title));
    if (!response?.ok) continue;
    for (const item of rows(await response.json())) {
      if (!item || !str(item.slug)) continue;
      const candidate = normalized(item.title || item.name);
      if (!titles.includes(candidate)) continue;
      best = item;
      break;
    }
    if (best) break;
  }
  if (!best) return [];
  const detail = await fetch(base+'/api/animes/'+encodeURIComponent(str(best.slug)));
  if (!detail?.ok) return [];
  const body = await detail.json();
  const seasons = rows(body?.seasons || body);
  const chosenSeason = seasons.find(row=>coordinate(row,'season_number','seasonNumber') === s);
  if (!chosenSeason) return [];
  const chosenEpisode = rows(chosenSeason.episodes).find(row=>coordinate(row,'episode_number','episodeNumber') === e);
  if (!chosenEpisode) return [];
  const tag = 'S'+String(s).padStart(2,'0')+'E'+String(e).padStart(2,'0');
  return rows(chosenEpisode.streams).filter(row=>str(row?.video_url)).slice(0,8).map(row=>({
    url:str(row.video_url),name:'AnimeVOST.fr '+tag,title: str(best.title || best.name)+' '+tag,
    provider:ORACLE_PROVIDER_ID,seasonNumber:s,episodeNumber:e,
    language:str(row.language || 'VOSTFR'),quality:str(row.quality || 'HD'),
    headers:{Referer:base+'/'},
    subtitles:rows(chosenEpisode.subtitles)
      .filter(sub=>subtitleBelongs(sub,s,e))
      .map(sub=>({url:str(sub.url),language:str(sub.language || 'Unknown'),
        seasonNumber:s,episodeNumber:e}))
  }));
}
module.exports={getStreams, ORACLE_PROVIDER_ID};
