'use strict';

const fs = require('node:fs');

const paths = process.argv.slice(2);
if (!paths.length) {
  console.error('usage: node gate_native_player_reached.cjs <log> [log...]');
  process.exit(2);
}

let readable = 0;
let attempts = 0;
const byClient = new Map();
for (const file of paths) {
  if (!fs.existsSync(file)) continue;
  readable += 1;
  const text = fs.readFileSync(file, 'utf8');
  for (const raw of text.split(/\r?\n/)) {
    const at = raw.indexOf('FIELD_NATIVE_PLAYER_BEGIN ');
    if (at < 0) continue;
    attempts += 1;
    const line = raw.slice(at);
    const match = line.match(/\bclient=([^\s]+)/);
    const client = match ? match[1] : 'unknown';
    byClient.set(client, Number(byClient.get(client) || 0) + 1);
  }
}

if (!readable) {
  console.error('FIELD_NATIVE_PLAYER_REACH_GATE status=fail reason=no_readable_logs attempts=0');
  process.exit(3);
}
if (!attempts) {
  console.error('FIELD_NATIVE_PLAYER_REACH_GATE status=fail reason=player_never_reached attempts=0');
  process.exit(4);
}
const clients = [...byClient.entries()].map(([client, count]) => `${client}:${count}`).join(',');
console.log(`FIELD_NATIVE_PLAYER_REACH_GATE status=pass attempts=${attempts} clients=${clients}`);
