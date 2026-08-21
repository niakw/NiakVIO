'use strict';

const fs = require('node:fs');

const paths = process.argv.slice(2);
if (!paths.length) {
  console.error('usage: node gate_native_player_reached.cjs <log> [log...]');
  process.exit(2);
}

function fields(line) {
  const out = new Map();
  for (const token of line.trim().split(/\s+/).slice(1)) {
    const index = token.indexOf('=');
    if (index <= 0) continue;
    out.set(token.slice(0, index), token.slice(index + 1));
  }
  return out;
}

let readable = 0;
let terminalEvidence = 0;
let productionPlayerReached = 0;
let rejectedSetup = 0;
const byClient = new Map();
for (const file of paths) {
  if (!fs.existsSync(file)) continue;
  readable += 1;
  const text = fs.readFileSync(file, 'utf8');
  for (const raw of text.split(/\r?\n/)) {
    const at = raw.indexOf('FIELD_NATIVE_PLAYER ');
    if (at < 0) continue;
    terminalEvidence += 1;
    const line = raw.slice(at);
    const parsed = fields(line);
    const client = parsed.get('client') || 'unknown';
    const engine = parsed.get('engine') || '';
    const failureStage = parsed.get('failure_stage') || '';
    const errorCode = parsed.get('error_code') || '';
    const isProduction = /-production$/i.test(engine);
    const isSetupOnly = failureStage === 'player_setup' || errorCode === 'NO_LAUNCH_INTENT';
    if (!isProduction || isSetupOnly) {
      if (isSetupOnly) rejectedSetup += 1;
      continue;
    }
    productionPlayerReached += 1;
    byClient.set(client, Number(byClient.get(client) || 0) + 1);
  }
}

if (!readable) {
  console.error('FIELD_NATIVE_PLAYER_REACH_GATE status=fail reason=no_readable_logs terminal=0 production=0 setup_rejected=0');
  process.exit(3);
}
if (!productionPlayerReached) {
  console.error(
    `FIELD_NATIVE_PLAYER_REACH_GATE status=fail reason=production_player_never_reached ` +
    `terminal=${terminalEvidence} production=0 setup_rejected=${rejectedSetup}`
  );
  process.exit(4);
}
const clients = [...byClient.entries()].map(([client, count]) => `${client}:${count}`).join(',');
console.log(
  `FIELD_NATIVE_PLAYER_REACH_GATE status=pass terminal=${terminalEvidence} ` +
  `production=${productionPlayerReached} setup_rejected=${rejectedSetup} clients=${clients}`
);
