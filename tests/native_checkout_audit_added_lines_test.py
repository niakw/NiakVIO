#!/usr/bin/env python3
import subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from audit_native_client_checkout import audit_checkout
def git(r,*a): subprocess.run(["git",*a],cwd=r,check=True,capture_output=True,text=True)
with tempfile.TemporaryDirectory() as td:
 r=Path(td);git(r,"init","-q");git(r,"config","user.name","t");git(r,"config","user.email","t@example.invalid")
 p=r/"app/build.gradle.kts";p.parent.mkdir(parents=True)
 p.write_text('android {\n buildTypes {\n  debug {\n   signingConfig = signingConfigs.getByName("release")\n  }\n }\n}\nval official = ExoPlayer.Builder(context)\n')
 git(r,"add",".");git(r,"commit","-qm","baseline")
 p.write_text(p.read_text().replace('getByName("release")','getByName("debug")'));audit_checkout(r,"tv")
 p.write_text(p.read_text()+'val injected = ExoPlayer.Builder(context)\n')
 try:audit_checkout(r,"tv")
 except SystemExit as e:assert "ExoPlayer.Builder" in str(e)
 else:raise AssertionError("tracked forbidden addition accepted")
 git(r,"reset","--hard","HEAD");q=r/"app/src/androidTest/java/T.kt";q.parent.mkdir(parents=True);q.write_text('val injected = ExoPlayer.Builder(context)\n')
 try:audit_checkout(r,"tv")
 except SystemExit as e:assert "ExoPlayer.Builder" in str(e)
 else:raise AssertionError("untracked forbidden addition accepted")
print("native checkout audit added-byte ownership passed")
