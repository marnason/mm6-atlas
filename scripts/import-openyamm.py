#!/usr/bin/env python3
"""Import MM6 outdoor maps and POIs from a local OpenYAMM checkout.

Requires PyYAML and Pillow. Example:
  uv run --no-project --python 3.12 --with PyYAML --with Pillow \
    python scripts/import-openyamm.py /path/to/openyamm

The OpenYAMM checkout must contain MM6 maps, icons_x2 images, event scripts,
and the shared data tables used by tools/maw_site/world_maps.py.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(SOURCE / 'tools' / 'maw_site'))
import world_maps  # noqa: E402

# Magic Grounds directory names, retained only for matching archived guides.
LEGACY_REGIONS = {
    'outa1': 'Sweet Water', 'outa2': 'Paradise Valley', 'outa3': 'Hermits Isle',
    'outb1': 'Kriegspire', 'outb2': 'Blackshire', 'outb3': 'Dragonsand',
    'outc1': 'White Cap', 'outc2': 'Free Haven', 'outc3': 'Mire Of The Damned',
    'outd1': 'Silver Cove', 'outd2': 'Bootleg Bay', 'outd3': 'Castle Ironfist',
    'oute1': 'Eel Infested Waters', 'oute2': 'Mist', 'oute3': 'New Sorpigal',
}

def main():
    commit = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
    output = ROOT / 'src' / 'assets' / 'openyamm'
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='mm6-openyamm-') as temp:
        records = world_maps.build(Path(temp), only={stem + '.odm' for stem in LEGACY_REGIONS})
        if len(records) != 15:
            raise RuntimeError(f'Expected 15 MM6 outdoor maps, got {len(records)}')
        maps = []
        for record in records:
            stem = record['id']
            source_image = Path(temp) / 'img' / 'maps' / f'{stem}.webp'
            if not source_image.is_file():
                raise RuntimeError(f'Missing image for {stem}')
            shutil.copy2(source_image, output / f'{stem}.webp')
            pois = []
            for poi in record['pois']:
                item = {key: poi[key] for key in ('id', 't', 'n', 'k', 'd', 'map', 'people', 'u', 'v') if key in poi}
                if not poi['id'].startswith('edge'):
                    item['x'] = round(poi['u'] * 65536 - 32768)
                    item['y'] = round(32768 - poi['v'] * 65536)
                pois.append(item)
            maps.append({'id': stem, 'region': record['name'], 'legacyRegion': LEGACY_REGIONS[stem], 'sourceName': record['name'],
                         'image': f'assets/openyamm/{stem}.webp', 'width': record['w'],
                         'height': record['h'], 'pois': pois})
    payload = {'source': 'https://github.com/pjasicek/openyamm', 'commit': commit, 'maps': maps}
    (ROOT / 'src' / 'openyamm-data.js').write_text('window.OPENYAMM=' + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'Imported {len(maps)} maps and {sum(len(m["pois"]) for m in maps)} points from OpenYAMM {commit[:12]}')

if __name__ == '__main__':
    main()
