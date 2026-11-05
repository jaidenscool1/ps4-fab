# Measuring guide for the fat PS4 matte top cover: 2 Letter pages (PDF + PNGs).
# `ps4fab guide` -> measure-guide-matte-cover.pdf
import os, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch
from matplotlib.backends.backend_pdf import PdfPages

INK, PART, MAT, CAL, ACC = '#222', '#555', '#f2f2f2', '#c0392b', '#1f6fb2'

def arrow(ax, a, b, txt, col=CAL, off=(0, 0), fs=9, both=True):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='<->' if both else '->', mutation_scale=10, color=col, lw=1.4))
    m = ((a[0] + b[0]) / 2 + off[0], (a[1] + b[1]) / 2 + off[1])
    ax.text(*m, txt, color=col, fontsize=fs, ha='center', va='center', weight='bold',
            bbox=dict(fc='white', ec='none', pad=1))

def jaws(ax, x, y0, y1, side):  # little caliper jaw at x, spanning y0..y1, pointing to `side` (+1 right / -1 left)
    ax.add_patch(Polygon([(x, y0), (x + side * 1.2, y0), (x + side * 1.2, y1), (x, y1 - 1.0)], color=CAL, alpha=0.85))

def mat_page(ax, x, y, w=21.6, h=27.9, label=''):
    ax.add_patch(Rectangle((x, y), w, h, fc='white', ec=INK, lw=1))
    sq = w * 0.81 / 7
    for i in range(7):
        for j in range(9):
            if (i + j) % 2 == 0:
                ax.add_patch(Rectangle((x + w * 0.095 + i * sq, y + h * 0.08 + j * sq), sq, sq, fc='#444', ec='none'))
    ax.text(x + w / 2, y + h + 1.2, label, ha='center', fontsize=8)

def phone(ax, x, y, s=1.0):
    ax.add_patch(Rectangle((x - 2 * s, y), 4 * s, 7.5 * s, fc='#ddd', ec=INK, lw=1, zorder=5))
    ax.add_patch(Rectangle((x - 0.5 * s, y + 5.6 * s), 1 * s, 1 * s, fc=INK, zorder=6))

def header(fig, t, sub):
    fig.text(0.5, 0.965, t, ha='center', fontsize=15, weight='bold')
    fig.text(0.5, 0.94, sub, ha='center', fontsize=9.5, color='#444')

def step(ax, n, title, lines):
    ax.set_title(f'{n}.  {title}', loc='left', fontsize=11, weight='bold', pad=4)
    ax.text(0, -0.04, '\n'.join(lines), transform=ax.transAxes, va='top', fontsize=8.6, linespacing=1.35)

def write_guide(OUT='.'):
    pages = []
    # ---------------- PAGE 1: printing + the two mat photos ----------------
    fig = plt.figure(figsize=(8.5, 11)); pages.append(fig)
    header(fig, 'Measuring the matte top cover - page 1 of 2', 'One photo on the printed mat does most of the measuring. Caliper only for the small stuff on page 2.')

    ax = fig.add_axes([0.07, 0.72, 0.86, 0.17]); ax.set_xlim(0, 100); ax.set_ylim(-6, 20); ax.axis('off'); ax.set_aspect('equal')
    mat_page(ax, 2, -4, 14, 18, 'measuring_mat.pdf page')
    ax.plot([30, 80], [6, 6], color=INK, lw=2); ax.plot([30, 30], [4.5, 7.5], color=INK, lw=2); ax.plot([80, 80], [4.5, 7.5], color=INK, lw=2)
    jaws(ax, 30, 7.5, 13, -1); jaws(ax, 80, 7.5, 13, 1)
    ax.add_patch(Rectangle((28.8, 13), 52.4, 3, fc='#888', ec=INK)); ax.text(55, 14.5, 'caliper', ha='center', va='center', fontsize=8, color='white')
    arrow(ax, (30, 2.5), (80, 2.5), 'the printed 100 mm bar: write down what the caliper says')
    step(ax, 1, 'Print the mat and check its size', [
        'Print measuring_mat.pdf (2 pages) on plain paper. In the print window pick "Actual size" / 100% - NOT "Fit to page".',
        'Open the caliper jaws on the black bar at the bottom of page 1 (tips on the two end ticks). It should read 100.0 mm.',
        'Write the number down even if it is 99.4 or 100.6 - the script corrects for it. No tape or glue needed on the pages.'])

    ax = fig.add_axes([0.07, 0.40, 0.86, 0.22]); ax.set_xlim(0, 100); ax.set_ylim(-2, 44); ax.axis('off'); ax.set_aspect('equal')
    mat_page(ax, 2, 2, label='page 1'); mat_page(ax, 76.4, 2, label='page 2')
    ax.add_patch(Rectangle((27.5, 2.5), 45, 28.6, fc=PART, ec=INK, lw=1))          # cover, inside up (1 unit = 1 cm)
    ax.add_patch(Rectangle((28.3, 3.3), 43.4, 27.0, fc='#777', ec='#999', lw=0.8))
    for k in range(9): ax.add_patch(Rectangle((72.5 - 1.7, 4 + k * 2.9), 1.5, 1.6, fc='white', ec='none'))   # back vents
    ax.add_patch(Rectangle((27.5, 2.5), 45, 1.2, fc='#b9c4cc', ec=INK, lw=0.6)); ax.text(50, 1.2, 'grey light strip (leave it on)', ha='center', fontsize=7)
    ax.text(50, 17, 'cover, INSIDE facing up\n(outside face on the table)', ha='center', va='center', color='white', fontsize=8.5)
    ax.text(75.5, 17, 'back\n(vents)', fontsize=7, ha='right', va='center', color='white'); ax.text(28.6, 17, 'front', fontsize=7, va='center', color='white')
    phone(ax, 50, 36, 0.8); ax.text(54, 39, 'phone flat, straight down\nabout 2 ft up, 1x zoom', fontsize=8, va='center')
    step(ax, 2, 'Photo A - cover inside up, between the two mat pages', [
        'Lay page 1 and page 2 flat on the table, one on each side of the cover, touching or almost touching it.',
        'Cover INSIDE facing up. Phone held flat (screen parallel to the table), whole cover + both pages fully in the frame.',
        'Good light, no flash. Take 2-3 shots; slightly different spots are fine.',
        'This one photo gives: width, length, both slanted ends, every latch and screw position, the vent spacing.'])

    ax = fig.add_axes([0.07, 0.08, 0.86, 0.17]); ax.set_xlim(0, 100); ax.set_ylim(0, 30); ax.axis('off'); ax.set_aspect('equal')
    # why photo A is enough: side view of the front end, rim and plate seen from above
    prof = np.array([(13.84, 0), (40, 0), (40, 2.1), (14.44, 2.1), (3.83, 20.5), (5.83, 20.5), (5.83, 22), (1.14, 22)]) + [9, 2]
    ax.add_patch(Polygon(prof, fc=PART, ec=INK))   # real front-end profile, cover inside up (mm)
    ax.plot([10.1, 10.1], [24, 29], ls=':', color=ACC); ax.plot([23.4, 23.4], [4.1, 29], ls=':', color=ACC)
    ax.text(10, 29.5, 'rim seen here', color=ACC, fontsize=7.5, ha='center'); ax.text(24.5, 29.5, 'wall meets plate here', color=ACC, fontsize=7.5)
    ax.plot([0, 45], [2, 2], color=INK, lw=0.8); ax.text(42, 0.3, 'table', fontsize=7)
    ax.text(48, 20, 'Side view of the FRONT end (cover inside up).', fontsize=8.5, weight='bold')
    ax.text(48, 7, 'The phone sees where the rim is and where the slanted\nwall meets the plate. With the wall height (C0 on page 2)\nthe script works out the slant - so no second pose is\nneeded. Same for the back end.', fontsize=8.5)
    step(ax, 3, 'Why one photo is enough', ['If you still have the narrow LEFT STRIP of PS4 1: take photo A of it too (same way, inside up).'])
    for f in [fig]:
        pass

    # ---------------- PAGE 2: caliper readings ----------------
    fig = plt.figure(figsize=(8.5, 11)); pages.append(fig)
    header(fig, 'Measuring the matte top cover - page 2 of 2', 'Caliper readings. Drawings are cut-through views (as if the cover were sawn in half). Red = caliper jaws.')

    def section(ax, hook=True):
        # cut across the cover near a latch: top plate + outer side wall + latch hook (mm, from the v1 model)
        ax.add_patch(Polygon([(0, 0), (60, 0), (60, 2.1), (2, 2.1), (2, 22), (0, 22)], fc=PART, ec=INK, lw=1))
        if hook: ax.add_patch(Polygon([(2, 19), (3.2, 19), (3.2, 20.8), (2.0, 22)], fc=PART, ec=INK, lw=1))

    ax = fig.add_axes([0.06, 0.70, 0.40, 0.19]); ax.set_xlim(-10, 50); ax.set_ylim(-6, 30); ax.axis('off'); ax.set_aspect('equal')
    section(ax, False); ax.text(30, 4.5, 'top plate', fontsize=8); ax.text(-1, 24, 'side wall', fontsize=8, ha='center')
    jaws(ax, 40, -4.5, 0, 1); jaws(ax, 40, 2.1, 6.5, 1)
    arrow(ax, (47, 0), (47, 2.1), 'C1', off=(2.5, 0)); arrow(ax, (-4, 0), (-4, 22), 'C0', off=(-3.5, 0))
    step(ax, 'C0 + C1', 'Wall height + plate thickness', ['C0: jaws from the flat outside face to the', 'top edge of the side wall (about 22 mm).', 'C1: jaws on the flat plate at the open inner', 'edge, next to the grey strip (about 2 mm).'])

    ax = fig.add_axes([0.54, 0.70, 0.40, 0.19]); ax.set_xlim(-10, 50); ax.set_ylim(-6, 30); ax.axis('off'); ax.set_aspect('equal')
    section(ax, False); jaws(ax, -4.5, 17, 22, 1); jaws(ax, 6.5, 17, 22, -1)
    arrow(ax, (0, 25), (2, 25), 'C2', off=(5, 0))
    step(ax, 'C2', 'Side wall thickness', ['Clamp across the side wall at its top', 'edge, away from any latch.', 'Expect about 2 mm.'])

    ax = fig.add_axes([0.06, 0.40, 0.40, 0.22]); ax.set_xlim(-4, 60); ax.set_ylim(-8, 30); ax.axis('off'); ax.set_aspect('equal')
    ax.add_patch(Rectangle((0, 0), 56, 20, fc=PART, ec=INK))
    for k in range(4): ax.add_patch(Rectangle((3 + k * 15.2, 2), 10, 15.5, fc='white', ec=INK))
    arrow(ax, (3, 23), (13, 23), 'C3a'); arrow(ax, (13, -4), (18.2, -4), 'C3b'); arrow(ax, (31, 2), (31, 17.5), 'C3c', off=(4, 0))
    step(ax, 'C3', 'Back vents (looking at the back end)', ['C3a: width of one opening (use the small', 'top jaws, open them inside the hole).',
         'C3b: width of one bar between openings.', 'C3c: height of one opening.'])

    ax = fig.add_axes([0.54, 0.40, 0.40, 0.22]); ax.set_xlim(-12, 24); ax.set_ylim(-4, 30); ax.axis('off'); ax.set_aspect('equal')
    ax.add_patch(Polygon([(0, 0), (20, 0), (20, 2.1), (2, 2.1), (2, 22), (0, 22)], fc=PART, ec=INK, lw=1))
    ax.add_patch(Polygon([(2, 18.5), (3.4, 18.5), (3.4, 20.6), (2.0, 22)], fc='#888', ec=CAL, lw=1.4))
    arrow(ax, (0, 25.5), (3.4, 25.5), 'C4b', off=(6, 0)); arrow(ax, (6.5, 18.5), (6.5, 22), 'C4c', off=(4.5, 0))
    ax.text(9, 12, 'latch hook\n(cut view)', fontsize=8)
    step(ax, 'C4', 'One square latch (on the side wall)', ['C4a: hook width, along the wall (jaws).', 'C4b: wall + hook together, at the hook.',
         'C4c: wall top edge down to the hook\'s', 'flat underside (depth rod).'])

    ax = fig.add_axes([0.06, 0.07, 0.88, 0.22]); ax.axis('off')
    ax.set_title('Send back', loc='left', fontsize=11, weight='bold')
    rows = [['1', 'Mat check bar', '____ mm'], ['A', 'Photo A (inside up, 2-3 shots)', 'photo'], ['C0', 'Wall height', '____ mm'],
            ['C1', 'Plate thickness', '____ mm'], ['C2', 'Side wall thickness', '____ mm'],
            ['C3', 'Vent: opening a / bar b / height c', '___ / ___ / ___'], ['C4', 'Latch: width a / wall+hook b / top-to-hook c', '___ / ___ / ___']]
    t = ax.table(cellText=rows, colLabels=['#', 'What', 'Your reading'], loc='upper left', colWidths=[0.06, 0.55, 0.3], cellLoc='left')
    t.auto_set_font_size(False); t.set_fontsize(9.5); t.scale(1, 1.45)

    os.makedirs(OUT, exist_ok=True)
    with PdfPages(os.path.join(OUT, 'measure-guide-matte-cover.pdf')) as pdf:
        for i, f in enumerate(pages):
            pdf.savefig(f); f.savefig(os.path.join(OUT, f'measure-guide-page{i + 1}.png'), dpi=110)
    return os.path.join(OUT, 'measure-guide-matte-cover.pdf')
