// Preserve provider function names for causal diagnosis; never persist raw stacks.
'use strict';
function providerCallNames(stack, providerPath) {
  if (!providerPath || typeof stack !== 'string') return [];
  const names = [];
  for (const line of stack.split('\n').slice(0, 20)) {
    if (!line.includes(providerPath)) continue;
    const match = line.match(/\bat\s+(?:async\s+)?([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s+\(/);
    const name = match && match[1].split('.').pop();
    if (name && name.length <= 64 && !names.includes(name)) names.push(name);
    if (names.length >= 8) break;
  }
  return names;
}
module.exports = { providerCallNames };
