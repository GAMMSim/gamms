"""Geometric primitives for occlusion checks.

Each polygon stored in the graph engine represents a vertical prism: an
``(x, y)`` polygonal footprint extruded between ``base`` and
``base + height``. Sensor rays are tested against the *trapezoidal* faces
that make up the lateral walls of the prism, plus the polygon top (when
the ray descends through it from above).

The implementation deliberately favours clarity over micro-optimised
linear algebra so that the per-ray cost stays predictable when the polygon
count is small to moderate. For large maps callers should restrict the
candidate set spatially (e.g. via the polygon store's bounding-box index)
before invoking :func:`segment_blocked_by_polygons`.
"""

from typing import Iterable, Sequence, Tuple

Vec3 = Tuple[float, float, float]
Vec2 = Tuple[float, float]


def _segment_segment_intersect_2d(
    p: Vec2, r: Vec2, q: Vec2, s: Vec2
) -> bool:
    """Return True if 2D segments p->p+r and q->q+s intersect (proper or T)."""
    rxs = r[0] * s[1] - r[1] * s[0]
    qmp = (q[0] - p[0], q[1] - p[1])
    qmpxr = qmp[0] * r[1] - qmp[1] * r[0]

    if abs(rxs) < 1e-12:
        # Parallel - treat collinear overlap as a hit, otherwise miss.
        if abs(qmpxr) > 1e-12:
            return False
        rdotr = r[0] * r[0] + r[1] * r[1]
        if rdotr == 0:
            return False
        t0 = (qmp[0] * r[0] + qmp[1] * r[1]) / rdotr
        t1 = t0 + (s[0] * r[0] + s[1] * r[1]) / rdotr
        lo, hi = min(t0, t1), max(t0, t1)
        return hi >= 0.0 and lo <= 1.0

    t = (qmp[0] * s[1] - qmp[1] * s[0]) / rxs
    u = qmpxr / rxs
    return 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0


def segment_intersects_trapezoid(
    a: Vec3,
    b: Vec3,
    p1: Vec2,
    p2: Vec2,
    base: float,
    height: float,
) -> bool:
    """Return True if the 3D segment ``a-b`` crosses the trapezoidal face
    spanning the wall (p1, p2) between z=base and z=base+height.

    The face has four corners::

        (p1.x, p1.y, base) -- (p2.x, p2.y, base)
        (p1.x, p1.y, top ) -- (p2.x, p2.y, top )

    The wall lies in a vertical plane. Implementation: parametrise the ray
    with t in [0, 1], find the t where it crosses the (vertical) wall plane,
    and check whether the corresponding (u, z) point lies inside the
    trapezoid (u in [0, 1] along the wall, z in [base, top]).
    """
    top = base + height
    ax, ay, az = a
    bx, by, bz = b
    dx, dy, dz = bx - ax, by - ay, bz - az

    wx, wy = p2[0] - p1[0], p2[1] - p1[1]
    # Plane normal in xy: rotate w by 90 deg.
    nx, ny = -wy, wx
    denom = nx * dx + ny * dy
    rhs = nx * (p1[0] - ax) + ny * (p1[1] - ay)

    if abs(denom) < 1e-12:
        # Ray parallel to wall plane. If it's coplanar we still need to check
        # whether the projection touches the wall in z; treat near-parallel as
        # a miss because a parallel sensor ray skims the wall surface.
        return False

    t = rhs / denom
    if t < 0.0 or t > 1.0:
        return False

    # Solve for the point along the wall direction.
    wlen_sq = wx * wx + wy * wy
    if wlen_sq == 0.0:
        return False
    px = ax + t * dx
    py = ay + t * dy
    u = ((px - p1[0]) * wx + (py - p1[1]) * wy) / wlen_sq
    if u < 0.0 or u > 1.0:
        return False

    z = az + t * dz
    return base <= z <= top


def segment_intersects_polygon_top(
    a: Vec3,
    b: Vec3,
    polygon: Sequence[Vec2],
    base: float,
    height: float,
) -> bool:
    """Return True if the segment crosses the top face (z = base+height)
    inside the polygon footprint.
    """
    top = base + height
    az, bz = a[2], b[2]
    if (az - top) * (bz - top) > 0:
        return False
    if az == bz:
        return False
    t = (top - az) / (bz - az)
    if t < 0.0 or t > 1.0:
        return False
    px = a[0] + t * (b[0] - a[0])
    py = a[1] + t * (b[1] - a[1])
    return _point_in_polygon((px, py), polygon)


def _point_in_polygon(point: Vec2, polygon: Sequence[Vec2]) -> bool:
    x, y = point
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi):
            inside = not inside
        j = i
    return inside


def segment_blocked_by_polygon(
    a: Vec3,
    b: Vec3,
    polygon: Sequence[Vec2],
    base: float,
    height: float,
) -> bool:
    """True if the 3D segment a-b is blocked by the prism defined by
    ``polygon`` extruded between ``base`` and ``base+height``.

    A polygon with fewer than three vertices is silently ignored.
    """
    if len(polygon) < 3:
        return False

    if segment_intersects_polygon_top(a, b, polygon, base, height):
        return True
    n = len(polygon)
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        if segment_intersects_trapezoid(a, b, p1, p2, base, height):
            return True
    return False


def segment_blocked_by_polygons(
    a: Vec3,
    b: Vec3,
    polygons: Iterable,
) -> bool:
    """Return True if any of the supplied polygon prisms block the segment.

    ``polygons`` is an iterable of dicts with ``coords``, ``base`` and
    ``height`` keys (matching the format used by :class:`GraphEngine`).
    """
    for poly in polygons:
        coords = poly.get("coords") if isinstance(poly, dict) else poly[0]
        base = poly.get("base", 0.0) if isinstance(poly, dict) else poly[1]
        height = poly.get("height", 0.0) if isinstance(poly, dict) else poly[2]
        if segment_blocked_by_polygon(a, b, coords, base, height):
            return True
    return False
