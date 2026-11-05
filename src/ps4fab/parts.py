"""Every printable part, with the measurements it was built from. Add a part = add a function + a PARTS entry."""
import os
from build123d import Box, Cylinder, Align, Location, Pos, Rot, export_stl
from .covers import cover, split_and_save

MIN = (Align.MIN, Align.MIN, Align.MIN)


def fat_matte_top(out):
    """Fat PS4 matte top cover v2 - CUH-12xx (PS4 1, CUH-1215A), part marking 4-572-317.
    Caliper: wall 22 high / 2.0 thick, plate 2.5, back vents 22 wide x 20 high with 2 mm bars, latch 4 wide, wall+latch 5.
    Measuring-mat photo (height-corrected): rim 0->274, face 11->285, width 162, latches x 45/84/124/160/203,
    vent bars z 16,28..148 (24 pitch),158, light-guide screw boss (235,159), front clips z 25-35/40-48/78-85/112-118.
    Side photos: end walls lean 26-27 deg (11 mm over 22). Front clip shape is an ESTIMATE - print TEST2 first."""
    W, latch_x = 162.0, [45, 84, 124, 160, 203]
    s = cover(W, vent_bars=[16, 28, 52, 76, 100, 124, 148, 158], latch_x=latch_x,
              front_clips=[(25, 35), (40, 48), (78, 85), (112, 118)], bosses=[(235.0, 159.0)])
    split_and_save(s, 'fat_matte_top', W, split_x=142.0, out_dir=out, tests=[
        ('TEST1_side_latch', Box(36, 60, 22, align=(Align.CENTER, Align.MIN, Align.MIN)).locate(Location((latch_x[0], -10, -2)))),
        ('TEST2_front_corner_clips', Box(30, 60, 60, align=MIN).locate(Location((-5, -10, 0))))])


def fat_left_strip(out):
    """Fat PS4 left strip v1 - CUH-12xx (PS4 1), part marking 4-572-450. Same side profile as the matte top.
    Mat photo: width 105.5 (162 + 105.5 + ~7.5 light-bar groove = 275 case width), 8 back vents 12 mm pitch,
    inner-edge tabs x 43-65/98-120/148-173/200-225/250-265, screw bosses (62,98)(102,98)(142,98)(179,98)(107,56),
    latch loop x 180. Front clips not visible in the photo - none modelled yet."""
    W = 105.5
    s = cover(W, vent_bars=[6, 17, 29, 41, 53, 65, 77, 89, 101], latch_x=[180.0],
              bosses=[(62, 98), (102, 98), (142, 98), (179, 98), (107, 56)],
              edge_tabs=[(43, 65), (98, 120), (148, 173), (200, 225), (250, 265)], boss_r=(3.5, 1.0))
    split_and_save(s, 'fat_left_strip', W, split_x=135.0, out_dir=out, tests=[
        ('TEST_latch', Box(36, 60, 22, align=(Align.CENTER, Align.MIN, Align.MIN)).locate(Location((180.0, -10, -2))))])


def hdd_sled(out):
    """Quick-swap sled for a bare 2.5" drive in the fat's metal-shield pocket (PS4 1).
    Drive per SFF-8201: 69.85 wide, 100.45 long, side M3 holes 3.0 up at 14.0 / 90.6 from the non-connector end.
    Pocket (caliper): 84.3 / 85.2 wide, slot 13.0 high. Slotted holes (+-1.5 mm) absorb error. Fit NOT tested."""
    DRV_W, HOLE_Z, HOLES_X = 69.85, 3.0, (14.0, 90.6)
    W = 84.3 - 2 * 0.9; IN_W = DRV_W + 0.45; FLOOR, WALL_T, WALL_H, L = 1.6, 2.4, 8.0, 95.0
    s = Box(L, W, FLOOR, align=(Align.MIN, Align.CENTER, Align.MIN))
    for side in (1, -1):
        s += Box(L, WALL_T, WALL_H, align=MIN).locate(Location((0, side * IN_W / 2 + (0 if side > 0 else -WALL_T), FLOOR)))
    s += Box(10, 24, FLOOR + 0.8, align=(Align.MAX, Align.CENTER, Align.MIN))          # pull tab
    s -= Pos(-5, 0, -1) * Cylinder(5.5, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))   # finger hole
    s -= Box(60, 44, 10, align=(Align.MIN, Align.CENTER, Align.MIN)).locate(Location((20, 0, -1)))  # save filament
    for x in HOLES_X:   # slotted M3 holes through both walls
        s -= Box(3.0, W + 2, 3.5, align=(Align.CENTER, Align.CENTER, Align.CENTER)).locate(Location((x, 0, FLOOR + HOLE_Z)))
        for dx in (-1.5, 1.5):
            s -= Pos(x + dx, 0, FLOOR + HOLE_Z) * Rot(90, 0, 0) * Cylinder(1.75, W + 2)
    bb = s.bounding_box()
    assert bb.size.Y <= 84.3 - 1.5 and bb.size.Z < 13.0, bb
    os.makedirs(out, exist_ok=True)
    s = Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * s
    export_stl(s, os.path.join(out, 'hdd_sled.stl'), tolerance=0.02)
    print(f'hdd_sled: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, ~{s.volume / 1000 * 1.27:.0f} g PETG')


PARTS = {'fat_matte_top': fat_matte_top, 'fat_left_strip': fat_left_strip, 'hdd_sled': hdd_sled}
