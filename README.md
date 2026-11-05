# ps4fab

The **PS4 Teardown Tracer** as a program you run yourself, plus the tools behind it.

- **Teardown Tracer app** (`ps4fab serve`): console profiles, the two-sided 3D board with every mapped part,
  click-a-part tracing to the APU, pin readings, teardown stages, and the Bench Blueprint, Chain of trust,
  Caliper sheet and c1 shot-list pages.
- **Printable parts per profile**: a profile shows STL download buttons when we have measured parts for its model
  (right now CUH-12xx: matte top cover, left strip, HDD sled).
- **Measuring mat**: two printed marker pages beside a part turn one phone photo into true millimetres.
  On a synthetic test, a 160 x 280 mm box came back within 0.07 mm.

## Install

Python 3.10-3.12 ([uv](https://docs.astral.sh/uv/) recommended):

```sh
git clone https://github.com/jaidenscool1/ps4-fab && cd ps4-fab
uv venv -p 3.12 .venv && uv pip install -p .venv/bin/python -e '.[test]'
.venv/bin/python -m pytest -q        # 10 tests
```

## Run the app

```sh
.venv/bin/ps4fab serve               # then open http://localhost:8780/
```

Everything you change in the app (profiles, notes, readings) is saved as JSON files in `data/db/`
(one file per document). To share with the group:

- **Through git:** commit and push `data/`; the others `git pull`. Small, readable diffs per console.
- **Live on one network:** one person runs `ps4fab serve --host 0.0.0.0` and the rest open `http://<their-ip>:8780/`.
  Edits show up for everyone within a few seconds. There is no login, so only do this on a home network.

The 3D view loads three.js and fonts from the internet. Everything else works offline.

## Commands

| Command | What it does |
|---|---|
| `ps4fab serve [--data DIR] [--port N] [--host H]` | Runs the Teardown Tracer app |
| `ps4fab import export.json` | Loads `{collection: {doc: data}}` documents into `data/db` |
| `ps4fab mat` | Writes `measuring_mat.pdf`. Print both pages at **100% / Actual size**, caliper the 100 mm bar |
| `ps4fab guide -o DIR` | Measuring guide with diagrams (caliper spots, how to take the photo) |
| `ps4fab measure PHOTO --check 100.0 --h 0 22` | Camera pose + true-scale top views at those heights. HEIC works |
| `ps4fab view PHOTO --origin X Y --angle A --size L W --h H` | Top view lined up with a part, with its own mm grid |
| `ps4fab list` / `ps4fab build [PART ...]` | List parts and their sources / build STLs (oriented for printing) |

## Measuring a part

1. Print the mat; pass the caliper reading of the 100 mm bar as `--check`.
2. Pages flat on either side of the part (no tape needed), phone held flat about 2 ft up, 1x zoom, no flash.
3. `ps4fab measure photo.HEIC --h 0 22`, find the part's corner and angle, then `ps4fab view ...`.
4. **Read every feature at its own height.** A 22 mm rim near the end of a 280 mm part shifts about 5 mm between
   the table-height view and the rim-height view.
5. Caliper only what photos can't show: wall and plate thickness, clip depth.

## Adding a printable part

Write a builder in `src/ps4fab/parts.py` (build123d) that writes STLs into the folder it's given.
Put **where every number came from** in its docstring, mark guesses ESTIMATE, and set
`.fits = [...]` (the Model ids from the app's profile list, e.g. `'CUH-12xx'`) and a short `.title`.
Add it to `PARTS`. The profile page then offers it automatically. Shared cover shapes live in `covers.py`.

## Layout

```
src/ps4fab/web/     the app: tracer.html (the page), shim.js (database bridge), tiles/ (3D textures), pages/
src/ps4fab/serve.py web server + JSON-file database + STL zips
data/db/            the shared data (stages, consoles, auto-detected parts, readings)
```

## Rules

- Keep the repo **private**. The iFixit reference board (textures and part positions) is derived from the
  [iFixit PS4 teardown](https://www.ifixit.com/Teardown/PlayStation+4+Teardown/19493) (CC BY-NC-SA 3.0)
  and McMaster's SAA-001 scans ([siliconpr0n](https://siliconpr0n.org/map/sony/saa-001/)). Non-commercial use only.
- No personal or room photos in git (`.gitignore` blocks loose photos). Board textures the app needs live in `src/ps4fab/web/`.
- Printable parts use only our own measurements, never numbers copied from other people's models.
- Every number says how it was measured and how sure it is.
