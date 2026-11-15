import { cp, mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const source = path.join(root, 'source-mirror/user.xmission.com/~tnelson/mm6/gameplay/places');
const out = path.join(root, 'dist');

const walk = async dir => (await Promise.all((await readdir(dir, { withFileTypes: true })).map(async entry => {
  const full = path.join(dir, entry.name);
  return entry.isDirectory() ? walk(full) : full;
}))).flat();

const entities = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' };
const decode = value => value
  .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
  .replace(/&([a-z]+);/gi, (all, key) => entities[key.toLowerCase()] ?? all);
const text = html => decode(html
  .replace(/<(script|style)[\s\S]*?<\/\1>/gi, ' ')
  .replace(/<br\s*\/?>/gi, '\n').replace(/<\/p>|<\/tr>|<\/h\d>/gi, '\n')
  .replace(/<[^>]+>/g, ' ').replace(/[ \t]+/g, ' ')
  .replace(/\s*\n\s*/g, '\n').replace(/\n{3,}/g, '\n\n').trim());
const titleCase = value => value.replace(/\.html?$/i, '').replace(/[-_]/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/\b\w/g, c => c.toUpperCase());

await rm(out, { recursive: true, force: true });
await mkdir(path.join(out, 'assets'), { recursive: true });
await cp(path.join(root, 'src'), out, { recursive: true });
await cp(path.join(root, 'LICENSE.md'), path.join(out, 'LICENSE.md'));
await cp(source, path.join(out, 'assets/places'), { recursive: true });

const files = (await walk(source)).filter(file => /\.html?$/i.test(file));
const pages = [];
for (const file of files) {
  const html = await readFile(file, 'utf8');
  const relative = path.relative(source, file).split(path.sep).join('/');
  if (relative === 'places.html') continue;
  const segments = relative.split('/');
  const region = titleCase(segments[0]);
  const heading = [...html.matchAll(/<h[1-4][^>]*>([\s\S]*?)<\/h[1-4]>/gi)].map(m => text(m[1])).find(Boolean);
  const rawTitle = text(html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1] ?? '');
  const title = heading || rawTitle.replace(/Magic Grounds\s*[-:]?\s*/i, '').trim() || (segments.length === 2 && /location\.html/i.test(segments[1]) ? region : titleCase(path.basename(file)));
  const images = [...html.matchAll(/<img[^>]+src=["']([^"']+)["']/gi)]
    .map(m => path.posix.normalize(path.posix.join(path.posix.dirname(relative), decode(m[1]).replace(/\\/g, '/'))))
    .filter(src => !src.startsWith('..') && !src.includes('mglogo'));
  const body = text(html.match(/<body[^>]*>([\s\S]*?)<\/body>/i)?.[1] ?? html)
    .replace(/Leave us a message at:[\s\S]*$/i, '').trim();
  pages.push({ id: relative.replace(/\.html?$/i, '').replace(/[^a-z0-9]+/gi, '-').toLowerCase(), region, title, body, images: [...new Set(images)], sourcePath: relative });
}

pages.sort((a, b) => a.region.localeCompare(b.region) || (a.sourcePath.endsWith('location.html') ? -1 : 1) || a.title.localeCompare(b.title));
await writeFile(path.join(out, 'data.js'), `window.ATLAS_PAGES=${JSON.stringify(pages)};\n`);
const offlineFiles = (await walk(out))
  .filter(file => !file.endsWith('sw.js'))
  .map(file => `./${path.relative(out, file).split(path.sep).join('/')}`);
const serviceWorkerPath = path.join(out, 'sw.js');
const serviceWorker = await readFile(serviceWorkerPath, 'utf8');
await writeFile(serviceWorkerPath, serviceWorker.replace('__PRECACHE__', JSON.stringify(offlineFiles)));
console.log(`Built ${pages.length} searchable pages with ${pages.reduce((n, p) => n + p.images.length, 0)} image references.`);
