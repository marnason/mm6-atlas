#!/usr/bin/env python3
"""Export MM6 unique items and documented item turn-ins from OpenYAMM tables."""

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]).resolve()
TABLES = SOURCE / 'assets_dev/worlds/mm6/_legacy/tables'
COMMIT = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
BASE = f'https://github.com/pjasicek/openyamm/blob/{COMMIT}/assets_dev/worlds/mm6/_legacy/tables/'

def rows(filename):
    with (TABLES / filename).open(encoding='cp1252', errors='replace', newline='') as stream:
        for line, row in enumerate(csv.reader(stream, delimiter='\t'), 1):
            yield line, row

items = []
for line, row in rows('ITEMS.txt'):
    if len(row) < 17 or not row[0].isdigit() or not 2020 <= int(row[0]) <= 2049:
        continue
    if row[8] not in ('Artifact', 'Relic'):
        raise ValueError(f'Unexpected MM6 unique-item category on line {line}')
    items.append({'id': int(row[0]), 'name': row[2], 'kind': row[8], 'slot': row[5],
                  'description': row[16].strip(), 'source': BASE + f'ITEMS.txt#L{line}'})
if len(items) != 30:
    raise ValueError(f'Expected 30 MM6 artifacts and relics, got {len(items)}')

buyer_specs = [
    (460, 'Cobra Eggs', 'Hejaz Mawsil', 300, 'New Sorpigal', 'h1328', 'Abandoned Temple', 'h422'),
    (461, 'Temple Gongs', 'Lawrence Aleman', 2000, 'Free Haven', 'h1540', None, None),
    (462, 'Bones', 'Lon Miller', 1000, 'Free Haven', 'h1557', None, None),
    (463, 'Lodestones', 'Davis Carp', 5, 'Free Haven', 'h1558', None, None),
    (464, 'Feathers', 'Bonnie Rotterdam', 10, 'Free Haven', 'h1546', None, None),
    (465, 'Pyramids', 'Renee Blackburn', 1000, 'Free Haven', 'h1556', None, None),
    (466, 'Kegs of Wine', 'Nick Fenster', 300, 'Free Haven', 'h1559', None, None),
    (467, 'Teeth', 'Sy Roth', 500, 'Free Haven', 'h1560', None, None),
    (468, 'Clovers', 'Geoff Southy', 25, 'Free Haven', 'h1562', None, None),
    (469, 'Amber', 'Dillan Robinson', 500, 'Free Haven', 'h1563', None, None),
]
notes = {}
for line, row in rows('Autonote.txt'):
    if row and row[0].isdigit():
        notes[int(row[0])] = (line, row[1])
exchanges = []
for note_id, item, buyer, gold, region, poi, found_at, found_poi in buyer_specs:
    line, note = notes[note_id]
    if 'buy' not in note.lower() or str(gold) not in note:
        raise ValueError(f'Buyer note {note_id} changed: {note}')
    exchanges.append({'item': item, 'kind': 'buyer', 'buyer': buyer, 'gold': gold,
                      'region': region, 'poi': poi, 'foundAt': found_at, 'foundPoi': found_poi,
                      'note': note, 'source': BASE + f'Autonote.txt#L{line}'})
exchanges.append({'item': 'Whisp wrappings', 'aliases': ['Wisp Wrappings', 'Whisp Wrappings'],
                  'kind': 'quest', 'buyer': 'Verdant', 'region': 'Castle Ironfist',
                  'foundAt': "Corlagon's Estate", 'foundPoi': 'h440',
                  'note': "OpenYAMM's combined-game quest dialogue sends players to Corlagon's Estate for the wrappings and asks them to bring the item to Verdant for the Telelocator. No repeatable gold or XP exchange is documented in these sources.",
                  'source': f'https://github.com/pjasicek/openyamm/blob/{COMMIT}/assets_dev/engine/data_tables/npc_topic_text.txt#L5936-L5942'})

payload = {'source': 'https://github.com/pjasicek/openyamm', 'commit': COMMIT, 'items': items, 'exchanges': exchanges}
(ROOT / 'src/items-data.js').write_text('window.ATLAS_ITEMS=' + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(f'Imported {len(items)} unique MM6 items and {len(exchanges)} item turn-ins/quests')
