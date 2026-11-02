"""Author-side kit conformance tests; synthetic solutions, not independent review.

Alternatives and mutants marked "review" reproduce the independent review's
probes (valid alternative formulations and bug classes that once slipped
through). Plain checks only, so the fixture also works under python -O.
"""
import ast
import cmath
import importlib.util
import math
from pathlib import Path

LABS = Path(__file__).resolve().parents[2] / "content" / "labs"


def require(condition, message):
    if not condition:
        raise SystemExit("manual_kits fixture failed: " + message)


def load(name):
    file = LABS / name
    tree = ast.parse(file.read_text(encoding="utf8"))
    require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
            name + " uses assert; python -O would strip its checks")
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


def finite_result(M):
    flat = [x for row in M for x in row] if isinstance(M[0], list) else M
    if not all(math.isfinite(x) for x in flat):
        raise ValueError
    return M


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
    return finite_result(multiply(A, B))


def invert(T):
    valid(T)
    a, b, c, d = T[0][0], T[0][1], T[1][0], T[1][1]
    x, y = T[0][2], T[1][2]
    return finite_result([[a, c, -(a*x+c*y)], [b, d, -(b*x+d*y)], [0., 0., 1.]])


def vector(T, v, point):
    valid(T)
    if not (isinstance(v, (list, tuple)) and len(v) == 2 and all(real(x) for x in v)):
        raise ValueError
    return finite_result([sum(T[i][j]*v[j] for j in range(2)) + (T[i][2] if point else 0.)
                          for i in range(2)])


def fk(a, b, c, d):
    if not (all(real(x) for x in (a, b, c, d)) and abs(a) <= 2*math.pi
            and abs(b) <= 2*math.pi and 0 < c <= 10 and 0 < d <= 10):
        raise ValueError
    return (c*math.cos(a)+d*math.cos(a+b), c*math.sin(a)+d*math.sin(a+b), a+b)


frames, planar = load("L01-SE2.v1.py"), load("L02-planar.v1.py")
require(frames.self_check(), "unimplemented Frames starter must fail")
require(planar.self_check(), "unimplemented FK starter must fail")
refs = dict(make_transform=make, compose=compose, invert=invert,
            apply_point=lambda T, p: vector(T, p, True),
            apply_direction=lambda T, v: vector(T, v, False), is_rotation=rotation)


def frames_with(over):
    for name, fn in refs.items():
        setattr(frames, name, fn)
    for name, fn in over.items():
        setattr(frames, name, fn)
    result = frames.self_check()
    for name, fn in refs.items():
        setattr(frames, name, fn)
    return result


def planar_with(fn):
    planar.planar_2r = fn
    return planar.self_check()


# ---- Valid Frames alternatives ----

def compose_angle(A, B):
    valid(A)
    valid(B)
    t = math.atan2(A[1][0], A[0][0])+math.atan2(B[1][0], B[0][0])
    c, s = math.cos(t), math.sin(t)
    p = vector(A, [B[0][2], B[1][2]], True)
    return [[c, -s, p[0]], [s, c, p[1]], [0., 0., 1.]]


# review: complex-number formulation (exact bottom row, tuple vectors).
def c_rotation(R, tol=1e-9):
    if not (real(tol) and 0 < tol <= .01):
        raise ValueError
    if not (isinstance(R, (list, tuple)) and len(R) == 2
            and all(isinstance(r, (list, tuple)) and len(r) == 2 and all(real(x) for x in r) for r in R)):
        raise ValueError
    z, w = complex(R[0][0], R[1][0]), complex(R[0][1], R[1][1])
    return bool(abs(abs(z) - 1) <= tol and abs(w - 1j*z) <= tol)


def c_split(T):
    if not (isinstance(T, (list, tuple)) and len(T) == 3
            and all(isinstance(r, (list, tuple)) and len(r) == 3 and all(real(x) for x in r) for r in T)):
        raise ValueError
    if list(T[2]) != [0, 0, 1] or not c_rotation([T[0][:2], T[1][:2]]):
        raise ValueError
    return complex(T[0][0], T[1][0]), complex(T[0][2], T[1][2])


def c_matrix(r, t):
    out = [[r.real, -r.imag, t.real], [r.imag, r.real, t.imag], [0.0, 0.0, 1.0]]
    return finite_result(out)


def c_vec(v):
    if not (isinstance(v, (list, tuple)) and len(v) == 2 and all(real(x) for x in v)):
        raise ValueError
    return complex(v[0], v[1])


def c_make(theta, x, y):
    if not all(real(v) for v in (theta, x, y)) or abs(theta) > 2*math.pi or abs(x) > 100 or abs(y) > 100:
        raise ValueError
    return c_matrix(cmath.exp(1j*theta), complex(x, y))


def c_compose(A, B):
    ra, ta = c_split(A)
    rb, tb = c_split(B)
    return c_matrix(ra*rb, ra*tb + ta)


def c_invert(T):
    r, t = c_split(T)
    return c_matrix(r.conjugate(), -r.conjugate()*t)


def c_point(T, p):
    r, t = c_split(T)
    q = r*c_vec(p) + t
    if not (math.isfinite(q.real) and math.isfinite(q.imag)):
        raise ValueError
    return (q.real, q.imag)


def c_direction(T, v):
    r, _ = c_split(T)
    q = r*c_vec(v)
    return (q.real, q.imag)


complex_frames = dict(make_transform=c_make, compose=c_compose, invert=c_invert,
                      apply_point=c_point, apply_direction=c_direction, is_rotation=c_rotation)


def rotation_by_angle(R, tol=1e-9):
    c_rotation(R, tol)  # validation only
    t = math.atan2(R[1][0], R[0][0])
    c, s = math.cos(t), math.sin(t)
    return all(abs(a-b) <= tol for a, b in zip((R[0][0], R[0][1], R[1][0], R[1][1]), (c, -s, s, c)))


def invert_adjugate(T):
    c_split(T)
    a, b, c, d = T[0][0], T[0][1], T[1][0], T[1][1]
    det = a*d - b*c
    Ri = [[d/det, -b/det], [-c/det, a/det]]
    t = [-(Ri[0][0]*T[0][2] + Ri[0][1]*T[1][2]), -(Ri[1][0]*T[0][2] + Ri[1][1]*T[1][2])]
    return [[Ri[0][0], Ri[0][1], t[0]], [Ri[1][0], Ri[1][1], t[1]], [0., 0., 1.]]


def make_int_where_exact(theta, x, y):
    return [[round(v) if abs(v - round(v)) < 1e-15 else v for v in r] for r in c_make(theta, x, y)]


frame_alternatives = [
    ("author reference", {}),
    ("angle-sum compose", dict(compose=compose_angle)),
    ("review: complex-number formulation", complex_frames),
    ("review: tuple-of-tuples matrices", dict(make_transform=lambda t, x, y: tuple(map(tuple, make(t, x, y))))),
    ("review: int entries where exact", dict(make_transform=make_int_where_exact)),
    ("review: is_rotation by angle reconstruction", dict(is_rotation=rotation_by_angle)),
    ("review: adjugate inverse", dict(invert=invert_adjugate)),
]
for label, over in frame_alternatives:
    result = frames_with(over)
    require(result == [], "false reject (" + label + "): " + str(result))


# ---- Valid FK alternatives ----

def fk_chain(a, b, c, d):
    fk(a, b, c, d)  # declared primitive domain validation only
    M = multiply(multiply(make(a, 0., 0.), make(0., c, 0.)),
                 multiply(make(b, 0., 0.), make(0., d, 0.)))
    return (M[0][2], M[1][2], math.atan2(M[1][0], M[0][0]))


def fk_phasor(a, b, c, d):
    fk(a, b, c, d)
    e1 = cmath.exp(1j*a)
    e12 = e1*cmath.exp(1j*b)
    p = c*e1 + d*e12
    return [p.real, p.imag, cmath.phase(e12)]


def fk_polar(a, b, c, d):
    fk(a, b, c, d)
    r = math.sqrt(max(0.0, c*c + d*d + 2*c*d*math.cos(b)))
    phi = a + math.atan2(d*math.sin(b), c + d*math.cos(b))
    return (r*math.cos(phi), r*math.sin(phi), (a+b) % (2*math.pi))


fk_alternatives = [
    ("author reference", fk),
    ("transform chain", fk_chain),
    ("review: complex phasor, wrapped heading", fk_phasor),
    ("review: polar/law of cosines, heading in [0, 2pi)", fk_polar),
    ("review: int outputs where exact",
     lambda a, b, c, d: tuple(int(v) if v == int(v) else v for v in fk_phasor(a, b, c, d))),
]
for label, fn in fk_alternatives:
    result = planar_with(fn)
    require(result == [], "false FK reject (" + label + "): " + str(result))


# ---- Frames mutants ----

def mutate(A, B):
    result = compose(A, B)
    A[0][2] += 1
    return result


def bottom_row_only(T):
    if not (isinstance(T, (list, tuple)) and len(T) == 3
            and all(isinstance(r, (list, tuple)) and len(r) == 3 and all(real(x) for x in r) for r in T)
            and list(T[2]) == [0, 0, 1]):
        raise ValueError


def invert_bottom_only(T):
    bottom_row_only(T)
    a, b, c, d, x, y = T[0][0], T[0][1], T[1][0], T[1][1], T[0][2], T[1][2]
    return [[a, c, -(a*x+c*y)], [b, d, -(b*x+d*y)], [0., 0., 1.]]


def point_unvalidated_T(T, p):
    c_vec(p)
    return [T[0][0]*p[0]+T[0][1]*p[1]+T[0][2], T[1][0]*p[0]+T[1][1]*p[1]+T[1][2]]


def direction_unvalidated_T(T, v):
    c_vec(v)
    return [T[0][0]*v[0]+T[0][1]*v[1], T[1][0]*v[0]+T[1][1]*v[1]]


def point_mutates(T, p):
    valid(T)
    if not (isinstance(p, list) and len(p) == 2):
        raise ValueError
    p.append(1.0)
    return [sum(T[i][j]*p[j] for j in range(3)) for i in range(2)]


def point_mutates_lists_only(T, p):
    result = vector(T, p, True)
    if isinstance(p, list):
        p[0] = result[0]
    return result


def rotation_fixed_tol(R, tol=1e-9):
    rotation(R, tol)  # validation only
    return rotation(R, 1e-3)


def rotation_nan_false(R, tol=1e-9):
    if not (real(tol) and 0 < tol <= .01 and isinstance(R, (list, tuple)) and len(R) == 2
            and all(isinstance(r, (list, tuple)) and len(r) == 2 for r in R)):
        raise ValueError
    try:
        z, w = complex(R[0][0], R[1][0]), complex(R[0][1], R[1][1])
    except TypeError:
        raise ValueError
    return bool(abs(abs(z)-1) <= tol and abs(w-1j*z) <= tol)


def rotation_clamps_tol(R, tol=1e-9):
    if not (real(tol) and tol > 0):
        raise ValueError
    return rotation(R, min(tol, .01))


def rotation_bool_entries(R, tol=1e-9):
    if not (real(tol) and 0 < tol <= .01 and isinstance(R, (list, tuple)) and len(R) == 2
            and all(isinstance(r, (list, tuple)) and len(r) == 2
                    and all(isinstance(x, (int, float)) and math.isfinite(x) for x in r) for r in R)):
        raise ValueError
    return c_rotation([[float(x) for x in r] for r in R], tol)


def rotation_form_only(R, tol=1e-9):
    rotation(R, tol)  # validation only
    (a, b), (c, d) = R
    return abs(a-d) <= tol and abs(b+c) <= tol


def invert_form_only(T):
    if not (isinstance(T, (list, tuple)) and len(T) == 3
            and all(isinstance(r, (list, tuple)) and len(r) == 3 and all(real(x) for x in r) for r in T)
            and rotation_form_only([T[0][:2], T[1][:2]]) and list(T[2]) == [0, 0, 1]):
        raise ValueError
    a, b, c, d = T[0][0], T[0][1], T[1][0], T[1][1]
    x, y = T[0][2], T[1][2]
    return [[a, c, -(a*x+c*y)], [b, d, -(b*x+d*y)], [0., 0., 1.]]


def compose_truncating(A, B):
    if not all(isinstance(M, (list, tuple)) and len(M) == 3 for M in (A, B)):
        raise ValueError
    return compose([list(r[:3]) for r in A], [list(r[:3]) for r in B])


def make_nan_blind(theta, x, y):
    if not real(theta) or abs(theta) > 2*math.pi or abs(x) > 100 or abs(y) > 100:
        raise ValueError
    c, s = math.cos(theta), math.sin(theta)
    return [[c, -s, x], [s, c, y], [0., 0., 1.]]


def rotation_truthy(R, tol=1e-9):
    return 1 if rotation(R, tol) else 0


def unchecked_make(theta, x, y):
    c, s = math.cos(theta), math.sin(theta)
    return [[c, -s, x], [s, c, y], [0., 0., 1.]]


def make_x_bound_only(theta, x, y):
    if real(y) and abs(y) > 100:
        make(theta, x, 0.)  # every other check still applies
        return unchecked_make(theta, x, y)
    return make(theta, x, y)


def make_upper_theta_only(theta, x, y):
    if real(theta) and theta < -2*math.pi:
        make(0., x, y)
        return unchecked_make(theta, x, y)
    return make(theta, x, y)


def make_floats_only(theta, x, y):
    if not all(type(v) is float for v in (theta, x, y)):
        raise ValueError
    return make(theta, x, y)


def compose_unvalidated(A, B):
    return multiply(A, B)


def compose_no_overflow_check(A, B):
    valid(A)
    valid(B)
    return multiply(A, B)


def point_no_overflow_check(T, p):
    valid(T)
    c_vec(p)
    return [sum(T[i][j]*p[j] for j in range(2)) + T[i][2] for i in range(2)]


def compose_exact_bottom_rejects_ints(A, B):
    if any(type(x) is not float for row in (*A, *B) for x in row):
        raise ValueError
    return compose(A, B)


def invert_minus_R_t(T):
    r, t = c_split(T)
    return [[r.real, r.imag, (-r*t).real], [-r.imag, r.real, (-r*t).imag], [0., 0., 1.]]


def point_rejects_tuple(T, p):
    if not isinstance(p, list):
        raise ValueError
    return vector(T, p, True)


def invert_rejects_near_rotation(T):
    valid(T)
    if T[0][1] != -T[1][0] or T[0][0] != T[1][1]:
        raise ValueError
    return invert(T)


frame_mutants = [
    ("compose: reversed order", dict(compose=lambda A, B: compose(B, A))),
    ("compose: 4x4 output", dict(compose=lambda A, B: [r+[0.] for r in compose(A, B)]+[[0.]*4])),
    ("compose: mutates input", dict(compose=mutate)),
    ("invert: transpose with -p", dict(invert=lambda T: [[T[0][0], T[1][0], -T[0][2]], [T[0][1], T[1][1], -T[1][2]], [0., 0., 1.]])),
    ("apply_direction: adds translation", dict(apply_direction=lambda T, v: vector(T, v, True))),
    ("apply_point: NaN output", dict(apply_point=lambda T, p: [float('nan'), 0.])),
    ("is_rotation: determinant only", dict(is_rotation=lambda R, tol=1e-9: abs(R[0][0]*R[1][1]-R[0][1]*R[1][0]-1) <= tol)),
    ("is_rotation: always True", dict(is_rotation=lambda R, tol=1e-9: True)),
    ("review: make_transform y bound unchecked", dict(make_transform=make_x_bound_only)),
    ("review: make_transform theta lower bound unchecked", dict(make_transform=make_upper_theta_only)),
    ("review: make_transform rejects ints", dict(make_transform=make_floats_only)),
    ("review: invert checks bottom row only (accepts reflection)", dict(invert=invert_bottom_only)),
    ("review: invert -R t instead of -R^T t", dict(invert=invert_minus_R_t)),
    ("review: compose without input validation", dict(compose=compose_unvalidated)),
    ("review: compose without overflow check", dict(compose=compose_no_overflow_check)),
    ("compose rejects int entries", dict(compose=compose_exact_bottom_rejects_ints)),
    ("review: apply_point without T validation", dict(apply_point=point_unvalidated_T)),
    ("review: apply_point without overflow check", dict(apply_point=point_no_overflow_check)),
    ("review: apply_point mutates point (appends 1)", dict(apply_point=point_mutates)),
    ("apply_point writes result into list point", dict(apply_point=point_mutates_lists_only)),
    ("apply_point rejects tuple point", dict(apply_point=point_rejects_tuple)),
    ("apply_direction without T validation", dict(apply_direction=direction_unvalidated_T)),
    ("invert rejects near-rotation within default tol", dict(invert=invert_rejects_near_rotation)),
    ("review: is_rotation ignores tol (fixed 1e-3)", dict(is_rotation=rotation_fixed_tol)),
    ("review: is_rotation NaN entry returns False", dict(is_rotation=rotation_nan_false)),
    ("review: is_rotation clamps tol > .01", dict(is_rotation=rotation_clamps_tol)),
    ("review: is_rotation accepts bool entries", dict(is_rotation=rotation_bool_entries)),
    ("is_rotation returns 1/0 instead of bool", dict(is_rotation=rotation_truthy)),
    ("re-review: is_rotation checks [[c,-s],[s,c]] form only", dict(is_rotation=rotation_form_only)),
    ("re-review: invert accepts a uniformly scaled block", dict(invert=invert_form_only)),
    ("re-review: compose truncates 3x4 rows", dict(compose=compose_truncating)),
    ("re-review: make_transform NaN-blind x/y bounds", dict(make_transform=make_nan_blind)),
]
for label, over in frame_mutants:
    require(frames_with(over), "false accept: " + label)


# ---- FK mutants ----

def fk_only_l1_validated(a, b, c, d):
    if not (all(real(x) for x in (a, b, c)) and not isinstance(d, bool)
            and abs(a) <= 2*math.pi and abs(b) <= 2*math.pi and 0 < c <= 10):
        raise ValueError
    return (c*math.cos(a)+d*math.cos(a+b), c*math.sin(a)+d*math.sin(a+b), a+b)


def fk_l2_upper_only(a, b, c, d):
    if not (all(real(x) for x in (a, b, c, d)) and abs(a) <= 2*math.pi
            and abs(b) <= 2*math.pi and 0 < c <= 10 and d <= 10):
        raise ValueError
    return (c*math.cos(a)+d*math.cos(a+b), c*math.sin(a)+d*math.sin(a+b), a+b)


def fk_nan_l2(a, b, c, d):
    if not (all(real(x) for x in (a, b, c)) and abs(a) <= 2*math.pi
            and abs(b) <= 2*math.pi and 0 < c <= 10) or d <= 0 or d > 10:
        raise ValueError
    return (c*math.cos(a)+d*math.cos(a+b), c*math.sin(a)+d*math.sin(a+b), a+b)


def fk_bool_q2(a, b, c, d):
    return fk(a, float(b) if isinstance(b, bool) else b, c, d)


def fk_floats_only(a, b, c, d):
    if not all(type(v) is float for v in (a, b, c, d)):
        raise ValueError
    return fk(a, b, c, d)


def fk_q_upper_only(a, b, c, d):
    if real(a) and real(b) and (a < -2*math.pi or b > 2*math.pi):
        return (c*math.cos(a)+d*math.cos(a+b), c*math.sin(a)+d*math.sin(a+b), a+b)
    return fk(a, b, c, d)


fk_mutants = [
    ("absolute instead of relative q2", lambda a, b, c, d: (c*math.cos(a)+d*math.cos(b), c*math.sin(a)+d*math.sin(b), b)),
    ("swapped links", lambda a, b, c, d: fk(a, b, d, c)),
    ("degrees", lambda a, b, c, d: fk(math.radians(a), math.radians(b), c, d)),
    ("theta = q1", lambda a, b, c, d: (*fk(a, b, c, d)[:2], a)),
    ("NaN theta", lambda a, b, c, d: (*fk(a, b, c, d)[:2], float('nan'))),
    ("bool theta", lambda a, b, c, d: (*fk(a, b, c, d)[:2], True)),
    ("extra field", lambda a, b, c, d: (*fk(a, b, c, d), 0.)),
    ("constant", lambda a, b, c, d: (1., 2., 0.)),
    ("review: only l1 validated", fk_only_l1_validated),
    ("review: l2 <= 0 accepted", fk_l2_upper_only),
    ("review: NaN l2 accepted", fk_nan_l2),
    ("review: bool q2 accepted", fk_bool_q2),
    ("review: rejects int inputs", fk_floats_only),
    ("q1 lower / q2 upper bound unchecked", fk_q_upper_only),
    ("review: theta = endpoint bearing", lambda a, b, c, d: (*fk(a, b, c, d)[:2], math.atan2(fk(a, b, c, d)[1], fk(a, b, c, d)[0]))),
    ("review: elbow sign flipped", lambda a, b, c, d: (*fk(a, -b, c, d)[:2], fk(a, b, c, d)[2])),
]
for label, fn in fk_mutants:
    require(planar_with(fn), "false FK accept: " + label)

alternatives = len(frame_alternatives) + len(fk_alternatives)
mutants = len(frame_mutants) + len(fk_mutants)
print("Manual kits: " + str(alternatives) + " valid alternatives accepted, "
      + str(mutants) + " injected bugs rejected; starters fail as intended")
