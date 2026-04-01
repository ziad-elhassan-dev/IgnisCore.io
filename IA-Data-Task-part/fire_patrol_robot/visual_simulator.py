#!/usr/bin/env python3
"""
visual_simulator.py
====================
Fire Patrol Robot — Visual Simulator

Uses the real project classes directly:
  - FireDetector    (fire_detection/FireDetector.py)
  - AdvisorService  (navigation/advisor_service.py)
  - RobotController (robot/robot_controller.py)
  - a_star          (navigation/pathfinding_a_star.py)

Dataset contains ONLY raw sensor readings (ppm, temperature, humidity) + timer.
No pre-determined movement, no warnings, no motor data.

Each frame (500ms):
  1. Read ppm + temp from dataset entry
  2. Convert to sensor_data dict via FireDetector.from_dataset_entry()
  3. Inject into RobotController via inject_sensor_data()
  4. Call RobotController.step() — FSM decides state, AdvisorService picks
     target zone, A* computes path, robot moves one cell on the grid
  5. Draw everything

Controls:
  SPACE       play / pause
  LEFT/RIGHT  step one frame
  R           reset
  1 / 2 / 3  speed x1 / x5 / x20
  S           export rapport_session.json
  ESC         quit
"""

import json
import math
import os
import sys
import time
from collections import deque
from datetime import datetime, timezone

import pygame
import paho.mqtt.client as mqtt

# ─────────────────────────────────────────────────────────────────────────────
#  PROJECT IMPORTS  — real classes, not copies
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from fire_detection.FireDetector import FireDetector
from navigation.advisor_service import AdvisorService, ZONE_CENTERS
from navigation.pathfinding_a_star import a_star
from robot.robot_controller import RobotController, RobotState, MAP_GRID

# ─────────────────────────────────────────────────────────────────────────────
#  DATASET
# ─────────────────────────────────────────────────────────────────────────────
DATASET_PATH = os.path.join(PROJECT_ROOT, "dataset_robot_fire_detection_001.json")

# ─────────────────────────────────────────────────────────────────────────────
#  MQTT
# ─────────────────────────────────────────────────────────────────────────────
MQTT_BROKER   = "51.254.138.154"
MQTT_PORT     = 1883
MQTT_TOPIC    = "robot/simulator/sensor_data"
MQTT_USER     = "admin"
MQTT_PASSWORD = "YNOVBOOST2026!"

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

# ─────────────────────────────────────────────────────────────────────────────
#  LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
WIN_W      = 1280
WIN_H      = 820
HEADER_H   = 56
TIMELINE_H = 44
LEFT_W     = 220
RIGHT_W    = 220
ARENA_X    = LEFT_W
ARENA_Y    = HEADER_H
ARENA_W    = WIN_W - LEFT_W - RIGHT_W   # 840
ARENA_H    = WIN_H - HEADER_H - TIMELINE_H  # 720
TIMELINE_Y = WIN_H - TIMELINE_H
FPS        = 60
FRAME_MS   = 500
SPARKLINE_N = 150  # ~75 seconds of history at 0.5s/frame

# ─────────────────────────────────────────────────────────────────────────────
#  GRID  (derived from MAP_GRID in robot_controller)
# ─────────────────────────────────────────────────────────────────────────────
GRID_ROWS = len(MAP_GRID)     # 5
GRID_COLS = len(MAP_GRID[0])  # 9
CELL_W    = ARENA_W / GRID_COLS
CELL_H    = ARENA_H / GRID_ROWS
ROBOT_R   = 16

def cell_to_px(row, col):
    """Return the centre pixel of a grid cell in arena-local coordinates."""
    return (col * CELL_W + CELL_W / 2,
            row * CELL_H + CELL_H / 2)

# ─────────────────────────────────────────────────────────────────────────────
#  PALETTE
# ─────────────────────────────────────────────────────────────────────────────
BG         = (8,   10,  16)
PANEL_BG   = (14,  18,  28)
PANEL_BG2  = (18,  23,  36)
CARD_BG    = (20,  26,  42)
BORDER     = (36,  48,  68)
BORDER_LIT = (52,  74, 112)
WHITE      = (228, 234, 248)
GRAY       = (110, 125, 150)
GRAY_DIM   = (55,  66,  84)
CYAN       = (0,   218, 255)
ORANGE     = (255, 148,   0)
RED_C      = (218,  44,  44)
GREEN      = (42,  198,  72)
YELLOW     = (255, 212,   0)
WALL_COL   = (26,  34,  52)
FREE_COL   = (10,  13,  21)
GRID_LINE  = (20,  26,  40)

FSM_RGB = {
    RobotState.IDLE:       GRAY,
    RobotState.PATROL:     CYAN,
    RobotState.SUSPICION:  YELLOW,
    RobotState.CONFIRM:    ORANGE,
    RobotState.EXTINGUISH:     RED_C,
    RobotState.REPORT:         GREEN,
    RobotState.RETURN_TO_BASE: (120, 80, 220),  # purple
}

# ─────────────────────────────────────────────────────────────────────────────
#  DRAW HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def txt(surf, text, font, color, x, y, anchor="topleft"):
    img = font.render(str(text), True, color)
    r   = img.get_rect(**{anchor: (x, y)})
    surf.blit(img, r)

def card(surf, rect, bg=CARD_BG):
    pygame.draw.rect(surf, bg,     rect)
    pygame.draw.rect(surf, BORDER, rect, 1)

def pill(surf, text, font, cx, cy, col):
    img    = font.render(text, True, col)
    iw, ih = img.get_size()
    pw, ph = iw + 12, ih + 6
    r      = pygame.Rect(cx - pw // 2, cy - ph // 2, pw, ph)
    bg     = pygame.Surface((pw, ph), pygame.SRCALPHA)
    bg.fill((*col, 40))
    surf.blit(bg, r)
    pygame.draw.rect(surf, col, r, 1, border_radius=3)
    surf.blit(img, (r.x + 6, r.y + 3))

def hbar(surf, x, y, w, h, val, maxv, col):
    pygame.draw.rect(surf, BG, (x, y, w, h))
    fw = max(0, int(min(val / max(maxv, 0.001), 1.0) * w))
    if fw:
        pygame.draw.rect(surf, col, (x, y, fw, h))
    pygame.draw.rect(surf, BORDER, (x, y, w, h), 1)

def sparkline(surf, rx, ry, rw, rh, vals, col):
    pygame.draw.rect(surf, PANEL_BG2, (rx, ry, rw, rh))
    pygame.draw.rect(surf, BORDER,    (rx, ry, rw, rh), 1)
    v = list(vals)
    if len(v) < 2:
        return
    mn, mx = min(v), max(v)
    if mx == mn:
        mx = mn + 1.0
    pad = 3
    n   = len(v)
    pts = [
        (rx + pad + int(i / (n - 1) * (rw - pad * 2)),
         ry + rh - pad - int((x - mn) / (mx - mn) * (rh - pad * 2)))
        for i, x in enumerate(v)
    ]
    pygame.draw.lines(surf, col, False, pts, 1)
    pygame.draw.circle(surf, col, pts[-1], 2)

def sec_label(surf, label, font, x, y, x2):
    txt(surf, label, font, GRAY_DIM, x, y)
    y2 = y + 13
    pygame.draw.line(surf, BORDER, (x, y2), (x2, y2), 1)
    return y2 + 5

# ─────────────────────────────────────────────────────────────────────────────
#  ROBOT SPRITE
# ─────────────────────────────────────────────────────────────────────────────
def draw_robot(surf, cx, cy, angle, col, pump=False, wheel_rot=0.0):
    import random
    cx, cy = int(cx), int(cy)

    # Water spray when extinguishing
    if pump:
        for _ in range(6):
            sa = angle + random.uniform(-0.7, 0.7)
            sl = random.randint(ROBOT_R + 8, ROBOT_R + 30)
            pygame.draw.line(surf, (60, 130, 255), (cx, cy),
                             (int(cx + sl * math.cos(sa)),
                              int(cy + sl * math.sin(sa))), 1)

    # Vision cone
    cl, sp = ROBOT_R + 38, 0.38
    cone = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    pygame.draw.polygon(cone, (*YELLOW, 18), [
        (cx, cy),
        (int(cx + cl * math.cos(angle - sp)), int(cy + cl * math.sin(angle - sp))),
        (int(cx + cl * math.cos(angle + sp)), int(cy + cl * math.sin(angle + sp))),
    ])
    surf.blit(cone, (0, 0))

    # Wheels — tread marks rotate with wheel_rot for spin effect
    perp = angle + math.pi / 2
    ca, sa = math.cos(angle), math.sin(angle)
    for side in (1, -1):
        wx = cx + side * (ROBOT_R + 3) * math.cos(perp)
        wy = cy + side * (ROBOT_R + 3) * math.sin(perp)
        corners = [(-8, -3), (8, -3), (8, 3), (-8, 3)]
        wpts = [(int(wx + lx * ca - ly * sa),
                 int(wy + lx * sa + ly * ca)) for lx, ly in corners]
        pygame.draw.polygon(surf, (45, 55, 72), wpts)
        pygame.draw.polygon(surf, (70, 82, 100), wpts, 1)
        # Tread tick — a small line that rotates with wheel_rot
        tick_offset = math.sin(wheel_rot + side * 1.2) * 5
        t1 = (int(wx + tick_offset * ca), int(wy + tick_offset * sa))
        t2 = (int(wx + tick_offset * ca - 2 * math.cos(perp) * side),
              int(wy + tick_offset * sa - 2 * math.sin(perp) * side))
        pygame.draw.line(surf, (100, 118, 140), t1, t2, 1)

    # Glow rings
    t     = pygame.time.get_ticks()
    pulse = 0.5 + 0.5 * math.sin(t / 250.0)
    for rg, ba in ((ROBOT_R + 7, 20), (ROBOT_R + 3, 42)):
        gc = tuple(min(255, int(c * 0.36)) for c in col)
        gs = pygame.Surface(((rg + 2) * 2, (rg + 2) * 2), pygame.SRCALPHA)
        gpts = [
            (rg + 2 + rg * math.cos(angle + i * math.pi / 3),
             rg + 2 + rg * math.sin(angle + i * math.pi / 3))
            for i in range(6)
        ]
        pygame.draw.polygon(gs, (*gc, int(ba * (0.55 + 0.45 * pulse))), gpts)
        surf.blit(gs, (cx - rg - 2, cy - rg - 2))

    # Hex body
    hpts = [
        (cx + ROBOT_R * math.cos(angle + i * math.pi / 3),
         cy + ROBOT_R * math.sin(angle + i * math.pi / 3))
        for i in range(6)
    ]
    pygame.draw.polygon(surf, col,   hpts)
    pygame.draw.polygon(surf, WHITE, hpts, 1)

    # Direction dot
    pygame.draw.circle(
        surf, WHITE,
        (int(cx + (ROBOT_R - 5) * math.cos(angle)),
         int(cy + (ROBOT_R - 5) * math.sin(angle))), 3
    )

# ─────────────────────────────────────────────────────────────────────────────
#  ARENA
# ─────────────────────────────────────────────────────────────────────────────
def draw_arena(surf, robot, fonts):
    ax, ay = ARENA_X, ARENA_Y
    t      = pygame.time.get_ticks()
    pulse  = 0.5 + 0.5 * math.sin(t / 280.0)

    pygame.draw.rect(surf, FREE_COL, (ax, ay, ARENA_W, ARENA_H))

    # ── Cells + walls ─────────────────────────────────────────────────────────
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            rx = int(ax + c * CELL_W)
            ry = int(ay + r * CELL_H)
            rw = int(CELL_W)
            rh = int(CELL_H)
            if MAP_GRID[r][c] == 1:
                pygame.draw.rect(surf, WALL_COL, (rx, ry, rw, rh))
                pygame.draw.rect(surf, (38, 48, 68), (rx, ry, rw, rh), 1)
                for d in range(0, rw + rh, 16):
                    x1 = rx + min(d, rw);      y1 = ry + max(0, d - rw)
                    x2 = rx + max(0, d - rh);  y2 = ry + min(d, rh)
                    pygame.draw.line(surf, (22, 30, 46), (x1, y1), (x2, y2), 1)
            else:
                pygame.draw.rect(surf, FREE_COL, (rx, ry, rw, rh))
                pygame.draw.rect(surf, GRID_LINE, (rx, ry, rw, rh), 1)

    # ── Zone risk heatmap — colour every free cell by its nearest zone's risk ───
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if MAP_GRID[r][c] != 0:
                continue
            # Find closest zone center
            best_zid, best_dist = None, float("inf")
            for zid, (zr, zc_) in ZONE_CENTERS.items():
                d = abs(r - zr) + abs(c - zc_)
                if d < best_dist:
                    best_dist, best_zid = d, zid
            zrisk = robot.advisor.zone_data[best_zid]["avg_risk_score"] if best_zid else 0
            if zrisk > 0.02:
                # Blend: low risk = deep blue tint, mid = orange, high = red
                if zrisk < 0.35:
                    rc = (0, 80, 180)
                elif zrisk < 0.60:
                    rc = ORANGE
                else:
                    rc = RED_C
                alpha = int(min(zrisk * 110, 100))
                heat = pygame.Surface((int(CELL_W) - 2, int(CELL_H) - 2), pygame.SRCALPHA)
                heat.fill((*rc, alpha))
                surf.blit(heat, (int(ax + c * CELL_W) + 1, int(ay + r * CELL_H) + 1))

    # ── Zone labels + destination highlight ───────────────────────────────────
    for zid, (zr, zc) in ZONE_CENTERS.items():
        zpx, zpy = cell_to_px(zr, zc)
        zpx += ax; zpy += ay
        zrisk   = robot.advisor.zone_data[zid]["avg_risk_score"]
        is_dest = (robot.destination_zone == zid)

        if is_dest:
            ds = pygame.Surface((int(CELL_W) - 2, int(CELL_H) - 2), pygame.SRCALPHA)
            ds.fill((*CYAN, 22))
            surf.blit(ds, (int(ax + zc * CELL_W) + 1, int(ay + zr * CELL_H) + 1))
            pygame.draw.rect(surf, CYAN,
                             (int(ax + zc * CELL_W) + 1, int(ay + zr * CELL_H) + 1,
                              int(CELL_W) - 2, int(CELL_H) - 2), 1)

        lc = CYAN if is_dest else (RED_C if zrisk > 0.5 else (ORANGE if zrisk > 0.1 else GRAY_DIM))
        txt(surf, zid, fonts["sm_bold"], lc, int(zpx), int(zpy - 8), "center")
        if zrisk > 0.01:
            txt(surf, f"{zrisk:.2f}", fonts["sm"], GRAY_DIM,
                int(zpx), int(zpy + 4), "center")

    # ── Trail ─────────────────────────────────────────────────────────────────
    trail = robot._trail
    full  = trail + [robot.current_pos]
    n     = len(full)
    if n >= 2:
        for i in range(1, n):
            p1 = cell_to_px(*full[i - 1])
            p2 = cell_to_px(*full[i])
            p1 = (int(p1[0] + ax), int(p1[1] + ay))
            p2 = (int(p2[0] + ax), int(p2[1] + ay))
            fade = max(0.10, i / n)
            pygame.draw.line(surf, tuple(int(c * fade) for c in CYAN), p1, p2, 2)

    # ── A* planned path ───────────────────────────────────────────────────────
    if robot.current_path:
        full_path = [robot.current_pos] + robot.current_path
        np_ = len(full_path)
        for i in range(1, np_):
            p1 = cell_to_px(*full_path[i - 1])
            p2 = cell_to_px(*full_path[i])
            p1 = (int(p1[0] + ax), int(p1[1] + ay))
            p2 = (int(p2[0] + ax), int(p2[1] + ay))
            fade = max(0.25, 1.0 - i / np_)
            c    = tuple(int(ch * fade) for ch in (0, 190, 240))
            pygame.draw.line(surf, c, p1, p2, 2)
            pygame.draw.circle(surf, c, p2, 3)

        # Pulsing ring at destination cell
        if robot.destination_pos:
            dp = cell_to_px(*robot.destination_pos)
            dp = (int(dp[0] + ax), int(dp[1] + ay))
            pr = int(10 + 4 * pulse)
            ds = pygame.Surface((pr * 2 + 4, pr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ds, (*CYAN, 110), (pr + 2, pr + 2), pr, 2)
            surf.blit(ds, (dp[0] - pr - 2, dp[1] - pr - 2))
            pygame.draw.circle(surf, CYAN, dp, 4)

    # ── Fire marker ───────────────────────────────────────────────────────────
    if robot._fire_cell:
        fp = cell_to_px(*robot._fire_cell)
        mx = int(fp[0] + ax)
        my = int(fp[1] + ay)
        for rr, alpha in ((int(18 + 7 * pulse), 45),
                          (int(11 + 4 * pulse), 95),
                          (6, 200)):
            fs = pygame.Surface((rr * 2 + 2, rr * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(fs, (*RED_C, alpha), (rr + 1, rr + 1), rr, 2)
            surf.blit(fs, (mx - rr - 1, my - rr - 1))
        pygame.draw.circle(surf, RED_C, (mx, my), 6)
        txt(surf, "FIRE", fonts["sm"], RED_C, mx + 10, my - 7)

    # ── Current cell highlight ────────────────────────────────────────────────
    fsc    = FSM_RGB.get(robot.current_state, CYAN)
    cr, cc = robot.current_pos
    crect  = pygame.Rect(int(ax + cc * CELL_W) + 1, int(ay + cr * CELL_H) + 1,
                         int(CELL_W) - 2, int(CELL_H) - 2)
    cs = pygame.Surface(crect.size, pygame.SRCALPHA)
    cs.fill((*fsc, 25))
    surf.blit(cs, crect)
    pygame.draw.rect(surf, fsc, crect, 1)

    # ── Robot sprite ──────────────────────────────────────────────────────────
    pump_on = (robot.current_state == RobotState.EXTINGUISH)
    draw_robot(surf, ax + robot._px, ay + robot._py,
               robot._angle, fsc, pump=pump_on, wheel_rot=robot._wheel_rot)

    txt(surf, robot.current_state, fonts["sm_bold"], fsc,
        int(ax + robot._px), int(ay + robot._py) - ROBOT_R - 13, "midbottom")
    txt(surf, f"cell({robot.current_pos[0]},{robot.current_pos[1]})",
        fonts["sm"], GRAY_DIM, ax + 4, ay + ARENA_H - 13)

    pygame.draw.rect(surf, BORDER_LIT, (ax, ay, ARENA_W, ARENA_H), 1)

# ─────────────────────────────────────────────────────────────────────────────
#  LEFT PANEL
# ─────────────────────────────────────────────────────────────────────────────
def draw_left(surf, fi, data, fonts, robot, scores):
    pygame.draw.rect(surf, PANEL_BG, (0, HEADER_H, LEFT_W, WIN_H - HEADER_H))
    pygame.draw.line(surf, BORDER_LIT, (LEFT_W - 1, HEADER_H), (LEFT_W - 1, WIN_H), 1)

    e   = data[fi]
    pad = 8
    W   = LEFT_W
    y   = HEADER_H + 8

    def sec(label):
        nonlocal y
        y = sec_label(surf, label, fonts["sm"], pad, y, W - pad)

    def row(label, val, vc):
        nonlocal y
        txt(surf, label, fonts["sm"], GRAY,    pad + 5, y)
        txt(surf, val,   fonts["sm"], vc,      W - pad - 5, y, "topright")
        y += 17

    # Robot status
    sec("ROBOT STATUS")
    cr = pygame.Rect(pad, y, W - pad * 2, 68)
    card(surf, cr)
    y += 6
    row("STATE",  "ACTIVE", GREEN)
    row("MQTT",   "CONNECTED", GREEN)
    up = e["timer"]["uptime_ms"]
    mm, ss = up // 60000, (up % 60000) // 1000
    row("UPTIME", f"{mm:02d}:{ss:02d}", WHITE)
    row("FRAME",  str(fi + 1), GRAY)
    y = cr.bottom + 8

    # FSM
    sec("FSM STATE")
    cr2 = pygame.Rect(pad, y, W - pad * 2, 100)
    card(surf, cr2)
    y += 6
    fsc = FSM_RGB.get(robot.current_state, CYAN)
    row("STATE",   robot.current_state, fsc)
    row("ARMED",   "NO" if robot.fire_handled else "YES",
        ORANGE if robot.fire_handled else GREEN)
    row("INCIDENTS", str(len(robot.incident_log)),
        ORANGE if robot.incident_log else GREEN)
    if robot.incident_log:
        sev = robot.last_severity or "—"
        sc  = RED_C if sev == "CRITICAL" else (ORANGE if sev == "MODERATE" else GRAY)
        row("LAST SEV.", sev, sc)
    if robot.current_state in (RobotState.SUSPICION, RobotState.CONFIRM):
        sr = len(robot.suspicion_readings)
        txt(surf, f"READS {sr}/3", fonts["sm"], YELLOW, pad + 5, y)
        y += 14
        bw = W - pad * 2 - 10
        pygame.draw.rect(surf, BG,     (pad + 5, y, bw, 5))
        pygame.draw.rect(surf, YELLOW, (pad + 5, y, int(sr / 3 * bw), 5))
        pygame.draw.rect(surf, BORDER, (pad + 5, y, bw, 5), 1)
        y += 10
    y = cr2.bottom + 8

    # FireDetector scores
    sec("FIRE DETECTOR")
    cr3 = pygame.Rect(pad, y, W - pad * 2, 84)
    card(surf, cr3)
    y += 6
    g  = scores["global"]
    gc = RED_C if g >= 0.5 else (ORANGE if g >= 0.2 else GREEN)
    row("GLOBAL", f"{g:.3f}", gc)
    hbar(surf, pad + 5, y, W - pad * 2 - 10, 6, g, 1.0, gc)
    y += 12
    for lbl, val, vc in (("TEMP",  scores["temp"],  ORANGE),
                          ("SMOKE", scores["smoke"], YELLOW),
                          ("IR",    scores["ir"],    RED_C)):
        txt(surf, lbl,        fonts["sm"], GRAY_DIM, pad + 5,      y)
        txt(surf, f"{val:.2f}", fonts["sm"], vc,     W - pad - 5,  y, "topright")
        hbar(surf, pad + 36, y + 2, W - pad * 2 - 76, 4, val, 1.0, vc)
        y += 14
    y = cr3.bottom + 8

    # Navigation
    sec("NAVIGATION")
    cr4 = pygame.Rect(pad, y, W - pad * 2, 52)
    card(surf, cr4)
    y += 6
    row("TARGET ZONE", robot.destination_zone or "—", CYAN)
    row("PATH STEPS",  str(len(robot.current_path)), WHITE)
    y = cr4.bottom + 8

# ─────────────────────────────────────────────────────────────────────────────
#  RIGHT PANEL
# ─────────────────────────────────────────────────────────────────────────────
def draw_right(surf, fi, data, ppm_h, temp_h, fonts, robot):
    rx0 = WIN_W - RIGHT_W
    pygame.draw.rect(surf, PANEL_BG, (rx0, HEADER_H, RIGHT_W, WIN_H - HEADER_H))
    pygame.draw.line(surf, BORDER_LIT, (rx0, HEADER_H), (rx0, WIN_H), 1)

    e   = data[fi]
    aq  = e["air_quality"]
    tmp = e["temperature"]
    pad = 8
    rw  = RIGHT_W - pad * 2
    y   = HEADER_H + 8

    def sec(label):
        nonlocal y
        y = sec_label(surf, label, fonts["sm"], rx0 + pad, y, WIN_W - pad)

    def row(label, val, vc):
        nonlocal y
        txt(surf, label, fonts["sm"], GRAY,    rx0 + pad + 5, y)
        txt(surf, val,   fonts["sm"], vc,      WIN_W - pad - 5, y, "topright")
        y += 17

    # Air quality — alert computed live, not from dataset
    sec("AIR QUALITY  MQ-4")
    aq_r = pygame.Rect(rx0 + pad, y, rw, 100)
    card(surf, aq_r)
    qy  = y + 6
    ppm = aq["readings"]["processed"]["ppm"]
    if ppm >= 400:   aq_alert = "danger"
    elif ppm >= 150: aq_alert = "warning"
    else:            aq_alert = "normal"
    pc = RED_C if aq_alert == "danger" else (ORANGE if aq_alert == "warning" else GREEN)

    txt(surf, f"{ppm:.1f}", fonts["large"], pc,   rx0 + pad + 6, qy)
    txt(surf, "ppm",        fonts["sm"],    GRAY, rx0 + pad + 6, qy + 26)
    pill(surf, aq_alert.upper(), fonts["sm"], WIN_W - pad - 38, qy + 10, pc)
    qy += 44
    for label, val in (("ADC",   str(aq["readings"]["raw"]["adc_value"])),
                       ("VOLT",  f"{aq['readings']['raw']['voltage']:.2f}V"),
                       ("RS/R0", f"{aq['readings']['raw']['rs_r0']:.3f}")):
        txt(surf, label, fonts["sm"], GRAY_DIM, rx0 + pad + 6,  qy)
        txt(surf, val,   fonts["sm"], WHITE,    rx0 + pad + 60, qy)
        qy += 16
    y = aq_r.bottom + 8

    # Temperature — alert computed live
    sec("TEMPERATURE  DHT11")
    tp_r = pygame.Rect(rx0 + pad, y, rw, 96)
    card(surf, tp_r)
    ty = y + 6
    tv = tmp["readings"]["temperature"]["value"]
    hv = tmp["readings"]["humidity"]["value"]
    hi = tmp["readings"]["heat_index"]["value"]
    if tv >= 50:   t_alert = "danger"
    elif tv >= 35: t_alert = "warning"
    else:          t_alert = "normal"
    tc = RED_C if t_alert == "danger" else (ORANGE if t_alert == "warning" else CYAN)

    txt(surf, f"{tv}",     fonts["large"], tc,   rx0 + pad + 6,   ty)
    txt(surf, "°C",        fonts["sm"],    GRAY, rx0 + pad + 6,   ty + 26)
    txt(surf, f"{hv}%RH",  fonts["sm"],    CYAN, WIN_W - pad - 6, ty, "topright")
    ty += 36
    txt(surf, "HEAT INDEX",  fonts["sm"], GRAY,  rx0 + pad + 6,   ty)
    txt(surf, f"{hi:.1f}°C", fonts["sm"], WHITE, WIN_W - pad - 6, ty, "topright")
    ty += 18
    pill(surf, t_alert.upper(), fonts["sm"], rx0 + pad + 30, ty, tc)
    y = tp_r.bottom + 8

    # Sparklines
    sec(f"PPM TREND  (last {SPARKLINE_N})")
    sparkline(surf, rx0 + pad, y, rw, 42, list(ppm_h) or [0, 0], pc)
    if len(ppm_h) >= 2:
        txt(surf, f"{min(ppm_h):.0f}", fonts["sm"], GRAY_DIM, rx0 + pad + 2, y + 30)
        txt(surf, f"{max(ppm_h):.0f}", fonts["sm"], GRAY_DIM, rx0 + pad + 2, y + 2)
    y += 52

    sec(f"TEMP TREND  (last {SPARKLINE_N})")
    sparkline(surf, rx0 + pad, y, rw, 42, list(temp_h) or [0, 0], tc)
    if len(temp_h) >= 2:
        txt(surf, f"{min(temp_h):.0f}°", fonts["sm"], GRAY_DIM, rx0 + pad + 2, y + 30)
        txt(surf, f"{max(temp_h):.0f}°", fonts["sm"], GRAY_DIM, rx0 + pad + 2, y + 2)
    y += 52

    # Zone priorities from AdvisorService
    remaining = TIMELINE_Y - y - 6
    if remaining > 30:
        sec("ZONE PRIORITIES  (Advisor)")
        zr2 = pygame.Rect(rx0 + pad, y, rw, remaining)
        card(surf, zr2)
        zy  = y + 4
        priorities = {z: robot.advisor.calculate_priority_score(z) for z in ZONE_CENTERS}
        for zid, p in sorted(priorities.items(), key=lambda x: -x[1]):
            if zy > zr2.bottom - 12:
                break
            risk    = robot.advisor.zone_data[zid]["avg_risk_score"]
            zc      = RED_C if risk > 0.5 else (ORANGE if risk > 0.1 else GREEN)
            is_dest = (robot.destination_zone == zid)
            lc      = CYAN if is_dest else GRAY
            txt(surf, ("► " if is_dest else "  ") + zid,
                fonts["sm"], lc, rx0 + pad + 4, zy)
            txt(surf, f"{p:.2f}", fonts["sm"], zc, WIN_W - pad - 6, zy, "topright")
            hbar(surf, rx0 + pad + 36, zy + 3, rw - 68, 4, risk, 1.0, zc)
            zy += 14

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
def draw_header(surf, fi, total, data, fonts, playing, speed, robot, scores):
    pygame.draw.rect(surf, PANEL_BG, (0, 0, WIN_W, HEADER_H))
    pygame.draw.line(surf, BORDER_LIT, (0, HEADER_H - 1), (WIN_W, HEADER_H - 1), 1)
    mid = HEADER_H // 2

    txt(surf, "FIRE PATROL",     fonts["title"], CYAN,  14, mid, "midleft")
    txt(surf, "ROBOT SIMULATOR", fonts["md"],    GRAY, 142, mid, "midleft")

    sc = GREEN if playing else GRAY
    txt(surf, "> PLAY" if playing else "|| PAUSE", fonts["md"], sc,
        WIN_W // 2 - 52, mid, "midleft")
    txt(surf, f"x{speed}", fonts["md"], YELLOW, WIN_W // 2 + 16, mid, "midleft")

    fsc = FSM_RGB.get(robot.current_state, CYAN)
    pill(surf, f"FSM: {robot.current_state}", fonts["md"],
         WIN_W // 2 + 115, mid, fsc)

    # Blink alert if fire score is high
    g = scores["global"]
    if g >= 0.40 and not robot.fire_handled and (pygame.time.get_ticks() // 500) % 2 == 0:
        col = RED_C if g >= 0.6 else ORANGE
        lbl = "!! FIRE DETECTED" if g >= 0.6 else "!  SMOKE DETECTED"
        bw  = 240
        bx  = WIN_W - RIGHT_W - bw - 12
        br  = pygame.Rect(bx, 8, bw, HEADER_H - 16)
        bs  = pygame.Surface(br.size, pygame.SRCALPHA)
        bs.fill((*col, 55))
        surf.blit(bs, br)
        pygame.draw.rect(surf, col, br, 2)
        txt(surf, lbl, fonts["md"], col, br.centerx, br.centery, "center")

    up = data[fi]["timer"]["uptime_ms"]
    mm, ss = up // 60000, (up % 60000) // 1000
    txt(surf, f"{mm:02d}:{ss:02d}  [{fi + 1}/{total}]",
        fonts["sm"], GRAY, WIN_W - 12, mid, "midright")

# ─────────────────────────────────────────────────────────────────────────────
#  TIMELINE
# ─────────────────────────────────────────────────────────────────────────────
def draw_timeline(surf, fi, total, data, fonts, scores_hist, robot, fsm_events):
    pygame.draw.rect(surf, PANEL_BG2, (0, TIMELINE_Y, WIN_W, TIMELINE_H))
    pygame.draw.line(surf, BORDER_LIT, (0, TIMELINE_Y), (WIN_W, TIMELINE_Y), 1)

    bx = LEFT_W + 8
    bw = WIN_W - LEFT_W - RIGHT_W - 16
    by = TIMELINE_Y + 8
    bh = 12

    # Draw score history as a mini graph behind the scrub bar
    sh = list(scores_hist)
    if len(sh) > 1:
        n = len(sh)
        for i in range(1, n):
            x1 = bx + int((i - 1) / (total - 1) * bw)
            x2 = bx + int(i       / (total - 1) * bw)
            g  = sh[i]
            c  = RED_C if g >= 0.6 else (ORANGE if g >= 0.40 else (28, 40, 60))
            pygame.draw.line(surf, c, (x1, by + bh), (x2, by + bh - int(g * bh)), 1)

    pygame.draw.rect(surf, BG,     (bx, by, bw, bh))
    pygame.draw.rect(surf, BORDER, (bx, by, bw, bh), 1)

    prog = fi / max(1, total - 1)
    fw   = int(prog * bw)
    g    = sh[-1] if sh else 0
    if robot.fire_handled:
        pc = CYAN
    else:
        pc = RED_C if g >= 0.6 else (ORANGE if g >= 0.40 else CYAN)
    if fw > 0:
        pygame.draw.rect(surf, pc, (bx, by, fw, bh))

    # FSM event markers above the bar
    marker_colors = {"suspicion": ORANGE, "confirm": RED_C, "extinguish": (80, 200, 255)}
    for (ef, etype) in fsm_events:
        mx = bx + int(ef / max(1, total - 1) * bw)
        mc = marker_colors.get(etype, WHITE)
        pygame.draw.line(surf, mc, (mx, by - 6), (mx, by + bh + 2), 2)
        pygame.draw.circle(surf, mc, (mx, by - 7), 3)

    # Scrubber knob
    cx_ = bx + fw
    pygame.draw.circle(surf, WHITE, (cx_, by + bh // 2), 7)
    pygame.draw.circle(surf, BG,    (cx_, by + bh // 2), 4)

    up  = data[fi]["timer"]["uptime_ms"]
    end = data[-1]["timer"]["uptime_ms"]
    mm, ss = up  // 60000, (up  % 60000) // 1000
    tm, ts = end // 60000, (end % 60000) // 1000
    txt(surf, f"{mm:02d}:{ss:02d}", fonts["sm"], WHITE, bx,      TIMELINE_Y + 2)
    txt(surf, f"{tm:02d}:{ts:02d}", fonts["sm"], GRAY,  bx + bw, TIMELINE_Y + 2, "topright")
    txt(surf,
        "[SPACE] play/pause   [←/→] step   [R] reset   [1/2/3] speed   [S] export",
        fonts["sm"], GRAY_DIM, WIN_W // 2, TIMELINE_Y + TIMELINE_H - 3, "midbottom")

# ─────────────────────────────────────────────────────────────────────────────
#  FONTS
# ─────────────────────────────────────────────────────────────────────────────
def make_fonts():
    def F(sz, bold=False):
        for name in ("Consolas", "Courier New", "DejaVu Sans Mono"):
            try:
                f = pygame.font.SysFont(name, sz, bold=bold)
                if f:
                    return f
            except Exception:
                pass
        return pygame.font.Font(None, sz)
    return {
        "title":   F(17, True),
        "large":   F(23, True),
        "md":      F(13, True),
        "sm":      F(10),
        "sm_bold": F(10, True),
    }

# ─────────────────────────────────────────────────────────────────────────────
#  EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def export_report(fi, data, robot, scores, scores_hist, fsm_events):
    up  = data[fi]["timer"]["uptime_ms"]
    out = os.path.join(PROJECT_ROOT, "rapport_session.json")

    # Scores summary
    sh = list(scores_hist)
    score_summary = {
        "min":  round(min(sh), 3) if sh else 0,
        "max":  round(max(sh), 3) if sh else 0,
        "avg":  round(sum(sh) / len(sh), 3) if sh else 0,
        "frames_above_0_40": sum(1 for s in sh if s >= 0.40),
        "frames_above_0_60": sum(1 for s in sh if s >= 0.60),
    }

    # Zone visit counts from advisor
    zone_summary = {
        zid: {
            "avg_risk_score": round(zdata["avg_risk_score"], 3),
            "last_inspected_ago_s": round(time.time() - zdata["last_inspected"], 1),
        }
        for zid, zdata in robot.advisor.zone_data.items()
    }

    # Cells visited (unique)
    cells_visited = list({tuple(pos) for pos in robot._trail + [robot.current_pos]})

    rep = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "frame":          fi,
        "total_frames":   len(data),
        "duration":       f"{up // 60000:02d}:{(up % 60000) // 1000:02d}",
        "fsm_state":      robot.current_state,
        "fire_handled":   robot.fire_handled,
        "robot_cell":     robot.current_pos,
        "destination":    robot.destination_zone,
        "incidents":      len(robot.incident_log),
        "incident_log":   robot.incident_log,
        "fd_scores":      scores,
        "score_summary":  score_summary,
        "zone_summary":   zone_summary,
        "cells_visited":  len(cells_visited),
        "fsm_events":     [{"frame": ef, "event": et} for ef, et in fsm_events],
        "ppm_max": round(max(
            d["air_quality"]["readings"]["processed"]["ppm"]
            for d in data[:fi + 1]), 2),
        "temp_max": max(
            d["temperature"]["readings"]["temperature"]["value"]
            for d in data[:fi + 1]),
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)
    return out

# ─────────────────────────────────────────────────────────────────────────────
#  SIMULATION STATE BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def build_sim():
    """Create a fresh simulation — new detector, advisor, robot, visual state."""
    detector = FireDetector()
    advisor  = AdvisorService()
    robot    = RobotController(detector=detector, advisor=advisor, initial_pos=(4, 0))

    # Visual helpers attached directly to robot instance
    robot._trail     = []                      # [(row,col), ...] visited cells
    robot._fire_cell = None                    # cell where fire was first confirmed
    robot._px, robot._py = cell_to_px(4, 0)   # smooth pixel position
    robot._angle        = 0.0   # current facing angle (lerped each render frame)
    robot._target_angle  = 0.0   # target facing angle set by advance()
    robot._wheel_rot     = 0.0   # wheel spin accumulator

    ppm_h       = deque(maxlen=SPARKLINE_N)
    temp_h      = deque(maxlen=SPARKLINE_N)
    scores      = {"temp": 0.0, "smoke": 0.0, "ir": 0, "global": 0.0, "proximity": 0}
    scores_hist = deque(maxlen=10000)
    fsm_events  = []   # [(frame_index, event_type)] — "suspicion","confirm","extinguish"

    return robot, ppm_h, temp_h, scores, scores_hist, fsm_events

# ─────────────────────────────────────────────────────────────────────────────
#  ADVANCE ONE FRAME
# ─────────────────────────────────────────────────────────────────────────────
def advance(fi, data, robot, ppm_h, temp_h, scores_hist, fsm_events):
    """
    Process one dataset frame:
      - Extract raw sensor values (ppm, temp) — no warnings, no motor data
      - Inject into robot via inject_sensor_data()
      - Step FSM: AdvisorService picks zone, A* plans path, robot moves
      - Update visual helpers (trail, angle, fire cell)
      - Return updated fi and scores dict
    """
    if fi >= len(data) - 1:
        return fi, {"temp": 0.0, "smoke": 0.0, "ir": 0, "global": 0.0, "proximity": 0}

    fi += 1
    e = data[fi]

    # ── Build sensor_data from raw dataset values only ─────────────────────
    sensor_data = FireDetector.from_dataset_entry(e)

    # ── Inject and step ────────────────────────────────────────────────────
    prev_pos   = robot.current_pos
    prev_state = robot.current_state
    robot.inject_sensor_data(sensor_data)
    robot.step()

    # ── Update visual helpers ──────────────────────────────────────────────
    if robot.current_pos != prev_pos:
        robot._trail.append(prev_pos)
        if len(robot._trail) > 30:          # rolling window — comet tail of last 30 steps
            robot._trail = robot._trail[-30:]

        dr = robot.current_pos[0] - prev_pos[0]
        dc = robot.current_pos[1] - prev_pos[1]
        if   dc ==  1: robot._target_angle = 0.0
        elif dc == -1: robot._target_angle = math.pi
        elif dr ==  1: robot._target_angle = math.pi / 2
        elif dr == -1: robot._target_angle = -math.pi / 2

    # Record FSM transition events for timeline markers
    if prev_state != robot.current_state:
        if robot.current_state == RobotState.SUSPICION:
            fsm_events.append((fi, "suspicion"))
        elif robot.current_state == RobotState.CONFIRM:
            fsm_events.append((fi, "confirm"))
        elif robot.current_state == RobotState.EXTINGUISH:
            fsm_events.append((fi, "extinguish"))

    # Record the cell where fire was first confirmed
    if (robot._fire_cell is None and
            robot.current_state in (RobotState.CONFIRM,
                                    RobotState.EXTINGUISH,
                                    RobotState.REPORT)):
        robot._fire_cell = robot.current_pos

    # Clear fire marker once REPORT is done and robot is back on patrol
    if prev_state == RobotState.REPORT and robot.current_state == RobotState.PATROL:
        robot._fire_cell = None

    # ── Scores for display ─────────────────────────────────────────────────
    preprocessed = robot.detector.preprocess(sensor_data.copy())
    scores       = robot.detector.calculate_fire_risk(preprocessed)

    ppm_h.append(sensor_data["smoke"])
    temp_h.append(sensor_data["temperature"])
    scores_hist.append(scores["global"])

    # ── MQTT publish ──────────────────────────────────────────────────────────
    try:
        payload = json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "frame": fi,
            "robot": {
                "state": str(robot.current_state),
                "position": list(robot.current_pos),
            },
            "sensors": {
                "temperature": sensor_data["temperature"],
                "smoke":       sensor_data["smoke"],
                "humidity":    sensor_data.get("humidity", 0),
                "ir":          sensor_data.get("ir", 0),
            },
            "fire_risk": scores,
        })
        mqtt_client.publish(MQTT_TOPIC, payload)
    except Exception:
        pass

    return fi, scores

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Fire Patrol Robot — Simulator")
    clock  = pygame.time.Clock()
    fonts  = make_fonts()

    # Load dataset
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    total = len(data)

    robot, ppm_h, temp_h, scores, scores_hist, fsm_events = build_sim()

    # ── MQTT connect ──────────────────────────────────────────────────────────
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        print(f"[MQTT] Connected to {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as exc:
        print(f"[MQTT] Connection failed: {exc}")

    # Prime frame 0 — IDLE -> PATROL, plans first A* path
    sensor_data  = FireDetector.from_dataset_entry(data[0])
    robot.inject_sensor_data(sensor_data)
    robot.step()
    preprocessed = robot.detector.preprocess(sensor_data.copy())
    scores       = robot.detector.calculate_fire_risk(preprocessed)
    ppm_h.append(sensor_data["smoke"])
    temp_h.append(sensor_data["temperature"])
    scores_hist.append(scores["global"])

    fi         = 0
    playhead   = 0.0
    playing    = True
    speed_mult = 1
    emsg       = None
    etimer     = 0

    running = True
    while running:
        dt = clock.tick(FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False

                elif ev.key == pygame.K_SPACE:
                    playing = not playing

                elif ev.key == pygame.K_RIGHT:
                    fi, scores = advance(fi, data, robot, ppm_h, temp_h, scores_hist, fsm_events)
                    playhead   = float(fi)

                elif ev.key == pygame.K_LEFT:
                    # Can't go backwards in a stateful sim — just rewind display
                    fi = max(0, fi - 1)
                    playhead = float(fi)

                elif ev.key == pygame.K_r:
                    fi       = 0
                    playhead = 0.0
                    playing  = True
                    robot, ppm_h, temp_h, scores, scores_hist, fsm_events = build_sim()
                    sensor_data  = FireDetector.from_dataset_entry(data[0])
                    robot.inject_sensor_data(sensor_data)
                    robot.step()
                    preprocessed = robot.detector.preprocess(sensor_data.copy())
                    scores       = robot.detector.calculate_fire_risk(preprocessed)
                    ppm_h.append(sensor_data["smoke"])
                    temp_h.append(sensor_data["temperature"])
                    scores_hist.append(scores["global"])

                elif ev.key == pygame.K_1: speed_mult = 1
                elif ev.key == pygame.K_2: speed_mult = 5
                elif ev.key == pygame.K_3: speed_mult = 20

                elif ev.key == pygame.K_s:
                    p      = export_report(fi, data, robot, scores, scores_hist, fsm_events)
                    emsg   = f"Exported: {os.path.basename(p)}"
                    etimer = 3000

        # Advance playhead at the correct speed
        if playing:
            playhead += (1000.0 / FRAME_MS) * speed_mult * (dt / 1000.0)
            new_fi    = min(int(playhead), total - 1)
            while fi < new_fi:
                fi, scores = advance(fi, data, robot, ppm_h, temp_h, scores_hist, fsm_events)
                if fi >= total - 1:
                    playing = False
                    break

        # Smooth pixel interpolation — dt-based so speed is frame-rate independent.
        # Lerp factor scales with playback speed so robot keeps up visually.
        tx, ty      = cell_to_px(*robot.current_pos)
        base_lerp   = 1.0 - math.exp(-12.0 * speed_mult * dt / 1000.0)
        lerp_f      = min(base_lerp, 0.92)
        robot._px  += (tx - robot._px) * lerp_f
        robot._py  += (ty - robot._py) * lerp_f

        # Angle lerp — shortest rotation path, handles 0↔2π wrap
        da = robot._target_angle - robot._angle
        # Wrap da into [-π, π]
        da = (da + math.pi) % (2 * math.pi) - math.pi
        angle_lerp  = min(1.0 - math.exp(-14.0 * speed_mult * dt / 1000.0), 0.92)
        robot._angle += da * angle_lerp

        # Wheel rotation — accumulate based on pixel distance moved
        moved = math.hypot(tx - robot._px, ty - robot._py)
        robot._wheel_rot = (robot._wheel_rot + moved * 0.18) % (2 * math.pi)

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(BG)
        draw_header(screen, fi, total, data, fonts, playing, speed_mult, robot, scores)
        draw_left(screen, fi, data, fonts, robot, scores)
        draw_arena(screen, robot, fonts)
        draw_right(screen, fi, data, ppm_h, temp_h, fonts, robot)
        draw_timeline(screen, fi, total, data, fonts, scores_hist, robot, fsm_events)

        # Export toast notification
        if emsg and etimer > 0:
            etimer -= dt
            ns = pygame.Surface((340, 26), pygame.SRCALPHA)
            ns.fill((0, 150, 50, 185))
            pygame.draw.rect(ns, GREEN, (0, 0, 340, 26), 1)
            ns.blit(fonts["md"].render(emsg, True, WHITE), (8, 5))
            screen.blit(ns, (WIN_W // 2 - 170, TIMELINE_Y + TIMELINE_H + 3))

        pygame.display.flip()

    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()