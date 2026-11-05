# Measure from one phone photo of the printed mat (see mat.py): camera pose from the markers, then any pixel -> mm
# on a plane at a known height above the table. `ps4fab measure` / `ps4fab view` wrap this.
# check: what the caliper read on the printed 100 mm bar (corrects printer scaling).
import numpy as np, cv2
from PIL import Image, ImageOps
from .mat import board

try:
    from pillow_heif import register_heif_opener; register_heif_opener()   # iPhone .HEIC photos
except ImportError:
    pass

def load(path):
    """BGR image (EXIF rotation applied) + 35 mm-equivalent focal length from EXIF (None if missing)."""
    im = Image.open(path); f35 = None
    try: f35 = float(im.getexif().get_ifd(0x8769).get(0xA405) or 0) or None
    except Exception: pass
    im = ImageOps.exif_transpose(im).convert('RGB')
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR), f35

def detect(gray, page):
    b = board(page)
    det = cv2.aruco.CharucoDetector(b)
    cc, ci, mc, mi = det.detectBoard(gray)
    if ci is None or len(ci) < 6: return None, None
    obj = b.getChessboardCorners()[ci.ravel()]          # (n,3) mm in the page's board frame
    return obj.astype(np.float64), cc.reshape(-1, 2).astype(np.float64)

def focal_px(f35, w, h):
    # 35 mm-equivalent focal length -> pixels; default = typical phone main camera (26 mm equiv)
    return (f35 or 26.0) / 43.27 * np.hypot(w, h)          # 43.27 mm = 35 mm-frame diagonal

def solve(path, check=100.0, focal=None, calib=False):
    img, f35 = load(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); H, W = gray.shape
    s = 100.0 / check                                   # printer scale correction (mm on paper per nominal mm)
    pages = {p: detect(gray, p) for p in (0, 1)}
    pages = {p: (o * s, i) for p, (o, i) in pages.items() if o is not None}
    if not pages: raise ValueError(f'{path}: no mat page found - are both printed pages in the photo?')
    f = focal or focal_px(f35, W, H)
    K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1]])
    ref = min(pages)
    # page-to-page placement on the table: from each page's own pose, flattened to an in-plane rigid move
    obj_all, img_all = [], []
    _, r0, t0 = cv2.solvePnP(*pages[ref], K, None, flags=cv2.SOLVEPNP_IPPE)
    R0 = cv2.Rodrigues(r0)[0]
    for p, (o, i) in pages.items():
        if p != ref:
            _, r, t = cv2.solvePnP(o, i, K, None, flags=cv2.SOLVEPNP_IPPE)
            R = cv2.Rodrigues(r)[0]
            M = R0.T @ R; d = R0.T @ (t - t0)               # page p frame -> ref frame
            a = np.arctan2(M[1, 0], M[0, 0])
            M2 = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
            o = (M2 @ o.T).T + np.array([d[0, 0], d[1, 0], 0])
        obj_all.append(o); img_all.append(i)
    obj_all, img_all = np.vstack(obj_all), np.vstack(img_all)
    # refine focal + pose on all corners (principal point fixed, no distortion: phone photos are pre-corrected)
    flags = cv2.CALIB_FIX_PRINCIPAL_POINT | cv2.CALIB_FIX_ASPECT_RATIO | cv2.CALIB_ZERO_TANGENT_DIST | \
            cv2.CALIB_FIX_K1 | cv2.CALIB_FIX_K2 | cv2.CALIB_FIX_K3 | cv2.CALIB_USE_INTRINSIC_GUESS
    # straight-down photos of a flat mat can't pin the focal length (zoom vs distance), so the EXIF value is used;
    # calibrate only when asked (several tilted photos)
    if calib and len(pages) > 1:
        err, K, _, rv, tv = cv2.calibrateCamera([obj_all.astype(np.float32)], [img_all.astype(np.float32)], (W, H), K.copy(), None, flags=flags)
        r, t = rv[0], tv[0]
    else:
        _, r, t = cv2.solvePnP(obj_all, img_all, K, None)
    proj = cv2.projectPoints(obj_all, r, t, K, None)[0].reshape(-1, 2)
    rms = float(np.sqrt(((proj - img_all) ** 2).sum(1).mean()))
    return img, dict(K=K.tolist(), rvec=r.ravel().tolist(), tvec=t.ravel().tolist(), pages=sorted(pages),
                     corners=len(obj_all), reproj_px=rms, check=check)

def to_mm(pose, uv, h):
    """image pixel(s) -> (x, y) mm on the plane at height h above the table (mat frame of page 1)."""
    K = np.array(pose['K']); R = cv2.Rodrigues(np.array(pose['rvec']))[0]; t = np.array(pose['tvec']).reshape(3, 1)
    uv = np.atleast_2d(uv).astype(float)
    ray = np.linalg.inv(K) @ np.vstack([uv.T, np.ones(len(uv))])     # camera frame
    Rt = R.T; c = -Rt @ t; d = Rt @ ray                                 # camera centre + rays in mat frame
    # mat z axis: OpenCV board frame has z pointing away from the camera side? use the side the camera is on
    up = 1.0 if c[2, 0] > 0 else -1.0
    lam = (up * h - c[2, 0]) / d[2]
    p = c + d * lam
    return p[:2].T

def ortho(img, pose, h, ppmm=8, pad=20):
    K = np.array(pose['K']); R = cv2.Rodrigues(np.array(pose['rvec']))[0]; t = np.array(pose['tvec']).reshape(3, 1)
    Hh, Ww = img.shape[:2]
    corners = to_mm(pose, [[0, 0], [Ww, 0], [0, Hh], [Ww, Hh]], h)
    lo, hi = corners.min(0) - pad, corners.max(0) + pad
    lo = np.maximum(lo, -600); hi = np.minimum(hi, 900)
    up = 1.0 if (-R.T @ t)[2, 0] > 0 else -1.0
    # homography: ortho pixel -> mm (x,y,h) -> image
    A = np.array([[1 / ppmm, 0, lo[0]], [0, 1 / ppmm, lo[1]], [0, 0, 1]])    # ortho px -> mm (mat frame is y-down, so not mirrored)
    P = K @ np.hstack([R, t])
    Hm = P @ np.array([[1, 0, 0], [0, 1, 0], [0, 0, up * h], [0, 0, 1]])   # (x, y, 1) -> image, at height h
    Ho = Hm @ A
    size = (int((hi[0] - lo[0]) * ppmm), int((hi[1] - lo[1]) * ppmm))
    out = cv2.warpPerspective(img, Ho, size, flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR)
    for x in np.arange(np.ceil(lo[0] / 10) * 10, hi[0], 10):
        u = int((x - lo[0]) * ppmm); cv2.line(out, (u, 0), (u, size[1]), (0, 200, 255) if x % 50 else (0, 0, 255), 1)
    for y in np.arange(np.ceil(lo[1] / 10) * 10, hi[1], 10):
        v = int((y - lo[1]) * ppmm); cv2.line(out, (0, v), (size[0], v), (0, 200, 255) if y % 50 else (0, 0, 255), 1)
    for x in np.arange(np.ceil(lo[0] / 50) * 50, hi[0], 50):
        cv2.putText(out, f'{int(x)}', (int((x - lo[0]) * ppmm) + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
    for y in np.arange(np.ceil(lo[1] / 50) * 50, hi[1], 50):
        cv2.putText(out, f'{int(y)}', (2, int((y - lo[1]) * ppmm) - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
    return out, dict(lo=lo.tolist(), hi=hi.tolist(), ppmm=ppmm)

def ortho_frame(img, pose, h, origin, angle_deg, size_mm, ppmm=10, margin=12):
    """True-scale view in the PART's own frame: x along angle_deg from origin (mat mm), y 90 deg to it.
    Grid every 5 mm (labels every 10). Returns image; part mm = (u/ppmm - margin, v/ppmm - margin)."""
    K = np.array(pose['K']); R = cv2.Rodrigues(np.array(pose['rvec']))[0]; t = np.array(pose['tvec']).reshape(3, 1)
    up = 1.0 if (-R.T @ t)[2, 0] > 0 else -1.0
    a = np.radians(angle_deg); ca, sa = np.cos(a), np.sin(a)
    # out px -> part mm -> mat mm
    S = np.array([[1 / ppmm, 0, -margin], [0, 1 / ppmm, -margin], [0, 0, 1]])
    Rf = np.array([[ca, -sa, origin[0]], [sa, ca, origin[1]], [0, 0, 1]])
    Hm = K @ np.hstack([R, t]) @ np.array([[1, 0, 0], [0, 1, 0], [0, 0, up * h], [0, 0, 1]])
    size = (int((size_mm[0] + 2 * margin) * ppmm), int((size_mm[1] + 2 * margin) * ppmm))
    out = cv2.warpPerspective(img, Hm @ Rf @ S, size, flags=cv2.WARP_INVERSE_MAP | cv2.INTER_CUBIC)
    for k in range(-margin // 5 * 5, int(size_mm[0]) + margin, 5):
        u = int((k + margin) * ppmm); cv2.line(out, (u, 0), (u, size[1]), (0, 0, 255) if k % 10 == 0 else (0, 200, 255), 1)
        if k % 10 == 0: cv2.putText(out, str(k), (u + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    for k in range(-margin // 5 * 5, int(size_mm[1]) + margin, 5):
        v = int((k + margin) * ppmm); cv2.line(out, (0, v), (size[0], v), (0, 0, 255) if k % 10 == 0 else (0, 200, 255), 1)
        if k % 10 == 0: cv2.putText(out, str(k), (2, v - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    return out
