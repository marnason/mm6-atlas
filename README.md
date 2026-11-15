# Enroth Atlas

A responsive, searchable, installable, offline-first single-page restoration of the Magic Grounds *Might and Magic VI* Places guide.

The atlas also includes 15 higher-resolution region maps, 646 mapped places, 30 named MM6 Artifacts and Relics, and documented item turn-ins derived from OpenYAMM. Coordinates are approximate in-game X/Y positions, not real-world GPS. OpenYAMM source and asset credits are in [LICENSE.md](LICENSE.md).

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
