"""Core parametric LED U-channel — the building block of the Mood ceiling artwork.

The physical part is a "channel-letter" tray: a flat aluminium back-plate with
return walls bent on edge along a path, and silicone LED neon-flex seated in the
slot, light facing down. We model it the same way it's built:

    back-plate (flat sheet)         z in [0, BACK_T]
    return walls (along path)       z in [-(WALL_H+NEON_H), 0]
    neon-flex (in the slot, mouth)  z in [-(WALL_H+NEON_H), -WALL_H]

All dimensions in millimetres. Tune NEON_W / SLOT_CLR with calibrate.py before
committing — the snap fit is product-dependent.
"""
from dataclasses import dataclass
from build123d import (
    BuildLine, BuildSketch, Spline, Polyline, CenterArc,
    trace, extrude, Pos, Plane,
)


@dataclass
class ChannelParams:
    neon_w: float = 16.0      # silicone neon-flex width (top view)
    neon_h: float = 16.0      # neon-flex height (into the slot)
    wall_t: float = 2.0       # aluminium return-wall thickness
    wall_h: float = 10.0      # wall shielding height above the neon face
    back_t: float = 3.0       # back-plate thickness
    slot_clr: float = 0.4     # per-side clearance neon <-> wall (snap fit)

    @property
    def inner_w(self) -> float:
        return self.neon_w + 2 * self.slot_clr

    @property
    def outer_w(self) -> float:
        return self.inner_w + 2 * self.wall_t

    @property
    def depth(self) -> float:
        return self.wall_h + self.neon_h


# ---- path helpers -----------------------------------------------------------
# A "path" is (kind, points): the centreline the channel follows in the XY plane.
#   ("spline",   [(x,y), ...])      smooth flowing line (figures)
#   ("polyline", [(x,y), ...])      straight segments (grid)
#   ("circle",   [(cx, cy, r)])     full ring (the columns)

def path_line(kind, points):
    with BuildLine() as ln:
        if kind == "spline":
            Spline(*[(x, y) for x, y in points])
        elif kind == "polyline":
            Polyline(*[(x, y) for x, y in points])
        elif kind == "circle":
            cx, cy, r = points[0]
            CenterArc((cx, cy), r, 0, 360)
        else:
            raise ValueError(f"unknown path kind: {kind}")
    return ln.line


# ---- solids -----------------------------------------------------------------

def walls(line, p: ChannelParams):
    """The aluminium return walls (the U, minus its back) extruded down."""
    outer = trace(line, line_width=p.outer_w)
    inner = trace(line, line_width=p.inner_w)
    ribbon = outer - inner
    return extrude(ribbon, amount=-p.depth)


def neon(line, p: ChannelParams):
    """The lit silicone neon tube, seated at the mouth (for the viewer/glow)."""
    tube = extrude(trace(line, line_width=p.neon_w), amount=-p.neon_h)
    return Pos(0, 0, -p.wall_h) * tube


def coupon(p: ChannelParams, length: float = 120.0):
    """A straight test segment: back-plate + walls + neon, for fit checks."""
    line = path_line("polyline", [(0, 0), (length, 0)])
    w = walls(line, p)
    n = neon(line, p)
    back = extrude(trace(line, line_width=p.outer_w), amount=p.back_t)
    return back + w, n
