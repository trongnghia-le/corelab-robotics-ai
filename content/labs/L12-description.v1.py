"""CoreLab Robot Description (URDF chain and TF) lab - original MIT code, Copyright (c) 2026 Le Trong Nghia.

MANUAL SELF-CHECK ONLY. No signed evidence, verified I or robot permission.
Implement the five functions below, then run your edited file locally:
  Windows: py -3 L12-description.v1.py
  macOS/Linux: python3 L12-description.v1.py (or python)
Python 3 standard library only. Run only code you trust; no isolation is provided.
Parsing the XML TEXT you are given with xml.etree.ElementTree is fine
(ET.fromstring(text)); never open a file or fetch anything. ET's ParseError is a
SyntaxError, NOT a ValueError: catch it and raise ValueError yourself.

The description format is a small URDF-like subset (a serial chain only):
  <robot name="r">
    <link name="base"/> ...
    <joint name="j1" type="revolute|prismatic|fixed">
      <parent link="base"/> <child link="upper"/>
      <origin xyz="x y z" rpy="roll pitch yaw"/>      (optional, default zeros)
      <axis xyz="ax ay az"/>                            (optional, default 1 0 0)
    </joint> ...
  </robot>
Numbers: three whitespace-separated finite decimals (exponents allowed); xyz in
metres, rpy in radians, |xyz| <= 100, |rpy| <= 10 per component. Anything else
under <robot>, <link> or <joint> (visual, collision, inertial, material, limit,
dynamics, mimic, transmission, ...) is IGNORED and not validated; mesh files are
never loaded; limits are not enforced and a mimic tag is not applied. Joint
types "continuous", "floating" and "planar" are outside this lab: ValueError.
Names are non-empty strings of at most 64 characters. At most 13 links.
Only DIRECT children of <robot> count as links and joints: a <joint> nested
inside, say, <transmission> or <gazebo> is ignored. A <joint> needs exactly one
<parent> and one <child>.

Conventions (state them in your own notes; another library may differ):
  * rpy is FIXED-AXIS roll-pitch-yaw: R = Rz(yaw) * Ry(pitch) * Rx(roll), i.e.
    rotate about the parent x axis by roll first, then about the parent y axis
    by pitch, then about the parent z axis by yaw. Right-handed, counter-
    clockwise positive.
  * A joint's frame is its child link's frame. Joint origin = the child frame
    at joint value 0, expressed in the parent frame: T_origin = [R(rpy) | xyz].
    The axis is a direction in the JOINT frame (unchanged by the joint's own
    motion). Joint motion comes AFTER the origin:
        T_parent_child = T_origin * T_motion(q)
        revolute:  T_motion = rotation by q radians about the unit axis
        prismatic: T_motion = translation by q metres along the unit axis
        fixed:     T_motion = identity (a q is not accepted for it)
  * T_a_b (4x4) maps coordinates in frame b to coordinates in frame a:
    p_a = T_a_b * p_b. The BASE frame is the root link's frame. A TF lookup
    "lookup_transform(target, source)" returns T_target_source, so
    T_target_source = inverse(T_base_target) * T_base_source.

Contracts (text is a str of 1..20000 characters; q is a dict {joint name: value}
holding EXACTLY the revolute and prismatic joints, each a finite int/float,
never bool, |value| <= 100 (rad or m); bounds inclusive):
  parse_chain(text) -> dict with keys
        "root":   name of the one link that is nobody's child
        "links":  list of link names, root first, then following the chain
        "joints": list of dicts in CHAIN order (root side first, NOT file
                  order), each with keys "name", "type", "parent", "child",
                  "xyz" (3 numbers), "rpy" (3 numbers) and "axis" (3 numbers).
                  The axis is NORMALISED to unit length (a text axis such as
                  "0 3 4" gives (0, 0.6, 0.8)); a revolute or prismatic joint
                  with no <axis> gets (1, 0, 0); a fixed joint always reports
                  (0, 0, 0). A missing <origin> or missing xyz/rpy means zeros.
      Raise ValueError (never return a partial answer) for: text that is not
      well-formed XML or whose root element is not <robot>; a DOCTYPE or ENTITY
      declaration (rejected up front, in any letter case and anywhere in the
      text, even inside a comment or CDATA section - conservative on purpose;
      entities are never expanded); a missing
      or duplicate link or joint name; a joint without type, parent, child, or
      with a repeated parent/child/origin/axis element; an unknown type; a
      parent or child that is not a defined link (including a joint whose
      parent equals its child); a link that is the child of two joints; a
      link with two child joints (branching); more than one root, or no root
      (a cycle), or links that the chain does not reach; a number list that
      does not have exactly three finite values; a zero-length axis on a
      revolute or prismatic joint; values out of the stated bounds.
      A robot with one link and no joints is valid.
  rpy_matrix(roll, pitch, yaw) -> 3x3 nested list/tuple R = Rz*Ry*Rx
      (finite int/float, |angle| <= 10 rad each). Orthonormal, det = +1.
  link_transform(text, link, q) -> 4x4 nested list/tuple T_base_link at joint
      values q. The root link gives the identity. Bottom row (0, 0, 0, 1).
      Unknown link, bad q (missing joint, extra or fixed-joint name, non-str
      key, non-dict, bad value) or bad text: ValueError. q is not modified.
  lookup_transform(text, target_frame, source_frame, q) -> 4x4 T_target_source
      as defined above; the same frame twice gives the identity.
  joint_axis_in_base(text, joint, q) -> (point, axis): two length-3 sequences,
      the joint frame's origin at motion 0 and its unit axis direction, both
      in the BASE frame (point = position of T_base_parent * T_origin; axis =
      R_base_parent * R_origin * axis). They depend on the joints ABOVE this
      one, not on its own value. A fixed joint has no axis: ValueError.
Tolerances (absolute): parsed numbers 1e-12; transform and axis entries 1e-9
(fixtures stay within a few metres). Any correct method is accepted: matrix
products, quaternions or Rodrigues for the rotation, walking the chain from the
root or from both frames up to a common ancestor for a lookup. Failure messages
name the case and the kind of mismatch, never the expected numbers. "your code
raised X on a VALID input" means the case is inside the contract and must
return; "invalid f(name=...)" lines are the opposite: that input must raise
ValueError. A function still raising NotImplementedError is reported once.

Pause before coding - write your predictions down first:
  1. rpy = (pi/2, 0, pi/2): which matrix is it, and what changes if the order
     were Rx*Rz instead of Rz*Rx? Write both and compare the first column.
  2. A joint has origin rpy = (pi/2, 0, 0) and axis (0, 0, 1). Which direction
     is the axis in the parent frame? Which way does the child point after q?
  3. Why does the transform between two NON-root links not depend on the
     joints above the upper one? What does it depend on?
  4. For a planar chain of z-axis joints, what do your numbers have to equal
     (compare with your L02 planar_2r)? Passing that alone proves little:
     which parts of the code does a planar chain never exercise?
  5. If a transform comes out as the INVERSE of what you wanted, which single
     line in lookup_transform decides the direction?
  6. List three ways a text can fail structurally. Which of them does an
     element-by-element reader miss unless you check it on purpose?
Self-check tolerances are per-case numbers, not physical accuracy.
This kit covers a numerical description-and-transform replay only: no meshes,
inertia, collision geometry, xacro/macros, ROS 2 or TF2 runtime, message
timestamps or interpolation, robot_state_publisher, visualisation, branching
trees, joint limits or hardware.
Reflection: why does passing this toy NOT validate a real robot description?
(Think about measured link offsets versus CAD numbers, joint zero offsets and
calibration, mimic and transmission ratios, floating and continuous joints,
branching trees and tool frames, REP-103 frame conventions, mesh scale and
units, time stamps and interpolation in a live TF tree, and checking a model
against the physical robot.)
"""
import math
import xml.etree.ElementTree as ET


def parse_chain(text):
    raise NotImplementedError("Parse links and joints, validate the structure, order the joints root-first")


def rpy_matrix(roll, pitch, yaw):
    raise NotImplementedError("Rz(yaw) * Ry(pitch) * Rx(roll)")


def link_transform(text, link, q):
    raise NotImplementedError("Accumulate origin then motion joint by joint from the root")


def lookup_transform(text, target_frame, source_frame, q):
    raise NotImplementedError("inverse(T_base_target) * T_base_source, or walk to a common ancestor")


def joint_axis_in_base(text, joint, q):
    raise NotImplementedError("Rotate the declared axis by the frames above the joint")


# ---- SPOILER BELOW: the reference parser/transforms and the case tables hold ----
# ---- expected answers. Attempt the functions first. ----


class _Mismatch(Exception):
    """Kit-side check failure. Messages never reveal the expected values."""


def _real(value):
    return type(value) in (int, float) and math.isfinite(value)


def _vector(value, length):
    return (isinstance(value, (list, tuple)) and len(value) == length
            and all(_real(v) for v in value))


def _mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))]
            for i in range(len(a))]


def _chain(*mats):
    out = mats[0]
    for m in mats[1:]:
        out = _mul(out, m)
    return out


def _tr(x, y, z):
    return [[1.0, 0.0, 0.0, x], [0.0, 1.0, 0.0, y], [0.0, 0.0, 1.0, z], [0.0, 0.0, 0.0, 1.0]]


def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return [[1.0, 0.0, 0.0, 0.0], [0.0, c, -s, 0.0], [0.0, s, c, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0.0, s, 0.0], [0.0, 1.0, 0.0, 0.0], [-s, 0.0, c, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0.0, 0.0], [s, c, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _rpy_closed(r, p, y):
    """Fully expanded Rz(y)*Ry(p)*Rx(r): a different route from products of matrices."""
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p), math.sin(p),
                              math.cos(y), math.sin(y))
    return [[cy*cp, cy*sp*sr - sy*cr, cy*sp*cr + sy*sr],
            [sy*cp, sy*sp*sr + cy*cr, sy*sp*cr - cy*sr],
            [-sp, cp*sr, cp*cr]]


def _quat_rotation(axis, angle):
    """Rotation matrix of a unit quaternion (cos(a/2), sin(a/2)*axis)."""
    n = math.sqrt(sum(v*v for v in axis))
    u = [v/n for v in axis]
    w, s = math.cos(angle/2), math.sin(angle/2)
    x, y, z = u[0]*s, u[1]*s, u[2]*s
    return [[1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
            [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
            [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)]]


def _h(rot, shift):
    return [list(rot[0]) + [shift[0]], list(rot[1]) + [shift[1]],
            list(rot[2]) + [shift[2]], [0.0, 0.0, 0.0, 1.0]]


def _inv_rigid(t):
    rt = [[t[j][i] for j in range(3)] for i in range(3)]
    p = [-sum(rt[i][k]*t[k][3] for k in range(3)) for i in range(3)]
    return _h(rt, p)


def _nums(s):
    return tuple(float(v) for v in s.split())


def _ref_model(text):
    """Reference reader for VALID texts: joints in chain order, floats, unit axes."""
    root = ET.fromstring(text)
    names = [e.get("name") for e in root.findall("link")]
    joints = []
    for e in root.findall("joint"):
        o, a = e.find("origin"), e.find("axis")
        typ = e.get("type")
        xyz = _nums(o.get("xyz", "0 0 0")) if o is not None else (0.0, 0.0, 0.0)
        rpy = _nums(o.get("rpy", "0 0 0")) if o is not None else (0.0, 0.0, 0.0)
        if typ == "fixed":
            axis = (0.0, 0.0, 0.0)
        else:
            raw = _nums(a.get("xyz")) if a is not None else (1.0, 0.0, 0.0)
            n = math.sqrt(sum(v*v for v in raw))
            axis = tuple(v/n for v in raw)
        joints.append({"name": e.get("name"), "type": typ,
                       "parent": e.find("parent").get("link"),
                       "child": e.find("child").get("link"),
                       "xyz": xyz, "rpy": rpy, "axis": axis})
    children = {j["child"] for j in joints}
    top = [n for n in names if n not in children][0]
    by_parent = {j["parent"]: j for j in joints}
    ordered, at = [], top
    while at in by_parent:
        ordered.append(by_parent[at])
        at = by_parent[at]["child"]
    return top, ordered


def _ref_frames(text, q):
    """{link: T_base_link} by quaternion axis-angle and the closed-form rpy."""
    top, joints = _ref_model(text)
    frames = {top: _tr(0.0, 0.0, 0.0)}
    current = frames[top]
    for j in joints:
        origin = _h(_rpy_closed(*j["rpy"]), j["xyz"])
        value = q.get(j["name"], 0.0)
        if j["type"] == "revolute":
            motion = _h(_quat_rotation(j["axis"], value), (0.0, 0.0, 0.0))
        elif j["type"] == "prismatic":
            motion = _tr(*(value*c for c in j["axis"]))
        else:
            motion = _tr(0.0, 0.0, 0.0)
        current = _chain(current, origin, motion)
        frames[j["child"]] = current
    return frames


def _ref_axis(text, joint, q):
    top, joints = _ref_model(text)
    current = _tr(0.0, 0.0, 0.0)
    for j in joints:
        origin = _h(_rpy_closed(*j["rpy"]), j["xyz"])
        if j["name"] == joint:
            frame = _mul(current, origin)
            point = [frame[i][3] for i in range(3)]
            axis = [sum(frame[i][k]*j["axis"][k] for k in range(3)) for i in range(3)]
            return point, axis
        value = q.get(j["name"], 0.0)
        if j["type"] == "revolute":
            motion = _h(_quat_rotation(j["axis"], value), (0.0, 0.0, 0.0))
        elif j["type"] == "prismatic":
            motion = _tr(*(value*c for c in j["axis"]))
        else:
            motion = _tr(0.0, 0.0, 0.0)
        current = _chain(current, origin, motion)
    return None


def _fk_ref(a, b, c, d):
    """Planar L02 endpoint by angle-sum identities (independent of any chain code)."""
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
    return (c*ca + d*(ca*cb - sa*sb), c*sa + d*(sa*cb + ca*sb))


# ---- case texts ----
def _num(v):
    return repr(float(v))


def _xyz(v):
    return " ".join(_num(c) for c in v)


def _link(name):
    return '<link name="' + name + '"/>'


def _joint(name, typ, parent, child, xyz=None, rpy=None, axis=None, extra=""):
    body = '<parent link="' + parent + '"/><child link="' + child + '"/>'
    if xyz is not None or rpy is not None:
        body += "<origin" + (' xyz="' + xyz + '"' if xyz is not None else "") \
            + (' rpy="' + rpy + '"' if rpy is not None else "") + "/>"
    if axis is not None:
        body += '<axis xyz="' + axis + '"/>'
    return '<joint name="' + name + '" type="' + typ + '">' + body + extra + "</joint>"


def _robot(links, joints, head=""):
    return head + '<robot name="fixture">' + "".join(links) + "".join(joints) + "</robot>"


def _planar(l1, l2, shuffle=False):
    joints = [_joint("shoulder", "revolute", "base", "upper", "0 0 0", "0 0 0", "0 0 1"),
              _joint("elbow", "revolute", "upper", "fore", _xyz((l1, 0, 0)), "0 0 0", "0 0 1"),
              _joint("tool_mount", "fixed", "fore", "tool", _xyz((l2, 0, 0)))]
    links = [_link(n) for n in ("base", "upper", "fore", "tool")]
    if shuffle:
        joints.reverse()
        links.reverse()
    return _robot(links, joints)


_PAN_TILT = _robot(
    [_link(n) for n in ("camera", "head", "pan_link", "base")],
    [_joint("lens", "fixed", "head", "camera", "1 0 0"),
     _joint("tilt", "revolute", "pan_link", "head", "0 0 0", None, "0 1 0"),
     _joint("pan", "revolute", "base", "pan_link", "0 0 0.5", None, "0 0 1")])

_ARM3 = _robot(
    [_link(n) for n in ("base", "turret", "boom", "slider", "hand")],
    [_joint("tip", "fixed", "slider", "hand", "0.05 0.02 -0.04", "0 0 -0.6"),
     _joint("reach", "prismatic", "boom", "slider", "0.3 0 0.1", "0 0.5 0", "1 0 0"),
     _joint("turn", "revolute", "base", "turret", "0 0 0.25", "0 0 0.3", "0 0 1"),
     _joint("lift", "revolute", "turret", "boom", "0.1 0.05 0.2", "0.4 -0.3 0.2", "0 1 0")])

_WRIST = _robot(
    [_link(n) for n in ("base", "l1", "l2", "l3", "l4")],
    [_joint("r1", "revolute", "base", "l1", "0.1 -0.2 0.3", "0.2 0.1 -0.4", "1 2 2",
            "<limit lower=\"-3\" upper=\"3\" effort=\"1\" velocity=\"1\"/>"),
     _joint("p1", "prismatic", "l1", "l2", "0 0 0.5", None, "0 -3 4"),
     _joint("r2", "revolute", "l2", "l3", "0.2 0 0", "-0.5 0.6 0.9", "-1 0 0"),
     _joint("flange", "fixed", "l3", "l4", "0 0.1 0", "1.5708 0 0")])

_DEFAULTS = ('<?xml version="1.0"?>\n<!-- defaults -->\n<robot name="d">\n'
             '  <material name="grey"><color rgba="1 1 1 1"/></material>\n'
             '  <link name="a"><visual><geometry><mesh filename="a.stl"/></geometry></visual></link>\n'
             '  <link name="b"/>\n  <link name="c"/>\n'
             '  <joint name="j2" type="prismatic"><child link="c"/><parent link="b"/>'
             '<origin xyz="1e-1\t0.2\n0.3"/></joint>\n'
             '  <joint name="j1" type="revolute"><parent link="a"/><child link="b"/></joint>\n'
             '</robot>')

_ODD = _robot(
    [_link("m"), _link("n"), _link("o")],
    [_joint("fx", "fixed", "n", "o", "1 2 3", "0 0 1", "0 0 5", "<dynamics damping=\"1\"/>"),
     _joint("ax", "revolute", "m", "n", "0 0 0", None, "0 3 4")])


def _joint_row(name, typ, parent, child, xyz=(0.0, 0.0, 0.0), rpy=(0.0, 0.0, 0.0),
               axis=(0.0, 0.0, 0.0)):
    return {"name": name, "type": typ, "parent": parent, "child": child,
            "xyz": xyz, "rpy": rpy, "axis": axis}


_PLANAR_WANT = {"root": "base", "links": ["base", "upper", "fore", "tool"], "joints": [
    _joint_row("shoulder", "revolute", "base", "upper", axis=(0.0, 0.0, 1.0)),
    _joint_row("elbow", "revolute", "upper", "fore", xyz=(2.0, 0.0, 0.0), axis=(0.0, 0.0, 1.0)),
    _joint_row("tool_mount", "fixed", "fore", "tool", xyz=(1.0, 0.0, 0.0))]}
_PARSE_CASES = [
    ("planar 2R in chain order", _planar(2.0, 1.0), _PLANAR_WANT),
    ("planar 2R with joints and links listed tip first", _planar(2.0, 1.0, True), _PLANAR_WANT),
    ("single link, no joints", _robot([_link("solo")], []),
     {"root": "solo", "links": ["solo"], "joints": []}),
    ("defaults, comments, tabs, exponent, ignored mesh tag", _DEFAULTS,
     {"root": "a", "links": ["a", "b", "c"], "joints": [
         _joint_row("j1", "revolute", "a", "b", axis=(1.0, 0.0, 0.0)),
         _joint_row("j2", "prismatic", "b", "c", xyz=(0.1, 0.2, 0.3), axis=(1.0, 0.0, 0.0))]}),
    ("axis (0, 3, 4) is normalised; a fixed joint reports a zero axis", _ODD,
     {"root": "m", "links": ["m", "n", "o"], "joints": [
         _joint_row("ax", "revolute", "m", "n", axis=(0.0, 0.6, 0.8)),
         _joint_row("fx", "fixed", "n", "o", xyz=(1.0, 2.0, 3.0), rpy=(0.0, 0.0, 1.0))]}),
    ("spatial arm, joints in shuffled file order", _ARM3,
     {"root": "base", "links": ["base", "turret", "boom", "slider", "hand"], "joints": [
         _joint_row("turn", "revolute", "base", "turret", xyz=(0.0, 0.0, 0.25),
                    rpy=(0.0, 0.0, 0.3), axis=(0.0, 0.0, 1.0)),
         _joint_row("lift", "revolute", "turret", "boom", xyz=(0.1, 0.05, 0.2),
                    rpy=(0.4, -0.3, 0.2), axis=(0.0, 1.0, 0.0)),
         _joint_row("reach", "prismatic", "boom", "slider", xyz=(0.3, 0.0, 0.1),
                    rpy=(0.0, 0.5, 0.0), axis=(1.0, 0.0, 0.0)),
         _joint_row("tip", "fixed", "slider", "hand", xyz=(0.05, 0.02, -0.04),
                    rpy=(0.0, 0.0, -0.6))]}),
    ("wrist with tilted non-unit axes", _WRIST,
     {"root": "base", "links": ["base", "l1", "l2", "l3", "l4"], "joints": [
         _joint_row("r1", "revolute", "base", "l1", xyz=(0.1, -0.2, 0.3), rpy=(0.2, 0.1, -0.4),
                    axis=(1/3, 2/3, 2/3)),
         _joint_row("p1", "prismatic", "l1", "l2", xyz=(0.0, 0.0, 0.5), axis=(0.0, -0.6, 0.8)),
         _joint_row("r2", "revolute", "l2", "l3", xyz=(0.2, 0.0, 0.0), rpy=(-0.5, 0.6, 0.9),
                    axis=(-1.0, 0.0, 0.0)),
         _joint_row("flange", "fixed", "l3", "l4", xyz=(0.0, 0.1, 0.0), rpy=(1.5708, 0.0, 0.0))]}),
]

_P = math.pi
_RPY_CASES = [
    ("identity", (0, 0, 0), ((1, 0, 0), (0, 1, 0), (0, 0, 1))),
    ("yaw 90 degrees", (0.0, 0.0, _P/2), ((0, -1, 0), (1, 0, 0), (0, 0, 1))),
    ("roll 90 degrees", (_P/2, 0.0, 0.0), ((1, 0, 0), (0, 0, -1), (0, 1, 0))),
    ("pitch 90 degrees", (0.0, _P/2, 0.0), ((0, 0, 1), (0, 1, 0), (-1, 0, 0))),
    ("roll and yaw 90 degrees (order matters)", (_P/2, 0.0, _P/2),
     ((0, 0, 1), (1, 0, 0), (0, 1, 0))),
    ("generic angles", (0.4, -0.3, 0.2), None),
    ("generic large angles", (-1.2, 0.8, 2.5), None),
    ("bounds", (10.0, -10.0, 10.0), None),
]


def _hand_arm3(q, upto):
    """Elementary matrices multiplied by hand for the _ARM3 numbers (no text parsing)."""
    t1, t2, t3 = q["turn"], q["lift"], q["reach"]
    mats = [_tr(0, 0, 0.25), _rz(0.3), _rz(t1)]
    if upto >= 2:
        mats += [_tr(0.1, 0.05, 0.2), _rz(0.2), _ry(-0.3), _rx(0.4), _ry(t2)]
    if upto >= 3:
        mats += [_tr(0.3, 0, 0.1), _ry(0.5), _tr(t3, 0, 0)]
    if upto >= 4:
        mats += [_tr(0.05, 0.02, -0.04), _rz(-0.6)]
    return _chain(*mats)


def _hand_planar(l1, l2, q, upto):
    """Planar chain from the L02 angle-sum expansion: frame k has heading q1 + q2 ..."""
    heading = [0.0, q["shoulder"], q["shoulder"] + q["elbow"], q["shoulder"] + q["elbow"]][upto]
    x, y = [(0.0, 0.0), (0.0, 0.0), (l1*math.cos(q["shoulder"]), l1*math.sin(q["shoulder"])),
            _fk_ref(q["shoulder"], q["elbow"], l1, l2)][upto]
    c, s = math.cos(heading), math.sin(heading)
    return [[c, -s, 0.0, x], [s, c, 0.0, y], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def _ref_link(text):
    return lambda link, q: _ref_frames(text, q)[link]


_IDENT = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
_Q_P = {"shoulder": 0.7, "elbow": -1.1}
_Q_A = {"reach": 0.12, "turn": 0.9, "lift": -0.45}
_Q_W = {"r2": -1.3, "r1": 0.8, "p1": 0.15}
_Q_T = {"tilt": -0.8, "pan": 0.5}
_PL = _planar(0.6, 0.35)
_PLS = _planar(0.6, 0.35, True)
# (label, text, link, q, want(link, q) -> 4x4)
_LINK_CASES = [
    ("planar root is the identity", _PL, "base", _Q_P, lambda link, q: _IDENT),
    ("planar tool at a straight pose", _planar(2.0, 1.0), "tool", {"shoulder": 0.0, "elbow": 0.0},
     lambda link, q: [[1, 0, 0, 3], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
    ("planar tool, q1 = pi/2, q2 = -pi/2", _planar(2.0, 1.0), "tool",
     {"shoulder": _P/2, "elbow": -_P/2},
     lambda link, q: [[1, 0, 0, 1], [0, 1, 0, 2], [0, 0, 1, 0], [0, 0, 0, 1]]),
    ("planar tool, folded", _planar(2.0, 1.0), "tool", {"shoulder": 0.0, "elbow": _P},
     lambda link, q: [[-1, 0, 0, 1], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
    ("planar forearm, fresh joint values", _PL, "fore", _Q_P,
     lambda link, q: _hand_planar(0.6, 0.35, q, 2)),
    ("planar tool, fresh joint values (matches the L02 planar FK)", _PL, "tool", _Q_P,
     lambda link, q: _hand_planar(0.6, 0.35, q, 3)),
    ("planar tool, tip-first file order", _PLS, "tool", {"shoulder": -2.2, "elbow": 2.9},
     lambda link, q: _hand_planar(0.6, 0.35, q, 3)),
    ("pan-tilt camera, pan 90 degrees", _PAN_TILT, "camera", {"pan": _P/2, "tilt": 0.0},
     lambda link, q: [[0, -1, 0, 0], [1, 0, 0, 1], [0, 0, 1, 0.5], [0, 0, 0, 1]]),
    ("pan-tilt camera, tilt 90 degrees about y", _PAN_TILT, "camera", {"pan": 0.0, "tilt": _P/2},
     lambda link, q: [[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, -0.5], [0, 0, 0, 1]]),
    ("spatial arm, turret", _ARM3, "turret", _Q_A, lambda link, q: _hand_arm3(q, 1)),
    ("spatial arm, boom", _ARM3, "boom", _Q_A, lambda link, q: _hand_arm3(q, 2)),
    ("spatial arm, slider (prismatic)", _ARM3, "slider", _Q_A, lambda link, q: _hand_arm3(q, 3)),
    ("spatial arm, hand", _ARM3, "hand", _Q_A, lambda link, q: _hand_arm3(q, 4)),
    ("spatial arm, hand at zero", _ARM3, "hand", {"turn": 0.0, "lift": 0.0, "reach": 0.0},
     lambda link, q: _hand_arm3(q, 4)),
    ("spatial arm, hand, negative values", _ARM3, "hand", {"turn": -2.4, "lift": 1.7, "reach": -0.05},
     lambda link, q: _hand_arm3(q, 4)),
    ("wrist, tilted non-unit axes, l3", _WRIST, "l3", _Q_W, _ref_link(_WRIST)),
    ("wrist, tilted non-unit axes, l4", _WRIST, "l4", _Q_W, _ref_link(_WRIST)),
]
# lookup_transform: (label, text, target, source, q, want(q) -> 4x4)
def _look(text, target, source, q):
    frames = _ref_frames(text, q)
    return _mul(_inv_rigid(frames[target]), frames[source])


def _planar_between(l1, l2, q2):
    """Hand product Trans(l1, 0, 0) * Rz(q2) * Trans(l2, 0, 0): upper -> tool."""
    return _chain(_tr(l1, 0, 0), _rz(q2), _tr(l2, 0, 0))


_LOOKUP_CASES = [
    ("same frame twice", _PL, "fore", "fore", _Q_P, lambda q: _IDENT),
    ("fore -> tool is a fixed offset whatever the joints do", _PL, "fore", "tool", _Q_P,
     lambda q: _tr(0.35, 0, 0)),
    ("upper -> tool does not depend on the shoulder", _PL, "upper", "tool", _Q_P,
     lambda q: _planar_between(0.6, 0.35, q["elbow"])),
    ("tool seen from the base frame (inverse of the base -> tool chain)", _PL, "tool", "base", _Q_P,
     lambda q: _inv_rigid(_hand_planar(0.6, 0.35, q, 3))),
    ("base from the tool (direction check)", _PL, "base", "tool", _Q_P,
     lambda q: _hand_planar(0.6, 0.35, q, 3)),
    ("planar boundary pose, upper -> tool folded", _planar(2.0, 1.0), "upper", "tool",
     {"shoulder": 1.3, "elbow": _P}, lambda q: [[-1, 0, 0, 1], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
    ("spatial arm, turret from hand", _ARM3, "turret", "hand", _Q_A,
     lambda q: _mul(_inv_rigid(_hand_arm3(q, 1)), _hand_arm3(q, 4))),
    ("spatial arm, hand from boom", _ARM3, "hand", "boom", _Q_A,
     lambda q: _mul(_inv_rigid(_hand_arm3(q, 4)), _hand_arm3(q, 2))),
    ("spatial arm, slider from turret, other values", _ARM3, "slider", "turret",
     {"turn": -1.9, "lift": 0.6, "reach": 0.2},
     lambda q: _mul(_inv_rigid(_hand_arm3(q, 3)), _hand_arm3(q, 1))),
    ("wrist, l2 from l4", _WRIST, "l2", "l4", _Q_W, lambda q: _look(_WRIST, "l2", "l4", q)),
    ("wrist, l4 from base", _WRIST, "l4", "base", _Q_W, lambda q: _look(_WRIST, "l4", "base", q)),
]
# joint_axis_in_base: (label, text, joint, q, (point, axis) or None for the reference)
_AXIS_CASES = [
    ("planar shoulder axis", _PL, "shoulder", _Q_P, ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0))),
    ("pan-tilt: tilt axis after a 90 degree pan", _PAN_TILT, "tilt", {"pan": _P/2, "tilt": 0.3},
     ((0.0, 0.0, 0.5), (-1.0, 0.0, 0.0))),
    ("pan-tilt: pan axis", _PAN_TILT, "pan", _Q_T, ((0.0, 0.0, 0.5), (0.0, 0.0, 1.0))),
    ("planar elbow axis and point follow the shoulder", _PL, "elbow", _Q_P,
     ((0.6*math.cos(0.7), 0.6*math.sin(0.7), 0.0), (0.0, 0.0, 1.0))),
    ("spatial arm, lift", _ARM3, "lift", _Q_A, None),
    ("spatial arm, reach", _ARM3, "reach", _Q_A, None),
    ("wrist, r2", _WRIST, "r2", _Q_W, None),
]
_BAD_TEXTS = [
    ("not XML", "this is not xml"),
    ("unclosed tag", "<robot name='x'><link name='a'/>"),
    ("wrong root element", "<model><link name='a'/></model>"),
    ("DOCTYPE declaration", '<!DOCTYPE robot [<!ENTITY e "x">]><robot name="r"><link name="a"/></robot>'),
    ("lowercase doctype", '<!doctype robot><robot name="r"><link name="a"/></robot>'),
    ("undefined entity", '<robot name="r"><link name="&e;"/></robot>'),
    ("no links", '<robot name="r"/>'),
    ("link without a name", '<robot name="r"><link/></robot>'),
    ("empty link name", '<robot name="r"><link name=""/></robot>'),
    ("duplicate link", _robot([_link("a"), _link("a"), _link("b")], [_joint("j", "fixed", "a", "b")])),
    ("duplicate joint", _robot([_link("a"), _link("b"), _link("c")],
                               [_joint("j", "fixed", "a", "b"), _joint("j", "fixed", "b", "c")])),
    ("joint without type", _robot([_link("a"), _link("b")],
                                  ['<joint name="j"><parent link="a"/><child link="b"/></joint>'])),
    ("unknown joint type", _robot([_link("a"), _link("b")], [_joint("j", "screw", "a", "b")])),
    ("continuous joint (outside this lab)",
     _robot([_link("a"), _link("b")], [_joint("j", "continuous", "a", "b")])),
    ("joint without parent", _robot([_link("a"), _link("b")],
                                    ['<joint name="j" type="fixed"><child link="b"/></joint>'])),
    ("joint with two parent elements", _robot([_link("a"), _link("b")],
                                              ['<joint name="j" type="fixed"><parent link="a"/>'
                                               '<parent link="a"/><child link="b"/></joint>'])),
    ("parent link not defined", _robot([_link("a"), _link("b")], [_joint("j", "fixed", "zz", "b")])),
    ("child link not defined", _robot([_link("a"), _link("b")], [_joint("j", "fixed", "a", "b"),
                                                                   _joint("k", "fixed", "b", "zz")])),
    ("joint whose parent is its child", _robot([_link("a"), _link("b")],
                                               [_joint("j", "fixed", "a", "b"),
                                                _joint("k", "fixed", "b", "b")])),
    ("link that is the child of two joints", _robot([_link("a"), _link("b"), _link("c")],
                                                    [_joint("j", "fixed", "a", "c"),
                                                     _joint("k", "fixed", "b", "c")])),
    ("branching: one link with two child joints", _robot([_link("a"), _link("b"), _link("c")],
                                                         [_joint("j", "fixed", "a", "b"),
                                                          _joint("k", "fixed", "a", "c")])),
    ("two roots", _robot([_link("a"), _link("b"), _link("c"), _link("d")],
                         [_joint("j", "fixed", "a", "b"), _joint("k", "fixed", "c", "d")])),
    ("pure cycle, no root", _robot([_link("a"), _link("b"), _link("c")],
                                   [_joint("j", "fixed", "a", "b"), _joint("k", "fixed", "b", "c"),
                                    _joint("m", "fixed", "c", "a")])),
    ("a cycle next to a valid chain", _robot([_link("r"), _link("s"), _link("a"), _link("b")],
                                             [_joint("j", "fixed", "r", "s"),
                                              _joint("k", "fixed", "a", "b"),
                                              _joint("m", "fixed", "b", "a")])),
    ("isolated extra link", _robot([_link("a"), _link("b"), _link("x")], [_joint("j", "fixed", "a", "b")])),
    ("zero axis", _robot([_link("a"), _link("b")], [_joint("j", "revolute", "a", "b", None, None, "0 0 0")])),
    ("axis with two numbers", _robot([_link("a"), _link("b")], [_joint("j", "revolute", "a", "b", None, None, "0 1")])),
    ("axis element repeated", _robot([_link("a"), _link("b")], [_joint(
        "j", "revolute", "a", "b", None, None, "0 0 1", '<axis xyz="1 0 0"/>')])),
    ("NaN in xyz", _robot([_link("a"), _link("b")], [_joint("j", "fixed", "a", "b", "nan 0 0")])),
    ("infinity in rpy", _robot([_link("a"), _link("b")], [_joint("j", "fixed", "a", "b", "0 0 0", "0 inf 0")])),
    ("xyz with four numbers", _robot([_link("a"), _link("b")], [_joint("j", "fixed", "a", "b", "1 2 3 4")])),
    ("xyz with a xacro expression", _robot([_link("a"), _link("b")], [_joint("j", "fixed", "a", "b", "${l} 0 0")])),
    ("xyz out of bounds", _robot([_link("a"), _link("b")], [_joint("j", "fixed", "a", "b", "101 0 0")])),
    ("rpy out of bounds", _robot([_link("a"), _link("b")], [_joint("j", "fixed", "a", "b", "0 0 0", "0 0 10.5")])),
    ("origin repeated", _robot([_link("a"), _link("b")], [_joint(
        "j", "fixed", "a", "b", "0 0 0", None, None, '<origin xyz="1 0 0"/>')])),
]


def _pad(text, n):
    return text + " "*(n - len(text))


def _chain_links(count, first_name="l"):
    names = [first_name + str(i) for i in range(count)]
    joints = [_joint("j" + str(i), "fixed", names[i], names[i + 1], "0.1 0 0") for i in range(count - 1)]
    return names, joints


_N13, _J13 = _chain_links(13)
_N14, _J14 = _chain_links(14)
_BASIC = _robot([_link("a"), _link("b")], [_joint("j", "fixed", "a", "b")])
_BAD_TEXTS += [
    ("DOCTYPE without any ENTITY", '<!DOCTYPE robot><robot name="r"><link name="a"/></robot>'),
    ("comment, then DOCTYPE with an internal entity",
     '<!-- c --><!DOCTYPE robot [<!ENTITY e "x">]><robot name="r"><link name="a"/></robot>'),
    ("XML declaration, DOCTYPE and a nested entity chain",
     '<?xml version="1.0"?><!DOCTYPE robot [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;&a;">'
     '<!ENTITY c "&b;&b;&b;&b;">]><robot name="r"><link name="&c;"/></robot>'),
    ("parameter entity", '<!DOCTYPE robot [<!ENTITY % p "x"> %p;]><robot name="r"><link name="a"/></robot>'),
    ("external SYSTEM entity",
     '<!DOCTYPE robot [<!ENTITY x SYSTEM "file:///nonexistent/secret">]><robot name="r"><link name="&x;"/></robot>'),
    ("doctype words inside a comment are rejected too (conservative gate)",
     '<robot name="r"><!-- <!doctype x> --><link name="a"/></robot>'),
    ("entity words inside a comment are rejected too (conservative gate)",
     '<robot name="r"><!-- <!ENTITY e> --><link name="a"/></robot>'),
    ("14 links", _robot([_link(n) for n in _N14], _J14)),
    ("65-character link name", _robot([_link("n"*65), _link("b")], [_joint("j", "fixed", "n"*65, "b")])),
    ("65-character joint name", _robot([_link("a"), _link("b")], [_joint("j"*65, "fixed", "a", "b")])),
    ("text of 20001 characters", _pad(_BASIC, 20001)),
    ("repeated child element", _robot([_link("a"), _link("b"), _link("c")],
                                      [_joint("j", "fixed", "a", "b", None, None, None, '<child link="c"/>'),
                                       _joint("k", "fixed", "b", "c")])),
    ("xyz just above the bound", _robot([_link("a"), _link("b")], [_joint("j", "fixed", "a", "b", "100.0001 0 0")])),
    ("rpy just above the bound", _robot([_link("a"), _link("b")], [_joint("j", "fixed", "a", "b", "0 0 0", "10.0001 0 0")])),
    ("axis component above the bound", _robot([_link("a"), _link("b")], [_joint("j", "revolute", "a", "b", None, None, "100.5 0 0")])),
]
_NESTED = _robot([_link("a"), _link("b")], [_joint("j1", "fixed", "a", "b", "1 0 0"),
    '<transmission name="t"><type>x</type><joint name="j1"><hardwareInterface>p</hardwareInterface></joint></transmission>',
    '<gazebo><joint name="ghost" type="bogus"><parent link="nowhere"/></joint></gazebo>'])
_EDGE_PARSE = [
    ("13 links is the maximum", _robot([_link(n) for n in _N13], _J13), _N13),
    ("64-character names", _robot([_link("p"*64), _link("q"*64)], [_joint("j"*64, "fixed", "p"*64, "q"*64)]),
     ["p"*64, "q"*64]),
    ("text of exactly 20000 characters", _pad(_BASIC, 20000), ["a", "b"]),
    ("a nested joint inside transmission or gazebo is ignored", _NESTED, ["a", "b"]),
]
_EDGE_LINK = [
    ("xyz, rpy and axis at the inclusive bounds, q = 100",
     _robot([_link("a"), _link("b"), _link("c")],
            [_joint("r", "revolute", "a", "b", "100 -100 100", "10 -10 10", "100 0 0"),
             _joint("s", "prismatic", "b", "c", "0 0 0", None, "0 100 0")]),
     "c", {"r": 100, "s": -100}),
    ("q = -100 on a revolute joint", _planar(0.6, 0.35), "tool", {"shoulder": -100.0, "elbow": 100.0}),
]


def _raised(error):
    text = "your code raised " + type(error).__name__ + " on a VALID input (inside the contract"
    if isinstance(error, ValueError):
        return text + ": over-strict validation of text, names or q?)"
    return text + ")"


def _matrix_problem(got, want, tolerance):
    """None if the 4x4 matches, else a message that never shows expected values."""
    if not (isinstance(got, (list, tuple)) and len(got) == 4
            and all(_vector(row, 4) for row in got)):
        return "output must be a 4x4 nested list/tuple of finite int/float"
    if any(abs(got[3][j] - (1.0 if j == 3 else 0.0)) > 1e-12 for j in range(4)):
        return "bottom row must be (0, 0, 0, 1)"
    rot_bad = [(i, j) for i in range(3) for j in range(3)
               if not abs(got[i][j] - want[i][j]) <= tolerance]
    if rot_bad:
        if all(abs(got[j][i] - want[i][j]) <= tolerance for i in range(3) for j in range(3)):
            return ("rotation block is the TRANSPOSE of the right one (the inverse rotation:"
                    " check the direction of the transform)")
        return ("rotation block entry [" + str(rot_bad[0][0]) + "][" + str(rot_bad[0][1])
                + "] is wrong (" + str(len(rot_bad)) + " of 9 wrong, tolerance "
                + repr(tolerance) + ")")
    shift_bad = [i for i in range(3) if not abs(got[i][3] - want[i][3]) <= tolerance]
    if shift_bad:
        return ("rotation is right but translation entry " + "xyz"[shift_bad[0]]
                + " is wrong (tolerance " + repr(tolerance) + ")")
    return None


def _fresh_q(q):
    return dict(q)


def self_check(notes=None):
    """Return failure descriptions. These fixed author fixtures are practice only.

    Explicit checks only (no assert), so python -O cannot disable them.
    """
    failures = []
    calls, missing = {}, {}

    def attempt(name, label, function, args):
        calls[name] = calls.get(name, 0) + 1
        try:
            return True, function(*args)
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
        except Exception as error:
            failures.append(label + ": " + _raised(error))
        return False, None

    def run(label, function, args, compare):
        ok, got = attempt(label.split(" ")[0], label, function, args)
        if not ok:
            return
        try:
            compare(got)
        except _Mismatch as error:
            failures.append(label + ": " + str(error))
        except Exception as error:
            failures.append(label + ": the output could not be checked (" + type(error).__name__
                            + "); return the documented shape")

    def numbers(value, want, name, where):
        if not _vector(value, 3):
            raise _Mismatch(where + " " + name + " must be 3 finite int/float")
        if any(not abs(value[i] - want[i]) <= 1e-12 for i in range(3)):
            raise _Mismatch(where + " " + name + " is wrong (tolerance 1e-12)")

    for i, (label, text, want) in enumerate(_PARSE_CASES):
        def compare(got, want=want):
            if not (isinstance(got, dict) and "root" in got and "links" in got and "joints" in got):
                raise _Mismatch('output must be a dict with keys "root", "links", "joints"')
            if got["root"] != want["root"]:
                raise _Mismatch("root link is wrong")
            if not (isinstance(got["links"], (list, tuple)) and list(got["links"]) == want["links"]):
                raise _Mismatch("links must be the link names, root first, in chain order")
            joints = got["joints"]
            if not isinstance(joints, (list, tuple)) or len(joints) != len(want["joints"]):
                raise _Mismatch("joints must be a list with one dict per joint")
            for k, (row, expected) in enumerate(zip(joints, want["joints"])):
                where = "joint " + str(k)
                if not (isinstance(row, dict) and all(key in row for key in expected)):
                    raise _Mismatch(where + " must be a dict with name, type, parent, child,"
                                    " xyz, rpy, axis")
                for key in ("name", "type", "parent", "child"):
                    if row[key] != expected[key]:
                        raise _Mismatch(where + " (chain order, root side first) has a wrong "
                                        + key)
                for key in ("xyz", "rpy", "axis"):
                    numbers(row[key], expected[key], key, where)
        run("parse_chain " + str(i) + " (" + label + ")", parse_chain, (text,), compare)

    for i, (label, text, links) in enumerate(_EDGE_PARSE):
        def compare(got, links=links):
            if not (isinstance(got, dict) and isinstance(got.get("links"), (list, tuple))
                    and list(got["links"]) == links):
                raise _Mismatch("a valid description at a documented limit was not parsed"
                                " (or the ignored-tag rule was broken)")
        run("parse_chain edge " + str(i) + " (" + label + ")", parse_chain, (text,), compare)

    for i, (label, text, link, q) in enumerate(_EDGE_LINK):
        def compare(got, text=text, link=link, q=q):
            problem = _matrix_problem(got, _ref_frames(text, q)[link], 1e-9)
            if problem:
                raise _Mismatch(problem)
        run("link_transform edge " + str(i) + " (" + label + ")", link_transform,
            (text, link, dict(q)), compare)

    for i, (label, args, want) in enumerate(_RPY_CASES):
        def compare(got, args=args, want=want):
            if not (isinstance(got, (list, tuple)) and len(got) == 3
                    and all(_vector(row, 3) for row in got)):
                raise _Mismatch("output must be a 3x3 nested list/tuple of finite int/float")
            ref = want if want is not None else _rpy_closed(*args)
            if any(not abs(got[r][c] - ref[r][c]) <= 1e-9 for r in range(3) for c in range(3)):
                raise _Mismatch("rotation matrix differs (is it Rz(yaw)*Ry(pitch)*Rx(roll)?)")
            if want is None:
                for r in range(3):
                    for c in range(3):
                        dot = sum(got[r][k]*got[c][k] for k in range(3))
                        if not abs(dot - (1.0 if r == c else 0.0)) <= 1e-9:
                            raise _Mismatch("rows are not orthonormal")
        run("rpy_matrix " + str(i) + " (" + label + ")", rpy_matrix, args, compare)

    for i, (label, text, link, q, want) in enumerate(_LINK_CASES):
        def compare(got, text=text, link=link, q=q, want=want, call_q=None):
            problem = _matrix_problem(got, want(link, q), 1e-9)
            if problem:
                raise _Mismatch(problem)
        call_q = _fresh_q(q)

        def compare2(got, compare=compare, call_q=call_q, q=q):
            if call_q != q:
                raise _Mismatch("the q dict was modified")
            compare(got)
        run("link_transform " + str(i) + " (" + label + ")", link_transform,
            (text, link, call_q), compare2)

    for i, (label, text, target, source, q, want) in enumerate(_LOOKUP_CASES):
        call_q = _fresh_q(q)

        def compare(got, want=want, q=q, call_q=call_q):
            if call_q != q:
                raise _Mismatch("the q dict was modified")
            problem = _matrix_problem(got, want(q), 1e-9)
            if problem:
                raise _Mismatch(problem)
        run("lookup_transform " + str(i) + " (" + label + ")", lookup_transform,
            (text, target, source, call_q), compare)

    for i, (label, text, joint, q, want) in enumerate(_AXIS_CASES):
        call_q = _fresh_q(q)

        def compare(got, text=text, joint=joint, q=q, want=want, call_q=call_q):
            if call_q != q:
                raise _Mismatch("the q dict was modified")
            if not (isinstance(got, (list, tuple)) and len(got) == 2
                    and _vector(got[0], 3) and _vector(got[1], 3)):
                raise _Mismatch("output must be (point, axis), each 3 finite int/float")
            point, axis = want if want is not None else _ref_axis(text, joint, q)
            if any(not abs(got[0][k] - point[k]) <= 1e-9 for k in range(3)):
                raise _Mismatch("joint point in the base frame is wrong (tolerance 1e-9)")
            if any(not abs(got[1][k] - axis[k]) <= 1e-9 for k in range(3)):
                raise _Mismatch("joint axis in the base frame is wrong (tolerance 1e-9)")
        run("joint_axis_in_base " + str(i) + " (" + label + ")", joint_axis_in_base,
            (text, joint, call_q), compare)

    def expect_value_error(name, label, function, args):
        calls[name] = calls.get(name, 0) + 1
        try:
            function(*args)
        except ValueError:
            return
        except NotImplementedError:
            missing.setdefault(name, []).append(label)
            return
        except Exception as error:
            failures.append(label + ": raised " + type(error).__name__ + " instead of ValueError")
            return
        failures.append(label + ": returned instead of raising ValueError")

    for label, text in _BAD_TEXTS:
        expect_value_error("parse_chain", "invalid parse_chain(" + label + ")", parse_chain, (text,))
    for label, text in _BAD_TEXTS[:3] + _BAD_TEXTS[12:13] + _BAD_TEXTS[17:18]:
        expect_value_error("link_transform", "invalid link_transform(" + label + ")",
                           link_transform, (text, "a", {}))

    nan, inf = float("nan"), float("inf")
    text0, qp = _PL, {"shoulder": 0.2, "elbow": 0.3}
    bad_texts = [None, 5, True, b"<robot/>", ["<robot/>"], "", " ", "x" * 20001]
    bad_names = [None, 5, True, "", "nope", ["base"], "Base"]
    bad_q = [None, [], [("shoulder", 0.2), ("elbow", 0.3)], {}, {"shoulder": 0.2},
             {"shoulder": 0.2, "elbow": 0.3, "wrist": 0.1},
             {"shoulder": 0.2, "elbow": 0.3, "tool_mount": 0.0},
             {"shoulder": nan, "elbow": 0.3}, {"shoulder": inf, "elbow": 0.3},
             {"shoulder": True, "elbow": 0.3}, {"shoulder": "0.2", "elbow": 0.3},
             {"shoulder": None, "elbow": 0.3}, {"shoulder": 100.5, "elbow": 0.3}, {"shoulder": 100.0001, "elbow": 0.3},
             {"shoulder": 0.2, "elbow": -100.5}, {1: 0.2, "elbow": 0.3}]
    angle = [nan, inf, -inf, True, "0", None, 10.01, -10.01]
    calls_spec = [
        ("rpy_matrix", rpy_matrix, ("roll", "pitch", "yaw"), (0.1, 0.2, 0.3), {
            "roll": angle, "pitch": angle, "yaw": angle}),
        ("link_transform", link_transform, ("text", "link", "q"), (text0, "tool", qp), {
            "text": bad_texts, "link": bad_names, "q": bad_q}),
        ("lookup_transform", lookup_transform, ("text", "target", "source", "q"),
         (text0, "upper", "tool", qp), {
             "text": bad_texts, "target": bad_names, "source": bad_names, "q": bad_q}),
        ("joint_axis_in_base", joint_axis_in_base, ("text", "joint", "q"),
         (text0, "elbow", qp), {
             "text": bad_texts, "joint": bad_names + ["tool_mount", "tool"], "q": bad_q}),
    ]
    for title, function, slots, args, bad in calls_spec:
        for slot, name in enumerate(slots):
            for value in bad[name]:
                shown = repr(value)
                label = ("invalid " + title + "(" + name + "="
                         + (shown if len(shown) <= 24 else shown[:21] + "...") + ")")
                trial = args[:slot] + (value,) + args[slot + 1:]
                expect_value_error(title, label, function, trial)
    summary = []
    for name, labels in missing.items():
        if len(labels) < calls[name]:
            summary.append(name + ": raised NotImplementedError in " + str(len(labels)) + " of "
                           + str(calls[name]) + " checks (first: " + labels[0] + "); finish it")
        else:
            summary.append(name + ": not implemented yet (raises NotImplementedError; "
                           + str(calls[name]) + " checks skipped)")
    return summary + failures


if __name__ == "__main__":
    notes = []
    failures = self_check(notes)
    print("CoreLab manual robot-description self-check - practice only, no signed evidence")
    for note in notes:
        print("Note: " + note)
    if failures:
        print(str(len(failures)) + " failure(s):")
        for failure in failures:
            print("  - " + failure)
    else:
        print("Failures: none in this fixed fixture set")
    raise SystemExit(1 if failures else 0)
