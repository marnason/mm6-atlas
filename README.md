# Enroth Atlas

A responsive, searchable, installable, offline-first single-page restoration of the Magic Grounds *Might and Magic VI* Places guide.

The atlas also includes 15 higher-resolution region maps and 646 mapped places derived from OpenYAMM. Coordinates are approximate in-game X/Y positions, not real-world GPS. OpenYAMM source and asset credits are in [LICENSE.md](LICENSE.md).

## Build and test

```sh
npm test
```

The generated GitHub Pages site is written to `dist/`.

## Refresh OpenYAMM data

Use a checkout of [OpenYAMM](https://github.com/pjasicek/openyamm) containing the MM6 map, event, table, and `icons_x2` files, then run:

```sh
uv run --no-project --python 3.12 --with PyYAML --with Pillow python scripts/import-openyamm.py /path/to/openyamm
npm test
```

The import regenerates the 15 WebP maps and `src/openyamm-data.js`. Review its source commit and update the attribution in `LICENSE.md` when refreshing.
