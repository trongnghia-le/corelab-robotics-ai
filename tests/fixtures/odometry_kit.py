"""Original author-side conformance fixture; never independent review or evidence.

Entries marked "review" reproduce the independent review's probes (valid
alternative integrators and bug classes that once slipped through). Plain
checks only, so the fixture also works under python -O.
"""
import ast
import cmath
import importlib.util
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('odometry_kit fixture failed: ' + message)


file = Path(__file__).resolve().parents[2] / 'content/labs/L03-odometry.v1.py'
tree = ast.parse(file.read_text(encoding='utf8'))
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
spec = importlib.util.spec_from_file_location('odometry_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
require(kit.self_check(), 'unimplemented starter must report failure')


def finite(value, limit):
    if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > limit:
        raise ValueError


def width(track):
    finite(track, 2.)
    if track < .1:
        raise ValueError


def valid_pose(pose):
    if not isinstance(pose, (list, tuple)) or len(pose) != 3:
        raise ValueError
    finite(pose[0], 1000.)
    finite(pose[1], 1000.)
    finite(pose[2], 2*math.pi)


def wheel(vl, vr, track):
    finite(vl, 2.)
    finite(vr, 2.)
    width(track)
    return ((vl+vr)/2, (vr-vl)/track)


def body(v, omega, track):
    finite(v, 2.)
    finite(omega, 40.)
    width(track)
    return [v-omega*track/2, v+omega*track/2]


def motion(pose, dl, dr, track, alternate=False):
    valid_pose(pose)
    finite(dl, 10.)
    finite(dr, 10.)
    width(track)
    x, y, theta = pose
    distance, angle = (dl+dr)/2, (dr-dl)/track
    if alternate:
        bx = distance if angle == 0 else distance*math.sin(angle)/angle
        by = 0. if angle == 0 else distance*2*math.sin(angle/2)**2/angle
        return [x+math.cos(theta)*bx-math.sin(theta)*by,
                y+math.sin(theta)*bx+math.cos(theta)*by,
                (theta+angle+math.pi) % (2*math.pi)-math.pi]
    half = angle/2
    scale = distance if half == 0 else distance*math.sin(half)/half
    return (x+scale*math.cos(theta+half), y+scale*math.sin(theta+half),
            math.atan2(math.sin(theta+angle), math.cos(theta+angle)))


def velocity(pose, vl, vr, track, dt):
    valid_pose(pose)
    wheel(vl, vr, track)
    finite(dt, 5.)
    if dt <= 0:
        raise ValueError
    return motion(pose, vl*dt, vr*dt, track)


refs = {'wheel_to_body': wheel, 'body_to_wheels': body,
        'odom_step': motion, 'velocity_step': velocity}


def run_with(over):
    for name, fn in refs.items():
        setattr(kit, name, fn)
    for name, fn in over.items():
        setattr(kit, name, fn)
    result = kit.self_check()
    for name, fn in refs.items():
        setattr(kit, name, fn)
    return result


def wrap_remainder(a):
    r = math.remainder(a, 2*math.pi)
    return math.pi if r == -math.pi else r


def odom_icc(pose, dl, dr, track):
    """review A: instantaneous centre with 2 sin^2 and a series fallback."""
    motion(pose, dl, dr, track)  # input-domain validation only
    x, y, t = pose
    d, a = (dl+dr)/2, (dr-dl)/track
    if abs(a) < 1e-6:
        fx, fy = d*(1 - a*a/6), d*(a/2 - a**3/24)
    else:
        fx, fy = d/a*math.sin(a), d/a*2*math.sin(a/2)**2
    return (x + math.cos(t)*fx - math.sin(t)*fy, y + math.sin(t)*fx + math.cos(t)*fy, wrap_remainder(t+a))


def odom_complex(pose, dl, dr, track):
    """review B: complex exponential along the mid heading with a series sinc."""
    motion(pose, dl, dr, track)
    x, y, t = pose
    d, a = (dl+dr)/2, (dr-dl)/track
    h = a/2
    sinc = 1 - h*h/6 + h**4/120 if abs(h) < 1e-4 else math.sin(h)/h
    z = complex(x, y) + d*sinc*cmath.exp(1j*(t+h))
    return [z.real, z.imag, wrap_remainder(t+a)]


def odom_rk4(pose, dl, dr, track, n=2000):
    """review C: numerical sub-stepping, judged only on the stated tolerances."""
    motion(pose, dl, dr, track)
    x, y, t = pose
    d, a = (dl+dr)/2, (dr-dl)/track
    ds, da = d/n, a/n
    for _ in range(n):
        x += ds*(math.cos(t) + 4*math.cos(t+da/2) + math.cos(t+da))/6
        y += ds*(math.sin(t) + 4*math.sin(t+da/2) + math.sin(t+da))/6
        t += da
    return (x, y, wrap_remainder(t))


def odom_guard_mid(pose, dl, dr, track):
    """review E: sin-difference form; tiny turns move along the mid heading."""
    motion(pose, dl, dr, track)
    x, y, t = pose
    d, a = (dl+dr)/2, (dr-dl)/track
    if abs(a) < 1e-9:
        return (x + d*math.cos(t+a/2), y + d*math.sin(t+a/2), wrap_remainder(t+a))
    R = d/a
    return (x + R*(math.sin(t+a) - math.sin(t)), y - R*(math.cos(t+a) - math.cos(t)), wrap_remainder(t+a))


def velocity_via_body(step):
    """review: velocity_step routed through body velocities, then wheel travel."""
    def run(pose, vl, vr, track, dt):
        velocity(pose, vl, vr, track, dt)  # validation only
        v, w = wheel(vl, vr, track)
        a, d = w*dt, v*dt
        return step(pose, d - a*track/2, d + a*track/2, track)
    return run


alternatives = [
    ('author half-angle reference', {}),
    ('author 2 sin^2 body-frame form', {'odom_step': lambda p, l, r, b: motion(p, l, r, b, True)}),
    ('review A: ICC + series, remainder wrap, velocity via body',
     {'odom_step': odom_icc, 'velocity_step': velocity_via_body(odom_icc)}),
    ('review B: complex mid-heading sinc',
     {'odom_step': odom_complex, 'velocity_step': velocity_via_body(odom_complex)}),
    ('review C: RK4 with 2000 substeps',
     {'odom_step': odom_rk4, 'velocity_step': velocity_via_body(odom_rk4)}),
    ('review E: small-turn guard along the mid heading', {'odom_step': odom_guard_mid}),
    ('tuple outputs everywhere', {'body_to_wheels': lambda v, w, b: tuple(body(v, w, b)),
                                  'odom_step': lambda p, l, r, b: tuple(motion(p, l, r, b))}),
]
for label, over in alternatives:
    result = run_with(over)
    require(result == [], 'false reject (' + label + '): ' + str(result))


def euler(pose, dl, dr, track):
    motion(pose, dl, dr, track)  # reuse input-domain validation only
    x, y, t = pose
    d, a = (dl+dr)/2, (dr-dl)/track
    return (x+d*math.cos(t), y+d*math.sin(t), math.atan2(math.sin(t+a), math.cos(t+a)))


def midpoint(pose, dl, dr, track):
    motion(pose, dl, dr, track)
    x, y, t = pose
    d, a = (dl+dr)/2, (dr-dl)/track
    return (x+d*math.cos(t+a/2), y+d*math.sin(t+a/2), math.atan2(math.sin(t+a), math.cos(t+a)))


def cancellation(pose, dl, dr, track):
    motion(pose, dl, dr, track)
    x, y, t = pose
    d, a = (dl+dr)/2, (dr-dl)/track
    bx, by = (d, 0.) if a == 0 else (d*math.sin(a)/a, d*(1-math.cos(a))/a)
    return (x+math.cos(t)*bx-math.sin(t)*by, y+math.sin(t)*bx+math.cos(t)*by,
            math.atan2(math.sin(t+a), math.cos(t+a)))


def initial_heading_guard(pose, dl, dr, track):
    """review D: straight line along the INITIAL heading for tiny turns."""
    motion(pose, dl, dr, track)
    x, y, t = pose
    d, a = (dl+dr)/2, (dr-dl)/track
    if abs(a) < 1e-9:
        return (x + d*math.cos(t), y + d*math.sin(t), wrap_remainder(t+a))
    R = d/a
    return (x + R*(math.sin(t+a) - math.sin(t)), y - R*(math.cos(t+a) - math.cos(t)), wrap_remainder(t+a))


def mutating(pose, dl, dr, track):
    result = motion(pose, dl, dr, track)
    pose[0] += 1
    return result


def straight_unwrapped(pose, dl, dr, track):
    result = motion(pose, dl, dr, track)
    return (result[0], result[1], pose[2]) if dl == dr else result


def list_pose_only(pose, dl, dr, track):
    if not isinstance(pose, list):
        raise ValueError
    return motion(pose, dl, dr, track)


def floats_only(pose, dl, dr, track):
    if not isinstance(pose, (list, tuple)) or not all(type(v) is float for v in (*pose, dl, dr, track)):
        raise ValueError
    return motion(pose, dl, dr, track)


def raw_arc(pose, dl, dr, track):
    x, y, t = pose
    d, a = (dl+dr)/2, (dr-dl)/track
    h = a/2
    s = d if h == 0 else d*math.sin(h)/h
    return (x+s*math.cos(t+h), y+s*math.sin(t+h), math.atan2(math.sin(t+a), math.cos(t+a)))


def skip_check(check):
    """Full validation except one named gap; used for the asymmetric-bound mutants."""
    def odom(pose, dl, dr, track):
        if check(pose, dl, dr, track):
            return raw_arc(pose, dl, dr, track)
        return motion(pose, dl, dr, track)
    return odom


def is_real(v):
    return type(v) in (int, float) and math.isfinite(v)


def clipped_output(pose, dl, dr, track):
    x, y, t = motion(pose, dl, dr, track)
    return (max(-1000., min(1000., x)), max(-1000., min(1000., y)), t)


def rejects_large_output(pose, dl, dr, track):
    result = motion(pose, dl, dr, track)
    valid_pose(result)
    return result


def body_no_upper_track(v, omega, track):
    finite(v, 2.)
    finite(omega, 40.)
    if not is_real(track) or track < .1:
        raise ValueError
    return [v-omega*track/2, v+omega*track/2]


def wheel_bool_track(vl, vr, track):
    return wheel(vl, vr, float(track) if isinstance(track, bool) else track)


def wheel_float_track_only(vl, vr, track):
    if type(track) is not float:
        raise ValueError
    return wheel(vl, vr, track)


def velocity_no_track_check(pose, vl, vr, track, dt):
    valid_pose(pose)
    finite(vl, 2.)
    finite(vr, 2.)
    finite(dt, 5.)
    if dt <= 0:
        raise ValueError
    return raw_arc(pose, vl*dt, vr*dt, track)


def velocity_vr_unbounded(pose, vl, vr, track, dt):
    if is_real(vr) and abs(vr) > 2 and is_real(dt) and 0 < dt <= 5:
        valid_pose(pose)
        width(track)
        return raw_arc(pose, vl*dt, vr*dt, track)
    return velocity(pose, vl, vr, track, dt)


def quarter_track(v, omega, track):
    body(v, omega, track)  # validation only
    return [v-omega*track/4, v+omega*track/4]


def heading_write_back(pose, dl, dr, track):
    result = motion(pose, dl, dr, track)
    if isinstance(pose, list):
        pose[2] = result[2]
    return result


def velocity_midpoint(pose, vl, vr, track, dt):
    velocity(pose, vl, vr, track, dt)  # validation only
    return midpoint(pose, vl*dt, vr*dt, track)


def odom_nan_blind_track(pose, dl, dr, track):
    if type(track) in (int, float) and track != track:
        return (0., 0., 0.)  # comparisons with NaN are all false
    return motion(pose, dl, dr, track)


def velocity_nan_blind_dt(pose, vl, vr, track, dt):
    if type(dt) in (int, float) and dt != dt:
        return tuple(pose)
    return velocity(pose, vl, vr, track, dt)


mutants = [
    ('re-review: NaN track passes bound checks', {'odom_step': odom_nan_blind_track}),
    ('re-review: NaN dt passes bound checks', {'velocity_step': velocity_nan_blind_dt}),
    ('left/right swapped', {'wheel_to_body': lambda l, r, b: wheel(r, l, b)}),
    ('half track', {'wheel_to_body': lambda l, r, b: ((l+r)/2, (r-l)/(2*b))}),
    ('inverse wheel order', {'body_to_wheels': lambda v, w, b: list(reversed(body(v, w, b)))}),
    ('inverse clipping', {'body_to_wheels': lambda v, w, b: [max(-2, min(2, x)) for x in body(v, w, b)]}),
    ('review: quarter track inverse', {'body_to_wheels': quarter_track}),
    ('no motion', {'odom_step': lambda p, l, r, b: tuple(p)}),
    ('forgot initial heading', {'odom_step': lambda p, l, r, b: motion([p[0], p[1], 0.], l, r, b)}),
    ('Euler instead of exact arc', {'odom_step': euler}),
    ('midpoint without sinc', {'odom_step': midpoint}),
    ('small-angle cancellation', {'odom_step': cancellation}),
    ('review D: tiny-turn guard along the initial heading', {'odom_step': initial_heading_guard}),
    ('unwrapped heading', {'odom_step': lambda p, l, r, b: (*motion(p, l, r, b)[:2], p[2]+(r-l)/b)}),
    ('review: heading wrapped to [0, 2pi)', {'odom_step': lambda p, l, r, b: (*motion(p, l, r, b)[:2], (p[2]+(r-l)/b) % (2*math.pi))}),
    ('review: straight-line branch keeps input heading unwrapped', {'odom_step': straight_unwrapped}),
    ('extra field', {'odom_step': lambda p, l, r, b: (*motion(p, l, r, b), 0.)}),
    ('bool heading', {'odom_step': lambda p, l, r, b: (*motion(p, l, r, b)[:2], True)}),
    ('NaN heading', {'odom_step': lambda p, l, r, b: (*motion(p, l, r, b)[:2], float('nan'))}),
    ('NaN wheel/body output', {'wheel_to_body': lambda l, r, b: (float('nan'), 0.)}),
    ('mutated pose', {'odom_step': mutating}),
    ('review: writes wrapped heading back into list pose',
     {'odom_step': heading_write_back}),
    ('review: rejects tuple pose', {'odom_step': list_pose_only}),
    ('review: rejects int inputs', {'odom_step': floats_only}),
    ('review: rejects int track', {'wheel_to_body': wheel_float_track_only}),
    ('review: |dr| bound unchecked', {'odom_step': skip_check(lambda p, l, r, b: is_real(r) and abs(r) > 10)}),
    ('review: |y| bound unchecked', {'odom_step': skip_check(lambda p, l, r, b: isinstance(p, list) and len(p) == 3 and is_real(p[1]) and abs(p[1]) > 1000)}),
    ('review: theta lower bound unchecked', {'odom_step': skip_check(lambda p, l, r, b: isinstance(p, list) and len(p) == 3 and is_real(p[2]) and p[2] < -2*math.pi)}),
    ('odom_step track upper bound unchecked', {'odom_step': skip_check(lambda p, l, r, b: is_real(b) and b > 2)}),
    ('review: bool track accepted', {'wheel_to_body': wheel_bool_track}),
    ('review: body_to_wheels track upper bound unchecked', {'body_to_wheels': body_no_upper_track}),
    ('review: velocity_step track never validated', {'velocity_step': velocity_no_track_check}),
    ('velocity_step |vr| bound unchecked', {'velocity_step': velocity_vr_unbounded}),
    ('review: output positions clipped to +-1000', {'odom_step': clipped_output}),
    ('output beyond +-1000 rejected', {'odom_step': rejects_large_output}),
    ('forgot dt', {'velocity_step': lambda p, l, r, b, dt: motion(p, l, r, b)}),
    ('dt applied twice', {'velocity_step': lambda p, l, r, b, dt: motion(p, l*dt*dt, r*dt*dt, b)}),
    ('invalid dt accepted', {'velocity_step': lambda p, l, r, b, dt: velocity(p, l, r, b, dt) if type(dt) in (int, float) and math.isfinite(dt) and 0 < dt <= 5 else (0., 0., 0.)}),
    ('review: dt = 0 accepted', {'velocity_step': lambda p, l, r, b, dt: tuple(p) if dt == 0 and type(dt) in (int, float) else velocity(p, l, r, b, dt)}),
    ('review: midpoint Euler on body velocity', {'velocity_step': velocity_midpoint}),
]
for label, over in mutants:
    require(run_with(over), 'false accept: ' + label)
print('Odometry kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
