"""ps4fab - measure console parts from phone photos and build printable replacement parts."""
import argparse, json, os, sys


def main(argv=None):
    ap = argparse.ArgumentParser(prog='ps4fab', description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('mat', help='write the 2-page printable measuring mat (print at 100%%)'); p.add_argument('-o', default='measuring_mat.pdf')
    p = sub.add_parser('guide', help='write the measuring guide with diagrams'); p.add_argument('-o', default='.')
    p = sub.add_parser('measure', help='camera pose + true-scale top views from a photo of the mat')
    p.add_argument('photo'); p.add_argument('--check', type=float, default=100.0, help='caliper reading of the printed 100 mm bar')
    p.add_argument('--h', type=float, nargs='*', default=[0.0], help='heights above the table to render (mm)')
    p.add_argument('--ppmm', type=float, default=8, help='output pixels per mm')
    p = sub.add_parser('view', help="true-scale view lined up with a part (after 'measure')")
    p.add_argument('photo'); p.add_argument('--origin', type=float, nargs=2, required=True, metavar=('X', 'Y'), help='part corner, mat mm')
    p.add_argument('--angle', type=float, default=0.0); p.add_argument('--size', type=float, nargs=2, required=True, metavar=('L', 'W'))
    p.add_argument('--h', type=float, default=0.0); p.add_argument('--ppmm', type=float, default=8); p.add_argument('--check', type=float, default=100.0)
    p = sub.add_parser('build', help='build printable STLs'); p.add_argument('parts', nargs='*', help='part names (default: all)')
    p.add_argument('-o', default='out')
    sub.add_parser('list', help='list parts and what they were measured from')
    p = sub.add_parser('serve', help='run the Teardown Tracer app (open the printed address in a browser)')
    p.add_argument('--data', default='data', help='folder with db/ (default: ./data)'); p.add_argument('--port', type=int, default=8780)
    p.add_argument('--host', default='127.0.0.1', help='0.0.0.0 = let others on your network in (no login - home network only)')
    p = sub.add_parser('import', help='load an export {collection: {doc: data}} into the database')
    p.add_argument('file'); p.add_argument('--data', default='data')
    a = ap.parse_args(argv)

    if a.cmd == 'mat':
        from .mat import write_mat; print(write_mat(a.o))
    elif a.cmd == 'guide':
        from .guide import write_guide; os.makedirs(a.o, exist_ok=True); print(write_guide(a.o))
    elif a.cmd in ('measure', 'view'):
        import cv2
        from .measure import solve, ortho, ortho_frame
        img, pose = solve(a.photo, a.check)
        base = os.path.splitext(a.photo)[0]
        print(f"pages {pose['pages']}, {pose['corners']} corners, reprojection {pose['reproj_px']:.2f} px")
        if a.cmd == 'measure':
            for h in a.h:
                o, meta = ortho(img, pose, h, a.ppmm); cv2.imwrite(f'{base}.ortho_h{h:g}.png', o); pose[f'ortho_h{h:g}'] = meta
            with open(f'{base}.mat.json', 'w') as f: json.dump(pose, f, indent=1)
            print(f'wrote {base}.mat.json and {len(a.h)} top view(s)')
        else:
            out = f'{base}.view_h{a.h:g}.png'
            cv2.imwrite(out, ortho_frame(img, pose, a.h, a.origin, a.angle, a.size, a.ppmm)); print(f'wrote {out}')
    elif a.cmd == 'build':
        from .parts import PARTS
        names = a.parts or list(PARTS)
        bad = [n for n in names if n not in PARTS]
        if bad: sys.exit(f'unknown part(s): {bad}; try: ps4fab list')
        for n in names: PARTS[n](a.o)
    elif a.cmd == 'serve':
        from .serve import serve
        srv = serve(a.data, a.host, a.port)
        print(f'Teardown Tracer running: http://{"localhost" if a.host == "127.0.0.1" else a.host}:{a.port}/  (data: {os.path.abspath(a.data)}, Ctrl+C stops)')
        try: srv.serve_forever()
        except KeyboardInterrupt: pass
    elif a.cmd == 'import':
        from .serve import Store
        st, n = Store(a.data), 0
        with open(a.file) as f: exp = json.load(f)
        for col, docs in exp.items():
            for doc, data in docs.items(): st.write(col, doc, data); n += 1
        print(f'imported {n} documents into {os.path.abspath(a.data)}/db')
    elif a.cmd == 'list':
        from .parts import PARTS
        import inspect
        for n, f in PARTS.items(): print(f'{n}\n  ' + inspect.cleandoc(f.__doc__ or '').replace('\n', '\n  ') + '\n')


if __name__ == '__main__':
    main()
