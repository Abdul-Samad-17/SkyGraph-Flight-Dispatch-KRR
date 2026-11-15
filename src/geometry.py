"""Geometry helpers (pure Python, no external dependencies)."""
import math

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _orient(ax, ay, bx, by, cx, cy):
    v = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    if abs(v) < 1e-12:
        return 0
    return 1 if v > 0 else -1


def _on_segment(ax, ay, bx, by, px, py):
    return (min(ax, bx) - 1e-12 <= px <= max(ax, bx) + 1e-12 and
            min(ay, by) - 1e-12 <= py <= max(ay, by) + 1e-12)


def segments_intersect(p1, p2, p3, p4):
    """Closed-segment intersection test; points are (x, y) = (lon, lat)."""
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = p1, p2, p3, p4
    o1 = _orient(ax, ay, bx, by, cx, cy)
    o2 = _orient(ax, ay, bx, by, dx, dy)
    o3 = _orient(cx, cy, dx, dy, ax, ay)
    o4 = _orient(cx, cy, dx, dy, bx, by)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(ax, ay, bx, by, cx, cy):
        return True
    if o2 == 0 and _on_segment(ax, ay, bx, by, dx, dy):
        return True
    if o3 == 0 and _on_segment(cx, cy, dx, dy, ax, ay):
        return True
    if o4 == 0 and _on_segment(cx, cy, dx, dy, bx, by):
        return True
    return False


def point_in_polygon(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xin:
                inside = not inside
    return inside


def segment_crosses_polygon(p1, p2, poly):
    """True if the straight (lon/lat plane) segment touches/enters the polygon."""
    if point_in_polygon(p1, poly) or point_in_polygon(p2, poly):
        return True
    n = len(poly)
    for i in range(n):
        if segments_intersect(p1, p2, poly[i], poly[(i + 1) % n]):
            return True
    return False
