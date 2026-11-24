# Enroth Atlas

The atlas now includes a mirrored, searchable Might and Magic VII guide from Mike's RPG Center alongside the Might and Magic VI map and item database. Open `#/mm7` for the MM7 index and maps. The global search covers both games. Source material is cached for offline use by the service worker after the first load.

To refresh the MM7 mirror, run `uv run --with beautifulsoup4 python scripts/import-mikes-mm7.py`, then `npm test`. The import follows guide links within Mike's `/mm7/` section and copies referenced content images. Its `DELAY` constant controls request spacing.

A responsive, searchable, installable, offline-first single-page restoration of the Magic Grounds *Might and Magic VI* Places guide.

The atlas also includes 15 higher-resolution region maps, 646 mapped places, 30 named MM6 Artifacts and Relics, and documented item turn-ins derived from OpenYAMM. Coordinates are approximate in-game X/Y positions, not real-world GPS. OpenYAMM source and asset credits are in [LICENSE.md](LICENSE.md).

## World globe

`src/globe/` is a standalone page (linked as **Globe** in the main navigation) that shows Enroth, Jadame and Antagarich on a rotatable planet. Hovering highlights a region's rectangle and clicking opens that region's OpenYAMM map. The globe textures are stitched and recoloured from OpenYAMM renders of the MM6, MM7 and MM8 outdoor maps; coast beyond the game maps, Vori, Krewlod and the ocean islands are invented filler.

To regenerate the textures from a folder of OpenYAMM renders laid out as `maps/mm6/*.odm.png`, `maps/mm7/*.odm.png` and `maps/mm8/*.odm.png` (needs NumPy, SciPy, OpenCV and Pillow):

```sh
python3 scripts/build-globe.py /path/to/renders src/globe
```

The region layout lives in that script and is mirrored in the `META` constant in `src/globe/index.html`; change both together.

## Build and test

```sh
npm test
```

The generated GitHub Pages site is written to `dist/`.

## Refresh OpenYAMM data

Use a checkout of [OpenYAMM](https://github.com/pjasicek/openyamm) containing the MM6 map, event, table, and `icons_x2` files, then run:

```sh
uv run --no-project --python 3.12 --with PyYAML --with Pillow python scripts/import-openyamm.py /path/to/openyamm
python3 scripts/import-items.py /path/to/openyamm
npm test
```

The imports regenerate the 15 WebP maps, `src/openyamm-data.js`, and `src/items-data.js`. Review the source commit and update the attribution in `LICENSE.md` when refreshing.
