"""CoreLab Frames lab — original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. This file grants no CoreLab evidence or verified I.
Edit the six functions below, derive the equations, then run your own file:
  Windows: py -3 L01-SE2.v1.py
  macOS/Linux: python3 L01-SE2.v1.py   (or python)
Python standard library only. Run only code you trust; this is not a sandbox.

Conventions: column vectors; T_AB maps B coordinates into A; 3x3 homogeneous
matrices, bottom row [0,0,1]; metres, radians, counter-clockwise positive.
Return nested lists/tuples for matrices, list/tuple for vectors, exact bool
(True/False) from is_rotation. Real values are int or float, never bool, NaN
or infinity. Bad inputs raise ValueError; never mutate any argument.
make_transform: real theta, x, y with |theta| <= 2*pi and |x|,|y| <= 100.
Valid SE(2) input to compose, invert, apply_point and apply_direction: a 3x3
list/tuple of real entries, bottom row [0,0,1] (exact, or within 1e-9) and a
rotation block for which is_rotation(block) is True with the default tol.
Reject anything else (reflections, shear, scaled blocks, a bad bottom row,
other shapes) with ValueError; no silent repair. Points and directions are
length-2 lists/tuples of real values. Composed transforms and mapped points
may exceed 100 m, but if compose or apply_point (which add translations)
overflows to inf/NaN, raise ValueError instead of returning it.
is_rotation(R, tol): R is a 2x2 list/tuple of real values and tol is real with
0 < tol <= .01, otherwise ValueError. Return True when R^T R = I and
det(R) = +1 both hold to within tol, else False; honour the tol argument.
Fixture tolerance is 1e-9 on these bounded cases, not a promise of
arbitrary-scale floating-point accuracy. Run with or without python -O.

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


# ---- Self-check below. Attempt the functions above before reading on. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def self_check():
    """Author-side fixed fixtures, not a release grader or security boundary.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []

    def check(name, fn):
        try:
            if fn() is not True:
                raise _Mismatch("wrong result")
        except _Mismatch as error:
            failures.append(name + ": " + str(error))
        except Exception as error:
            failures.append(name + ": your code raised " + type(error).__name__)

    def num(v):
        return type(v) in (int, float) and math.isfinite(v)

    def matrix(got, expected):
        if not (isinstance(got, (list, tuple)) and len(got) == 3
                and all(isinstance(row, (list, tuple)) and len(row) == 3
                        and all(num(x) for x in row) for row in got)):
            raise _Mismatch("result must be a 3x3 list/tuple of finite int/float")
        for i in range(3):
            for j in range(3):
                if not abs(got[i][j] - expected[i][j]) <= 1e-9:
                    raise _Mismatch("entry [" + str(i) + "][" + str(j) + "] is wrong")
        return True

    def vector(got, expected):
        if not (isinstance(got, (list, tuple)) and len(got) == 2
                and all(num(x) for x in got)):
            raise _Mismatch("result must be a length-2 list/tuple of finite int/float")
        for i in range(2):
            if not abs(got[i] - expected[i]) <= 1e-9:
                raise _Mismatch("component " + str(i) + " is wrong")
        return True

    def exact_bool(got, expected):
        if type(got) is not bool:
            raise _Mismatch("is_rotation must return exactly True or False")
        if got is not expected:
            raise _Mismatch("returned " + str(got))
        return True

    def rejects(fn, *args):
        try:
            fn(*args)
        except ValueError:
            return True
        except Exception as error:
            raise _Mismatch("raised " + type(error).__name__ + " instead of ValueError")
        raise _Mismatch("returned a result instead of raising ValueError")

    A = [[0., -1., 1.], [1., 0., 2.], [0., 0., 1.]]
    B = [[1., 0., 3.], [0., 1., -1.], [0., 0., 1.]]
    H = [[0., -1., 2.], [1., 0., 5.], [0., 0., 1.]]
    identity = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
    check("construct", lambda: matrix(make_transform(math.pi/2, 1., 2.), A))
    check("integer construction", lambda: matrix(make_transform(0, 1, 2),
          [[1., 0., 1.], [0., 1., 2.], [0., 0., 1.]]))
    check("noncommuting composition", lambda: matrix(compose(A, B), H))
    check("integer-entry composition", lambda: matrix(
        compose(A, [[1, 0, 3], [0, 1, -1], [0, 0, 1]]), H))
    check("mapped point", lambda: vector(apply_point(H, [1., 2.]), [0., 6.]))
    check("tuple point", lambda: vector(apply_point(H, (1., 2.)), [0., 6.]))
    check("direction excludes translation", lambda: vector(apply_direction(A, [2., 0.]), [0., 2.]))
    check("inverse point", lambda: vector(apply_point(invert(A), [1., 4.]), [2., 0.]))
    check("inverse round trip", lambda: matrix(compose(invert(H), H), identity))
    check("near-rotation within default tol", lambda: matrix(
        invert([[1., 1e-12, 0.], [0., 1., 0.], [0., 0., 1.]]), identity))
    check("proper rotation", lambda: exact_bool(is_rotation([[0., -1.], [1., 0.]]), True))
    for name, R, args, expected in [
        ("reflection", [[1., 0.], [0., -1.]], (), False),
        ("shear", [[1., 1.], [0., 1.]], (), False),
        ("scaled det+1", [[2., 0.], [0., .5]], (), False),
        ("off by 1e-6 with default tol", [[1., 1e-6], [0., 1.]], (), False),
        ("off by 1e-6 with tol=1e-5", [[1., 1e-6], [0., 1.]], (1e-5,), True),
        ("largest tolerance .01", [[1., .004], [0., 1.]], (.01,), True),
        ("uniform scale", [[2., 0.], [0., 2.]], (), False),
        ("scaled rotation", [[0., -.5], [.5, 0.]], (), False),
        ("integer rotation entries", [[0, -1], [1, 0]], (), True),
    ]:
        check("is_rotation " + name,
              lambda R=R, args=args, expected=expected: exact_bool(is_rotation(R, *args), expected))
    big = [[1., 0., 1e308], [0., 1., 0.], [0., 0., 1.]]
    for name, fn, args in [
        ("invert bad bottom", invert, ([[1., 0., 0.], [0., 1., 0.], [0., 0., 2.]],)),
        ("invert bottom off by 1e-6", invert, ([[1., 0., 0.], [0., 1., 0.], [0., 1e-6, 1.]],)),
        ("invert 4x4 prefix", invert, ([r + [0.] for r in A] + [[0.]*4],)),
        ("invert bool entry", invert, ([[True, 0., 0.], [0., 1., 0.], [0., 0., 1.]],)),
        ("invert reflection block", invert, ([[1., 0., 0.], [0., -1., 0.], [0., 0., 1.]],)),
        ("invert NaN entry", invert, ([[1., 0., float('nan')], [0., 1., 0.], [0., 0., 1.]],)),
        ("compose shear block", compose, (A, [[1., 1., 0.], [0., 1., 0.], [0., 0., 1.]])),
        ("compose block off by 1e-6", compose, ([[1., 1e-6, 0.], [0., 1., 0.], [0., 0., 1.]], B)),
        ("compose bad bottom (first)", compose, ([[1., 0., 0.], [0., 1., 0.], [1., 0., 1.]], B)),
        ("compose non-matrix", compose, (A, "B")),
        ("compose overflow", compose, (big, big)),
        ("apply_point bad bottom", apply_point, ([[1., 0., 0.], [0., 1., 0.], [0., 0., 2.]], [1., 2.])),
        ("apply_point reflection block", apply_point, ([[-1., 0., 0.], [0., 1., 0.], [0., 0., 1.]], [1., 2.])),
        ("apply_point overflow", apply_point, (big, [1e308, 0.])),
        ("point shape", apply_point, (A, [1.])),
        ("point bool", apply_point, (A, [True, 0.])),
        ("apply_direction 4x4", apply_direction, ([r + [0.] for r in A] + [[0., 0., 0., 1.]], [2., 0.])),
        ("invert uniform-scale block", invert, ([[2., 0., 0.], [0., 2., 0.], [0., 0., 1.]],)),
        ("compose 3x4 second", compose, (A, [r + [0.] for r in B])),
        ("apply_point 3x4", apply_point, ([r + [0.] for r in A], [1., 2.])),
        ("apply_direction scaled block", apply_direction, ([[2., 0., 0.], [0., .5, 0.], [0., 0., 1.]], [2., 0.])),
        ("direction finiteness", apply_direction, (A, [float('inf'), 0.])),
        ("nonfinite make", make_transform, (float('nan'), 0., 0.)),
        ("bool make", make_transform, (True, 0., 0.)),
        ("angle domain", make_transform, (7., 0., 0.)),
        ("negative angle domain", make_transform, (-7., 0., 0.)),
        ("x domain", make_transform, (0., 101., 0.)),
        ("y domain", make_transform, (0., 0., -101.)),
        ("rotation shape", is_rotation, ([[1., 0., 0.]],)),
        ("rotation 2x3", is_rotation, ([[1., 0., 0.], [0., 1., 0.]],)),
        ("nonfinite make x", make_transform, (0., float('nan'), 0.)),
        ("nonfinite make y", make_transform, (0., 0., float('inf'))),
        ("rotation NaN entry", is_rotation, ([[float('nan'), 0.], [0., 1.]],)),
        ("rotation bool entry", is_rotation, ([[True, 0.], [0., 1.]],)),
        ("zero tolerance", is_rotation, ([[1., 0.], [0., 1.]], 0.)),
        ("negative tolerance", is_rotation, ([[1., 0.], [0., 1.]], -1.)),
        ("tolerance above .01", is_rotation, ([[1., 0.], [0., 1.]], .02)),
        ("bool tolerance", is_rotation, ([[1., 0.], [0., 1.]], True)),
        ("NaN tolerance", is_rotation, ([[1., 0.], [0., 1.]], float('nan'))),
    ]:
        check(name, lambda fn=fn, args=args: rejects(fn, *args))

    def nonmutation():
        a, b, p, v = [r[:] for r in A], [r[:] for r in B], [1., 2.], [2., 0.]
        R = [[0., -1.], [1., 0.]]
        compose(a, b)
        invert(a)
        apply_point(a, p)
        apply_direction(a, v)
        is_rotation(R)
        if not (a == A and b == B and p == [1., 2.] and v == [2., 0.]
                and R == [[0., -1.], [1., 0.]]):
            raise _Mismatch("an argument was modified")
        return True
    check("input nonmutation", nonmutation)
    check("boundary construction", lambda: matrix(make_transform(2*math.pi, 100., -100.),
          [[1., 0., 100.], [0., 1., -100.], [0., 0., 1.]]))
    check("negative boundary construction", lambda: matrix(make_transform(-2*math.pi, -100., 100.),
          [[1., 0., -100.], [0., 1., 100.], [0., 0., 1.]]))
    check("composition translation may exceed input bound", lambda: matrix(
        compose(make_transform(0., 100., 100.), make_transform(0., 100., 100.)),
        [[1., 0., 200.], [0., 1., 200.], [0., 0., 1.]]))
    return failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual Frames self-check - practice only, no signed evidence")
    print("Failures:", failures if failures else "none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
