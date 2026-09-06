#!/usr/bin/env python3
from __future__ import annotations
import argparse,re
from pathlib import Path
MARKER="FIELD_NATIVE_REPOSITORY_APP_PATH"
FIELD_RE=re.compile(r"([a-z_]+)=([^\s]+)")
def parse(line):
    if MARKER not in line:return None
    return {k:v for k,v in FIELD_RE.findall(line)}
def b(v,n):
    x=v.strip().casefold()
    if x=="true":return True
    if x=="false":return False
    raise ValueError(f"invalid {n}={v!r}")
def n(v,name):
    x=int(v)
    if x<0:raise ValueError(f"invalid {name}={v!r}")
    return x
def validate(path,client):
    rows=[x for line in path.read_text(encoding="utf-8",errors="replace").splitlines() if (x:=parse(line)) and x.get("client")==client]
    if not rows:raise ValueError(f"{path}: missing {MARKER} client={client}")
    r=rows[-1];enabled=b(r.get("plugins_enabled",""),"plugins_enabled");loaded=n(r.get("loaded",""),"loaded");movie=n(r.get("movie_enabled",""),"movie_enabled");tv=n(r.get("tv_enabled",""),"tv_enabled");series=n(r.get("series_enabled",""),"series_enabled")
    if not enabled:raise ValueError(f"{path}: production plugin selection globally disabled")
    if loaded<=0 or movie<=0 or tv<=0 or series<=0:raise ValueError(f"{path}: zero app selection loaded={loaded} movie={movie} tv={tv} series={series}")
    if max(movie,tv,series)>loaded:raise ValueError(f"{path}: impossible app selection loaded={loaded} movie={movie} tv={tv} series={series}")
    return loaded,movie,tv,series
def main():
    p=argparse.ArgumentParser();p.add_argument("--client",choices=("desktop","mobile"),required=True);p.add_argument("logs",nargs="+");a=p.parse_args();mins=None
    for raw in a.logs:
        vals=validate(Path(raw),a.client);mins=vals if mins is None else tuple(min(x,y) for x,y in zip(mins,vals))
    print(f"native app provider selection gate passed: client={a.client} logs={len(a.logs)} min_loaded={mins[0]} min_movie_enabled={mins[1]} min_tv_enabled={mins[2]} min_series_enabled={mins[3]}")
    return 0
if __name__=="__main__":raise SystemExit(main())
