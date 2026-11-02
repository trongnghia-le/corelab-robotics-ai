"""Original author-side conformance fixture; never independent review or evidence.

Installs valid alternative implementations (different rotation, composition and
lookup formulations, parsers and output containers) that must pass, and named
injected bugs that must be rejected. Plain checks only, so it also works under
python -O.
"""
import ast
import importlib.util
import json
import math
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit('description_kit fixture failed: ' + message)


root = Path(__file__).resolve().parents[2]
file = root / 'content/labs/L12-description.v1.py'
text = file.read_text(encoding='utf8')
require(text.isascii(), 'kit must be ASCII-only')
tree = ast.parse(text)
require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        'kit uses assert; python -O would strip its checks')
imported = {alias.name.split('.')[0] for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
imported |= {node.module.split('.')[0] for node in ast.walk(tree)
             if isinstance(node, ast.ImportFrom) and node.module}
require(imported <= {'math', 'xml'}, 'kit imports beyond math and xml: ' + str(sorted(imported)))
called = {node.func.id for node in ast.walk(tree)
          if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
require(not called & {'open', 'eval', 'exec', 'compile', '__import__', 'input'},
        'kit calls a forbidden builtin')
attr_calls = {node.func.attr for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
require(not attr_calls & {'parse', 'iterparse', 'ElementTree', 'open', 'system', 'popen'},
        'kit reads files or runs programs: ' + str(attr_calls))
names = ('parse_chain', 'rpy_matrix', 'link_transform', 'lookup_transform', 'joint_axis_in_base')
spoiler = text.index('SPOILER BELOW')
require(all(text.index('def ' + name + '(') < spoiler for name in names),
        'starter functions must sit above the spoiler banner')
require(text.index('def _ref_model') > spoiler and text.index('def _rpy_closed') > spoiler,
        'oracle must sit below the spoiler banner')
spec = importlib.util.spec_from_file_location('description_kit', file)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
starter_notes = []
starter = kit.self_check(starter_notes)
require(starter and not starter_notes, 'unimplemented starter must report failure')
require(all(failure.isascii() for failure in starter), 'starter failure messages must be ASCII')
require(len(starter) == 5 and all('not implemented yet' in f for f in starter),
        'starter must collapse each function into one line: ' + str(starter))


# ---- samples manifest mirrors every positive self-check case ----
def dec(value):
    if type(value) is int:
        return str(value)
    shown = repr(float(value))
    return format(Decimal(shown), 'f') if 'e' in shown or 'E' in shown else shown


def qdec(q):
    return {name: dec(value) for name, value in q.items()}


expected_samples = (
    [{'structure': 'description.parse@1', 'inputs': {'urdf': t}} for _, t, _ in kit._PARSE_CASES]
    + [{'structure': 'description.rpy@1',
        'inputs': {'roll': dec(a[0]), 'pitch': dec(a[1]), 'yaw': dec(a[2])}}
       for _, a, _ in kit._RPY_CASES]
    + [{'structure': 'description.link-transform@1',
        'inputs': {'urdf': t, 'link': link, 'q': qdec(q)}}
       for _, t, link, q, _ in kit._LINK_CASES]
    + [{'structure': 'description.lookup@1',
        'inputs': {'urdf': t, 'target': a, 'source': b, 'q': qdec(q)}}
       for _, t, a, b, q, _ in kit._LOOKUP_CASES]
    + [{'structure': 'description.joint-axis@1',
        'inputs': {'urdf': t, 'joint': j, 'q': qdec(q)}}
       for _, t, j, q, _ in kit._AXIS_CASES])
samples = json.loads((root / 'content/labs/L12-description.samples.v1.json').read_text(encoding='utf8'))
require(set(samples) == {'schema', 'kits'} and samples['schema'] == 'corelab-kit-samples/1',
        'samples schema')
require(list(samples['kits']) == ['L12-description'], 'samples must hold only L12-description')
require(samples['kits']['L12-description'] == expected_samples,
        'samples manifest does not mirror the self-check cases')
require(len(expected_samples) <= 50, 'kit sample cap is 50 (have ' + str(len(expected_samples)) + ')')


# ---- the hand tables against the independent quaternion/closed-form reference ----
def close(a, b, tol=1e-9):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


for label, t, expected in kit._PARSE_CASES:
    top, joints = kit._ref_model(t)
    require(top == expected['root'] and [j['name'] for j in joints] == [j['name'] for j in expected['joints']],
            'parse table disagrees with the reference reader: ' + label)
    for got, want in zip(joints, expected['joints']):
        require(all(got[k] == want[k] for k in ('type', 'parent', 'child'))
                and all(close(got[k], want[k], 1e-12) for k in ('xyz', 'rpy', 'axis')),
                'parse table row disagrees: ' + label)
for label, t, link, q, want in kit._LINK_CASES:
    ref = kit._ref_frames(t, q)[link]
    expected = want(link, q)
    require(all(close(ref[i], expected[i]) for i in range(4)),
            'link table disagrees with the reference: ' + label)
for label, t, a, b, q, want in kit._LOOKUP_CASES:
    ref, expected = kit._look(t, a, b, q), want(q)
    require(all(close(ref[i], expected[i]) for i in range(4)),
            'lookup table disagrees with the reference: ' + label)
for label, t, j, q, want in kit._AXIS_CASES:
    if want is not None:
        ref = kit._ref_axis(t, j, q)
        require(close(ref[0], want[0]) and close(ref[1], want[1]),
                'axis table disagrees with the reference: ' + label)
for label, a, want in kit._RPY_CASES:
    if want is not None:
        ref = kit._rpy_closed(*a)
        require(all(close(ref[i], want[i]) for i in range(3)), 'rpy table disagrees: ' + label)
    prod = kit._chain(kit._rz(a[2]), kit._ry(a[1]), kit._rx(a[0]))
    ref = kit._rpy_closed(*a)
    require(all(close(prod[i][:3], ref[i]) for i in range(3)), 'closed rpy differs from products')
for label, t in kit._BAD_TEXTS:
    require(isinstance(label, str) and isinstance(t, str), 'bad text table shape')


# ---- author reference implementation: flags give the injected bugs ----
def mul(a, b):
    return kit._mul(a, b)


def ident():
    return kit._tr(0.0, 0.0, 0.0)


def transpose3(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


def rot_h(rot, shift=(0.0, 0.0, 0.0)):
    return kit._h(rot, shift)


def gauss_inverse(t):
    """General 4x4 inverse by Gauss-Jordan elimination (no rigid shortcut)."""
    n = 4
    a = [list(t[i]) + [1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(a[r][c]))
        a[c], a[p] = a[p], a[c]
        d = a[c][c]
        a[c] = [v/d for v in a[c]]
        for r in range(n):
            if r != c:
                f = a[r][c]
                a[r] = [x - f*y for x, y in zip(a[r], a[c])]
    return [row[n:] for row in a]


class Ref:
    """Complete reference; class attributes are the knobs the mutants turn."""
    reject_doctype = True
    leak_parse_error = False
    check_root_tag = True
    unique_links = True
    unique_joints = True
    check_refs = True
    single_parent = True
    no_branch = True
    single_root = True
    reach_check = True
    reject_zero_axis = True
    normalise = True
    default_axis = (1.0, 0.0, 0.0)
    fixed_axis_zero = True
    allow_nonfinite = False
    check_bounds = True
    exact_three = True
    unknown_type_as_fixed = False
    origin_required = False
    swap_xyz_rpy = False
    document_order = False
    root_is_first_link = False
    allow_empty_name = False
    doctype_mode = 'both'
    max_links = 13
    max_name = 64
    text_max = 20000
    xyz_exclusive = False
    rpy_exclusive = False
    q_exclusive = False
    q_loose = 100
    bound_loose = 0
    first_child_only = False
    nested_joints = False
    strict_ignored_tags = False
    strict_joint_tags = False
    one_origin = True
    fixed_gets_axis_text = False
    # numbers and rotation
    rpy_order = 'zyx'
    rpy_swap_roll_yaw = False
    rpy_transpose = False
    rpy_degrees = False
    rpy_flip_pitch = False
    rpy_accept_bad_args = False
    rpy_closed = False
    # composition
    motion_first = False
    reverse_product = False
    flip_sign = False
    q_degrees = False
    swap_types = False
    ignore_axis = False
    skip_fixed = False
    ignore_rpy = False
    rotate_xyz = False
    revolute_other_hand = False
    # lookup and inverse
    lookup_swapped = False
    lookup_subtract = False
    inverse_mode = 'rigid'
    out_3x4 = False
    unknown_link_identity = False
    # axis
    axis_ignore_rpy = False
    axis_point_after_motion = False
    axis_raw = False
    axis_local = False
    axis_fixed_ok = False
    # q checks
    q_allow_missing = False
    q_allow_extra = False
    q_allow_fixed = False
    q_allow_bool = False
    q_allow_nan = False
    q_bound = True
    q_mutate = False
    q_allow_str_key = True
    tuples = False

    def __init__(self, **over):
        for key, value in over.items():
            require(hasattr(type(self), key), 'unknown knob ' + key)
            setattr(self, key, value)

    # ---- parse ----
    def check_name(self, name):
        if type(name) is not str or len(name) > self.max_name or (not name and not self.allow_empty_name):
            raise ValueError('name')

    def vec(self, s, default, bound):
        if s is None:
            return default
        parts = s.split()
        if self.exact_three and len(parts) != 3:
            raise ValueError('three numbers')
        values = tuple(float(v) for v in parts[:3])
        if not self.allow_nonfinite and not all(math.isfinite(v) for v in values):
            raise ValueError('finite')
        limit = bound + self.bound_loose
        if self.check_bounds and any((abs(v) >= limit if (self.xyz_exclusive and bound == 100)
                                      or (self.rpy_exclusive and bound == 10) else abs(v) > limit)
                                     for v in values):
            raise ValueError('bounds')
        return values

    def read(self, source):
        if type(source) is not str or not 1 <= len(source) <= self.text_max:
            raise ValueError('text')
        low = source.lower()
        if self.reject_doctype:
            mode = self.doctype_mode
            hit = {'both': '<!doctype' in low or '<!entity' in low,
                   'entity_only': '<!entity' in low,
                   'leading': source.lstrip().lower().startswith('<!doctype') or source.lstrip().startswith('<?xml') and '<!doctype' in low.split('?>', 1)[-1].lstrip()[:12],
                   'case_sensitive': '<!DOCTYPE' in source or '<!ENTITY' in source}[mode]
            if hit:
                raise ValueError('doctype')
        try:
            top = ET.fromstring(source)
        except ET.ParseError:
            if self.leak_parse_error:
                raise
            raise ValueError('xml')
        if self.check_root_tag and top.tag != 'robot':
            raise ValueError('root')
        if self.strict_ignored_tags and any(e.tag not in ('link', 'joint') for e in top):
            raise ValueError('unexpected tag')
        names = [e.get('name') for e in top.findall('link')]
        for n in names:
            self.check_name(n)
        if not 1 <= len(names) <= self.max_links or (self.unique_links and len(set(names)) != len(names)):
            raise ValueError('links')
        joints = []
        for e in (top.iter('joint') if self.nested_joints else top.findall('joint')):
            name, typ = e.get('name'), e.get('type')
            self.check_name(name)
            if typ not in ('revolute', 'prismatic', 'fixed'):
                if not self.unknown_type_as_fixed:
                    raise ValueError('type')
                typ = 'fixed'
            if self.strict_joint_tags and any(c.tag not in ('parent', 'child', 'origin', 'axis') for c in e):
                raise ValueError('unexpected joint tag')
            parents, children = e.findall('parent'), e.findall('child')
            if self.first_child_only:
                children = children[:1]
            origins, axes = e.findall('origin'), e.findall('axis')
            if len(parents) != 1 or len(children) != 1 or len(axes) > 1 \
                    or (self.one_origin and len(origins) > 1):
                raise ValueError('structure')
            if self.origin_required and not origins:
                raise ValueError('origin')
            zero = (0.0, 0.0, 0.0)
            o = origins[0] if origins else None
            xyz = self.vec(o.get('xyz') if o is not None else None, zero, 100)
            rpy = self.vec(o.get('rpy') if o is not None else None, zero, 10)
            if self.swap_xyz_rpy:
                xyz, rpy = rpy, xyz
            axis = zero
            if typ != 'fixed' or self.fixed_gets_axis_text:
                raw = self.vec(axes[0].get('xyz') if axes else None, self.default_axis, 100)
                n = math.sqrt(sum(v*v for v in raw))
                if n == 0 and self.reject_zero_axis:
                    raise ValueError('zero axis')
                axis = tuple(v/n for v in raw) if (self.normalise and n) else raw
            elif typ == 'fixed' and not self.fixed_axis_zero:
                axis = self.default_axis
            joints.append({'name': name, 'type': typ, 'parent': parents[0].get('link'),
                           'child': children[0].get('link'), 'xyz': xyz, 'rpy': rpy, 'axis': axis})
        jn = [j['name'] for j in joints]
        if self.unique_joints and len(set(jn)) != len(jn):
            raise ValueError('joint names')
        if self.check_refs and any(j['parent'] not in names or j['child'] not in names
                                   or j['parent'] == j['child'] for j in joints):
            raise ValueError('refs')
        if self.single_parent and len({j['child'] for j in joints}) != len(joints):
            raise ValueError('two parents')
        if self.no_branch and len({j['parent'] for j in joints}) != len(joints):
            raise ValueError('branching')
        kids = {j['child'] for j in joints}
        roots = list(dict.fromkeys(n for n in names if n not in kids))
        if self.root_is_first_link:
            roots = [names[0]]
        if (self.single_root and len(roots) != 1) or not roots:
            raise ValueError('roots')
        top_link = roots[0]
        return top_link, names, self.order(top_link, joints)

    def order(self, top_link, joints):
        if self.document_order:
            return list(joints)
        by_parent = {j['parent']: j for j in joints}
        ordered, at = [], top_link
        while at in by_parent and len(ordered) <= len(joints):
            ordered.append(by_parent[at])
            at = by_parent[at]['child']
        if self.reach_check and len(ordered) != len(joints):
            raise ValueError('unreached joints')
        return ordered

    # ---- rotations ----
    def rpy(self, roll, pitch, yaw):
        if not self.rpy_accept_bad_args:
            for v in (roll, pitch, yaw):
                if type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 10:
                    raise ValueError('angle')
        if self.rpy_swap_roll_yaw:
            roll, yaw = yaw, roll
        if self.rpy_degrees:
            roll, pitch, yaw = (math.radians(v) for v in (roll, pitch, yaw))
        if self.rpy_flip_pitch:
            pitch = -pitch
        if self.rpy_closed and self.rpy_order == 'zyx':
            r = kit._rpy_closed(roll, pitch, yaw)
        else:
            axes = {'x': kit._rx(roll), 'y': kit._ry(pitch), 'z': kit._rz(yaw)}
            r4 = kit._chain(*(axes[c] for c in self.rpy_order))
            r = [row[:3] for row in r4[:3]]
        return transpose3(r) if self.rpy_transpose else r

    def axis_rot(self, axis, angle):
        return kit._quat_rotation(axis, angle) if self.revolute_other_hand is False \
            else transpose3(kit._quat_rotation(axis, angle))

    # ---- transforms ----
    def origin_T(self, j):
        r = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]] if self.ignore_rpy else self.rpy(*j['rpy'])
        shift = j['xyz']
        if self.rotate_xyz:
            shift = tuple(sum(r[i][k]*j['xyz'][k] for k in range(3)) for i in range(3))
            return rot_h(r, shift)
        return rot_h(r, shift)

    def motion_T(self, j, value):
        typ = j['type']
        if typ == 'fixed':
            return ident()
        if self.swap_types:
            typ = 'prismatic' if typ == 'revolute' else 'revolute'
        if self.q_degrees:
            value = math.radians(value)
        if self.flip_sign:
            value = -value
        axis = j['axis']
        if self.ignore_axis:
            axis = (0.0, 0.0, 1.0)
        if typ == 'revolute':
            return rot_h(self.axis_rot(axis, value))
        return kit._tr(*(value*c for c in axis))

    def joint_T(self, j, value):
        o, m = self.origin_T(j), self.motion_T(j, value)
        return mul(m, o) if self.motion_first else mul(o, m)

    def check_q(self, joints, q):
        if not isinstance(q, dict):
            raise ValueError('q type')
        movable = [j['name'] for j in joints if j['type'] != 'fixed']
        fixed = [j['name'] for j in joints if j['type'] == 'fixed']
        for key in q:
            if type(key) is not str and not self.q_allow_str_key:
                raise ValueError('key')
            if key in fixed:
                if not self.q_allow_fixed:
                    raise ValueError('fixed key')
            elif key not in movable and not self.q_allow_extra:
                raise ValueError('unknown key')
        for name in movable:
            if name not in q:
                if not self.q_allow_missing:
                    raise ValueError('missing joint value')
                continue
            v = q[name]
            if type(v) is bool and self.q_allow_bool:
                continue
            if type(v) not in (int, float):
                raise ValueError('value type')
            if not math.isfinite(v) and not self.q_allow_nan:
                raise ValueError('finite')
            if self.q_bound and (abs(v) >= 100 if self.q_exclusive else abs(v) > self.q_loose):
                raise ValueError('bound')

    def frames(self, source, q):
        top, names, joints = self.read(source)
        self.check_q(joints, q)
        if self.q_mutate:
            q.pop(next(iter(q)), None)
        out = {top: ident()}
        cur = out[top]
        for j in joints:
            if j['type'] == 'fixed' and self.skip_fixed:
                out[j['child']] = cur
                continue
            step = self.joint_T(j, q.get(j['name'], 0.0))
            cur = mul(step, cur) if self.reverse_product else mul(cur, step)
            out[j['child']] = cur
        return out, joints

    def inverse(self, t):
        mode = self.inverse_mode
        rt = transpose3([row[:3] for row in t[:3]])
        p = [t[i][3] for i in range(3)]
        if mode == 'rigid':
            return rot_h(rt, [-sum(rt[i][k]*p[k] for k in range(3)) for i in range(3)])
        if mode == 'neg_t':
            return rot_h(rt, [-v for v in p])
        if mode == 'rt_t':
            return rot_h(rt, [sum(rt[i][k]*p[k] for k in range(3)) for i in range(3)])
        return gauss_inverse(t)

    def shape(self, t):
        rows = t[:3] if self.out_3x4 else t
        if self.tuples:
            return tuple(tuple(r) for r in rows)
        return [list(r) for r in rows]

    # ---- public API ----
    def parse_chain(self, source):
        top, names, joints = self.read(source)
        ordered_names = [top] + [j['child'] for j in joints]
        rows = []
        for j in joints:
            row = dict(j)
            if self.tuples:
                row = {k: (tuple(v) if isinstance(v, (list, tuple)) else v) for k, v in row.items()}
                row['note'] = 'extra keys are fine'
            else:
                row = {k: (list(v) if isinstance(v, tuple) else v) for k, v in row.items()}
            rows.append(row)
        return {'root': top, 'links': ordered_names if not self.document_order else names,
                'joints': rows}

    def rpy_matrix(self, roll, pitch, yaw):
        r = self.rpy(roll, pitch, yaw)
        return tuple(tuple(row) for row in r) if self.tuples else [list(row) for row in r]

    def link_transform(self, source, link, q):
        frames, joints = self.frames(source, q)
        if type(link) is not str or link not in frames:
            if self.unknown_link_identity and type(link) is str:
                return self.shape(ident())
            raise ValueError('link')
        return self.shape(frames[link])

    def lookup_transform(self, source, target, origin, q):
        frames, joints = self.frames(source, q)
        for f in (target, origin):
            if type(f) is not str or f not in frames:
                raise ValueError('frame')
        a, b = (origin, target) if self.lookup_swapped else (target, origin)
        if self.lookup_subtract:
            return self.shape(kit._tr(*(frames[b][i][3] - frames[a][i][3] for i in range(3))))
        return self.shape(mul(self.inverse(frames[a]), frames[b]))

    def joint_axis_in_base(self, source, joint, q):
        top, names, joints = self.read(source)
        self.check_q(joints, q)
        cur = ident()
        for j in joints:
            if j['name'] == joint and type(joint) is str:
                if j['type'] == 'fixed' and not self.axis_fixed_ok:
                    raise ValueError('fixed joint has no axis')
                o = mul(cur, self.origin_T(j))
                if self.axis_ignore_rpy:
                    o = mul(cur, rot_h([[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]], j['xyz']))
                if self.axis_point_after_motion:
                    o = mul(o, self.motion_T(j, q.get(joint, 0.0)))
                point = [o[i][3] for i in range(3)]
                ax = j['axis']
                if self.axis_raw:
                    ax = tuple(v*3 for v in ax)
                if self.axis_local:
                    return (tuple(point), tuple(ax))
                axis = tuple(sum(o[i][k]*ax[k] for k in range(3)) for i in range(3))
                return (tuple(point), axis) if self.tuples else (point, list(axis))
            cur = mul(cur, self.joint_T(j, q.get(j['name'], 0.0)))
        raise ValueError('joint')


# ---- valid alternatives: different formulations, same behaviour ----
class QuatAlt(Ref):
    """Quaternion rpy composition and axis-angle; recursive root-first walk; tuples."""
    tuples = True

    def rpy(self, roll, pitch, yaw):
        for v in (roll, pitch, yaw):
            if type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 10:
                raise ValueError('angle')

        def q_axis(ax, ang):
            s = math.sin(ang/2)
            return (math.cos(ang/2), ax[0]*s, ax[1]*s, ax[2]*s)

        def qmul(a, b):
            return (a[0]*b[0] - a[1]*b[1] - a[2]*b[2] - a[3]*b[3],
                    a[0]*b[1] + a[1]*b[0] + a[2]*b[3] - a[3]*b[2],
                    a[0]*b[2] - a[1]*b[3] + a[2]*b[0] + a[3]*b[1],
                    a[0]*b[3] + a[1]*b[2] - a[2]*b[1] + a[3]*b[0])
        w, x, y, z = qmul(qmul(q_axis((0, 0, 1), yaw), q_axis((0, 1, 0), pitch)),
                          q_axis((1, 0, 0), roll))
        return [[1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
                [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
                [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)]]

    def frames(self, source, q):
        top, names, joints = self.read(source)
        self.check_q(joints, q)

        def walk(k, parent_T, acc):
            acc[joints[k - 1]['child'] if k else top] = parent_T
            if k < len(joints):
                j = joints[k]
                walk(k + 1, mul(parent_T, self.joint_T(j, q.get(j['name'], 0.0))), acc)
            return acc
        return walk(0, ident(), {}), joints


class RodriguesAlt(Ref):
    """(R, p) pairs with Rodrigues' formula; lookup through R transpose; list outputs."""

    def axis_rot(self, axis, angle):
        n = math.sqrt(sum(v*v for v in axis))
        kx, ky, kz = (v/n for v in axis)
        k = [[0.0, -kz, ky], [kz, 0.0, -kx], [-ky, kx, 0.0]]
        k2 = [[sum(k[i][m]*k[m][j] for m in range(3)) for j in range(3)] for i in range(3)]
        s, c1 = math.sin(angle), 1 - math.cos(angle)
        return [[(1.0 if i == j else 0.0) + s*k[i][j] + c1*k2[i][j] for j in range(3)]
                for i in range(3)]

    def frames(self, source, q):
        top, names, joints = self.read(source)
        self.check_q(joints, q)
        out = {top: ident()}
        rot, pos = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]], [0.0, 0.0, 0.0]
        for j in joints:
            r0 = self.rpy(*j['rpy'])
            pos = [pos[i] + sum(rot[i][k]*j['xyz'][k] for k in range(3)) for i in range(3)]
            rot = [[sum(rot[i][k]*r0[k][c] for k in range(3)) for c in range(3)] for i in range(3)]
            value = q.get(j['name'], 0.0)
            if j['type'] == 'revolute':
                r1 = self.axis_rot(j['axis'], value)
                rot = [[sum(rot[i][k]*r1[k][c] for k in range(3)) for c in range(3)]
                       for i in range(3)]
            elif j['type'] == 'prismatic':
                pos = [pos[i] + sum(rot[i][k]*value*j['axis'][k] for k in range(3))
                       for i in range(3)]
            out[j['child']] = rot_h(rot, pos)
        return out, joints


class ExpmAlt(Ref):
    """Rotation by the matrix exponential series; lookup by Gauss-Jordan inverse."""
    inverse_mode = 'general'

    def axis_rot(self, axis, angle):
        n = math.sqrt(sum(v*v for v in axis))
        angle = math.fmod(angle, 2*math.pi)
        kx, ky, kz = (v*angle/n for v in axis)
        a = [[0.0, -kz, ky], [kz, 0.0, -kx], [-ky, kx, 0.0]]
        term = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
        total = [row[:] for row in term]
        for m in range(1, 45):
            term = [[sum(term[i][k]*a[k][j] for k in range(3))/m for j in range(3)]
                    for i in range(3)]
            total = [[total[i][j] + term[i][j] for j in range(3)] for i in range(3)]
        return total


class LeafUpAlt(Ref):
    """Kahn ordering, leaf-to-root accumulation and a lookup through the shallower frame."""

    def order(self, top_link, joints):
        pending, ordered, have = list(joints), [], {top_link}
        while pending:
            ready = [j for j in pending if j['parent'] in have]
            if len(ready) != 1:
                raise ValueError('not a chain')
            ordered.append(ready[0])
            have.add(ready[0]['child'])
            pending.remove(ready[0])
        return ordered

    def frames(self, source, q):
        top, names, joints = self.read(source)
        self.check_q(joints, q)
        out = {top: ident()}
        for k in range(len(joints)):
            acc = ident()
            for j in reversed(joints[:k + 1]):
                acc = mul(self.joint_T(j, q.get(j['name'], 0.0)), acc)
            out[joints[k]['child']] = acc
        return out, joints

    def lookup_transform(self, source, target, origin, q):
        frames, joints = self.frames(source, q)
        for f in (target, origin):
            if type(f) is not str or f not in frames:
                raise ValueError('frame')
        chain = [j['parent'] for j in joints] + [joints[-1]['child']] if joints else [list(frames)[0]]
        a, b = chain.index(target), chain.index(origin)
        if a == b:
            return self.shape(ident())
        lo, hi = min(a, b), max(a, b)
        acc = ident()
        for j in joints[lo:hi]:
            acc = mul(acc, self.joint_T(j, q.get(j['name'], 0.0)))
        return self.shape(acc if a < b else self.inverse(acc))


class LooseAlt(Ref):
    """Closed-form rpy, tuples, extra dict keys, int-friendly outputs, mapping-safe q."""
    tuples = True
    rpy_closed = True
    inverse_mode = 'general'


alternatives = [
    ('author reference: matrix products, quaternion axis-angle, rigid inverse', Ref()),
    ('quaternion rpy and axis-angle, recursive walk, tuple outputs with extra keys', QuatAlt()),
    ('(R, p) pairs with Rodrigues, lookup through the transpose', RodriguesAlt()),
    ('matrix exponential series for the rotation, Gauss-Jordan lookup', ExpmAlt()),
    ('Kahn ordering, leaf-to-root accumulation, lookup through the shallower frame',
     LeafUpAlt()),
    ('closed-form rpy, general inverse, tuples', LooseAlt()),
]


def install(impl):
    kit.parse_chain = impl.parse_chain
    kit.rpy_matrix = impl.rpy_matrix
    kit.link_transform = impl.link_transform
    kit.lookup_transform = impl.lookup_transform
    kit.joint_axis_in_base = impl.joint_axis_in_base


def run_with(impl):
    install(impl)
    return kit.self_check()


for label, impl in alternatives:
    result = run_with(impl)
    require(result == [], 'false reject (' + label + '): ' + str(result[:4]))


# ---- injected bugs: each must be rejected, for the intended reason ----
class ForwardOnlyLookup(Ref):
    """Computes T_base_source only and ignores the target frame."""
    def lookup_transform(self, source, target, origin, q):
        frames, joints = self.frames(source, q)
        for f in (target, origin):
            if type(f) is not str or f not in frames:
                raise ValueError('frame')
        return self.shape(frames[origin])


class RollAxisMixed(Ref):
    """rpy matrix with the roll sign wrong (a classic hand-expansion slip)."""
    def rpy(self, roll, pitch, yaw):
        Ref.rpy(self, roll, pitch, yaw)
        return [row[:3] for row in kit._chain(kit._rz(yaw), kit._ry(pitch), kit._rx(-roll))[:3]]


class ZeroNeverRaises(Ref):
    def check_q(self, joints, q):
        return None


class FirstJointOnly(Ref):
    """Joint motion only for the first movable joint."""
    def frames(self, source, q):
        top, names, joints = self.read(source)
        self.check_q(joints, q)
        out, cur, used = {top: ident()}, ident(), False
        for j in joints:
            value = q.get(j['name'], 0.0)
            if j['type'] != 'fixed':
                value = 0.0 if used else value
                used = True
            cur = mul(cur, self.joint_T(j, value))
            out[j['child']] = cur
        return out, joints


class PrismaticAsRevoluteSign(Ref):
    """Prismatic travel measured along the axis in the PARENT frame, after the origin rotation."""
    def joint_T(self, j, value):
        o = self.origin_T(j)
        if j['type'] == 'prismatic':
            shifted = [row[:] for row in o]
            for i in range(3):
                shifted[i][3] += value*j['axis'][i]
            return shifted
        return super().joint_T(j, value)


class AxisDefaultLeak(Ref):
    """Fixed joint axis reported as the default x axis."""
    fixed_axis_zero = False


class MissingIsError(Ref):
    origin_required = True


class RootFirstFile(Ref):
    root_is_first_link = True


class DictOrderQ(Ref):
    """Reads q positionally (values in dict order) instead of by joint name."""
    def frames(self, source, q):
        top, names, joints = self.read(source)
        self.check_q(joints, q)
        movable = [j['name'] for j in joints if j['type'] != 'fixed']
        by_position = dict(zip(movable, list(q.values())))
        out, cur = {top: ident()}, ident()
        for j in joints:
            cur = mul(cur, self.joint_T(j, by_position.get(j['name'], 0.0)))
            out[j['child']] = cur
        return out, joints


class BadLink(Ref):
    """link_transform returns the transform of the PARENT link."""
    def link_transform(self, source, link, q):
        frames, joints = self.frames(source, q)
        if type(link) is not str or link not in frames:
            raise ValueError('link')
        parent = {j['child']: j['parent'] for j in joints}
        return self.shape(frames[parent.get(link, link)])


class RoundedOutput(Ref):
    """Rounds every transform entry to 4 decimals."""
    def shape(self, t):
        return [[round(v, 4) for v in row] for row in t]


class AxisSignDrop(Ref):
    """joint_axis_in_base reports the axis with the parent rotation applied twice."""
    def joint_axis_in_base(self, source, joint, q):
        point, axis = super().joint_axis_in_base(source, joint, q)
        top, names, joints = self.read(source)
        cur = ident()
        for j in joints:
            if j['name'] == joint:
                break
            cur = mul(cur, self.joint_T(j, q.get(j['name'], 0.0)))
        twice = tuple(sum(cur[i][k]*axis[k] for k in range(3)) for i in range(3))
        return (point, twice)


class NegatedLookupShift(Ref):
    """Lookup whose translation column has the wrong sign."""
    def lookup_transform(self, source, target, origin, q):
        t = [list(r) for r in super().lookup_transform(source, target, origin, q)]
        for i in range(3):
            t[i][3] = -t[i][3]
        return t


class LinksReversed(Ref):
    """Link names listed tip first."""
    def parse_chain(self, source):
        out = super().parse_chain(source)
        out['links'] = list(reversed(out['links']))
        return out


class JointsAsNames(Ref):
    def parse_chain(self, source):
        out = super().parse_chain(source)
        out['joints'] = [row['name'] for row in out['joints']]
        return out


class AxisTextKeepsFixed(Ref):
    fixed_gets_axis_text = True


class FullyLenientQ(Ref):
    q_allow_missing = True
    q_allow_extra = True
    q_allow_fixed = True


mutants = [
    ('rpy order reversed (Rx*Ry*Rz)', Ref(rpy_order='xyz')),
    ('rpy order Rz*Rx*Ry', Ref(rpy_order='zxy')),
    ('rpy order Ry*Rx*Rz', Ref(rpy_order='yxz')),
    ('rpy arguments read as (yaw, pitch, roll)', Ref(rpy_swap_roll_yaw=True)),
    ('rpy returns the transpose (inverse rotation)', Ref(rpy_transpose=True)),
    ('rpy angles taken as degrees', Ref(rpy_degrees=True)),
    ('rpy pitch sign flipped', Ref(rpy_flip_pitch=True)),
    ('rpy roll sign slip in the expansion', RollAxisMixed()),
    ('rpy_matrix accepts NaN/bool/oversized angles', Ref(rpy_accept_bad_args=True)),
    ('xyz and rpy attributes swapped when parsing', Ref(swap_xyz_rpy=True)),
    ('joints reported and composed in file order', Ref(document_order=True)),
    ('root taken as the first link in the file', RootFirstFile()),
    ('axis not normalised', Ref(normalise=False)),
    ('missing axis defaults to z instead of x', Ref(default_axis=(0.0, 0.0, 1.0))),
    ('fixed joint reports the default axis', AxisDefaultLeak()),
    ('fixed joint reports the axis text', AxisTextKeepsFixed()),
    ('missing origin is an error', MissingIsError()),
    ('DOCTYPE and ENTITY accepted', Ref(reject_doctype=False)),
    ('ParseError leaks (not a ValueError)', Ref(leak_parse_error=True)),
    ('root tag not checked', Ref(check_root_tag=False)),
    ('duplicate link names accepted', Ref(unique_links=False)),
    ('duplicate joint names accepted', Ref(unique_joints=False)),
    ('undefined child link accepted', Ref(check_refs=False)),
    ('undefined parent link accepted (unreached joint ignored)', Ref(check_refs=False, reach_check=False)),
    ('a link with two parent joints accepted', Ref(single_parent=False, single_root=False, reach_check=False)),
    ('branching accepted (unreached joint ignored)', Ref(no_branch=False, reach_check=False)),
    ('several roots accepted (first one used)', Ref(single_root=False, reach_check=False)),
    ('unreached joints and cycles accepted', Ref(reach_check=False, single_root=False)),
    ('zero axis accepted', Ref(reject_zero_axis=False)),
    ('NaN and infinity accepted in numbers', Ref(allow_nonfinite=True)),
    ('number bounds not enforced', Ref(check_bounds=False)),
    ('only the first three numbers are used', Ref(exact_three=False)),
    ('unknown joint type treated as fixed', Ref(unknown_type_as_fixed=True)),
    ('empty names accepted', Ref(allow_empty_name=True)),
    ('unexpected sibling tags under <robot> rejected', Ref(strict_ignored_tags=True)),
    ('limit/dynamics tags under <joint> rejected', Ref(strict_joint_tags=True)),
    ('DOCTYPE gate rejects only <!ENTITY', Ref(doctype_mode='entity_only')),
    ('DOCTYPE gate rejects only a leading <!DOCTYPE', Ref(doctype_mode='leading')),
    ('DOCTYPE gate is case-sensitive (comments with lowercase markers pass)', Ref(doctype_mode='case_sensitive')),
    ('at most 14 links accepted', Ref(max_links=14)),
    ('link count not limited accepted', Ref(max_links=1000)),
    ('link limit lowered to 12', Ref(max_links=12)),
    ('names up to 65 characters accepted', Ref(max_name=65)),
    ('names limited to 63 characters', Ref(max_name=63)),
    ('text limit 20001 accepted', Ref(text_max=20001)),
    ('text limit 19999 only', Ref(text_max=19999)),
    ('xyz bound exclusive (100 rejected)', Ref(xyz_exclusive=True)),
    ('rpy bound exclusive (10 rejected)', Ref(rpy_exclusive=True)),
    ('numeric bounds loose by 0.5 accepted', Ref(bound_loose=0.5)),
    ('q bound exclusive (100 rejected)', Ref(q_exclusive=True)),
    ('q bound loose (100.5 accepted)', Ref(q_loose=100.5)),
    ('repeated child element accepted (first used)', Ref(first_child_only=True)),
    ('joints nested in other tags are parsed', Ref(nested_joints=True)),
    ('repeated origin element accepted', Ref(one_origin=False)),
    ('joint motion applied before the origin', Ref(motion_first=True)),
    ('chain product accumulated child-first', Ref(reverse_product=True)),
    ('revolute direction flipped', Ref(flip_sign=True)),
    ('joint values taken as degrees', Ref(q_degrees=True)),
    ('revolute and prismatic swapped', Ref(swap_types=True)),
    ('joint axis ignored (always z)', Ref(ignore_axis=True)),
    ('fixed joints skipped entirely', Ref(skip_fixed=True)),
    ('origin rpy ignored', Ref(ignore_rpy=True)),
    ('origin translation rotated by the origin rpy again', Ref(rotate_xyz=True)),
    ('revolute rotation applied with the wrong hand', Ref(revolute_other_hand=True)),
    ('prismatic travel measured in the parent frame', PrismaticAsRevoluteSign()),
    ('only the first movable joint moves', FirstJointOnly()),
    ('q read by position, not by joint name', DictOrderQ()),
    ('lookup direction swapped (source -> target)', Ref(lookup_swapped=True)),
    ('lookup subtracts translations only', Ref(lookup_subtract=True)),
    ('lookup ignores the target frame', ForwardOnlyLookup()),
    ('inverse keeps the sign of t but transposes R', Ref(inverse_mode='rt_t')),
    ('inverse negates t without rotating it', Ref(inverse_mode='neg_t')),
    ('lookup translation sign negated', NegatedLookupShift()),
    ('3x4 matrix returned', Ref(out_3x4=True)),
    ('unknown link answers the identity', Ref(unknown_link_identity=True)),
    ('link_transform returns the parent frame', BadLink()),
    ('entries rounded to 4 decimals', RoundedOutput()),
    ('joint axis ignores origin rpy', Ref(axis_ignore_rpy=True)),
    ('joint point taken after the joint motion', Ref(axis_point_after_motion=True)),
    ('joint axis not normalised in the base frame', Ref(axis_raw=True)),
    ('joint axis left in the joint frame', Ref(axis_local=True)),
    ('joint axis of a fixed joint accepted', Ref(axis_fixed_ok=True)),
    ('parent rotation applied twice to the axis', AxisSignDrop()),
    ('links list in reverse order', LinksReversed()),
    ('joints returned as names only', JointsAsNames()),
    ('missing joint value defaults to zero', Ref(q_allow_missing=True)),
    ('unknown joint name in q accepted', Ref(q_allow_extra=True)),
    ('q for a fixed joint accepted', Ref(q_allow_fixed=True)),
    ('bool joint value accepted', Ref(q_allow_bool=True)),
    ('NaN joint value accepted', Ref(q_allow_nan=True)),
    ('joint value bound not enforced', Ref(q_bound=False)),
    ('q dict mutated', Ref(q_mutate=True)),
    ('q not validated at all', ZeroNeverRaises()),
    ('q checks fully lenient', FullyLenientQ()),
]


def failing_reason(impl):
    install(impl)
    return kit.self_check()


for label, impl in mutants:
    result = failing_reason(impl)
    require(result, 'false accept: ' + label)
    validation = any(w in label for w in (' accepted', 'leaks', 'not enforced', 'lenient',
                                          'not validated', 'defaults to zero', 'first three', 'accepts', 'loose', 'limit 20001', 'gate rejects', 'gate is',
                                          'answers the identity', 'not checked', 'treated as fixed'))
    invalid_hit = any(f.startswith('invalid') for f in result)
    if validation:
        require(invalid_hit, 'validation bug caught for the wrong reason: ' + label)
    else:
        require(any(not f.startswith('invalid') for f in result),
                'behaviour bug caught for the wrong reason: ' + label)
    require(all(f.isascii() for f in result), 'non-ASCII message for ' + label)
install(alternatives[0][1])
require(kit.self_check() == [], 'reference must pass after the mutants')
print('Description kit: ' + str(len(alternatives)) + ' valid alternatives accepted, '
      + str(len(mutants)) + ' injected bugs rejected; starter fails as intended')
