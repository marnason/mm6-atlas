"""Extract Mike's MM7 timetable into structured, source-faithful travel data.

Run with: uv run --with beautifulsoup4 python scripts/import-mm7-transport.py
"""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'source-mirror/www.mikesrpgcenter.com/mm7/transportation.html'
OUTPUT = ROOT / 'src/mm7-travel-data.js'
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
SHIPS = {'Wind Runner', 'Enchantress', 'The Lady Catherine', 'Sacred Sails', 'Narwhale', 'Sea Sprite'}
NAMES = {'Bracada Dessert': 'Bracada Desert', 'Evermorn Island': 'Evenmorn Island'}

soup = BeautifulSoup(SOURCE.read_bytes(), 'html.parser')
services = []
trips = []
for row in soup.select('#content table tr')[1:]:
    cells = [cell.get_text(' ', strip=True) for cell in row.find_all('td', recursive=False)]
    if len(cells) != 9:
        raise ValueError(f'Unexpected timetable row: {cells}')
    name, origin, *schedule = cells
    origin = NAMES.get(origin, origin)
    mode = 'ship' if name in SHIPS else 'coach'
    services.append({'name': name, 'origin': origin, 'mode': mode})
    for day, cell in zip(DAYS, schedule):
        for match in re.finditer(r'([^,]+?)\s*\((\d+)\)(?:,|$)', cell):
            destination = match.group(1).strip()
            destination = NAMES.get(destination, destination)
            trips.append({'service': name, 'origin': origin, 'destination': destination,
                          'mode': mode, 'day': day, 'days': int(match.group(2))})
        if cell and not re.fullmatch(r'(?:[^,]+?\s*\(\d+\))(?:,\s*[^,]+?\s*\(\d+\))*', cell):
            raise ValueError(f'Unparsed service: {name} {day}: {cell}')

globe = (ROOT / 'src/globe/index.html').read_text()
match = re.search(r'^const META=(\{.*\});$', globe, re.M)
if not match:
    raise ValueError('Stitched globe map metadata not found')
metadata = json.loads(match.group(1))
x0, y0, x1, y1 = next(c['ext'] for c in metadata['continents'] if c['key'] == 'antagarich')
positions = {}
for region in metadata['regions']:
    if region['game'] != 'mm7': continue
    left, top, right, bottom = region['rect']
    positions[region['name']] = [round(((left + right) / 2 - x0) / (x1 - x0) * 1000),
                                 round(((top + bottom) / 2 - y0) / (y1 - y0) * 857)]
# The Arena is a special destination, so its marker is diagrammatic.
positions['Arena'] = [round(((2.75 - x0) / (x1 - x0)) * 1000),
                      round(((1.9 - y0) / (y1 - y0)) * 857)]
missing = ({trip['origin'] for trip in trips} | {trip['destination'] for trip in trips}) - positions.keys()
if missing:
    raise ValueError(f'Missing globe positions for: {sorted(missing)}')
positions = {name: positions[name] for name in sorted({trip['origin'] for trip in trips} | {trip['destination'] for trip in trips})}
data = {'source': 'https://www.mikesrpgcenter.com/mm7/transportation.html',
        'days': DAYS, 'services': services, 'trips': trips, 'positions': positions}
OUTPUT.write_text('window.MM7_TRAVEL=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(f'Imported {len(services)} services and {len(trips)} scheduled trips')
