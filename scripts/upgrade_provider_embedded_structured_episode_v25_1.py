#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
BASE=ROOT/'scripts'/'provider_base_store.py'
MARKER='NIAKVIO_PROVIDER_EMBEDDED_STRUCTURED_EPISODE_V25_1'


def once(text:str,old:str,new:str,label:str)->str:
    count=text.count(old)
    if count!=1: raise AssertionError(f'{label}: expected one anchor, got {count}')
    return text.replace(old,new,1)


def patch()->bool:
    text=BASE.read_text(encoding='utf-8')
    if MARKER in text:
        validate(text);return False
    if 'NIAKVIO_PROVIDER_EPISODE_SCOPED_JSON_V21_4' not in text:
        raise AssertionError('V25.1 requires V21.4 episode scoping')
    anchor='function _spv214EpisodeNumber(row) {\n'
    helper=r'''/* NIAKVIO_PROVIDER_EMBEDDED_STRUCTURED_EPISODE_V25_1 */
function _spv251DecodeJsString(source, start) {
  const quote = source[start];
  if (quote !== '"' && quote !== "'") return null;
  let out = "", escaped = false;
  for (let i = start + 1; i < source.length && out.length <= 2097152; i += 1) {
    const ch = source[i];
    if (escaped) {
      if (ch === "n") out += "\n";
      else if (ch === "r") out += "\r";
      else if (ch === "t") out += "\t";
      else if (ch === "b") out += "\b";
      else if (ch === "f") out += "\f";
      else if (ch === "u" && /^[0-9a-fA-F]{4}$/.test(source.slice(i + 1, i + 5))) {
        out += String.fromCharCode(parseInt(source.slice(i + 1, i + 5), 16)); i += 4;
      } else out += ch;
      escaped = false; continue;
    }
    if (ch === "\\") { escaped = true; continue; }
    if (ch === quote) return { value: out, end: i + 1 };
    out += ch;
  }
  return null;
}
function _spv251BalancedJsonAt(source, start) {
  const open = source[start], close = open === "{" ? "}" : open === "[" ? "]" : "";
  if (!close) return null;
  const stack = [close];
  let quote = "", escaped = false;
  for (let i = start + 1; i < source.length && i - start <= 1048576; i += 1) {
    const ch = source[i];
    if (quote) {
      if (escaped) { escaped = false; continue; }
      if (ch === "\\") { escaped = true; continue; }
      if (ch === quote) quote = "";
      continue;
    }
    if (ch === '"') { quote = ch; continue; }
    if (ch === "{" ) stack.push("}");
    else if (ch === "[") stack.push("]");
    else if (ch === "}" || ch === "]") {
      if (stack[stack.length - 1] !== ch) return null;
      stack.pop();
      if (!stack.length) return { text: source.slice(start, i + 1), end: i + 1 };
    }
  }
  return null;
}
function _spv251EmbeddedJsonValues(raw) {
  const source = _text(raw).slice(0, 4194304);
  const chunks = [];
  const markers = ["self.__next_f.push([1,", "self.__next_f.push([0,"];
  for (const marker of markers) {
    let pos = 0, count = 0;
    while (count++ < 96) {
      const hit = source.indexOf(marker, pos);
      if (hit < 0) break;
      let cursor = hit + marker.length;
      while (cursor < source.length && /\s/.test(source[cursor])) cursor += 1;
      const decoded = _spv251DecodeJsString(source, cursor);
      if (decoded) { chunks.push(decoded.value); pos = decoded.end; }
      else pos = cursor + 1;
    }
  }
  const decoded = chunks.join("").slice(0, 2097152);
  const out = [], seen = new Set();
  for (let i = 0, scanned = 0; i < decoded.length && scanned < 160 && out.length < 32; i += 1) {
    if (decoded[i] !== ":") continue;
    let cursor = i + 1;
    while (cursor < decoded.length && /\s/.test(decoded[cursor])) cursor += 1;
    if (decoded[cursor] !== "{" && decoded[cursor] !== "[") continue;
    scanned += 1;
    const block = _spv251BalancedJsonAt(decoded, cursor);
    if (!block) continue;
    try {
      const value = JSON.parse(block.text);
      const fingerprint = block.text.slice(0, 512) + ":" + block.text.length;
      if (!seen.has(fingerprint)) { seen.add(fingerprint); out.push(value); }
    } catch (_) {}
    i = Math.max(i, block.end - 1);
  }
  return out;
}
function _spv251SeasonNumber(row) {
  if (!row || typeof row !== "object" || Array.isArray(row)) return 0;
  for (const key of ["season", "season_number", "seasonNumber"]) {
    const value = Number(row[key]);
    if (Number.isFinite(value) && value > 0 && value <= 1000) return Math.floor(value);
  }
  const id = _text(row.id).trim();
  const structural = row.lang || row.languages || row.episodes || row.episode || row.sources;
  if (structural && /^\d{1,3}$/.test(id)) return Number(id);
  return 0;
}
function _spv251UrlMatrix(value, wantedEpisode) {
  if (!Array.isArray(value) || !value.length || value.length > 12 || wantedEpisode <= 0) return null;
  if (!value.every(row => Array.isArray(row) && row.length >= wantedEpisode && row.length <= 2000)) return null;
  let urlCells = 0;
  const selected = [];
  for (const row of value) {
    for (const cell of row.slice(0, 12)) {
      if (typeof cell === "string" && /^(?:https?:)?\/\//i.test(cell.trim())) { urlCells += 1; break; }
    }
    const cell = row[wantedEpisode - 1];
    if (typeof cell === "string" && /^(?:https?:)?\/\//i.test(cell.trim())) selected.push(cell);
  }
  return urlCells === value.length && selected.length ? selected : null;
}
function _spv251SeasonEpisodeScopedValue(value, mediaType, season, episode, depth) {
  const lane = _text(mediaType).trim().toLowerCase();
  const wantedSeason = Math.floor(Number(season) || 0), wantedEpisode = Math.floor(Number(episode) || 0);
  depth = Number(depth) || 0;
  if ((lane !== "tv" && lane !== "anime") || wantedEpisode <= 0 || depth > 12 || value == null) return value;
  if (Array.isArray(value)) {
    const seasonRows = value.filter(row => _spv251SeasonNumber(row) > 0);
    if (wantedSeason > 0 && seasonRows.length) {
      const exact = seasonRows.filter(row => _spv251SeasonNumber(row) === wantedSeason);
      if (exact.length) return exact.map(row => _spv251SeasonEpisodeScopedValue(row, lane, wantedSeason, wantedEpisode, depth + 1));
    }
    const matrix = _spv251UrlMatrix(value, wantedEpisode);
    if (matrix) return matrix;
    return value.map(row => _spv251SeasonEpisodeScopedValue(row, lane, wantedSeason, wantedEpisode, depth + 1)).filter(row => row != null);
  }
  if (typeof value !== "object") return value;
  const rowSeason = _spv251SeasonNumber(value);
  if (wantedSeason > 0 && rowSeason > 0 && rowSeason !== wantedSeason) return null;
  const out = {};
  for (const [key, child] of Object.entries(value).slice(0, 256)) {
    const scoped = _spv251SeasonEpisodeScopedValue(child, lane, wantedSeason, wantedEpisode, depth + 1);
    if (scoped != null) out[key] = scoped;
  }
  return out;
}
'''
    text=once(text,anchor,helper+anchor,'v25.1-helper')
    old='''        if (typeof scopedPayloadValue === "string") {
          urls = _uniq([
            ..._extractUrls(scopedPayloadValue, payload.base),
            ..._spv15ExplicitPlayerAttrs(payload.value, payload.base)
          ]);
        } else {
'''
    new='''        if (typeof scopedPayloadValue === "string") {
          urls = _uniq([
            ..._extractUrls(scopedPayloadValue, payload.base),
            ..._spv15ExplicitPlayerAttrs(payload.value, payload.base)
          ]);
          const embeddedValues = _spv251EmbeddedJsonValues(payload.value);
          for (const embeddedValue of embeddedValues.slice(0, 16)) {
            const scopedEmbedded = _spv251SeasonEpisodeScopedValue(
              embeddedValue, mediaType, season, episode, 0
            );
            if (scopedEmbedded == null) continue;
            urls.push(..._jsonUrls(scopedEmbedded));
            urls.push(..._sourceUrls(scopedEmbedded, payload.base));
            urls.push(..._spv18ValueUrls(scopedEmbedded, payload.base, []));
            urls.push(..._spv205HttpValues(scopedEmbedded, payload.base, []));
          }
          urls = _uniq(urls);
        } else {
'''
    text=once(text,old,new,'v25.1-resolver')
    BASE.write_text(text,encoding='utf-8')
    validate(text)
    return True


def validate(text:str|None=None)->None:
    value=text if text is not None else BASE.read_text(encoding='utf-8')
    for needle in (
        MARKER,
        'function _spv251EmbeddedJsonValues(raw)',
        'function _spv251SeasonEpisodeScopedValue(value, mediaType, season, episode, depth)',
        'const embeddedValues = _spv251EmbeddedJsonValues(payload.value);',
        'urls.push(..._spv205HttpValues(scopedEmbedded, payload.base, []));',
    ):
        if needle not in value: raise AssertionError(f'V25.1 missing {needle}')
    section=value[value.index(MARKER):value.index('function _spv214EpisodeNumber',value.index(MARKER))].casefold()
    for forbidden in ('mugiwara','smoothpre','jujutsu','animeServer'.casefold(),'voiranime','wooka'):
        if forbidden in section: raise AssertionError(f'provider/site token leaked: {forbidden}')


if __name__=='__main__':
    changed=patch();print(f'PROVIDER_EMBEDDED_STRUCTURED_EPISODE_V25_1 changed={str(changed).lower()}')
