"""Observe a public provider homepage with the existing ordinary browser probe."""
import argparse
import json
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import probe_waf_browser_session as browser_probe

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live-context', required=True, type=Path)
    args = parser.parse_args()
    live = json.loads(args.live_context.read_text())
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if live.get('sourceSha') != source or live.get('http_script_shell_only') is not True:
        raise ValueError('browser observation requires exact-current script-shell evidence')
    provider = live['provider']
    data = json.loads((ROOT / 'provider-overrides.json').read_text())
    url = urlsplit(data['provider_patches'][provider]['official_site'])
    if url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password:
        raise ValueError('public provider origin unavailable')
    origin = urlunsplit((url.scheme, url.netloc, '/', '', ''))
    browser = browser_probe.browser_binary()
    result = browser_probe.probe_target(
        {'provider': provider, 'lane': 'public-homepage', 'url': origin,
         'publicUrl': origin, 'host': url.hostname, 'method': 'GET'},
        browser, timeout=25, virtual_time_ms=7000, attempts=1,
    )
    allowed = {'browser_unavailable', 'browser_content_reached', 'browser_challenge_persisted',
               'browser_timeout', 'browser_inconclusive', 'browser_error'}
    outcome = result.get('outcome')
    live['browser_observation'] = {
        'outcome': outcome if outcome in allowed else 'browser_inconclusive',
        'browser_available': bool(browser), 'publicationAuthority': False,
    }
    args.live_context.write_text(json.dumps(live, indent=2) + '\n')
    print('::notice title=Ordinary browser observation::provider=' + provider +
          ' outcome=' + live['browser_observation']['outcome'])

if __name__ == '__main__':
    main()
