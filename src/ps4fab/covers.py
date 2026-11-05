# Shared builder for fat PS4 top covers (matte top 4-572-317 and left strip 4-572-450), from the user's own measurements.
# Axes (console orientation): x = front -> back, y = up (0 = bottom rim, H = outside face),
#   z = across (0 = outer side wall face, W = inner edge at the light-bar groove).
# Profile (measured on the matte cover, shared by the strip because they sit flush side by side):
#   rim 0 -> 274, face 11 -> 285, both end walls lean 11 mm over 22 mm (side photos: 26-27 deg).
from build123d import *
import os

H, T_TOP, T_SIDE = 22.0, 2.5, 2.0
LEAN, X_RIM_F, X_RIM_B = 0.5, 0.0, 274.0
TH = T_SIDE * (1 + LEAN ** 2) ** 0.5
xf = lambda y: X_RIM_F + LEAN * y
xb = lambda y: X_RIM_B + LEAN * y
YP = H - T_TOP

def prism(pts, z0, z1):
    return extrude(Plane.XY.offset(z0) * Polygon(*pts, align=None), amount=z1 - z0)

def cover(W, vent_bars, latch_x, front_clips=(), bosses=(), edge_tabs=(), lip_w=4.5, lip_t=1.5, vent_y=(2.0, 20.0),
          latch=(4.0, 3.0, 3.0, 1.0), clip=(1.5, 2.5), boss_r=(3.0, 0.8), tab=(2.5, 1.5)):
    prof = [(xf(0), 0), (xf(0) + lip_w, 0), (xf(0) + lip_w, lip_t), (xf(lip_t) + TH, lip_t), (xf(YP) + TH, YP),
            (xb(YP) - TH, YP), (xb(0) - TH, 0), (xb(0), 0), (xb(H), H), (xf(H), H)]
    side = [(xf(0), 0), (xb(0), 0), (xb(H), H), (xf(H), H)]
    s = prism(prof, 0, W) + prism(side, 0, T_SIDE)
    # back vents between bars (bar centres, 2 mm wide)
    y0, y1 = vent_y
    cut = [(xb(y0) - TH - 1, y0), (xb(y0) + 1, y0), (xb(y1) + 1, y1), (xb(y1) - TH - 1, y1)]
    edges = [T_SIDE] + [e for b in vent_bars for e in (b - 1, b + 1)]
    for z0, z1 in zip(edges[0::2], edges[1::2]):
        if z1 - z0 > 3: s -= prism(cut, z0, z1)
    # Pi-loop latches inside the outer wall, at the rim
    lw, ld, lh, leg = latch
    for x in latch_x:
        loop = Box(lw, lh, ld, align=(Align.CENTER, Align.MIN, Align.MIN)).locate(Location((x, 0, T_SIDE)))
        win = Box(lw - 2 * leg, lh + 1, ld - leg, align=(Align.CENTER, Align.MIN, Align.MIN)).locate(Location((x, -0.5, T_SIDE)))
        s += loop - win
    # front clips under the front lip (estimated shape)
    for z0, z1 in front_clips:
        s += Box(clip[0], clip[1], z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN)).locate(Location((xf(0) + lip_w, lip_t, z0)))
    # screw bosses under the plate
    c = Align.CENTER
    for bx, bz in bosses:
        b = Cylinder(boss_r[0], 6, align=(c, c, Align.MIN)) - Cylinder(boss_r[1], 7, align=(c, c, Align.MIN))
        s += Pos(bx, YP, bz) * Rot(90, 0, 0) * b
    # thin tabs sticking out past the inner edge, flush with the outside face
    for x0, x1 in edge_tabs:
        s += Box(x1 - x0, tab[1], tab[0], align=(Align.MIN, Align.MAX, Align.MIN)).locate(Location((x0, H, W)))
    return s

def split_and_save(shell, prefix, W, split_x, tests=(), out_dir='out'):
    big = 400
    halves = [shell & Box(big, 60, W + 20, align=(Align.MAX, Align.MIN, Align.MIN)).locate(Location((split_x, -10, -10))),
              shell & Box(big, 60, W + 20, align=(Align.MIN, Align.MIN, Align.MIN)).locate(Location((split_x, -10, -10)))]
    assert abs(shell.volume - halves[0].volume - halves[1].volume) < 1, 'split lost material'
    splice = Box(30, 1.6, W - T_SIDE - 10, align=(Align.CENTER, Align.MAX, Align.MIN)).locate(Location((split_x, YP, T_SIDE + 4)))
    os.makedirs(out_dir, exist_ok=True)
    def save(part, name, check_bed=False):
        p = Rot(-90, 0, 0) * part          # y -> -z: outside face down on the bed
        b = p.bounding_box(); p = Pos(-b.min.X, -b.min.Y, -b.min.Z) * p
        export_stl(p, os.path.join(out_dir, f'{name}.stl'), tolerance=0.02)
        sz = p.bounding_box().size; print(f'{name}: {sz.X:.1f} x {sz.Y:.1f} x {sz.Z:.1f} mm, ~{p.volume / 1000 * 1.27:.0f} g PETG')
        if check_bed: assert sz.X <= 250 and sz.Y <= 250, f'{name} does not fit the 250 mm bed'
    save(shell, f'{prefix}_full_reference')
    save(halves[0], f'{prefix}_A_front', True); save(halves[1], f'{prefix}_B_back', True)
    save(splice, f'{prefix}_splice_plate', True)
    for name, box in tests: save(shell & box, f'{prefix}_{name}', True)
    bb = shell.bounding_box()
    assert abs(bb.size.Y - H) < 0.01 and abs(bb.size.Z - W) < 3.1, bb
    return shell
