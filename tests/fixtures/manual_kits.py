"""Author-side kit conformance tests; synthetic solutions, not independent review."""
import importlib.util
import math
from pathlib import Path


def load(name):
    file = Path(__file__).resolve().parents[2] / "content" / "labs" / name
    spec = importlib.util.spec_from_file_location("kit", file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def real(x):
    return type(x) in (int, float) and math.isfinite(x)


def rotation(R, tol=1e-9):
    if not (real(tol) and 0 < tol <= .01 and isinstance(R, (list, tuple))
            and len(R) == 2 and all(isinstance(r, (list, tuple)) and len(r) == 2
                                  and all(real(x) for x in r) for r in R)):
        raise ValueError
    a, b, c, d = R[0][0], R[0][1], R[1][0], R[1][1]
    return (abs(a*a+c*c-1) <= tol and abs(b*b+d*d-1) <= tol
            and abs(a*b+c*d) <= tol and abs(a*d-b*c-1) <= tol)


def valid(T):
    if not (isinstance(T, (list, tuple)) and len(T) == 3
            and all(isinstance(r, (list, tuple)) and len(r) == 3
                    and all(real(x) for x in r) for r in T)
            and all(abs(x-y) <= 1e-9 for x, y in zip(T[2], [0, 0, 1]))
            and rotation([T[0][:2], T[1][:2]])):
        raise ValueError


def make(t, x, y):
    if not all(real(v) for v in (t, x, y)) or abs(t) > 2*math.pi or max(abs(x), abs(y)) > 100:
        raise ValueError
    c, s = math.cos(t), math.sin(t)
    return [[c, -s, x], [s, c, y], [0., 0., 1.]]


def multiply(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def compose(A, B):
    valid(A)
    valid(B)
    return multiply(A, B)


def invert(T):
    valid(T)
    a, b, c, d = T[0][0], T[0][1], T[1][0], T[1][1]
    x, y = T[0][2], T[1][2]
    return [[a, c, -(a*x+c*y)], [b, d, -(b*x+d*y)], [0., 0., 1.]]


def vector(T, v, point):
    valid(T)
    if not (isinstance(v, (list, tuple)) and len(v) == 2 and all(real(x) for x in v)):
        raise ValueError
    return [sum(T[i][j]*v[j] for j in range(2)) + (T[i][2] if point else 0.) for i in range(2)]


def fk(a, b, c, d):
    if not (all(real(x) for x in (a, b, c, d)) and abs(a) <= 2*math.pi
            and abs(b) <= 2*math.pi and 0 < c <= 10 and 0 < d <= 10):
        raise ValueError
    return (c*math.cos(a)+d*math.cos(a+b), c*math.sin(a)+d*math.sin(a+b), a+b)


frames, planar = load("L01-SE2.v1.py"), load("L02-planar.v1.py")
assert frames.self_check(), "Unimplemented starter must fail"
assert planar.self_check(), "Unimplemented starter must fail"
refs = dict(make_transform=make, compose=compose, invert=invert,
            apply_point=lambda T, p: vector(T, p, True),
            apply_direction=lambda T, v: vector(T, v, False), is_rotation=rotation)
for name, fn in refs.items():
    setattr(frames, name, fn)
assert frames.self_check() == [], frames.self_check()
planar.planar_2r = fk
assert planar.self_check() == [], planar.self_check()


def compose_angle(A, B):
    valid(A)
    valid(B)
    t = math.atan2(A[1][0], A[0][0])+math.atan2(B[1][0], B[0][0])
    c, s = math.cos(t), math.sin(t)
    p = vector(A, [B[0][2], B[1][2]], True)
    return [[c, -s, p[0]], [s, c, p[1]], [0., 0., 1.]]


frames.compose = compose_angle
assert frames.self_check() == [], frames.self_check()
frames.compose = compose


def fk_chain(a, b, c, d):
    fk(a, b, c, d)  # declared primitive domain validation only
    M = multiply(multiply(make(a, 0., 0.), make(0., c, 0.)),
                 multiply(make(b, 0., 0.), make(0., d, 0.)))
    return (M[0][2], M[1][2], math.atan2(M[1][0], M[0][0]))


planar.planar_2r = fk_chain
assert planar.self_check() == [], planar.self_check()


def mutate(A, B):
    result = compose(A, B)
    A[0][2] += 1
    return result


frame_mutants = [
    ("compose", lambda A, B: compose(B, A)),
    ("compose", lambda A, B: [r+[0.] for r in compose(A, B)]+[[0.]*4]),
    ("compose", mutate),
    ("invert", lambda T: [[T[0][0], T[1][0], -T[0][2]], [T[0][1], T[1][1], -T[1][2]], [0., 0., 1.]]),
    ("apply_direction", lambda T, v: vector(T, v, True)),
    ("apply_point", lambda T, p: [float('nan'), 0.]),
    ("is_rotation", lambda R, tol=1e-9: abs(R[0][0]*R[1][1]-R[0][1]*R[1][0]-1) <= tol),
    ("is_rotation", lambda R, tol=1e-9: True),
]
for name, fn in frame_mutants:
    setattr(frames, name, fn)
    assert frames.self_check(), "False accept: " + name
    setattr(frames, name, refs[name])
fk_mutants = [
    lambda a, b, c, d: (c*math.cos(a)+d*math.cos(b), c*math.sin(a)+d*math.sin(b), b),
    lambda a, b, c, d: fk(a, b, d, c),
    lambda a, b, c, d: fk(math.radians(a), math.radians(b), c, d),
    lambda a, b, c, d: (*fk(a, b, c, d)[:2], a),
    lambda a, b, c, d: (*fk(a, b, c, d)[:2], float('nan')),
    lambda a, b, c, d: (*fk(a, b, c, d)[:2], True),
    lambda a, b, c, d: (*fk(a, b, c, d), 0.),
    lambda a, b, c, d: (1., 2., 0.),
]
for fn in fk_mutants:
    planar.planar_2r = fn
    assert planar.self_check(), "False FK accept"
print("Manual kits: 4 valid alternatives accepted, 16 injected bugs rejected; starters fail as intended")
