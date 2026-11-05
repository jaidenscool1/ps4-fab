# ps4fab

Measure console parts from ordinary phone photos and build printable replacement parts.

The measuring trick is a **printed marker mat**: two pages of ChArUco markers on the table next to the part.
From one photo the program finds the markers, works out exactly where the camera was, and turns any pixel into
real millimetres at a height you choose. Tested on a synthetic photo: a 160 x 280 mm box came back within
0.07 mm. Plain photo scaling was 3% off, because a 22 mm-tall rim is closer to the camera than the table.

## Install

Python 3.10-3.12 ([uv](https://docs.astral.sh/uv/) recommended):

```sh
git clone <this repo> && cd ps4-fab
uv venv -p 3.12 .venv && uv pip install -p .venv/bin/python -e '.[test]'
.venv/bin/ps4fab --help
.venv/bin/python -m pytest -q        # 4 tests: mat accuracy + every part builds and fits a 250 mm bed
```

## Commands

| Command | What it does |
|---|---|
| `ps4fab mat` | Writes `measuring_mat.pdf`. Print both pages at **100% / Actual size**, then caliper the 100 mm bar. |
| `ps4fab guide -o DIR` | Writes the measuring guide with diagrams: where to put the caliper, how to take the photo. |
| `ps4fab measure PHOTO --check 100.0 --h 0 22` | Camera pose + true-scale top views at each height (10 mm grid). HEIC works directly. |
| `ps4fab view PHOTO --origin X Y --angle A --size L W --h H` | A top view lined up with the part, with its own mm grid. Use it for reading features. |
| `ps4fab list` | Every part and the measurements it was built from. |
| `ps4fab build [PART ...] -o out` | Builds STLs (default: all). Already oriented for printing: outside face down. |

## Measuring workflow

1. Print the mat and write down the caliper reading of the 100 mm bar (pass it as `--check`).
2. Lay page 1 and page 2 on the table on either side of the part. No tape needed; they don't have to line up.
3. Phone held flat, about 2 ft up, 1x zoom, whole part + both pages in frame, no flash.
4. `ps4fab measure photo.HEIC --h 0 22` gives the overview. Find the part's corner and angle in it, then
   `ps4fab view ...` gives a part-aligned view.
5. **Read every feature at its own height.** With the camera about 600 mm up, a 22 mm rim near the end of a
   280 mm part shifts about 5 mm between the table-height view and the rim-height view.
6. Caliper only what photos can't see: wall and plate thickness, clip depth.

## Parts

| Part | Console | Status |
|---|---|---|
| `fat_matte_top` | Fat CUH-12xx matte top (marking 4-572-317) | v2 from real measurements. **Print the 2 TEST pieces first**: front clip shape is estimated |
| `fat_left_strip` | Fat CUH-12xx left strip (4-572-450) | v1 from a mat photo. Front clips not modelled yet |
| `hdd_sled` | Fat HDD pocket in the metal shield | Bare 2.5" drive sled, fit not tested |

Covers are split into two halves plus a splice plate (glue with 2-part plastic epoxy), so they fit a 250 x 250 bed.
Print settings: PETG, 0.2 mm layers, 4 walls, 40% gyroid, outside face down on a textured plate, no supports.
The original clear light guide is reused (it screws to the boss on the matte top).

## Adding a part

Add a function to `src/ps4fab/parts.py` that builds it with build123d and writes STLs to the `out` folder it is given.
Put **where each number came from** in the docstring (caliper, mat photo, datasheet), then add it to `PARTS`.
The shared cover shape (profile, vents, latch loops, clips, bosses, splitting) is in `covers.py`.

## Rules for this repo

- **Don't commit photos** (`.gitignore` blocks them; they show people's homes). Commit numbers and code.
- Only our own measurements go into parts. Don't copy numbers out of other people's models
  (many on Printables are CC BY-NC).
- Say how a number was measured and how sure it is. Estimates are marked ESTIMATE in the code.
