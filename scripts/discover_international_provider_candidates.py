#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, html, json, os, re, sys, unicodedata, urllib.parse, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED = ROOT / 'research' / 'international-provider-candidates.xlsx'
DEFAULT_CONFIG = ROOT / 'automation' / 'international-provider-discovery-sources.json'
DEFAULT_CATALOG = ROOT / 'provider_catalog.json'
DEFAULT_OUT_JSON = ROOT / 'research' / 'international-provider-candidates.json'
DEFAULT_OUT_CSV = ROOT / 'research' / 'international-provider-candidates.csv'
DEFAULT_OUT_XLSX = ROOT / 'research' / 'international-provider-candidates.xlsx'

UA = 'Mozilla/5.0 NiakVIO-ProviderDiscovery/1.0'
IGNORE_DIRS = {'.github','.vscode','builds','build','gradle','extractors','app','docs','assets'}


def norm(v: str) -> str:
    text = unicodedata.normalize('NFKD', str(v or '')).encode('ascii', 'ignore').decode().casefold()
    return re.sub(r'[^a-z0-9]+', '', text)


def fetch_text(url: str, timeout: float = 12.0, token: str = '') -> str:
    headers = {'User-Agent': UA, 'Accept': 'text/html,application/json;q=0.9,*/*;q=0.8'}
    parsed = urllib.parse.urlparse(url)
    if token and parsed.scheme == 'https' and parsed.hostname == 'api.github.com':
        headers['Authorization'] = f'Bearer {token}'
        headers['X-GitHub-Api-Version'] = '2022-11-28'
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='replace')


def load_catalog(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding='utf-8'))
    out = set()
    for item in data.get('providers') or []:
        if not isinstance(item, dict):
            continue
        for value in (item.get('canonicalId'), (item.get('scraper') or {}).get('id'), (item.get('scraper') or {}).get('name')):
            n = norm(str(value or ''))
            if n: out.add(n)
    return out


def load_seed(path: Path) -> list[dict]:
    """Load the previous catalogue as a fallback seed (XLSX preferred; JSON supported)."""
    if path.suffix.casefold() == '.json':
        data = json.loads(path.read_text(encoding='utf-8'))
        return list(data.get('candidates') or [])
    if path.suffix.casefold() != '.xlsx':
        raise ValueError(f'unsupported seed format: {path}')
    import xml.etree.ElementTree as ET
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path, 'r') as z:
        root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    matrix=[]
    for row in root.findall('.//m:sheetData/m:row', ns):
        vals=[]
        for c in row.findall('m:c', ns):
            typ=c.attrib.get('t')
            if typ == 'inlineStr':
                vals.append(''.join(t.text or '' for t in c.findall('.//m:t', ns)))
            else:
                v=c.find('m:v', ns)
                vals.append(v.text if v is not None else '')
        matrix.append(vals)
    if not matrix:
        return []
    headers=[norm(x) for x in matrix[0]]
    def idx(*names):
        wanted={norm(x) for x in names}
        for i,h in enumerate(headers):
            if h in wanted: return i
        return None
    cols={
        'market': idx('Pays / marché','market'),
        'languages': idx('Langue(s)','languages'),
        'name': idx('Candidat','name'),
        'content': idx('Contenu','content'),
        'score': idx('Score /100','score'),
        'route': idx('Route / hub observé','route'),
        'note': idx('Pourquoi / prochaine étape','note'),
        'source': idx('Source','Source(s)','sources'),
    }
    out=[]
    for raw in matrix[1:]:
        def get(key, default=''):
            i=cols[key]
            return raw[i] if i is not None and i < len(raw) else default
        name=str(get('name')).strip(); market=str(get('market')).strip()
        if not name or not market: continue
        try: score=int(float(get('score') or 75))
        except Exception: score=75
        source=str(get('source')).strip()
        out.append({'name':name,'market':market,'languages':str(get('languages')).strip(),
                    'content':str(get('content')).strip(),'score':score,'route':str(get('route')).strip(),
                    'note':str(get('note')).strip() or 'Previous catalogue fallback.',
                    'source':source})
    return out


def clean_provider_name(name: str) -> str:
    name = re.sub(r'(?i)(provider|pack)$', '', name.strip())
    name = name.replace('_',' ').replace('-',' ').strip()
    return re.sub(r'\s+', ' ', name)


def add(pool, candidate):
    name = str(candidate.get('name') or '').strip()
    market = str(candidate.get('market') or '').strip()
    if len(name) < 3 or not market:
        return
    key = norm(name)
    if not key:
        return
    current = pool.get(key)
    if current is None:
        candidate['sources'] = sorted(set(candidate.get('sources') or []))
        pool[key] = candidate
        return
    current['score'] = max(int(current.get('score') or 0), int(candidate.get('score') or 0))
    current['sources'] = sorted(set((current.get('sources') or []) + (candidate.get('sources') or [])))
    current['source_count'] = len(current['sources'])
    if not current.get('route') and candidate.get('route'): current['route'] = candidate['route']
    if not current.get('note') and candidate.get('note'): current['note'] = candidate['note']


class FMHYParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.tag=None; self.buf=[]; self.h2=''; self.h3=''; self.rows=[]
    def handle_starttag(self, tag, attrs):
        if tag in {'h2','h3','li'}: self.tag=tag; self.buf=[]
    def handle_data(self, data):
        if self.tag: self.buf.append(data)
    def handle_endtag(self, tag):
        if tag != self.tag: return
        text = re.sub(r'\s+',' ', html.unescape(''.join(self.buf))).strip()
        if tag=='h2': self.h2=text
        elif tag=='h3': self.h3=text
        elif tag=='li' and text: self.rows.append((self.h2,self.h3,text))
        self.tag=None; self.buf=[]


def fmhy_candidates(url: str, config: dict, timeout: float) -> list[dict]:
    doc = fetch_text(url, timeout)
    p = FMHYParser(); p.feed(doc)
    market_alias = config.get('fmhy_market_aliases') or {}
    stream_words = [x.casefold() for x in config.get('fmhy_streaming_headings') or ['streaming']]
    out=[]
    for h2,h3,item in p.rows:
        if not any(w in h3.casefold() for w in stream_words):
            continue
        prefix = re.split(r'[/|]', h2, 1)[0].strip()
        market = market_alias.get(prefix, prefix)
        if not market: continue
        raw = item.split(' - ',1)[0].strip()
        raw = re.sub(r',\s*\d+(?:\s*,\s*\d+)*\s*$', '', raw)
        for part in re.split(r'\s+or\s+', raw, flags=re.I):
            name = part.strip(' •·–—,')
            if len(name) < 3 or name.casefold().startswith(('http','telegram')): continue
            out.append({'name':name,'market':market,'languages':'','content':'movie,tv','score':82,
                        'route':'','note':'Discovered from current FMHY non-English streaming index.',
                        'sources':[url],'source_kind':'fmhy'})
    return out


def github_repo_candidates(source: dict, token: str, timeout: float) -> list[dict]:
    repo = source['repo']; market = source['market']; lang = source.get('languages','')
    url = f'https://api.github.com/repos/{repo}/contents'
    rows = json.loads(fetch_text(url, timeout, token))
    out=[]
    for row in rows:
        if row.get('type') != 'dir': continue
        raw = str(row.get('name') or '')
        if raw.casefold() in IGNORE_DIRS or raw.startswith('.'): continue
        name = clean_provider_name(raw)
        if len(norm(name)) < 3: continue
        out.append({'name':name,'market':market,'languages':lang,'content':'movie,tv','score':int(source.get('score',90)),
                    'route':'','note':f'Discovered from maintained CloudStream/provider repository {repo}.',
                    'sources':[f'https://github.com/{repo}'],'source_kind':'github_repo'})
    return out


def tier(score: int) -> str:
    return 'A' if score >= 88 else ('B' if score >= 76 else 'C')


def select(pool: dict, catalog_norms: set[str], max_candidates: int, cap: int) -> list[dict]:
    by_market=defaultdict(list)
    for c in pool.values():
        if norm(c['name']) in catalog_norms: continue
        c['source_count'] = len(set(c.get('sources') or []))
        c['score'] = min(99, int(c.get('score') or 0) + max(0,c['source_count']-1)*5)
        c['tier']=tier(c['score'])
        by_market[c['market']].append(c)
    for vals in by_market.values():
        vals.sort(key=lambda x:(-x['score'],-x.get('source_count',0),x['name'].casefold()))
    markets=sorted(by_market, key=lambda m:(-max(x['score'] for x in by_market[m]),m.casefold()))
    chosen=[]; idx=defaultdict(int)
    while len(chosen)<max_candidates:
        progressed=False
        for m in markets:
            if idx[m] >= min(cap,len(by_market[m])): continue
            chosen.append(by_market[m][idx[m]]); idx[m]+=1; progressed=True
            if len(chosen)>=max_candidates: break
        if not progressed: break
    chosen.sort(key=lambda x:(-x['score'],x['market'].casefold(),x['name'].casefold()))
    for i,c in enumerate(chosen,1): c['rank']=i
    return chosen


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    cols=['rank','market','languages','name','content','tier','score','route','note','sources']
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f); w.writerow(cols)
        for r in rows: w.writerow([r.get(k,'') if k!='sources' else ' | '.join(r.get('sources') or []) for k in cols])


def xcell(ref, value, style=0):
    s=f' s="{style}"' if style else ''
    if isinstance(value,(int,float)) and not isinstance(value,bool): return f'<c r="{ref}"{s}><v>{value}</v></c>'
    return f'<c r="{ref}" t="inlineStr"{s}><is><t>{escape(str(value or ""))}</t></is></c>'


def col_letter(n):
    s=''
    while n: n,rem=divmod(n-1,26); s=chr(65+rem)+s
    return s


def sheet_xml(matrix, widths, freeze=True):
    rows=[]
    for ri,row in enumerate(matrix,1):
        cells=[]
        for ci,v in enumerate(row,1): cells.append(xcell(f'{col_letter(ci)}{ri}',v,1 if ri==1 else 0))
        rows.append(f'<row r="{ri}">{"".join(cells)}</row>')
    cols=''.join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i,w in enumerate(widths,1))
    pane='<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>' if freeze else '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' + pane + f'<cols>{cols}</cols><sheetData>{"".join(rows)}</sheetData><autoFilter ref="A1:{col_letter(len(widths))}{len(matrix)}"/></worksheet>'


def write_xlsx(path: Path, rows: list[dict], meta: dict):
    headers=['Rank','Pays / marché','Langue(s)','Candidat','Contenu','Tier','Score /100','Route / hub observé','Pourquoi / prochaine étape','Source(s)']
    matrix=[headers]+[[r['rank'],r['market'],r.get('languages',''),r['name'],r.get('content',''),r['tier'],r['score'],r.get('route',''),r.get('note',''),' | '.join(r.get('sources') or [])] for r in rows]
    counts=defaultdict(list)
    for r in rows: counts[r['market']].append(r)
    cov=[['Pays / marché','Nb candidats','Score moyen','Tier A']]
    for m in sorted(counts):
        vals=counts[m]; cov.append([m,len(vals),round(sum(x['score'] for x in vals)/len(vals),1),sum(1 for x in vals if x['tier']=='A')])
    method=[['Champ','Détail'],['Generated at',meta['generated_at']],['Selection',meta['selection']],['Candidates',len(rows)],['Markets',len(counts)],['Safety','Research only; deduped against current NiakVIO catalog; never mutates providers/hubs/manifests.']]
    ct='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'+''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1,4))+'</Types>'
    rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    wb='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Candidates" sheetId="1" r:id="rId1"/><sheet name="Coverage" sheetId="2" r:id="rId2"/><sheet name="Method" sheetId="3" r:id="rId3"/></sheets></workbook>'
    wbrels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,4))+'<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
    styles='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs></styleSheet>'
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',ct); z.writestr('_rels/.rels',rels); z.writestr('xl/workbook.xml',wb); z.writestr('xl/_rels/workbook.xml.rels',wbrels); z.writestr('xl/styles.xml',styles)
        z.writestr('xl/worksheets/sheet1.xml',sheet_xml(matrix,[7,20,12,27,18,7,11,28,52,58]))
        z.writestr('xl/worksheets/sheet2.xml',sheet_xml(cov,[24,14,14,12]))
        z.writestr('xl/worksheets/sheet3.xml',sheet_xml(method,[24,95]))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',type=Path,default=DEFAULT_SEED); ap.add_argument('--config',type=Path,default=DEFAULT_CONFIG); ap.add_argument('--catalog',type=Path,default=DEFAULT_CATALOG)
    ap.add_argument('--max-candidates',type=int,default=100); ap.add_argument('--per-market-cap',type=int,default=4); ap.add_argument('--timeout',type=float,default=12); ap.add_argument('--offline',action='store_true')
    ap.add_argument('--out-json',type=Path,default=DEFAULT_OUT_JSON); ap.add_argument('--out-csv',type=Path,default=DEFAULT_OUT_CSV); ap.add_argument('--out-xlsx',type=Path,default=DEFAULT_OUT_XLSX)
    args=ap.parse_args(); cfg=json.loads(args.config.read_text(encoding='utf-8')); seed_rows=load_seed(args.seed); catalog=load_catalog(args.catalog); pool={}
    for r in seed_rows:
        add(pool,{'name':r['name'],'market':r['market'],'languages':r.get('languages',''),'content':r.get('content',''),'score':max(65,int(r.get('score') or 0)-8),'route':r.get('route',''),'note':r.get('note','Seed fallback.'),'sources':[r.get('source','')],'source_kind':'seed'})
    if not args.offline:
        token=os.environ.get('GITHUB_TOKEN','')
        for src in cfg.get('github_sources') or []:
            try:
                for c in github_repo_candidates(src,token,args.timeout): add(pool,c)
            except Exception as e: print(f'WARN github source {src.get("repo")}: {e}',file=sys.stderr)
        for url in cfg.get('fmhy_urls') or []:
            try:
                for c in fmhy_candidates(url,cfg,args.timeout): add(pool,c)
            except Exception as e: print(f'WARN fmhy {url}: {e}',file=sys.stderr)
        for c in cfg.get('direct_candidates') or []:
            try:
                body=fetch_text(c['source'],args.timeout)
                score=int(c.get('score',88)) + (4 if norm(c['name']) in norm(body) else 0)
                x=dict(c); x['score']=score; x['sources']=[c['source']]; add(pool,x)
            except Exception as e: print(f'WARN direct {c.get("name")}: {e}',file=sys.stderr)
    chosen=select(pool,catalog,max(1,min(args.max_candidates,100)),max(1,args.per_market_cap))
    meta={'schema_version':1,'generated_at':datetime.now(timezone.utc).isoformat(),'selection':f'round-robin by market, cap={args.per_market_cap}, max={args.max_candidates}','candidate_count':len(chosen)}
    payload={**meta,'candidates':chosen}; args.out_json.parent.mkdir(parents=True,exist_ok=True); args.out_json.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write_csv(args.out_csv,chosen); write_xlsx(args.out_xlsx,chosen,meta)
    print(f'international discovery complete: candidates={len(chosen)} markets={len(set(x["market"] for x in chosen))}')

if __name__=='__main__': main()
