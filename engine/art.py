"""Scene painters and the dotted world map.

Every painter receives a rectangle in page coordinates and works in
fractions of it (fx, fy in 0..1), so scenes scale cleanly between the
hero slots and the small card slots.  A scene is a place, an actor and
an action — never a lone glyph.
"""

from . import colours as C

SKIN = (222, 184, 150)
SKIN_D = (168, 122, 88)
HAIR = (38, 32, 28)


def _r(rect, fx, fy):
    x, y, w, h = rect
    return x + fx * w, y + fy * h


def _box(draw, rect, fx0, fy0, fx1, fy1, fill=None, outline=None, width=1):
    x0, y0 = _r(rect, fx0, fy0)
    x1, y1 = _r(rect, fx1, fy1)
    draw.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=width)


def _ellipse(draw, rect, fx0, fy0, fx1, fy1, fill=None, outline=None, width=1):
    x0, y0 = _r(rect, fx0, fy0)
    x1, y1 = _r(rect, fx1, fy1)
    draw.ellipse([x0, y0, x1, y1], fill=fill, outline=outline, width=width)


def _line(draw, rect, pts, fill, width=2):
    xy = [_r(rect, fx, fy) for fx, fy in pts]
    draw.line(xy, fill=fill, width=width, joint="curve")


def _poly(draw, rect, pts, fill=None, outline=None):
    xy = [_r(rect, fx, fy) for fx, fy in pts]
    draw.polygon(xy, fill=fill, outline=outline)


def person(draw, rect, fx, base, h, shirt, trousers, skin=SKIN,
           hair=HAIR, pose="stand"):
    """A standing figure: head, torso, legs, arms by pose.

    base = feet level (fraction), h = height (fraction of rect height).
    """
    w = rect[2]
    head_r = h * 0.11
    cx, by = _r(rect, fx, base)
    head_cy = by - h * rect[3] + head_r * rect[3] / rect[3] * 1.0
    # work in pixels for the figure so proportions hold at any slot size
    H = h * rect[3]
    head_cy = by - H + H * 0.10
    draw.ellipse([cx - H * 0.085, head_cy - H * 0.085,
                  cx + H * 0.085, head_cy + H * 0.085], fill=skin)
    draw.pieslice([cx - H * 0.088, head_cy - H * 0.095,
                   cx + H * 0.088, head_cy + H * 0.075],
                  start=180, end=360, fill=hair)
    neck = head_cy + H * 0.09
    hip = by - H * 0.42
    # torso
    draw.polygon([(cx - H * 0.11, neck), (cx + H * 0.11, neck),
                  (cx + H * 0.09, hip), (cx - H * 0.09, hip)], fill=shirt)
    # legs
    draw.line([cx - H * 0.04, hip, cx - H * 0.07, by], fill=trousers,
              width=max(2, int(H * 0.055)))
    draw.line([cx + H * 0.04, hip, cx + H * 0.07, by], fill=trousers,
              width=max(2, int(H * 0.055)))
    # arms
    aw = max(2, int(H * 0.05))
    if pose == "stand":
        draw.line([cx - H * 0.10, neck + H * 0.03, cx - H * 0.15, hip],
                  fill=shirt, width=aw)
        draw.line([cx + H * 0.10, neck + H * 0.03, cx + H * 0.15, hip],
                  fill=shirt, width=aw)
    elif pose == "vote":  # one arm forward, slipping a ballot in
        draw.line([cx - H * 0.10, neck + H * 0.03, cx - H * 0.15, hip],
                  fill=shirt, width=aw)
        draw.line([cx + H * 0.10, neck + H * 0.03, cx + H * 0.30,
                   neck + H * 0.16], fill=shirt, width=aw)
    elif pose == "raise":  # both arms up
        draw.line([cx - H * 0.10, neck + H * 0.03, cx - H * 0.20,
                   neck - H * 0.16], fill=shirt, width=aw)
        draw.line([cx + H * 0.10, neck + H * 0.03, cx + H * 0.20,
                   neck - H * 0.16], fill=shirt, width=aw)
    elif pose == "hold":  # holding a placard / document up
        draw.line([cx - H * 0.10, neck + H * 0.03, cx - H * 0.16,
                   neck - H * 0.10], fill=shirt, width=aw)
        draw.line([cx + H * 0.10, neck + H * 0.03, cx + H * 0.16,
                   neck - H * 0.10], fill=shirt, width=aw)


# ---------------------------------------------------------------- COP31
def scene_cop31(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=C.HALL)
    _box(draw, rect, 0, 0, 1, 0.16, fill=C.TEAL_DARK)
    # the big clock: the summit is waiting on two deadlines
    cx, cy = _r(rect, 0.845, 0.40)
    R = rect[3] * 0.30
    draw.ellipse([cx - R, cy - R, cx + R, cy + R], fill=C.WHITE,
                 outline=C.INK, width=3)
    for ang in range(0, 360, 30):
        import math
        x1 = cx + R * 0.86 * math.cos(math.radians(ang))
        y1 = cy + R * 0.86 * math.sin(math.radians(ang))
        x2 = cx + R * 0.97 * math.cos(math.radians(ang))
        y2 = cy + R * 0.97 * math.sin(math.radians(ang))
        draw.line([x1, y1, x2, y2], fill=C.INK, width=2)
    import math
    # hands at three o'clock: the objections deadline
    draw.line([cx, cy, cx + R * 0.78, cy], fill=C.RED, width=4)
    draw.line([cx, cy, cx, cy - R * 0.55], fill=C.INK, width=4)
    draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=C.INK)
    # delegates seated along the table, waiting — drawn before the
    # table so the tabletop hides their legs and they read as seated
    for i, fx in enumerate((0.10, 0.22, 0.34, 0.46, 0.58)):
        person(draw, rect, fx, 0.74, 0.40,
               shirt=(52, 64, 92) if i % 2 else (96, 60, 52),
               trousers=(40, 40, 48), skin=SKIN if i % 2 else SKIN_D)
    # long negotiating table: top, slim front, two legs
    _box(draw, rect, 0.04, 0.62, 0.70, 0.70, fill=(120, 88, 58))
    _box(draw, rect, 0.04, 0.70, 0.70, 0.79, fill=(146, 112, 76))
    _box(draw, rect, 0.06, 0.79, 0.09, 0.97, fill=(120, 88, 58))
    _box(draw, rect, 0.65, 0.79, 0.68, 0.97, fill=(120, 88, 58))
    # a stack of draft pages on the table
    _box(draw, rect, 0.615, 0.545, 0.685, 0.625, fill=C.WHITE, outline=C.INK)
    _line(draw, rect, [(0.625, 0.565), (0.675, 0.565)], fill=C.FAINT, width=1)
    _line(draw, rect, [(0.625, 0.585), (0.675, 0.585)], fill=C.FAINT, width=1)
    _line(draw, rect, [(0.625, 0.605), (0.665, 0.605)], fill=C.FAINT, width=1)


# ------------------------------------------------------------ Hong Kong
def scene_hongkong(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=(232, 222, 204))
    _box(draw, rect, 0, 0.78, 1, 1, fill=C.CONCRETE)
    # polling-station banner board (blank red board, no lettering)
    _box(draw, rect, 0.05, 0.06, 0.95, 0.24, fill=C.RED)
    _box(draw, rect, 0.05, 0.06, 0.95, 0.24, outline=C.INK, width=2)
    # ballot box
    _box(draw, rect, 0.56, 0.52, 0.86, 0.92, fill=(240, 238, 232),
         outline=C.INK, width=2)
    _box(draw, rect, 0.60, 0.545, 0.82, 0.575, fill=C.INK)
    _ellipse(draw, rect, 0.665, 0.68, 0.775, 0.84, fill=C.RED)
    # voter slipping the ballot in
    person(draw, rect, 0.40, 0.94, 0.52, shirt=C.TEAL, trousers=(44, 48, 60),
           pose="vote")
    # the ballot card in hand
    _box(draw, rect, 0.475, 0.60, 0.545, 0.685, fill=C.WHITE, outline=C.INK)
    # queue of voters behind
    person(draw, rect, 0.16, 0.95, 0.46, shirt=(120, 84, 60),
           trousers=(60, 60, 66), skin=SKIN_D)
    person(draw, rect, 0.26, 0.95, 0.42, shirt=(70, 84, 120),
           trousers=(50, 50, 56))


# -------------------------------------------------------------- cricket
def scene_cricket(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=C.SKY_DAY)
    _box(draw, rect, 0, 0.55, 1, 1, fill=C.GRASS)
    _box(draw, rect, 0.30, 0.62, 0.72, 1, fill=(206, 188, 150))  # pitch
    # stumps
    for fx in (0.335, 0.36, 0.385):
        _line(draw, rect, [(fx, 0.66), (fx, 0.86)], fill=C.GOLD, width=3)
    # batsman mid-drive
    person(draw, rect, 0.52, 0.90, 0.52, shirt=(240, 240, 238),
           trousers=(240, 240, 238), skin=SKIN_D, pose="vote")
    # bat
    _line(draw, rect, [(0.60, 0.52), (0.70, 0.70)], fill=(150, 116, 74),
          width=5)
    # ball flying away
    _ellipse(draw, rect, 0.80, 0.30, 0.845, 0.375, fill=C.RED)
    _line(draw, rect, [(0.70, 0.55), (0.79, 0.38)], fill=C.WHITE, width=2)
    # blank scoreboard (figures live in the text, not the scene)
    _box(draw, rect, 0.03, 0.06, 0.30, 0.34, fill=C.INK)
    _box(draw, rect, 0.055, 0.10, 0.275, 0.155, fill=(90, 100, 112))
    _box(draw, rect, 0.055, 0.19, 0.275, 0.245, fill=(90, 100, 112))
    _box(draw, rect, 0.055, 0.28, 0.20, 0.315, fill=(90, 100, 112))


# --------------------------------------------------------------- israel
def scene_israel(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=(226, 220, 206))
    _box(draw, rect, 0, 0.70, 1, 1, fill=C.CONCRETE)
    # doorway arch behind
    _box(draw, rect, 0.36, 0.10, 0.64, 0.72, fill=(206, 196, 174),
         outline=(150, 138, 116), width=2)
    # table with the mandate document
    _box(draw, rect, 0.18, 0.60, 0.82, 0.68, fill=(120, 88, 58))
    _box(draw, rect, 0.42, 0.47, 0.58, 0.60, fill=C.WHITE, outline=C.INK)
    _line(draw, rect, [(0.445, 0.505), (0.555, 0.505)], fill=C.FAINT, width=1)
    _line(draw, rect, [(0.445, 0.545), (0.535, 0.545)], fill=C.FAINT, width=1)
    # two men in suits shaking hands over the document
    person(draw, rect, 0.30, 0.92, 0.58, shirt=(36, 42, 58),
           trousers=(36, 42, 58), pose="vote")
    person(draw, rect, 0.70, 0.92, 0.58, shirt=(52, 52, 60),
           trousers=(52, 52, 60), skin=SKIN_D, pose="vote")


# ------------------------------------------------------------------- f1
def scene_f1(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=C.SKY_NIGHT)
    # floodlight pylons
    for fx in (0.12, 0.88):
        _line(draw, rect, [(fx, 0.10), (fx, 0.52)], fill=(150, 156, 168),
              width=3)
        _ellipse(draw, rect, fx - 0.05, 0.03, fx + 0.05, 0.12,
                 fill=(255, 244, 200))
    _box(draw, rect, 0, 0.62, 1, 1, fill=(52, 54, 62))  # asphalt
    _line(draw, rect, [(0, 0.80), (1, 0.80)], fill=C.WHITE, width=2)
    # grandstand block
    _box(draw, rect, 0.30, 0.30, 0.72, 0.55, fill=(44, 52, 74))
    for i in range(4):
        _line(draw, rect, [(0.31, 0.36 + i * 0.05), (0.71, 0.36 + i * 0.05)],
              fill=(86, 98, 124), width=2)
    # the car: low wedge body, wing, wheels
    _poly(draw, rect, [(0.16, 0.78), (0.30, 0.66), (0.62, 0.63),
                       (0.80, 0.74), (0.82, 0.80), (0.18, 0.82)],
          fill=(28, 92, 140))
    _box(draw, rect, 0.10, 0.60, 0.20, 0.80, fill=(20, 26, 36))  # rear wing
    _box(draw, rect, 0.78, 0.72, 0.90, 0.80, fill=(20, 26, 36))  # front wing
    _ellipse(draw, rect, 0.20, 0.76, 0.32, 0.94, fill=(16, 16, 20))
    _ellipse(draw, rect, 0.64, 0.76, 0.76, 0.94, fill=(16, 16, 20))
    _ellipse(draw, rect, 0.44, 0.585, 0.54, 0.665, fill=C.RED)  # helmet


# --------------------------------------------------------------- tennis
def scene_tennis(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=(52, 74, 110))
    _box(draw, rect, 0.04, 0.14, 0.96, 0.94, fill=(44, 96, 140))  # court
    _box(draw, rect, 0.04, 0.14, 0.96, 0.94, outline=C.WHITE, width=2)
    _line(draw, rect, [(0.5, 0.14), (0.5, 0.94)], fill=C.WHITE, width=2)
    _line(draw, rect, [(0.04, 0.54), (0.96, 0.54)], fill=C.WHITE, width=2)
    # net
    _box(draw, rect, 0.04, 0.50, 0.96, 0.565, fill=(20, 24, 32))
    # server, arm up, ball tossed
    person(draw, rect, 0.30, 0.88, 0.55, shirt=(240, 240, 240),
           trousers=(30, 40, 80), pose="raise")
    _ellipse(draw, rect, 0.335, 0.16, 0.375, 0.225, fill=(214, 226, 92))
    # racket
    _ellipse(draw, rect, 0.155, 0.24, 0.235, 0.40, outline=C.WHITE, width=2)
    _line(draw, rect, [(0.21, 0.38), (0.26, 0.50)], fill=(200, 200, 200),
          width=2)
    # receiver waiting
    person(draw, rect, 0.74, 0.80, 0.48, shirt=C.RED, trousers=(240, 240, 240),
           skin=SKIN_D, pose="hold")


# ------------------------------------------------------------ melbourne
def scene_melbourne(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=C.SKY_DAY)
    _box(draw, rect, 0, 0.66, 1, 1, fill=C.GRASS)
    # stadium bowl
    _poly(draw, rect, [(0.06, 0.42), (0.94, 0.42), (0.86, 0.78), (0.14, 0.78)],
          fill=(178, 172, 160))
    for i in range(3):
        fy = 0.50 + i * 0.085
        _line(draw, rect, [(0.10, fy), (0.90, fy)], fill=(140, 134, 122),
              width=2)
    _box(draw, rect, 0.06, 0.36, 0.94, 0.43, fill=(120, 116, 108))
    # light towers
    for fx in (0.16, 0.84):
        _line(draw, rect, [(fx, 0.36), (fx, 0.10)], fill=(90, 90, 96), width=3)
        _box(draw, rect, fx - 0.045, 0.045, fx + 0.045, 0.11,
             fill=(255, 244, 200), outline=(90, 90, 96))
    # cauldron and flame at centre
    _poly(draw, rect, [(0.44, 0.86), (0.56, 0.86), (0.52, 0.70),
                       (0.48, 0.70)], fill=(70, 70, 76))
    _poly(draw, rect, [(0.50, 0.44), (0.545, 0.60), (0.515, 0.70),
                       (0.485, 0.70), (0.455, 0.60)], fill=(240, 150, 44))
    _poly(draw, rect, [(0.50, 0.52), (0.525, 0.62), (0.50, 0.70),
                       (0.475, 0.62)], fill=(250, 200, 80))


# ------------------------------------------------------------- football
def scene_football(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=C.SKY_DUSK)
    _box(draw, rect, 0, 0.30, 1, 0.52, fill=(58, 64, 84))  # stand
    for i in range(3):
        _line(draw, rect, [(0.02, 0.35 + i * 0.055), (0.98, 0.35 + i * 0.055)],
              fill=(96, 104, 128), width=2)
    _box(draw, rect, 0, 0.52, 1, 1, fill=C.GRASS_DARK)
    _line(draw, rect, [(0.5, 0.52), (0.5, 1)], fill=C.WHITE, width=2)
    _ellipse(draw, rect, 0.42, 0.66, 0.58, 0.94, outline=C.WHITE, width=2)
    # two players contesting the ball
    person(draw, rect, 0.36, 0.92, 0.52, shirt=C.RED, trousers=C.WHITE,
           pose="raise")
    person(draw, rect, 0.62, 0.92, 0.52, shirt=(240, 240, 240),
           trousers=C.RED, skin=SKIN_D, pose="hold")
    _ellipse(draw, rect, 0.465, 0.80, 0.535, 0.895, fill=C.WHITE,
             outline=C.INK)


# ------------------------------------------------------------------ nfl
def scene_nfl(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=(40, 84, 52))
    for i in range(5):  # yard lines
        fx = 0.08 + i * 0.21
        _line(draw, rect, [(fx, 0.06), (fx, 0.94)], fill=(230, 236, 230),
              width=2)
    # quarterback mid-throw
    person(draw, rect, 0.38, 0.90, 0.56, shirt=(24, 52, 110),
           trousers=(240, 240, 240), pose="raise")
    _ellipse(draw, rect, 0.315, 0.20, 0.385, 0.315, fill=(240, 240, 240))
    # the ball in flight
    _ellipse(draw, rect, 0.62, 0.24, 0.70, 0.315, fill=(146, 84, 44))
    _line(draw, rect, [(0.50, 0.34), (0.60, 0.29)], fill=C.WHITE, width=2)
    # receiver running onto it
    person(draw, rect, 0.82, 0.86, 0.50, shirt=C.RED, trousers=(240, 240, 240),
           skin=SKIN_D, pose="raise")


# ---------------------------------------------------------------- nepal
def scene_nepal(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=C.SKY_DAY)
    # Himalaya ridge
    _poly(draw, rect, [(0, 0.52), (0.16, 0.22), (0.30, 0.44), (0.46, 0.14),
                       (0.60, 0.40), (0.74, 0.20), (0.88, 0.42), (1, 0.30),
                       (1, 0.52)], fill=(150, 164, 178))
    _poly(draw, rect, [(0.40, 0.235), (0.46, 0.14), (0.52, 0.235),
                       (0.485, 0.21), (0.46, 0.25), (0.435, 0.21)],
          fill=C.WHITE)
    _poly(draw, rect, [(0.685, 0.285), (0.74, 0.20), (0.795, 0.285),
                       (0.765, 0.26), (0.74, 0.29), (0.715, 0.26)],
          fill=C.WHITE)
    _box(draw, rect, 0, 0.66, 1, 1, fill=C.CONCRETE)  # runway
    _line(draw, rect, [(0, 0.83), (1, 0.83)], fill=C.WHITE, width=2)
    # airliner on finals
    _poly(draw, rect, [(0.30, 0.52), (0.62, 0.46), (0.68, 0.50),
                       (0.64, 0.56), (0.34, 0.60)], fill=(238, 240, 244))
    _poly(draw, rect, [(0.30, 0.52), (0.22, 0.40), (0.28, 0.40),
                       (0.36, 0.50)], fill=C.RED)  # tail
    _poly(draw, rect, [(0.44, 0.55), (0.52, 0.68), (0.58, 0.68),
                       (0.54, 0.54)], fill=(200, 206, 214))  # wing
    for i in range(6):
        _ellipse(draw, rect, 0.40 + i * 0.035, 0.515, 0.415 + i * 0.035,
                 0.545, fill=(70, 90, 120))


# -------------------------------------------------------------- lebanon
def scene_lebanon(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=C.SKY_DAY)
    _box(draw, rect, 0, 0.80, 1, 1, fill=C.CONCRETE)
    # flagpole
    cx, top = _r(rect, 0.5, 0.10)
    bx, base = _r(rect, 0.5, 0.92)
    draw.line([cx, top, bx, base], fill=(90, 90, 96), width=4)
    # the flag: red-white-red with a green cedar
    _box(draw, rect, 0.5, 0.10, 0.86, 0.235, fill=C.RED)
    _box(draw, rect, 0.5, 0.235, 0.86, 0.37, fill=C.WHITE)
    _box(draw, rect, 0.5, 0.37, 0.86, 0.50, fill=C.RED)
    _poly(draw, rect, [(0.68, 0.265), (0.715, 0.335), (0.68, 0.315),
                       (0.645, 0.335)], fill=(34, 110, 54))
    _line(draw, rect, [(0.68, 0.315), (0.68, 0.345)], fill=(34, 110, 54),
          width=2)
    # honour guard raising it
    person(draw, rect, 0.30, 0.94, 0.50, shirt=(52, 66, 44),
           trousers=(52, 66, 44), pose="raise")
    person(draw, rect, 0.70, 0.94, 0.50, shirt=(52, 66, 44),
           trousers=(52, 66, 44), skin=SKIN_D, pose="stand")


# ------------------------------------------------------------ ig metall
def scene_igmetall(draw, rect):
    _box(draw, rect, 0, 0, 1, 1, fill=(206, 208, 210))
    # factory block and chimneys
    _box(draw, rect, 0.04, 0.38, 0.62, 0.80, fill=(128, 130, 136))
    _box(draw, rect, 0.10, 0.16, 0.17, 0.38, fill=(104, 106, 112))
    _box(draw, rect, 0.24, 0.10, 0.31, 0.38, fill=(104, 106, 112))
    for r in range(2):
        for cidx in range(5):
            _box(draw, rect, 0.08 + cidx * 0.105, 0.46 + r * 0.16,
                 0.145 + cidx * 0.105, 0.545 + r * 0.16,
                 fill=(240, 226, 160))
    _box(draw, rect, 0, 0.80, 1, 1, fill=C.CONCRETE)
    # closed gates
    _box(draw, rect, 0.66, 0.42, 0.97, 0.80, fill=(88, 92, 100),
         outline=C.INK, width=2)
    _line(draw, rect, [(0.815, 0.42), (0.815, 0.80)], fill=C.INK, width=2)
    # workers outside with a blank banner
    _box(draw, rect, 0.06, 0.60, 0.52, 0.715, fill=C.WHITE, outline=C.INK,
         width=2)
    person(draw, rect, 0.12, 0.96, 0.42, shirt=C.RED, trousers=(44, 48, 60),
           pose="hold")
    person(draw, rect, 0.46, 0.96, 0.42, shirt=C.RED, trousers=(44, 48, 60),
           skin=SKIN_D, pose="hold")
    person(draw, rect, 0.28, 0.97, 0.38, shirt=(60, 70, 96),
           trousers=(44, 48, 60), pose="stand")


SCENES = {
    "cop31": scene_cop31,
    "hongkong": scene_hongkong,
    "cricket": scene_cricket,
    "israel": scene_israel,
    "f1": scene_f1,
    "tennis": scene_tennis,
    "melbourne": scene_melbourne,
    "football": scene_football,
    "nfl": scene_nfl,
    "nepal": scene_nepal,
    "lebanon": scene_lebanon,
    "igmetall": scene_igmetall,
}


# ------------------------------------------------------------- dot map
# Coarse hand-drawn land grid, equirectangular: 90 cols x 12 rows
# (row count matched to the strip band so dots stay separate dots),
# lon -180..180 left to right, lat 84..-56 top to bottom.
LAND = [
    "                #####   #####     #####                 #######     #########     ####### ",
    "        #######################                ######  ###################################",
    "          ###################                ###### ##################################    ",
    "            ################                  ################################### ###     ",
    "             #############                   ############## ##### #############           ",
    "              ######                           ############       ##### #####             ",
    "                 ########                      ###########            #############       ",
    "                  ########                       ########                 ###########     ",
    "                   #######                        ######                 ########         ",
    "                    #####                          ####                 #########         ",
    "                     ###                                                              ##  ",
    "                     ##                                                                   ",
]

MAP_LAT_TOP = 84.0
MAP_LAT_BOT = -56.0


def lonlat_to_xy(lon, lat, rect):
    x, y, w, h = rect
    fx = (lon + 180.0) / 360.0
    fy = (MAP_LAT_TOP - lat) / (MAP_LAT_TOP - MAP_LAT_BOT)
    return x + fx * w, y + fy * h


def draw_dot_map(draw, rect):
    """Dotted continents from the LAND grid."""
    rows = len(LAND)
    cols = len(LAND[0])
    x, y, w, h = rect
    # The band is far wider than it is tall, so dots stay small enough
    # to remain separate dots rather than merging into vertical bars.
    dot = 1.05
    for r, row in enumerate(LAND):
        for cidx, ch in enumerate(row):
            if ch != "#":
                continue
            cx = x + (cidx + 0.5) * w / cols
            cy = y + (r + 0.5) * h / rows
            draw.ellipse([cx - dot, cy - dot, cx + dot, cy + dot],
                         fill=(128, 112, 80))
