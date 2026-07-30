'use strict';
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'providers');
const files = fs.readdirSync(dir).filter((name) => name.includes('--nuvio--') && name.endsWith('.js'));
if (!files.length) {
  console.log('patched provider runtime smoke skipped (0 artifacts)');
  process.exit(0);
}

(async () => {
  for (const name of files) {
    const file = path.join(dir, name);
    const errors = [];
    const originalError = console.error;
    const originalFetch = global.fetch;
    console.error = (...args) => errors.push(args.map(String).join(' '));
    global.fetch = async () => new Response('{}', { status: 404, headers: { 'content-type': 'application/json' } });
    try {
      delete require.cache[file];
      const mod = require(file);
      if (!mod || typeof mod.getStreams !== 'function') throw new Error(`${name}: getStreams missing`);
      const result = await Promise.race([
        mod.getStreams('577922', 'movie', null, null, { title: 'Tenet', year: 2020 }),
        new Promise((_, reject) => setTimeout(() => reject(new Error(`${name}: smoke timeout`)), 7000)),
      ]);
      if (!Array.isArray(result)) throw new Error(`${name}: getStreams did not return an array`);
      const fatal = errors.find((line) => /ReferenceError|SyntaxError|is not defined|Unexpected identifier/i.test(line));
      if (fatal) throw new Error(`${name}: runtime smoke detected ${fatal}`);
    } finally {
      console.error = originalError;
      global.fetch = originalFetch;
    }
  }
  console.log(`patched provider runtime smoke passed (${files.length} artifact(s))`);
  process.exit(0);
})().catch((error) => {
  console.error(error && error.stack || error);
  process.exit(1);
});
