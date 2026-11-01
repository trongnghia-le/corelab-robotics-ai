"""CoreLab Frames lab — original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. This file grants no CoreLab evidence or verified I.
Edit the six functions below, derive the equations, then run your own file:
  Windows: py -3 L01-SE2.v1.py
  macOS/Linux: python3 L01-SE2.v1.py   (or python)
Python standard library only. Run only code you trust; this is not a sandbox.

Conventions: column vectors; T_AB maps B coordinates into A; 3x3 homogeneous
matrices, bottom row [0,0,1]; metres, radians, counter-clockwise positive.
Return nested lists for matrices, list/tuple for vectors, exact bool for rotation.
Real values exclude bool/NaN/infinity. Bad inputs raise ValueError; no mutation.
make_transform: |theta| <= 2*pi, |x|,|y| <= 100. Valid composed transforms may
exceed 100 m. No silent repair of reflections, shear or a bad bottom row.
is_rotation: exactly finite 2x2, tol finite and 0 < tol <= .01; test both R^T R
and determinant +1. Other operations accept valid finite SE(2) transforms.
Validate computed finiteness. Fixture tolerance is 1e-9 on these bounded cases,
not a promise of arbitrary-scale floating-point accuracy.

Pause before tests: which labels cancel in T_AB T_BC? Why does translation
affect a point but not a direction? Why is inverse translation -R^T p?
Add your own noncommuting, inverse round-trip and boundary tests. Explain each
failure before changing code. A green self-check remains practice, not mastery.
"""
import math


def make_transform(theta, x, y):
    raise NotImplementedError("Construct the homogeneous transform")


def compose(T_ab, T_bc):
    raise NotImplementedError("Compose without mutating either input")


def invert(T):
    raise NotImplementedError("Derive the inverse translation")


def apply_point(T, p):
    raise NotImplementedError("Map a length-2 point")


def apply_direction(T, v):
    raise NotImplementedError("Map a length-2 direction")


def is_rotation(R, tol=1e-9):
    raise NotImplementedError("Test a proper 2D rotation")


def self_check():
    """Author-side fixed fixtures, not a release grader or security boundary."""
    failures = []

    def check(name, fn):
        try:
            assert fn() is True
        except Exception as error:
            failures.append(name + ": " + type(error).__name__)

    def num(v):
        return type(v) in (int, float) and math.isfinite(v)

    def matrix(got, expected):
        return (isinstance(got, (list, tuple)) and len(got) == 3
                and all(isinstance(row, (list, tuple)) and len(row) == 3
                        and all(num(x) for x in row) for row in got)
                and all(abs(got[i][j] - expected[i][j]) <= 1e-9
                        for i in range(3) for j in range(3)))

    def vector(got, expected):
        return (isinstance(got, (list, tuple)) and len(got) == 2
                and all(num(x) for x in got)
                and all(abs(x-y) <= 1e-9 for x, y in zip(got, expected)))

    def rejects(fn, *args):
        try:
            fn(*args)
        except ValueError:
            return True
        return False

    A = [[0., -1., 1.], [1., 0., 2.], [0., 0., 1.]]
    B = [[1., 0., 3.], [0., 1., -1.], [0., 0., 1.]]
    H = [[0., -1., 2.], [1., 0., 5.], [0., 0., 1.]]
    identity = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
    check("construct", lambda: matrix(make_transform(math.pi/2, 1., 2.), A))
    check("noncommuting composition", lambda: matrix(compose(A, B), H))
    check("mapped point", lambda: vector(apply_point(H, [1., 2.]), [0., 6.]))
    check("direction excludes translation", lambda: vector(apply_direction(A, [2., 0.]), [0., 2.]))
    check("inverse point", lambda: vector(apply_point(invert(A), [1., 4.]), [2., 0.]))
    check("inverse round trip", lambda: matrix(compose(invert(H), H), identity))
    check("proper rotation", lambda: is_rotation([[0., -1.], [1., 0.]]) is True)
    for name, R in [("reflection", [[1., 0.], [0., -1.]]),
                    ("shear", [[1., 1.], [0., 1.]]),
                    ("scaled det+1", [[2., 0.], [0., .5]])]:
        check(name, lambda R=R: is_rotation(R) is False)
    for name, fn, args in [
        ("bad bottom", invert, ([[1., 0., 0.], [0., 1., 0.], [0., 0., 2.]],)),
        ("4x4 prefix", invert, ([r + [0.] for r in A] + [[0.]*4],)),
        ("bool matrix", invert, ([[True, 0., 0.], [0., 1., 0.], [0., 0., 1.]],)),
        ("nonfinite make", make_transform, (float('nan'), 0., 0.)),
        ("bool make", make_transform, (True, 0., 0.)),
        ("angle domain", make_transform, (7., 0., 0.)),
        ("length domain", make_transform, (0., 101., 0.)),
        ("point shape", apply_point, (A, [1.])),
        ("direction finiteness", apply_direction, (A, [float('inf'), 0.])),
        ("rotation shape", is_rotation, ([[1., 0., 0.]],)),
        ("bad tolerance", is_rotation, ([[1., 0.], [0., 1.]], 0.)),
    ]:
        check(name, lambda fn=fn, args=args: rejects(fn, *args))

    def nonmutation():
        a, b = [r[:] for r in A], [r[:] for r in B]
        compose(a, b)
        invert(a)
        apply_point(a, [1., 2.])
        apply_direction(a, [2., 0.])
        return a == A and b == B
    check("input nonmutation", nonmutation)
    check("boundary construction", lambda: matrix(make_transform(2*math.pi, 100., -100.),
          [[1., 0., 100.], [0., 1., -100.], [0., 0., 1.]]))
    check("composition translation may exceed input bound", lambda: matrix(
        compose(make_transform(0., 100., 100.), make_transform(0., 100., 100.)),
        [[1., 0., 200.], [0., 1., 200.], [0., 0., 1.]]))
    return failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual Frames self-check — practice only, no signed evidence")
    print("Failures:", failures if failures else "none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
