"""Small planar geometry helpers for city-scale nearest-feature lookups (no I/O)."""

import math
from collections import defaultdict
from itertools import pairwise


def dist_m(lat1, lon1, lat2, lon2):
    x = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    return 6371000 * math.hypot(x, math.radians(lat2 - lat1))


def cell(lat, lon):
    """~1.2 km x ~1.2 km grid cell at Calgary's latitude."""
    return (int(lat * 90), int(lon * 60))


class PointIndex:
    """Grid index for nearest-point lookups; items need 'lat' and 'lon'."""

    def __init__(self, items):
        self.cells = defaultdict(list)
        for it in items:
            self.cells[cell(it["lat"], it["lon"])].append(it)

    def nearest(self, lat, lon, rings=2):
        ky, kx = cell(lat, lon)
        best, bd = None, float("inf")
        for dy in range(-rings, rings + 1):
            for dx in range(-rings, rings + 1):
                for it in self.cells.get((ky + dy, kx + dx), ()):
                    d = dist_m(lat, lon, it["lat"], it["lon"])
                    if d < bd:
                        best, bd = it, d
        return best, bd

    def within(self, lat, lon, radius_m, rings=1):
        """All items within radius_m, as (item, distance) pairs."""
        ky, kx = cell(lat, lon)
        out = []
        for dy in range(-rings, rings + 1):
            for dx in range(-rings, rings + 1):
                for it in self.cells.get((ky + dy, kx + dx), ()):
                    d = dist_m(lat, lon, it["lat"], it["lon"])
                    if d <= radius_m:
                        out.append((it, d))
        return out


def seg_dist_m(lat, lon, a, b):
    kx = 111320 * math.cos(math.radians(lat))
    ax, ay = (a[0] - lon) * kx, (a[1] - lat) * 110540
    bx, by = (b[0] - lon) * kx, (b[1] - lat) * 110540
    vx, vy = bx - ax, by - ay
    length2 = vx * vx + vy * vy
    t = 0 if length2 == 0 else max(0, min(1, -(ax * vx + ay * vy) / length2))
    return math.hypot(ax + t * vx, ay + t * vy)


class LineIndex:
    """Grid index over polyline segments; items need 'coords' as [[ [lon, lat], ... ], ...]."""

    def __init__(self, segments):
        self.cells = defaultdict(list)
        for seg in segments:
            for line in seg["coords"]:
                for a, b in pairwise(line):
                    for c in {cell(a[1], a[0]), cell(b[1], b[0])}:
                        self.cells[c].append((a, b, seg))

    def nearest(self, lat, lon, accept=None):
        ky, kx = cell(lat, lon)
        best, bd = None, float("inf")
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for a, b, seg in self.cells.get((ky + dy, kx + dx), ()):
                    if accept and not accept(seg):
                        continue
                    d = seg_dist_m(lat, lon, a, b)
                    if d < bd:
                        best, bd = seg, d
        return best, bd
