#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function findHtmlFiles(dir) {
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) results.push(...findHtmlFiles(full));
    else if (entry.name.endsWith('.html')) results.push(full);
  }
  return results;
}

let failures = 0;
const layoutsDir = path.join(__dirname, '../../layouts');
for (const file of findHtmlFiles(layoutsDir)) {
  const content = fs.readFileSync(file, 'utf8');
  const matches = [...content.matchAll(/pattern="([^"]+)"/g)];
  for (const [, pattern] of matches) {
    try {
      new RegExp(pattern, 'v');
      console.log(`PASS [${path.relative(layoutsDir, file)}]: pattern="${pattern}"`);
    } catch (e) {
      console.error(`FAIL [${path.relative(layoutsDir, file)}]: pattern="${pattern}" — ${e.message}`);
      failures++;
    }
  }
}
if (failures > 0) {
  console.error(`\n${failures} regex pattern(s) failed v-flag validation`);
  process.exit(1);
}
console.log('\nAll regex patterns valid under Unicode sets v-flag');
