"""Mirror Mike's MM7 guide pages and content images, then build offline page data.
Run with: uv run --with beautifulsoup4 python scripts/import-mikes-mm7.py
"""
from __future__ import annotations
import json
import re
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / 'source-mirror/www.mikesrpgcenter.com/mm7'
BASE = 'https://www.mikesrpgcenter.com/mm7/'
OUT = ROOT / 'src/mm7-data.js'
DELAY = 1.0
last_request = 0.0

def fetch(url: str) -> bytes:
    global last_request
    wait = DELAY - (time.monotonic() - last_request)
    if wait > 0: time.sleep(wait)
    try:
        with urlopen(Request(url, headers={'User-Agent': 'mm6-atlas/1.0 (fan archive; https://github.com/marnason/mm6-atlas)'}), timeout=30) as response:
            result = response.read()
    finally:
        last_request = time.monotonic()
    return result

def local_path(url: str) -> Path | None:
    parsed = urlparse(url)
    if parsed.netloc != 'www.mikesrpgcenter.com' or not parsed.path.startswith('/mm7/'):
        return None
    relative = parsed.path[len('/mm7/'):]
    if not relative or '..' in Path(relative).parts: return None
    return MIRROR / relative

MIRROR.mkdir(parents=True, exist_ok=True)
queue = deque([BASE + 'index.html'])
seen: set[str] = set()
images: set[str] = set()
while queue:
    url = queue.popleft()
    if url in seen: continue
    seen.add(url)
    path = local_path(url)
    if path is None or path.suffix.lower() not in ('.html', '.htm'): continue
    if path.exists(): raw = path.read_bytes()
    else:
        try: raw = fetch(url)
        except Exception as exc:
            print(f'Page unavailable: {url}: {exc}', flush=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    soup = BeautifulSoup(raw, 'html.parser')
    content = soup.select_one('#content')
    if content is None: continue
    for link in content.select('a[href]'):
        target = urldefrag(urljoin(url, link['href'])).url
        dest = local_path(target)
        if dest and dest.suffix.lower() in ('.html', '.htm') and not dest.stem.endswith('_p'):
            queue.append(target)
    for img in content.select('img[src]'):
        target = urldefrag(urljoin(url, img['src'])).url
        if local_path(target): images.add(target)
    print(f'page {len(seen):3} {path.relative_to(MIRROR)}', flush=True)

for index, url in enumerate(sorted(images), 1):
    path = local_path(url)
    if path.exists(): continue
    try:
        data = fetch(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f'image {index:3}/{len(images)} {path.relative_to(MIRROR)}', flush=True)
    except Exception as exc: print(f'Image failed: {url}: {exc}', flush=True)

pages = []
for path in sorted(MIRROR.rglob('*.html')):
    if path.stem.endswith('_p'): continue
    relative = path.relative_to(MIRROR).as_posix()
    url = BASE + relative
    soup = BeautifulSoup(path.read_bytes(), 'html.parser')
    content = soup.select_one('#content')
    if content is None: continue
    for bad in content.select('script,style,iframe,object,embed,form'):
        bad.decompose()
    # Header art is common to all source pages; retain the actual guide material.
    for img in content.select('img[src]'):
        target = urldefrag(urljoin(url, img['src'])).url
        local = local_path(target)
        if local and local.exists():
            img['src'] = 'assets/mm7/' + local.relative_to(MIRROR).as_posix()
            if not img.get('alt'): img['alt'] = local.stem.replace('_',' ').replace('-',' ').title()
        else:
            notice = soup.new_tag('span')
            notice['class'] = 'missing-source-image'
            notice.string = 'Source image unavailable: ' + (local.name if local else img.get('src',''))
            img.replace_with(notice)
    for link in content.select('a[href]'):
        href = link['href']
        if href.startswith('#'):
            anchor = href[1:]
            link['href'] = '#/mm7/' + relative[:-5] + ('?anchor=' + anchor if anchor else '')
            link['data-link'] = ''
        else:
            parsed = urlparse(urljoin(url, href))
            dest = local_path(parsed.geturl())
            # The source's old items/quest.html link is dead; its anchors live in items.html.
            if dest and dest.relative_to(MIRROR).as_posix() == 'items/quest.html':
                dest = MIRROR / 'items.html'
            if dest and dest.exists() and dest.suffix.lower() in ('.html', '.htm'):
                link['href'] = '#/mm7/' + dest.relative_to(MIRROR).as_posix()[:-5] + ('?anchor=' + parsed.fragment if parsed.fragment else '')
                link['data-link'] = ''
            else:
                link['href'] = parsed.geturl()
                link['target'] = '_blank'
                link['rel'] = 'noopener'
    for tag in content.find_all(True):
        if tag.name == 'a' and tag.get('name') and not tag.get('id'):
            tag['id'] = tag['name']
        for attr in list(tag.attrs):
            if attr.lower().startswith('on') or attr.lower() in ('style', 'width', 'height', 'border', 'bgcolor', 'background'):
                del tag[attr]
    title_nodes = content.find_all(['h1','h2'])
    title_node = title_nodes[-1] if relative.startswith(('armor/','weapons/')) and title_nodes else (title_nodes[0] if title_nodes else None)
    title = title_node.get_text(' ', strip=True) if title_node else (soup.title.get_text(' ',strip=True) if soup.title else path.stem)
    if relative == 'index.html': title = 'Might and Magic VII'
    if relative.startswith('maps/'):
        section = 'Maps'
    else:
        section = 'Overview' if relative == 'index.html' else title
    body = content.get_text(' ', strip=True)
    body = re.sub(r'\s+', ' ', body)
    entries = []
    for tag in content.select('a[id]'):
        label = next(tag.stripped_strings, '').strip()
        label = re.sub(r'\s+', ' ', label)
        if label and len(label) < 130:
            entries.append({'title': label[:100], 'text': tag.get_text(' ', strip=True)[:1200], 'anchor': tag['id']})
    for index, row in enumerate(content.select('tr')):
        cells = row.find_all(['td','th'], recursive=False)
        if len(cells) < 2: continue
        for cell_index, cell in enumerate(cells):
            if cell_index == 0 or not cells[cell_index - 1].find('img'): continue
            label = cell.get_text(' ', strip=True)
            if not label or len(label) > 90 or label.lower() == 'name': continue
            anchor = 'entry-' + str(index) + '-' + str(cell_index)
            cell['id'] = anchor
            entries.append({'title': label, 'text': row.get_text(' ', strip=True)[:900], 'anchor': anchor})
    # These are included for navigation but omitted from search ranking.
    pages.append({'id': relative[:-5], 'title': title, 'section': section, 'body': body, 'entries': entries, 'html': str(content), 'sourcePath': relative})

OUT.write_text('window.MM7_PAGES=' + json.dumps(pages, ensure_ascii=False, separators=(',',':')) + ';\n', encoding='utf-8')
print(f'Imported {len(pages)} pages and {sum(p.is_file() and p.suffix != ".html" for p in MIRROR.rglob("*"))} images.')
