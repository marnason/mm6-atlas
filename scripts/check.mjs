import { access, readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
const root = path.resolve(import.meta.dirname, '..');
const dist = path.join(root, 'dist');
for (const file of ['index.html', 'app.js', 'styles.css', 'data.js', 'openyamm-data.js', 'sw.js', 'manifest.webmanifest']) await access(path.join(dist, file));
const data = await readFile(path.join(dist, 'data.js'), 'utf8');
const match = data.match(/^window\.ATLAS_PAGES=(.*);\s*$/s);
if (!match) throw new Error('Invalid data bundle');
const pages = JSON.parse(match[1]);
if (pages.length < 70) throw new Error(`Expected a complete mirror; found ${pages.length} pages`);
for (const page of pages) for (const image of page.images) await access(path.join(dist, 'assets/places', image));
const mapped = await readFile(path.join(dist, 'openyamm-data.js'), 'utf8');
const mappedMatch = mapped.match(/^window\.OPENYAMM=(.*);\s*$/s);
if (!mappedMatch) throw new Error('Invalid OpenYAMM data bundle');
const openyamm = JSON.parse(mappedMatch[1]);
if (openyamm.maps.length !== 15) throw new Error('Expected 15 high-resolution region maps');
if (openyamm.maps.reduce((count, map) => count + map.pois.length, 0) < 600) throw new Error('Missing mapped locations');
for (const map of openyamm.maps) {
  await access(path.join(dist, map.image));
  if (!pages.some(page => page.region === map.region)) throw new Error(`Unknown mapped region: ${map.region}`);
  if (map.width < 1024 || map.height < 1024) throw new Error(`Map is too small: ${map.region}`);
  for (const poi of map.pois) if (poi.u < 0 || poi.u > 1 || poi.v < 0 || poi.v > 1) throw new Error(`Invalid point on ${map.region}`);
}
const serviceWorker = await readFile(path.join(dist, 'sw.js'), 'utf8');
if (serviceWorker.includes('__PRECACHE__') || !serviceWorker.includes('assets/places/World/big.jpg')) throw new Error('Offline cache manifest was not generated');
const assets = await readdir(path.join(dist, 'assets/places'));
if (!assets.length) throw new Error('Missing mirrored assets');
console.log(`Verified ${pages.length} pages and all ${pages.reduce((n, p) => n + p.images.length, 0)} referenced images.`);
console.log(`Verified ${openyamm.maps.length} detailed maps and ${openyamm.maps.reduce((count, map) => count + map.pois.length, 0)} mapped places.`);
