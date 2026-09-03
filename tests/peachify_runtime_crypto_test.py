#!/usr/bin/env python3
"""Runtime crypto vector for the clean-v3 Peachify Lego."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))

PATCH = ROOT / "scripts/provider_patches/peachify_runtime_v1.py"


def load_patch():
    spec = importlib.util.spec_from_file_location("peachify_runtime_crypto_test_module", PATCH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_patch()
    key_hex = "a8f2a1b5e9c470814f6b2c3a5d8e7f9c1a2b3c4d5e3f7a8b8cad1e2d0a4d5c5d"
    payload = {
        "keyHex": key_hex,
        "origin": "https://peachify.top",
        "referer": "https://peachify.top/",
        "userAgent": "NiakVIO-Peachify-Test",
        "servers": [{"label": "Iron", "base": "https://uwu.eat-peach.test", "path": "moviebox"}],
    }
    wrapper = module.WRAPPER.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    expected = "https://media.example.test/peach/master.m3u8"
    node = f"""
const crypto = require("crypto");
const key = Buffer.from({json.dumps(key_hex)}, "hex");
const iv = Buffer.from("00112233445566778899aabb", "hex");
const plaintext = Buffer.from(JSON.stringify({{sources:[{{url:{json.dumps(expected)},quality:"1080p",language:"French"}}]}}), "utf8");
const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final()]);
const tag = cipher.getAuthTag();
function b64url(buf){{ return buf.toString("base64").replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/,""); }}
const token = b64url(iv)+"."+b64url(encrypted)+"."+b64url(tag);
globalThis.getStreams = async function(){{return []}};
globalThis.__nuvioMediaContext = {{tmdbId:"157336",canonicalMediaType:"movie"}};
globalThis.fetch = async function(url, options){{
  if (!String(url).includes("/moviebox/movie/157336")) return {{ok:false,status:404}};
  return {{ok:true,status:200,json:async()=>({{isEncrypted:true,data:token}})}};
}};
{wrapper}
(async()=>{{
 const rows=await globalThis.getStreams("157336","movie");
 process.stdout.write(JSON.stringify(rows));
}})().catch(e=>{{console.error(e);process.exit(1)}});
"""
    completed = subprocess.run(
        ["node", "-e", node],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    rows = json.loads(completed.stdout)
    assert len(rows) == 1, rows
    assert rows[0]["url"] == expected, rows
    assert rows[0]["quality"] == "1080p", rows
    assert rows[0]["language"] == "French", rows
    print("PEACHIFY_RUNTIME_CRYPTO_OK aes=256-gcm streams=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
