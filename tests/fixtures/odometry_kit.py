"""Original author-side conformance fixture; never independent review or evidence."""
import importlib.util
import math
from pathlib import Path

file = Path(__file__).resolve().parents[2] / 'content/labs/L03-odometry.v1.py'
spec = importlib.util.spec_from_file_location('odometry_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
assert kit.self_check(), 'Unimplemented starter must report failure'


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
for name, fn in refs.items():
    setattr(kit, name, fn)
assert kit.self_check() == [], kit.self_check()
kit.odom_step = lambda p, l, r, b: motion(p, l, r, b, True)
assert kit.self_check() == [], kit.self_check()
kit.odom_step = motion


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


def mutating(pose, dl, dr, track):
    result = motion(pose, dl, dr, track)
    pose[0] += 1
    return result


mutants = [
    ('left/right swapped', 'wheel_to_body', lambda l, r, b: wheel(r, l, b)),
    ('half track', 'wheel_to_body', lambda l, r, b: ((l+r)/2, (r-l)/(2*b))),
    ('inverse wheel order', 'body_to_wheels', lambda v, w, b: list(reversed(body(v, w, b)))),
    ('inverse clipping', 'body_to_wheels', lambda v, w, b: [max(-2, min(2, x)) for x in body(v, w, b)]),
    ('no motion', 'odom_step', lambda p, l, r, b: tuple(p)),
    ('forgot initial heading', 'odom_step', lambda p, l, r, b: motion([p[0], p[1], 0.], l, r, b)),
    ('Euler instead of exact arc', 'odom_step', euler),
    ('midpoint without sinc', 'odom_step', midpoint),
    ('small-angle cancellation', 'odom_step', cancellation),
    ('unwrapped heading', 'odom_step', lambda p, l, r, b: (*motion(p, l, r, b)[:2], p[2]+(r-l)/b)),
    ('extra field', 'odom_step', lambda p, l, r, b: (*motion(p, l, r, b), 0.)),
    ('bool heading', 'odom_step', lambda p, l, r, b: (*motion(p, l, r, b)[:2], True)),
    ('NaN heading', 'odom_step', lambda p, l, r, b: (*motion(p, l, r, b)[:2], float('nan'))),
    ('NaN wheel/body output', 'wheel_to_body', lambda l, r, b: (float('nan'), 0.)),
    ('mutated pose', 'odom_step', mutating),
    ('forgot dt', 'velocity_step', lambda p, l, r, b, dt: motion(p, l, r, b)),
    ('dt applied twice', 'velocity_step', lambda p, l, r, b, dt: motion(p, l*dt*dt, r*dt*dt, b)),
    ('invalid dt accepted', 'velocity_step', lambda p, l, r, b, dt: velocity(p, l, r, b, dt) if type(dt) in (int, float) and math.isfinite(dt) and 0 < dt <= 5 else (0., 0., 0.)),
]
for label, name, function in mutants:
    setattr(kit, name, function)
    assert kit.self_check(), 'False accept: ' + label
    setattr(kit, name, refs[name])
print('Odometry kit: 2 valid alternatives accepted, 18 injected bugs rejected; starter fails as intended')
