# Printable measuring mat: 2 US-Letter pages, each a ChArUco board with its own marker ids.
# `ps4fab mat` -> measuring_mat.pdf (print at 100% / "actual size", NOT "fit to page")
import cv2, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

PAGE_W, PAGE_H = 215.9, 279.4          # US Letter, mm
COLS, ROWS, SQ, MK = 7, 9, 25.0, 18.0  # 175 x 225 mm board, 25 mm squares, 18 mm markers
DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
N_MARK = (COLS * ROWS) // 2            # 31 markers per page
ORIGIN = ((PAGE_W - COLS * SQ) / 2, 22.0)   # board's lower-left corner on the page (mm from left, bottom)

def board(page):
    ids = np.arange(page * N_MARK, (page + 1) * N_MARK, dtype=np.int32)
    return cv2.aruco.CharucoBoard((COLS, ROWS), SQ, MK, DICT, ids)

def write_mat(path='measuring_mat.pdf'):
    with PdfPages(path) as pdf:
        for page in range(2):
            img = board(page).generateImage((COLS * 236, ROWS * 236), marginSize=0, borderBits=1)  # ~240 dpi
            fig = plt.figure(figsize=(PAGE_W / 25.4, PAGE_H / 25.4))
            ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, PAGE_W); ax.set_ylim(0, PAGE_H); ax.axis('off')
            x0, y0 = ORIGIN
            ax.imshow(img, cmap='gray', extent=(x0, x0 + COLS * SQ, y0, y0 + ROWS * SQ), interpolation='nearest')
            # 100 mm check bar: measure it with the caliper after printing
            ax.plot([x0, x0 + 100], [12, 12], 'k-', lw=1.2)
            for x in (x0, x0 + 100): ax.plot([x, x], [9, 15], 'k-', lw=1.2)
            ax.text(x0 + 105, 12, '<- measure: should be 100.0 mm', va='center', fontsize=8)
            ax.text(PAGE_W / 2, PAGE_H - 22 + 12, f'PS4 measuring mat - PAGE {page + 1} of 2   (print at 100%, actual size)',
                    ha='center', fontsize=10, weight='bold')
            pdf.savefig(fig); plt.close(fig)
    return path
