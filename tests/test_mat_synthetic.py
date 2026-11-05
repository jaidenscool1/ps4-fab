# Render a fake phone photo of both mat pages + a 22 mm tall box with a known camera,
# then check the measuring code recovers the box's top corners in mm.
import numpy as np, cv2, os
from ps4fab.mat import board, COLS, ROWS, SQ
from ps4fab.measure import solve, to_mm

W, H, F = 4032, 3024, 3000.0
K = np.array([[F, 0, W / 2], [0, F, H / 2], [0, 0, 1]])
PPS = 40  # board render px per mm
def place(a_deg, tx, ty):  # page board frame (mm) -> table (mm); board frame has y down, so flip y
    a = np.radians(a_deg); return np.array([[np.cos(a), np.sin(a), tx], [np.sin(a), -np.cos(a), ty], [0, 0, 1]])
PAGES = {0: place(0, 0, 230), 1: place(3, 420, 236)}     # page 2 is 3 deg off and not aligned: tape-free

def look_at(eye, target):
    z = target - eye; z /= np.linalg.norm(z); x = np.cross(z, [0, 1, 0]); x /= np.linalg.norm(x); y = np.cross(z, x)
    R = np.vstack([x, y, z]); return R, -R @ eye
R, t = look_at(np.array([330.0, 60.0, 700.0]), np.array([300.0, 120.0, 0.0]))   # tilted ~10 deg
def proj(P):  # table xyz (n,3) -> image px
    c = (R @ P.T).T + t; uv = (K @ c.T).T; return uv[:, :2] / uv[:, 2:]

def test_mat_recovers_box_to_tenth_mm(tmp_path):
    img = np.full((H, W, 3), 90, np.uint8)                   # dark table
    for p, M in PAGES.items():
        bimg = board(p).generateImage((int(COLS * SQ * PPS), int(ROWS * SQ * PPS)), marginSize=0, borderBits=1)
        pad = int(15 * PPS); bimg = cv2.copyMakeBorder(bimg, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
        src = np.array([[0, 0], [bimg.shape[1], 0], [bimg.shape[1], bimg.shape[0]], [0, bimg.shape[0]]], float)
        mm = (src - pad) / PPS                                  # board frame mm (y down)
        tab = (M @ np.vstack([mm.T, np.ones(4)])).T
        dst = proj(np.c_[tab[:, :2], np.zeros(4)])
        Hm = cv2.getPerspectiveTransform(src.astype(np.float32), dst.astype(np.float32))
        warped = cv2.warpPerspective(cv2.cvtColor(bimg, cv2.COLOR_GRAY2BGR), Hm, (W, H), flags=cv2.INTER_AREA)
        mask = cv2.warpPerspective(np.full(bimg.shape, 255, np.uint8), Hm, (W, H)) > 0
        img[mask] = warped[mask]
    # a 160 x 280 mm box, 22 mm tall, between the pages; its top face drawn in light grey
    box = np.array([[230, 60], [390, 60], [390, 340], [230, 340]], float)
    top = proj(np.c_[box, np.full(4, 22.0)])
    cv2.fillPoly(img, [top.astype(np.int32)], (200, 200, 200))
    img = cv2.GaussianBlur(img, (3, 3), 0)

    path = os.path.join(str(tmp_path), 'fake.jpg'); cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    _, pose = solve(path, focal=F)
    print(f"pages {pose['pages']}, corners {pose['corners']}, reproj {pose['reproj_px']:.2f} px, f {pose['K'][0][0]:.0f} (true {F:.0f})")
    got = to_mm(pose, top, 22.0)
    # truth in page-1 board frame
    Minv = np.linalg.inv(PAGES[0]); truth = (Minv @ np.vstack([box.T, np.ones(4)])).T[:, :2]
    err = np.linalg.norm(got - truth, axis=1)
    sides = lambda q: [np.linalg.norm(q[i] - q[(i + 1) % 4]) for i in range(4)]
    print('recovered box top sides mm:', np.round(sides(got), 2), ' true:', np.round(sides(truth), 2))
    print('corner errors mm:', np.round(err, 2))
    naive = to_mm(pose, top, 0.0)
    print('same corners if height ignored (plain photo scaling), sides:', np.round(sides(naive), 1))
    assert pose['pages'] == [0, 1] and err.max() < 0.6, 'mat measurement not accurate enough'
