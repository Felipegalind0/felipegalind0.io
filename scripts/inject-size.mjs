import { readFileSync, writeFileSync, statSync } from 'fs';

const p = 'dist/index.html';
const kb = (statSync(p).size / 1024).toFixed(1);
let h = readFileSync(p, 'utf-8');
h = h.replace('__SIZE__', `${kb}KB`);
writeFileSync(p, h);
console.log(`injected: ${kb}KB`);
