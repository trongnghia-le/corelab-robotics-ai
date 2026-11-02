"""CoreLab Planar FK lab — original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No CoreLab evidence, verified I or hardware permission.
Implement planar_2r, then run your own edited file with Python 3:
  Windows: py -3 L02-planar.v1.py
  macOS/Linux: python3 L02-planar.v1.py   (or python)
Standard library only. Run only code you trust. This is not isolated execution.

Conventions: two revolute joints; q1 and q2 RELATIVE angles in radians,
counter-clockwise positive; link lengths in metres, 0 < l1 <= 10 and
0 < l2 <= 10; |q1|,|q2| <= 2*pi. All four inputs are finite int/float (never
bool, NaN or infinity); anything else raises ValueError.
Return exactly (x,y,theta) as tuple/list of finite int/float (non-bool) values.
Theta is the orientation of link 2, compared modulo 2*pi, NOT just q2.
Position tolerance 1e-6 m, orientation tolerance 1e-6 rad on bounded fixtures.
Failures name the fixture and whether position or orientation was wrong.

Derive the endpoint from two vectors before coding. Alternatively compose
homogeneous transforms. Try unequal links and nonzero joint angles. Predict
stretched, folded and wrapped poses, then add your own tests. Explain why two
poses can have the same endpoint but different tool orientations.
Reading a solution or passing these fixed fixtures does not establish mastery.
"""
import math


def planar_2r(q1, q2, l1, l2):
    raise NotImplementedError("Derive endpoint and tool orientation")


# ---- SPOILER BELOW: the self-check contains an expanded reference formula.
# ---- Derive and implement planar_2r yourself before reading further.


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _expected_pose(a, b, c, d):
    """Independent scalar expansion (angle-sum identities), not a call to fk."""
    return (c*math.cos(a) + d*(math.cos(a)*math.cos(b)-math.sin(a)*math.sin(b)),
            c*math.sin(a) + d*(math.sin(a)*math.cos(b)+math.cos(a)*math.sin(b)), a+b)


def self_check():
    """Independent scalar expansion plus hand anchors; no result is imported.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []
    fixtures = [
        (math.pi/2, -math.pi/2, 2., 1., (1., 2., 0.)),
        (0., 0., 2., 1., (3., 0., 0.)),
        (0., math.pi, 2., 1., (1., 0., math.pi)),
        (math.pi, math.pi, 2., 1., (-1., 0., 0.)),
        (.3, .4, 2., 1., None), (-1.2, 2.2, .7, 1.3, None),
        (2.5, -.9, 1.1, .2, None), (-3., 3., .5, .5, None),
        (1e-3, 1e-3, 1., 2., None), (3.1, 3.1, 1., 2., None),
        (2*math.pi, -2*math.pi, 10., 10., (20., 0., 0.)),
        (0., 0., 1e-5, 1e-5, (2e-5, 0., 0.)),
        (0, 0, 2, 1, (3., 0., 0.)),
    ]
    for i, (a, b, c, d, expected) in enumerate(fixtures):
        if expected is None:
            expected = _expected_pose(a, b, c, d)
        try:
            got = planar_2r(a, b, c, d)
            if not (isinstance(got, (list, tuple)) and len(got) == 3
                    and all(type(x) in (int, float) and math.isfinite(x) for x in got)):
                raise _Mismatch("output must be a length-3 list/tuple of finite int/float")
            if not (abs(got[0]-expected[0]) <= 1e-6 and abs(got[1]-expected[1]) <= 1e-6):
                raise _Mismatch("position (x, y) is wrong")
            delta = got[2]-expected[2]
            if not abs(math.atan2(math.sin(delta), math.cos(delta))) <= 1e-6:
                raise _Mismatch("orientation theta is wrong")
        except _Mismatch as error:
            failures.append("pose " + str(i) + ": " + str(error))
        except Exception as error:
            failures.append("pose " + str(i) + ": your code raised " + type(error).__name__)
    nan, inf = float('nan'), float('inf')
    for args in [(0., 0., 0., 1.), (0., 0., -1., 1.), (0., 0., 1., 0.), (0., 0., 1., -1.),
                 (nan, 0., 1., 1.), (0., inf, 1., 1.), (0., 0., nan, 1.), (0., 0., 1., nan),
                 (True, 0., 1., 1.), (0., True, 1., 1.), (0., 0., True, 1.), (0., 0., 1., True),
                 (7., 0., 1., 1.), (-7., 0., 1., 1.), (0., 7., 1., 1.), (0., -7., 1., 1.),
                 (0., 0., 10.1, 1.), (0., 0., 1., 10.1), ("0", 0., 1., 1.)]:
        try:
            planar_2r(*args)
        except ValueError:
            continue
        except Exception as error:
            failures.append("invalid input " + repr(args) + ": raised "
                            + type(error).__name__ + " instead of ValueError")
            continue
        failures.append("invalid input not rejected with ValueError: " + repr(args))
    return failures


if __name__ == "__main__":
    failures = self_check()
    print("CoreLab manual FK self-check - practice only, no signed evidence")
    print("Failures:", failures if failures else "none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
