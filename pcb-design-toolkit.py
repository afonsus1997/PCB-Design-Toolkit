#!/usr/bin/env python3
"""
PCB Design Toolkit
Install: pip install PyQt6
Run:     python pcb-design-toolkit.py

A tabbed collection of checkers and calculators for everyday PCB design:
  • Voltage Divider Calculator
  • Voltage Divider Resistor Finder (E-series, with voltage error)
  • Resistor Power Dissipation (power rating + package suggestion)
  • Via Current Calculator (vias-per-hole-size for a target current)
  • More Tools (suggested roadmap)

The UI chrome intentionally mirrors the companion "Passive Component Part
Number Lookup" tool so the two feel like one suite.
"""

import sys, math
from typing import List, Optional, Tuple

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QLineEdit, QComboBox, QGroupBox, QGridLayout,
    QFrame, QStatusBar, QMessageBox, QPlainTextEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


# ─── UI palette (matching the companion passive-part tool) ───────────────────

class C:
    """UI-only colors for the application chrome."""
    BG_DARK   = "#1b2331"
    BG_MID    = "#232e3e"
    BG_LIGHT  = "#2c3a4e"
    BG_WIDGET = "#1e2a3a"
    TEXT      = "#d0d8e8"
    TEXT_DIM  = "#7b8da6"
    ACCENT    = "#4fc3f7"
    GOLD      = "#f0c040"
    BORDER    = "#3a4a5e"
    TABLE_ALT = "#232e3e"
    TABLE_SEL = "#2a4a6e"
    BTN_BG    = "#2c3a4e"
    BTN_HOVER = "#3a4a6e"
    GREEN     = "#4caf50"
    RED       = "#ef5350"
    ORANGE    = "#ff9800"
    PURPLE    = "#ab47bc"


STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {C.BG_DARK}; color: {C.TEXT};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; font-size: 13px;
}}
QGroupBox {{
    border: 1px solid {C.BORDER}; border-radius: 6px;
    margin-top: 10px; padding: 10px 8px 6px 8px;
    font-weight: bold; color: {C.ACCENT};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 6px; }}
QLineEdit, QComboBox, QTextEdit {{
    background-color: {C.BG_LIGHT}; border: 1px solid {C.BORDER};
    border-radius: 4px; padding: 4px 8px; color: {C.TEXT};
    selection-background-color: {C.TABLE_SEL};
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{ border-color: {C.ACCENT}; }}
QPushButton {{
    background-color: {C.BTN_BG}; border: 1px solid {C.BORDER};
    border-radius: 4px; padding: 5px 14px; color: {C.TEXT}; font-weight: 500;
}}
QPushButton:hover {{ background-color: {C.BTN_HOVER}; border-color: {C.ACCENT}; }}
QPushButton:pressed {{ background-color: {C.BG_DARK}; }}
QTabWidget::pane {{ border: 1px solid {C.BORDER}; border-radius: 4px; background: {C.BG_DARK}; }}
QTabBar::tab {{
    background: {C.BG_MID}; border: 1px solid {C.BORDER}; border-bottom: none;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
    padding: 6px 18px; color: {C.TEXT_DIM}; margin-right: 2px;
}}
QTabBar::tab:selected {{ background: {C.BG_DARK}; color: {C.ACCENT}; font-weight: bold; }}
QTableWidget {{
    background-color: {C.BG_WIDGET}; alternate-background-color: {C.TABLE_ALT};
    border: 1px solid {C.BORDER}; border-radius: 4px; gridline-color: {C.BORDER};
    color: {C.TEXT}; selection-background-color: {C.TABLE_SEL};
}}
QTableWidget::item {{ padding: 3px 6px; }}
QHeaderView::section {{
    background-color: {C.BG_MID}; border: 1px solid {C.BORDER};
    padding: 4px 8px; color: {C.ACCENT}; font-weight: bold; font-size: 12px;
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {C.BG_MID}; width: 10px; border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {C.BORDER}; border-radius: 5px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {C.ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {C.BG_MID}; height: 10px; border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {C.BORDER}; border-radius: 5px; min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background: {C.ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QStatusBar {{
    background-color: {C.BG_MID}; color: {C.TEXT_DIM};
    border-top: 1px solid {C.BORDER}; font-size: 12px;
}}
QMenuBar {{ background-color: {C.BG_MID}; color: {C.TEXT}; border-bottom: 1px solid {C.BORDER}; }}
QMenuBar::item:selected {{ background-color: {C.BTN_HOVER}; }}
QMenu {{ background-color: {C.BG_MID}; color: {C.TEXT}; border: 1px solid {C.BORDER}; }}
QMenu::item:selected {{ background-color: {C.TABLE_SEL}; }}
QDialog {{ background-color: {C.BG_DARK}; }}
QLabel {{ color: {C.TEXT}; }}
QFrame[frameShape="4"] {{ color: {C.BORDER}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox::down-arrow {{
    image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 6px solid {C.TEXT_DIM}; margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {C.BG_MID}; color: {C.TEXT}; border: 1px solid {C.BORDER};
    selection-background-color: {C.TABLE_SEL};
}}
"""


# ─── E-series standard values ────────────────────────────────────────────────

E_SERIES = {
    "E6":  [1.0, 1.5, 2.2, 3.3, 4.7, 6.8],
    "E12": [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2],
    "E24": [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
            3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1],
    "E48": [1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54, 1.62, 1.69,
            1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49, 2.61, 2.74, 2.87, 3.01,
            3.16, 3.32, 3.48, 3.65, 3.83, 4.02, 4.22, 4.42, 4.64, 4.87, 5.11, 5.36,
            5.62, 5.90, 6.19, 6.49, 6.81, 7.15, 7.50, 7.87, 8.25, 8.66, 9.09, 9.53],
    "E96": [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30,
            1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74,
            1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32,
            2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
            3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
            4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49,
            5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32,
            7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76],
}


def eseries_values(series: str, min_r: float = 1.0, max_r: float = 10e6) -> List[float]:
    """All standard values for a given E-series within [min_r, max_r]."""
    base = E_SERIES[series]
    values: set = set()
    decade = 1e-3
    while decade <= max_r * 10:
        for v in base:
            r = round(v * decade, 12)
            if min_r <= r <= max_r:
                values.add(r)
        decade *= 10
    return sorted(values)


def closest_eseries(val: float, series: str, n: int = 2) -> List[float]:
    """Return the *n* nearest E-series resistor values to *val*."""
    if val <= 0:
        return []
    exp = math.floor(math.log10(val))
    candidates = set()
    for e in range(exp - 1, exp + 3):
        dec = 10 ** e
        for s in E_SERIES.get(series, E_SERIES["E96"]):
            r = round(s * dec, 10)
            if 0.1 <= r <= 100e6:
                candidates.add(r)
    return sorted(candidates, key=lambda v: abs(v - val))[:n]


# ─── Value parsing / formatting ──────────────────────────────────────────────

def parse_resistance(text: str) -> Optional[float]:
    """Parse '10k', '4.7M', '33', '1R5', '4k7' → ohms."""
    import re
    text = text.strip().replace(",", ".").upper()
    if not text:
        return None
    text = text.rstrip("Ω").rstrip("OHM")
    mult = {"R": 1, "K": 1e3, "M": 1e6, "G": 1e9}
    # "4K7" / "1R5" style
    m = re.match(r'^(\d+)([RKMG])(\d+)$', text)
    if m:
        return float(f"{m.group(1)}.{m.group(3)}") * mult[m.group(2)]
    for suf, f in mult.items():
        if text.endswith(suf):
            try:
                return float(text[:-1]) * f
            except ValueError:
                return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_si(text: str, drop_unit: str) -> Optional[float]:
    """Case-sensitive SI parse (m=milli, k=kilo …). Used for V and A."""
    text = text.strip().replace(",", ".")
    if not text:
        return None
    for u in (drop_unit, drop_unit.lower()):
        if text.endswith(u):
            text = text[:-len(u)]
            break
    text = text.strip()
    pref = {"k": 1e3, "M": 1e6, "m": 1e-3, "u": 1e-6, "µ": 1e-6, "n": 1e-9}
    if text and text[-1] in pref:
        try:
            return float(text[:-1]) * pref[text[-1]]
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_voltage(text: str) -> Optional[float]:
    return _parse_si(text, "V")


def parse_current(text: str) -> Optional[float]:
    return _parse_si(text, "A")


def parse_freq(text: str) -> Optional[float]:
    return _parse_si(text, "Hz")


def parse_capacitance(text: str) -> Optional[float]:
    return _parse_si(text, "F")


def parse_inductance(text: str) -> Optional[float]:
    return _parse_si(text, "H")


def parse_length_mm(text: str) -> Optional[float]:
    """Parse '10mm', '1cm', '50mil', '2.5in', '0.5"' → mm."""
    text = text.strip().replace(",", ".").lower()
    if not text:
        return None
    for suf, mult in (("mil", 0.0254), ("mm", 1.0), ("cm", 10.0), ("in", 25.4),
                      ('"', 25.4), ("m", 1000.0)):
        if text.endswith(suf):
            try:
                return float(text[:-len(suf)].strip()) * mult
            except ValueError:
                return None
    try:
        return float(text)   # bare number = mm
    except ValueError:
        return None


def fmt_eng(val: float, unit: str, sig: int = 4) -> str:
    """Engineering-notation formatter, e.g. 0.0033 → '3.3 mA'."""
    if val == 0:
        return f"0 {unit}"
    neg = val < 0
    av = abs(val)
    prefixes = [(1e9, "G"), (1e6, "M"), (1e3, "k"), (1.0, ""),
                (1e-3, "m"), (1e-6, "µ"), (1e-9, "n"), (1e-12, "p")]
    for thr, p in prefixes:
        if av >= thr:
            num = av / thr
            s = f"{num:.{sig}g}"
            return f"{'-' if neg else ''}{s} {p}{unit}"
    return f"{val:.{sig}g} {unit}"


def fmt_ohm(val: float) -> str:
    if val >= 1e6:
        return f"{val/1e6:g}MΩ"
    if val >= 1e3:
        return f"{val/1e3:g}kΩ"
    return f"{val:g}Ω"


# ─── Engineering core (pure functions, unit-tested separately) ────────────────

def divider_vout(vin: float, r1: float, r2: float, rload: float = 0.0) -> float:
    """Vout of a top(R1)/bottom(R2) divider, optional load across R2."""
    r_bottom = r2 if rload <= 0 else (r2 * rload) / (r2 + rload)
    return vin * r_bottom / (r1 + r_bottom)


def find_divider_combos(vin: float, vout: float, series: str,
                        rmin: float, rmax: float,
                        max_results: int = 25) -> List[Tuple[float, float, float, float]]:
    """Brute-force R1/R2 pairs in [rmin, rmax]; return (r1, r2, vout_actual, err%)."""
    vals = eseries_values(series, rmin, rmax)
    out = []
    for r1 in vals:
        for r2 in vals:
            vo = vin * r2 / (r1 + r2)
            err = (vo - vout) / vout * 100.0
            out.append((r1, r2, vo, err))
    out.sort(key=lambda t: abs(t[3]))
    return out[:max_results]


def find_divider_auto(vin: float, vout: float, series: str,
                      max_results: int = 25) -> List[Tuple[float, float, float, float]]:
    """Sweep R2 over a wide range, snap ideal R1 to the E-series. Handles big ratios."""
    ratio = vin / vout - 1.0          # R1 / R2
    seen = set()
    out = []
    for r2 in eseries_values(series, 100.0, 1e6):
        ideal_r1 = r2 * ratio
        for r1 in closest_eseries(ideal_r1, series, n=2):
            key = (round(r1, 6), round(r2, 6))
            if key in seen:
                continue
            seen.add(key)
            vo = vin * r2 / (r1 + r2)
            err = (vo - vout) / vout * 100.0
            out.append((r1, r2, vo, err))
    out.sort(key=lambda t: abs(t[3]))
    return out[:max_results]


# Standard SMD chip-resistor packages: (imperial, metric, typical power rating W)
SMD_PACKAGES = [
    ("0201", "0603", 0.05),
    ("0402", "1005", 0.063),
    ("0603", "1608", 0.10),
    ("0805", "2012", 0.125),
    ("1206", "3216", 0.25),
    ("1210", "3225", 0.50),
    ("2010", "5025", 0.75),
    ("2512", "6332", 1.0),
]
# Common through-hole axial power ratings (W)
TH_RATINGS = [0.125, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0]


def recommend_package(power_w: float, derate: float):
    """Required rating after derating, plus smallest passing SMD pkg and TH rating."""
    required = power_w / derate
    smd = next((p for p in SMD_PACKAGES if p[2] >= required), None)
    th = next((r for r in TH_RATINGS if r >= required), None)
    return required, smd, th


# Standard finished via/hole diameters (mm)
VIA_HOLE_SIZES_MM = [0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.80, 1.00]
MM_PER_MIL = 0.0254
MIL_PER_MM = 1.0 / MM_PER_MIL  # 39.3700787...


def via_copper_area_mil2(d_mm: float, plating_um: float) -> float:
    """Cross-sectional copper area of a plated via barrel, in mil².
    Annulus area = π · t · (d + t), with d = finished hole dia, t = plating."""
    d_mil = d_mm * MIL_PER_MM
    t_mil = (plating_um / 1000.0) * MIL_PER_MM
    return math.pi * t_mil * (d_mil + t_mil)


def ipc_current(area_mil2: float, delta_t: float, k: float) -> float:
    """IPC-2221 current capacity: I = k · ΔT^0.44 · A^0.725  (A, °C, mil²)."""
    return k * (delta_t ** 0.44) * (area_mil2 ** 0.725)


def vias_needed(i_target: float, i_per_via: float, safety: float) -> int:
    if i_per_via <= 0:
        return 0
    return max(1, math.ceil(i_target * safety / i_per_via))


# ─── Traces: width, impedance, resistance ────────────────────────────────────

# Finished copper thickness in mil for a given plating weight (incl. typical
# plating on top of base foil — slightly rounded for everyday use).
COPPER_THICKNESS_MIL = {
    "0.5 oz (17 µm)": 0.65,
    "1 oz (35 µm)":   1.378,
    "2 oz (70 µm)":   2.756,
    "3 oz (105 µm)":  4.134,
}
COPPER_RHO_20C = 1.7241e-8       # Ω·m
COPPER_ALPHA   = 0.00393         # 1/K  (resistivity TC)


def trace_required_width_mil(i: float, dt: float, k: float, t_mil: float) -> float:
    """IPC-2221 inverted: width (mil) for current *i* (A)."""
    if i <= 0 or dt <= 0 or k <= 0 or t_mil <= 0:
        return 0.0
    area = (i / (k * dt ** 0.44)) ** (1.0 / 0.725)
    return area / t_mil


def trace_capacity_a(width_mil: float, t_mil: float, dt: float, k: float) -> float:
    """IPC-2221 current capacity for a trace (mil, mil, °C)."""
    return ipc_current(width_mil * t_mil, dt, k)


def trace_resistance_ohm(length_mm: float, width_mm: float,
                          thickness_um: float, temp_c: float = 20.0) -> float:
    area = (width_mm * 1e-3) * (thickness_um * 1e-6)
    if area <= 0:
        return 0.0
    rho = COPPER_RHO_20C * (1.0 + COPPER_ALPHA * (temp_c - 20.0))
    return rho * (length_mm * 1e-3) / area


# Controlled-impedance estimates — IPC-2141 simplified.
def microstrip_z0(w_mil: float, h_mil: float, t_mil: float, er: float) -> float:
    if w_mil <= 0 or h_mil <= 0 or er <= 0:
        return 0.0
    return 87.0 / math.sqrt(er + 1.41) * math.log(5.98 * h_mil / (0.8 * w_mil + t_mil))


def stripline_z0(w_mil: float, b_mil: float, t_mil: float, er: float) -> float:
    if w_mil <= 0 or b_mil <= 0 or er <= 0:
        return 0.0
    return 60.0 / math.sqrt(er) * math.log(4.0 * b_mil / (0.67 * math.pi * (0.8 * w_mil + t_mil)))


def diff_microstrip_z0(w_mil: float, s_mil: float, h_mil: float,
                        t_mil: float, er: float) -> float:
    z0 = microstrip_z0(w_mil, h_mil, t_mil, er)
    if z0 <= 0:
        return 0.0
    return 2.0 * z0 * (1.0 - 0.48 * math.exp(-0.96 * s_mil / h_mil))


def diff_stripline_z0(w_mil: float, s_mil: float, b_mil: float,
                       t_mil: float, er: float) -> float:
    z0 = stripline_z0(w_mil, b_mil, t_mil, er)
    if z0 <= 0:
        return 0.0
    return 2.0 * z0 * (1.0 - 0.347 * math.exp(-2.9 * s_mil / b_mil))


def microstrip_er_eff(w_mil: float, h_mil: float, er: float) -> float:
    if w_mil <= 0 or h_mil <= 0:
        return er
    return (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 12.0 * h_mil / w_mil) ** -0.5


def propagation_delay_ps_per_inch(er_eff: float) -> float:
    """~85 ps/inch in vacuum-equivalent, slowed by √εr_eff."""
    return 84.72 * math.sqrt(max(1.0, er_eff))


# ─── Components & values ─────────────────────────────────────────────────────

def led_resistor(vs: float, vf: float, i_f: float) -> Tuple[float, float]:
    drop = vs - vf
    if i_f <= 0 or drop <= 0:
        return 0.0, 0.0
    return drop / i_f, drop * i_f


def find_combo(target: float, series: str, max_results: int = 25):
    """Single / series / parallel E-series combos closest to *target* (Ω)."""
    if target <= 0:
        return []
    decade = math.floor(math.log10(target))
    vals = eseries_values(series, 10 ** (decade - 2), 10 ** (decade + 3))
    out = []
    for r in closest_eseries(target, series, 3):
        err = (r - target) / target * 100.0
        out.append(("single", r, 0.0, r, err))
    for r1 in vals:
        if r1 >= target:
            break
        ideal = target - r1
        for r2 in closest_eseries(ideal, series, 2):
            actual = r1 + r2
            err = (actual - target) / target * 100.0
            out.append(("series", r1, r2, actual, err))
    for r1 in vals:
        if r1 <= target:
            continue
        ideal = (r1 * target) / (r1 - target)
        for r2 in closest_eseries(ideal, series, 2):
            actual = (r1 * r2) / (r1 + r2)
            err = (actual - target) / target * 100.0
            out.append(("parallel", r1, r2, actual, err))
    seen, dedupe = set(), []
    for row in out:
        kind, a, b, _, _ = row
        key = (kind, min(a, b) if b else a, max(a, b) if b else 0.0)
        if key in seen:
            continue
        seen.add(key)
        dedupe.append(row)
    dedupe.sort(key=lambda r: abs(r[4]))
    return dedupe[:max_results]


# ─── Filters & capacitors ────────────────────────────────────────────────────

def rc_cutoff(r: float, c: float) -> float:
    return 1.0 / (2.0 * math.pi * r * c) if r > 0 and c > 0 else 0.0


def rl_cutoff(r: float, l: float) -> float:
    return r / (2.0 * math.pi * l) if r > 0 and l > 0 else 0.0


def cap_holdup_f(i_load: float, t_hold: float, dv: float) -> float:
    return i_load * t_hold / dv if dv > 0 else 0.0


def cap_for_ripple_buck(i_ripple: float, fsw: float, dv: float) -> float:
    return i_ripple / (8.0 * fsw * dv) if fsw > 0 and dv > 0 else 0.0


def cap_energy_j(c: float, v: float) -> float:
    return 0.5 * c * v * v


def crystal_matched_caps(cl: float, c_stray: float) -> float:
    """C1 = C2 needed to present CL to a crystal, given stray (all in F)."""
    return 2.0 * (cl - c_stray)


# ─── Power & thermal ─────────────────────────────────────────────────────────

def ldo_dissipation_w(vin: float, vout: float, iout: float, iq: float = 0.0) -> float:
    return max(0.0, (vin - vout) * iout + vin * iq)


def junction_temp_c(p_w: float, theta_ja: float, t_amb: float) -> float:
    return t_amb + p_w * theta_ja


def copper_pour_theta_ja(area_cm2: float, copper_oz: float = 1.0,
                          layers: float = 1.0) -> float:
    """Empirical θJA (°C/W) for a small SMT power device on a copper pour.
    Heuristic θJA ≈ 60/√(A·oz·layers) + 25, floored ~25 — only loosely
    matches JESD51-style numbers; vendor datasheet always wins."""
    if area_cm2 <= 0:
        return 200.0
    eff = max(0.5, area_cm2 * copper_oz * layers)
    return 60.0 / math.sqrt(eff) + 25.0


def buck_duty(vin: float, vout: float) -> float:
    return vout / vin if vin > 0 else 0.0


def boost_duty(vin: float, vout: float) -> float:
    return 1.0 - vin / vout if vout > 0 else 0.0


def buck_inductor_ripple_a(vin: float, vout: float, l: float, fsw: float) -> float:
    if vin <= 0 or l <= 0 or fsw <= 0:
        return 0.0
    d = vout / vin
    return vout * (1.0 - d) / (l * fsw)


def boost_inductor_ripple_a(vin: float, vout: float, l: float, fsw: float) -> float:
    if vout <= 0 or l <= 0 or fsw <= 0:
        return 0.0
    d = 1.0 - vin / vout
    return vin * d / (l * fsw)


# ─── Manufacturing ───────────────────────────────────────────────────────────

# IPC-6012 minimum external annular ring (mm) per producibility class.
IPC_CLASS_AR_MM = {
    "Class 1 (consumer)":  0.05,
    "Class 2 (general)":   0.05,
    "Class 3 (high-rel)":  0.10,
}


def annular_ring_mm(pad_mm: float, drill_mm: float,
                     drill_tol_mm: float = 0.075) -> float:
    """Worst-case annular ring after drilling and registration tolerance."""
    finished = drill_mm + drill_tol_mm
    return (pad_mm - finished) / 2.0


def boards_per_panel(board_x: float, board_y: float,
                      panel_x: float, panel_y: float,
                      spacing: float, rail: float):
    """Return (n_default, n_rotated, nx, ny, nx_rot, ny_rot)."""
    ux = panel_x - 2 * rail
    uy = panel_y - 2 * rail

    def fit(bx: float, by: float):
        if bx <= 0 or by <= 0 or ux <= 0 or uy <= 0:
            return 0, 0
        nx = max(0, math.floor((ux + spacing) / (bx + spacing)))
        ny = max(0, math.floor((uy + spacing) / (by + spacing)))
        return nx, ny

    nx1, ny1 = fit(board_x, board_y)
    nx2, ny2 = fit(board_y, board_x)
    return nx1 * ny1, nx2 * ny2, nx1, ny1, nx2, ny2


# IPC-7351-style "Nominal (N)" land patterns for common 2-/multi-terminal parts.
# Values are *approximate* and aimed at quick reference — verify with your
# library tool (e.g. KiCad's IPC calculator) before laying out a real footprint.
IPC7351_LANDS = [
    # (package,            density, pad_w_mm, pad_h_mm, pitch_mm, court_w, court_h, notes)
    ("0201 (0603 metric)", "N",  0.30, 0.30, 0.65, 1.10, 0.70,  "Chip R/C, hand-solder difficult"),
    ("0402 (1005 metric)", "N",  0.55, 0.55, 1.20, 1.90, 0.90,  "Chip R/C"),
    ("0603 (1608 metric)", "N",  0.80, 0.90, 1.80, 2.60, 1.40,  "Chip R/C, easy hand-rework"),
    ("0805 (2012 metric)", "N",  0.95, 1.30, 2.20, 3.00, 1.80,  "Chip R/C"),
    ("1206 (3216 metric)", "N",  1.10, 1.80, 3.10, 4.00, 2.10,  "Chip R/C, common power"),
    ("1210 (3225 metric)", "N",  1.10, 2.80, 3.10, 4.00, 3.10,  "Chip cap, MLCC bulk"),
    ("SOD-123",            "N",  0.90, 1.20, 3.55, 4.50, 2.10,  "Small-signal diode"),
    ("SOD-323",            "N",  0.60, 0.65, 2.20, 3.20, 1.60,  "Small-signal diode"),
    ("SOT-23-3",           "N",  1.00, 1.20, 1.90, 3.50, 3.00,  "Pitch 0.95 mm"),
    ("SOT-23-5",           "N",  0.65, 1.10, 0.95, 3.10, 3.00,  "Pitch 0.95 mm"),
    ("SOT-223",            "N",  1.60, 2.20, 2.30, 7.80, 4.30,  "Tab pad ~3.5 × 1.8 mm"),
    ("SOIC-8 (3.9 mm)",    "N",  0.60, 1.55, 1.27, 6.20, 5.40,  "Pitch 1.27 mm"),
    ("SOIC-16 (3.9 mm)",   "N",  0.60, 1.55, 1.27, 11.30, 5.40, "Pitch 1.27 mm"),
    ("SSOP-16",            "N",  0.40, 1.45, 0.635, 7.60, 5.20, "Pitch 0.635 mm"),
    ("TSSOP-14",           "N",  0.30, 1.30, 0.65, 6.10, 5.20,  "Pitch 0.65 mm"),
    ("QFP-32 0.8 mm",      "N",  0.40, 1.50, 0.80, 9.50, 9.50,  "Pitch 0.80 mm"),
    ("QFP-64 0.5 mm",      "N",  0.28, 1.50, 0.50, 12.50, 12.50,"Pitch 0.50 mm"),
    ("QFN 0.5 mm",         "N",  0.30, 0.70, 0.50, 5.20, 5.20,  "+ thermal pad"),
    ("QFN 0.4 mm",         "N",  0.23, 0.60, 0.40, 5.20, 5.20,  "+ thermal pad"),
    ("DPAK / TO-252",      "N",  1.65, 2.50, 4.57, 9.60, 7.00,  "Tab ~6.4 × 5.7 mm"),
]


# ─── Shared small widgets ────────────────────────────────────────────────────

def accent_button(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setStyleSheet(
        f"background:{C.ACCENT}; color:#000; font-weight:bold;"
        f"padding:7px 24px; border-radius:4px; font-size:13px;")
    return b


def result_card(title: str) -> Tuple[QGroupBox, QGridLayout]:
    grp = QGroupBox(title)
    grid = QGridLayout(grp)
    grid.setHorizontalSpacing(18)
    grid.setVerticalSpacing(7)
    return grp, grid


def big_value_label() -> QLabel:
    lbl = QLabel("—")
    lbl.setFont(QFont("Consolas", 15, QFont.Weight.Bold))
    lbl.setStyleSheet(f"color:{C.GOLD};")
    return lbl


def status_label() -> QLabel:
    lbl = QLabel("")
    lbl.setStyleSheet(f"color:{C.TEXT_DIM}; font-size:11px; padding:2px 4px;")
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setWordWrap(True)
    return lbl


def err_color(abs_pct: float) -> str:
    if abs_pct < 0.1:
        return C.GREEN
    if abs_pct < 1.0:
        return C.GOLD
    if abs_pct < 5.0:
        return C.ORANGE
    return C.RED


# ─── Tab 1: Voltage Divider Calculator ───────────────────────────────────────

class DividerCalcTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        grp = QGroupBox("Divider Inputs  (R1 = top / high side,  R2 = bottom / output side)")
        grid = QGridLayout(grp)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Input Voltage (Vin):"), 0, 0)
        self.w_vin = QLineEdit("5")
        self.w_vin.setPlaceholderText("e.g. 5, 3.3, 12")
        grid.addWidget(self.w_vin, 0, 1)

        grid.addWidget(QLabel("R1 (top):"), 0, 2)
        self.w_r1 = QLineEdit("10k")
        self.w_r1.setPlaceholderText("e.g. 10k, 4.7k")
        grid.addWidget(self.w_r1, 0, 3)

        grid.addWidget(QLabel("R2 (bottom):"), 1, 0)
        self.w_r2 = QLineEdit("10k")
        self.w_r2.setPlaceholderText("e.g. 10k, 2.2k")
        grid.addWidget(self.w_r2, 1, 1)

        grid.addWidget(QLabel("Load across R2 (optional):"), 1, 2)
        self.w_rload = QLineEdit("")
        self.w_rload.setPlaceholderText("e.g. 100k  (blank = none)")
        grid.addWidget(self.w_rload, 1, 3)

        self.btn = accent_button("Calculate")
        self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 2, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        outer.addWidget(grp)

        for w in (self.w_vin, self.w_r1, self.w_r2, self.w_rload):
            w.returnPressed.connect(self._calc)

        # quick Vin presets
        qf = QFrame()
        qf.setStyleSheet(f"background:{C.BG_MID}; border-radius:4px;")
        ql = QHBoxLayout(qf)
        ql.setContentsMargins(8, 4, 8, 4)
        ql.addWidget(QLabel("Quick Vin:"))
        for v in ["1.8", "3.3", "5", "12", "24", "48"]:
            b = QPushButton(v)
            b.setFixedWidth(46)
            b.setStyleSheet("padding:3px 4px; font-size:12px;")
            b.clicked.connect(lambda _, val=v: (self.w_vin.setText(val), self._calc()))
            ql.addWidget(b)
        ql.addStretch()
        outer.addWidget(qf)

        # results
        rc, rg = result_card("Results")
        self.lbl_vout = big_value_label()
        self.lbl_vout_loaded = QLabel("—")
        self.lbl_vout_loaded.setFont(QFont("Consolas", 12))
        self.lbl_vout_loaded.setStyleSheet(f"color:{C.ACCENT};")
        self.lbl_i = QLabel("—")
        self.lbl_p_total = QLabel("—")
        self.lbl_p_r1 = QLabel("—")
        self.lbl_p_r2 = QLabel("—")
        for w in (self.lbl_i, self.lbl_p_total, self.lbl_p_r1, self.lbl_p_r2):
            w.setFont(QFont("Consolas", 12))
            w.setStyleSheet(f"color:{C.TEXT};")

        def cap(t):
            l = QLabel(t); l.setStyleSheet(f"color:{C.TEXT_DIM};"); return l

        rg.addWidget(cap("Vout (no load):"), 0, 0)
        rg.addWidget(self.lbl_vout, 0, 1)
        rg.addWidget(cap("Vout (loaded):"), 0, 2)
        rg.addWidget(self.lbl_vout_loaded, 0, 3)
        rg.addWidget(cap("Quiescent current:"), 1, 0)
        rg.addWidget(self.lbl_i, 1, 1)
        rg.addWidget(cap("Total power:"), 1, 2)
        rg.addWidget(self.lbl_p_total, 1, 3)
        rg.addWidget(cap("Power in R1:"), 2, 0)
        rg.addWidget(self.lbl_p_r1, 2, 1)
        rg.addWidget(cap("Power in R2:"), 2, 2)
        rg.addWidget(self.lbl_p_r2, 2, 3)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)

        outer.addStretch(1)
        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        vin = parse_voltage(self.w_vin.text())
        r1 = parse_resistance(self.w_r1.text())
        r2 = parse_resistance(self.w_r2.text())
        rl_text = self.w_rload.text().strip()
        rload = parse_resistance(rl_text) if rl_text else 0.0

        if vin is None or r1 is None or r2 is None or (rl_text and rload is None):
            self.status.setText(f"<span style='color:{C.RED};'>Check your inputs — "
                                f"Vin, R1 and R2 must be valid numbers.</span>")
            return
        if r1 <= 0 or r2 <= 0:
            self.status.setText(f"<span style='color:{C.RED};'>R1 and R2 must be &gt; 0.</span>")
            return

        vout = divider_vout(vin, r1, r2, 0.0)
        i = vin / (r1 + r2)
        p_total = vin * i
        p_r1 = i * i * r1
        p_r2 = i * i * r2

        self.lbl_vout.setText(fmt_eng(vout, "V"))
        self.lbl_i.setText(fmt_eng(i, "A"))
        self.lbl_p_total.setText(fmt_eng(p_total, "W"))
        self.lbl_p_r1.setText(fmt_eng(p_r1, "W"))
        self.lbl_p_r2.setText(fmt_eng(p_r2, "W"))

        if rload and rload > 0:
            vout_l = divider_vout(vin, r1, r2, rload)
            droop = (vout_l - vout) / vout * 100.0 if vout else 0.0
            self.lbl_vout_loaded.setText(
                f"{fmt_eng(vout_l, 'V')}  ({droop:+.2f}%)")
        else:
            self.lbl_vout_loaded.setText("— (no load)")

        ratio = r2 / (r1 + r2)
        self.status.setText(
            f"<span style='color:{C.GREEN};'>Vout = Vin · R2/(R1+R2) = "
            f"{fmt_eng(vin,'V')} · {ratio:.4f} = {fmt_eng(vout,'V')}.</span>  "
            f"<span style='color:{C.TEXT_DIM};'>Tip: lower R values = stiffer output but "
            f"more standing current.</span>")


# ─── Tab 2: Voltage Divider Resistor Finder ──────────────────────────────────

class DividerFinderTab(QWidget):
    RANGES = {
        "100 Ω – 1 kΩ":   (100.0, 1e3),
        "1 k – 10 kΩ":    (1e3, 10e3),
        "10 k – 100 kΩ":  (10e3, 100e3),
        "100 k – 1 MΩ":   (100e3, 1e6),
        "Auto (wide)":    None,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        grp = QGroupBox("Find R1 / R2 for a Target Output Voltage")
        grid = QGridLayout(grp)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Vin:"), 0, 0)
        self.w_vin = QLineEdit("12")
        self.w_vin.setMinimumWidth(90)
        grid.addWidget(self.w_vin, 0, 1)

        grid.addWidget(QLabel("Target Vout:"), 0, 2)
        self.w_vout = QLineEdit("3.3")
        self.w_vout.setMinimumWidth(90)
        grid.addWidget(self.w_vout, 0, 3)

        grid.addWidget(QLabel("E-Series:"), 0, 4)
        self.w_series = QComboBox()
        self.w_series.addItems(["E6", "E12", "E24", "E48", "E96"])
        self.w_series.setCurrentText("E24")
        grid.addWidget(self.w_series, 0, 5)

        grid.addWidget(QLabel("Resistor range:"), 1, 0)
        self.w_range = QComboBox()
        self.w_range.addItems(list(self.RANGES.keys()))
        self.w_range.setCurrentText("10 k – 100 kΩ")
        self.w_range.setMinimumWidth(140)
        grid.addWidget(self.w_range, 1, 1, 1, 2)

        grid.addWidget(QLabel("Max results:"), 1, 3)
        self.w_max = QComboBox()
        self.w_max.addItems(["10", "25", "50"])
        self.w_max.setCurrentText("25")
        grid.addWidget(self.w_max, 1, 4)

        self.btn = accent_button("Find Resistors")
        self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 6, 2, 1)
        grid.setColumnStretch(6, 0)
        outer.addWidget(grp)

        for w in (self.w_vin, self.w_vout):
            w.returnPressed.connect(self._calc)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["R1 (top)", "R2 (bottom)", "Actual Vout", "Error", "Error (mV)", "Divider I"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for c in range(5):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemDoubleClicked.connect(self._copy_row)
        outer.addWidget(self.table, 1)

        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _copy_row(self, item):
        r = item.row()
        cells = [self.table.item(r, c).text() for c in range(3)]
        QApplication.clipboard().setText(
            f"R1={cells[0]}  R2={cells[1]}  Vout={cells[2]}")
        self.status.setText(f"<span style='color:{C.GREEN};'>Copied row.</span>")

    def _calc(self):
        vin = parse_voltage(self.w_vin.text())
        vout = parse_voltage(self.w_vout.text())
        if vin is None or vout is None:
            self.status.setText(f"<span style='color:{C.RED};'>Enter valid Vin and Vout.</span>")
            return
        if not (0 < vout < vin):
            self.status.setText(
                f"<span style='color:{C.RED};'>A passive divider needs 0 &lt; Vout &lt; Vin.</span>")
            self.table.setRowCount(0)
            return

        series = self.w_series.currentText()
        n = int(self.w_max.currentText())
        rng = self.RANGES[self.w_range.currentText()]
        if rng is None:
            results = find_divider_auto(vin, vout, series, n)
        else:
            results = find_divider_combos(vin, vout, series, rng[0], rng[1], n)
        self._populate(results, vin, vout)

    def _populate(self, results, vin, vout):
        self.table.setRowCount(len(results))
        for row, (r1, r2, vo, err) in enumerate(results):
            i_div = vin / (r1 + r2)
            err_mv = (vo - vout) * 1000.0
            cells = [fmt_ohm(r1), fmt_ohm(r2), fmt_eng(vo, "V"),
                     f"{err:+.3f}%", f"{err_mv:+.1f}", fmt_eng(i_div, "A")]
            for col, text in enumerate(cells):
                it = QTableWidgetItem(text)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col in (0, 1):
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                    it.setForeground(QColor(C.GOLD))
                    it.setToolTip("Double-click to copy this row")
                elif col == 2:
                    it.setFont(QFont("Consolas", 12))
                    it.setForeground(QColor(C.ACCENT))
                elif col in (3, 4):
                    it.setFont(QFont("Consolas", 11))
                    it.setForeground(QColor(err_color(abs(err))))
                else:
                    it.setFont(QFont("Consolas", 11))
                    it.setForeground(QColor(C.TEXT_DIM))
                self.table.setItem(row, col, it)
        self.table.resizeColumnsToContents()

        if results:
            b = results[0]
            self.status.setText(
                f"<span style='color:{C.GREEN};'>✓ {len(results)} pair(s). Best: "
                f"R1 {fmt_ohm(b[0])} / R2 {fmt_ohm(b[1])} → {fmt_eng(b[2],'V')} "
                f"({b[3]:+.3f}%).</span>  "
                f"<span style='color:{C.TEXT_DIM};'>Double-click a row to copy.</span>")
        else:
            self.status.setText(
                f"<span style='color:{C.RED};'>No combinations found in that range — "
                f"try a wider range or Auto.</span>")


# ─── Tab 3: Resistor Power Dissipation ───────────────────────────────────────

class ResistorPowerTab(QWidget):
    DERATE = {
        "Conservative — 50% of rating (2× headroom)": 0.50,
        "Standard — 60% of rating": 0.60,
        "Relaxed — 70% of rating": 0.70,
        "Minimal — 80% of rating": 0.80,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        grp = QGroupBox("Resistor & Current")
        grid = QGridLayout(grp)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Resistor value:"), 0, 0)
        self.w_r = QLineEdit("100")
        self.w_r.setPlaceholderText("e.g. 100, 4.7k, 0R1")
        grid.addWidget(self.w_r, 0, 1)

        grid.addWidget(QLabel("Max current:"), 0, 2)
        self.w_i = QLineEdit("50m")
        self.w_i.setPlaceholderText("e.g. 50m, 0.5, 1.2")
        grid.addWidget(self.w_i, 0, 3)

        grid.addWidget(QLabel("Derating policy:"), 1, 0)
        self.w_derate = QComboBox()
        self.w_derate.addItems(list(self.DERATE.keys()))
        self.w_derate.setMinimumWidth(260)
        grid.addWidget(self.w_derate, 1, 1, 1, 3)

        self.btn = accent_button("Calculate")
        self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 2, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        outer.addWidget(grp)

        for w in (self.w_r, self.w_i):
            w.returnPressed.connect(self._calc)
        self.w_derate.currentIndexChanged.connect(self._calc)

        rc, rg = result_card("Dissipation & Recommendation")

        def cap(t):
            l = QLabel(t); l.setStyleSheet(f"color:{C.TEXT_DIM};"); return l

        self.lbl_p = big_value_label()
        self.lbl_v = QLabel("—"); self.lbl_v.setFont(QFont("Consolas", 12))
        self.lbl_req = QLabel("—"); self.lbl_req.setFont(QFont("Consolas", 12))
        self.lbl_req.setStyleSheet(f"color:{C.ACCENT};")
        self.lbl_smd = QLabel("—"); self.lbl_smd.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.lbl_smd.setStyleSheet(f"color:{C.GREEN};")
        self.lbl_th = QLabel("—"); self.lbl_th.setFont(QFont("Consolas", 12))

        rg.addWidget(cap("Dissipated power (I²R):"), 0, 0); rg.addWidget(self.lbl_p, 0, 1)
        rg.addWidget(cap("Voltage across (I·R):"), 0, 2); rg.addWidget(self.lbl_v, 0, 3)
        rg.addWidget(cap("Required rating:"), 1, 0); rg.addWidget(self.lbl_req, 1, 1)
        rg.addWidget(cap("Suggested SMD package:"), 2, 0); rg.addWidget(self.lbl_smd, 2, 1, 1, 3)
        rg.addWidget(cap("Smallest through-hole:"), 3, 0); rg.addWidget(self.lbl_th, 3, 1, 1, 3)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["SMD Package (imperial)", "Metric", "Rated Power", "Verdict"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for c in range(3):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents)
        outer.addWidget(self.table, 1)

        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        r = parse_resistance(self.w_r.text())
        i = parse_current(self.w_i.text())
        if r is None or i is None or r <= 0 or i < 0:
            self.status.setText(
                f"<span style='color:{C.RED};'>Enter a valid resistor value and current.</span>")
            return

        p = i * i * r
        v = i * r
        derate = self.DERATE[self.w_derate.currentText()]
        required, smd, th = recommend_package(p, derate)

        self.lbl_p.setText(fmt_eng(p, "W"))
        self.lbl_v.setText(fmt_eng(v, "V"))
        self.lbl_req.setText(f"≥ {fmt_eng(required, 'W')}  (at {int(derate*100)}% of rating)")

        if smd:
            self.lbl_smd.setText(
                f"{smd[0]}  ({smd[1]} metric) — rated {fmt_eng(smd[2],'W')}")
            self.lbl_smd.setStyleSheet(f"color:{C.GREEN};")
        else:
            self.lbl_smd.setText("None — exceeds common chip-resistor ratings; "
                                 "use through-hole / power resistor.")
            self.lbl_smd.setStyleSheet(f"color:{C.ORANGE};")
        if th:
            self.lbl_th.setText(f"{fmt_eng(th, 'W')} axial / power resistor")
        else:
            self.lbl_th.setText("> 5 W — use a dedicated power/chassis resistor with heatsinking.")

        # full SMD table
        self.table.setRowCount(len(SMD_PACKAGES))
        for row, (imp, met, rated) in enumerate(SMD_PACKAGES):
            ok = rated >= required
            verdict = "✓ OK" if ok else "✗ too small"
            cells = [imp, met, fmt_eng(rated, "W"), verdict]
            for col, text in enumerate(cells):
                it = QTableWidgetItem(text)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                    it.setForeground(QColor(C.GOLD))
                elif col == 3:
                    it.setForeground(QColor(C.GREEN if ok else C.RED))
                    if smd and imp == smd[0]:
                        it.setText("✓ recommended")
                        it.setForeground(QColor(C.ACCENT))
                else:
                    it.setForeground(QColor(C.TEXT))
                self.table.setItem(row, col, it)
        self.table.resizeColumnsToContents()

        self.status.setText(
            f"<span style='color:{C.GREEN};'>P = I²·R = ({fmt_eng(i,'A')})² · {fmt_ohm(r)} "
            f"= {fmt_eng(p,'W')}.</span>  "
            f"<span style='color:{C.TEXT_DIM};'>Ratings are nominal at 70°C ambient; "
            f"check the datasheet derating curve for your temperature.</span>")


# ─── Tab 4: Via Current Calculator ───────────────────────────────────────────

class ViaCurrentTab(QWidget):
    PLATING = {
        "18 µm (~0.5 oz)": 18.0,
        "20 µm (IPC Class 2 min)": 20.0,
        "25 µm (IPC Class 3, ~1 oz)": 25.0,
        "35 µm (~1 oz nominal)": 35.0,
    }
    DELTA_T = {"10 °C rise": 10.0, "20 °C rise": 20.0, "30 °C rise": 30.0}
    LOCATION = {
        "Internal — conservative (k=0.024)": 0.024,
        "External — optimistic (k=0.048)": 0.048,
    }
    SAFETY = {"× 1.0 (none)": 1.0, "× 1.5": 1.5, "× 2.0": 2.0}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        grp = QGroupBox("Target Current & Via Assumptions")
        grid = QGridLayout(grp)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Max current:"), 0, 0)
        self.w_i = QLineEdit("3")
        self.w_i.setPlaceholderText("e.g. 3, 500m, 10")
        grid.addWidget(self.w_i, 0, 1)

        grid.addWidget(QLabel("Barrel plating:"), 0, 2)
        self.w_plate = QComboBox()
        self.w_plate.addItems(list(self.PLATING.keys()))
        self.w_plate.setCurrentText("25 µm (IPC Class 3, ~1 oz)")
        self.w_plate.setMinimumWidth(190)
        grid.addWidget(self.w_plate, 0, 3)

        grid.addWidget(QLabel("Temp rise (ΔT):"), 1, 0)
        self.w_dt = QComboBox()
        self.w_dt.addItems(list(self.DELTA_T.keys()))
        self.w_dt.setCurrentText("10 °C rise")
        grid.addWidget(self.w_dt, 1, 1)

        grid.addWidget(QLabel("Conductor model:"), 1, 2)
        self.w_loc = QComboBox()
        self.w_loc.addItems(list(self.LOCATION.keys()))
        self.w_loc.setMinimumWidth(190)
        grid.addWidget(self.w_loc, 1, 3)

        grid.addWidget(QLabel("Safety factor:"), 2, 0)
        self.w_sf = QComboBox()
        self.w_sf.addItems(list(self.SAFETY.keys()))
        grid.addWidget(self.w_sf, 2, 1)

        self.btn = accent_button("Calculate")
        self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 3, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        outer.addWidget(grp)

        self.w_i.returnPressed.connect(self._calc)
        for w in (self.w_plate, self.w_dt, self.w_loc, self.w_sf):
            w.currentIndexChanged.connect(self._calc)

        self.lbl_head = QLabel("")
        self.lbl_head.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_head.setStyleSheet(f"color:{C.GOLD}; font-size:13px; font-weight:bold;")
        outer.addWidget(self.lbl_head)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Finished Hole", "Hole (mil)", "Cu Area (mil²)", "Current / Via", "Vias Needed"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for c in range(4):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents)
        outer.addWidget(self.table, 1)

        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        i_target = parse_current(self.w_i.text())
        if i_target is None or i_target <= 0:
            self.status.setText(
                f"<span style='color:{C.RED};'>Enter a valid target current.</span>")
            return

        plating = self.PLATING[self.w_plate.currentText()]
        dt = self.DELTA_T[self.w_dt.currentText()]
        k = self.LOCATION[self.w_loc.currentText()]
        sf = self.SAFETY[self.w_sf.currentText()]

        self.lbl_head.setText(
            f"Carrying {fmt_eng(i_target,'A')} "
            f"(ΔT {dt:.0f} °C · {plating:.0f} µm barrel · safety ×{sf:g})")

        self.table.setRowCount(len(VIA_HOLE_SIZES_MM))
        for row, d_mm in enumerate(VIA_HOLE_SIZES_MM):
            area = via_copper_area_mil2(d_mm, plating)
            i_via = ipc_current(area, dt, k)
            n = vias_needed(i_target, i_via, sf)
            cells = [
                f"{d_mm:.2f} mm",
                f"{d_mm * MIL_PER_MM:.0f}",
                f"{area:.1f}",
                fmt_eng(i_via, "A"),
                str(n),
            ]
            for col, text in enumerate(cells):
                it = QTableWidgetItem(text)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                    it.setForeground(QColor(C.GOLD))
                elif col == 3:
                    it.setFont(QFont("Consolas", 12))
                    it.setForeground(QColor(C.ACCENT))
                elif col == 4:
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                    it.setForeground(QColor(C.GREEN if n <= 6 else
                                            (C.ORANGE if n <= 20 else C.RED)))
                else:
                    it.setForeground(QColor(C.TEXT))
                self.table.setItem(row, col, it)
        self.table.resizeColumnsToContents()

        self.status.setText(
            f"<span style='color:{C.TEXT_DIM};'>Estimate via IPC-2221: "
            f"I = k·ΔT<sup>0.44</sup>·A<sup>0.725</sup>, barrel area = π·t·(d+t). "
            f"This is a rough guide — real capacity depends on copper pour, thermal "
            f"relief, stacking and your fab's plating. Verify critical designs with "
            f"IPC-2152 and your manufacturer.</span>")


# ─── More shared helpers used by the new tabs ────────────────────────────────

def caption(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet(f"color:{C.TEXT_DIM};")
    return l


def mono(text: str = "—", size: int = 12, bold: bool = False,
          color: str = None) -> QLabel:
    l = QLabel(text)
    weight = QFont.Weight.Bold if bold else QFont.Weight.Normal
    l.setFont(QFont("Consolas", size, weight))
    l.setStyleSheet(f"color:{color or C.TEXT};")
    return l


# ─── Tab: Series / Parallel Resistor Solver ──────────────────────────────────

class SeriesParallelTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Target Resistance  (find single / series / parallel combos)")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)
        grid.addWidget(QLabel("Target:"), 0, 0)
        self.w_target = QLineEdit("123k")
        self.w_target.setPlaceholderText("e.g. 123k, 4k99, 27.5, 1.234M")
        grid.addWidget(self.w_target, 0, 1)

        grid.addWidget(QLabel("E-Series:"), 0, 2)
        self.w_series = QComboBox()
        self.w_series.addItems(["E12", "E24", "E48", "E96"])
        self.w_series.setCurrentText("E24")
        grid.addWidget(self.w_series, 0, 3)

        grid.addWidget(QLabel("Max results:"), 0, 4)
        self.w_max = QComboBox(); self.w_max.addItems(["10", "25", "50", "100"])
        self.w_max.setCurrentText("25")
        grid.addWidget(self.w_max, 0, 5)

        self.btn = accent_button("Find Combinations")
        self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 6)
        grid.setColumnStretch(1, 1)
        outer.addWidget(grp)

        self.w_target.returnPressed.connect(self._calc)
        self.w_series.currentIndexChanged.connect(self._calc)
        self.w_max.currentIndexChanged.connect(self._calc)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Topology", "R1", "R2", "Actual", "Error"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for c in range(4):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents)
        outer.addWidget(self.table, 1)

        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        target = parse_resistance(self.w_target.text())
        if target is None or target <= 0:
            self.status.setText(f"<span style='color:{C.RED};'>Enter a valid target resistance.</span>")
            self.table.setRowCount(0)
            return
        results = find_combo(target, self.w_series.currentText(), int(self.w_max.currentText()))
        self.table.setRowCount(len(results))
        for row, (kind, r1, r2, actual, err) in enumerate(results):
            kind_color = (C.GREEN if kind == "single" else
                          C.ACCENT if kind == "series" else C.PURPLE)
            cells = [
                kind,
                fmt_ohm(r1),
                "—" if kind == "single" else fmt_ohm(r2),
                fmt_ohm(actual),
                f"{err:+.3f}%",
            ]
            for col, t in enumerate(cells):
                it = QTableWidgetItem(t)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    it.setForeground(QColor(kind_color))
                    it.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
                elif col in (1, 2):
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                    it.setForeground(QColor(C.GOLD))
                elif col == 3:
                    it.setFont(QFont("Consolas", 12))
                    it.setForeground(QColor(C.ACCENT))
                else:
                    it.setForeground(QColor(err_color(abs(err))))
                    it.setFont(QFont("Consolas", 11))
                self.table.setItem(row, col, it)
        self.table.resizeColumnsToContents()

        if results:
            kind, r1, r2, actual, err = results[0]
            joiner = " + " if kind == "series" else (" ∥ " if kind == "parallel" else "")
            second = fmt_ohm(r2) if kind != "single" else ""
            self.status.setText(
                f"<span style='color:{C.GREEN};'>Best: {kind} → "
                f"{fmt_ohm(r1)}{joiner}{second} = {fmt_ohm(actual)} "
                f"({err:+.3f}%).</span>  "
                f"<span style='color:{C.TEXT_DIM};'>Single = closest E-series part; "
                f"series & parallel snap both legs to the E-series.</span>")


# ─── Tab: LED Series Resistor ────────────────────────────────────────────────

class LEDResistorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Supply, LED and Drive Current")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Vsupply:"), 0, 0)
        self.w_vs = QLineEdit("5"); self.w_vs.setPlaceholderText("e.g. 3.3, 5, 12")
        grid.addWidget(self.w_vs, 0, 1)

        grid.addWidget(QLabel("LED Vf (per LED):"), 0, 2)
        self.w_vf = QLineEdit("2.1")
        self.w_vf.setPlaceholderText("Red≈2.0, Green≈3.0, Blue/White≈3.2")
        grid.addWidget(self.w_vf, 0, 3)

        grid.addWidget(QLabel("LEDs in series:"), 0, 4)
        self.w_n = QComboBox()
        self.w_n.addItems([str(i) for i in range(1, 11)])
        grid.addWidget(self.w_n, 0, 5)

        grid.addWidget(QLabel("Forward current If:"), 1, 0)
        self.w_if = QLineEdit("10m"); self.w_if.setPlaceholderText("e.g. 5m, 10m, 20m")
        grid.addWidget(self.w_if, 1, 1)

        grid.addWidget(QLabel("E-Series:"), 1, 2)
        self.w_series = QComboBox(); self.w_series.addItems(["E12", "E24", "E96"])
        self.w_series.setCurrentText("E24")
        grid.addWidget(self.w_series, 1, 3)

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 6, 2, 1)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)
        for w in (self.w_vs, self.w_vf, self.w_if):
            w.returnPressed.connect(self._calc)
        self.w_n.currentIndexChanged.connect(self._calc)
        self.w_series.currentIndexChanged.connect(self._calc)

        rc, rg = result_card("Resistor & Power")
        self.lbl_r_ideal = mono(color=C.TEXT)
        self.lbl_r_e     = mono(bold=True, color=C.GOLD)
        self.lbl_drop    = mono(color=C.TEXT)
        self.lbl_p       = big_value_label()
        self.lbl_pkg     = mono(bold=True, color=C.GREEN)
        self.lbl_actual_i = mono(color=C.ACCENT)

        rg.addWidget(caption("Voltage across R:"), 0, 0); rg.addWidget(self.lbl_drop, 0, 1)
        rg.addWidget(caption("Ideal R:"),          0, 2); rg.addWidget(self.lbl_r_ideal, 0, 3)
        rg.addWidget(caption("Nearest E-series:"), 1, 0); rg.addWidget(self.lbl_r_e, 1, 1)
        rg.addWidget(caption("Actual If:"),        1, 2); rg.addWidget(self.lbl_actual_i, 1, 3)
        rg.addWidget(caption("Power in R:"),       2, 0); rg.addWidget(self.lbl_p, 2, 1)
        rg.addWidget(caption("SMD package:"),      2, 2); rg.addWidget(self.lbl_pkg, 2, 3)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)

        outer.addStretch(1)
        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        vs = parse_voltage(self.w_vs.text())
        vf = parse_voltage(self.w_vf.text())
        i_f = parse_current(self.w_if.text())
        n = int(self.w_n.currentText())
        if vs is None or vf is None or i_f is None or i_f <= 0:
            self.status.setText(f"<span style='color:{C.RED};'>Check supply, Vf and If.</span>")
            return
        total_vf = vf * n
        drop = vs - total_vf
        if drop <= 0:
            self.status.setText(
                f"<span style='color:{C.RED};'>Vsupply ({fmt_eng(vs,'V')}) ≤ total Vf "
                f"({fmt_eng(total_vf,'V')}) — LED won't conduct. Use fewer LEDs or a higher rail.</span>")
            self.lbl_r_ideal.setText("—"); self.lbl_r_e.setText("—")
            self.lbl_drop.setText(fmt_eng(drop, "V")); self.lbl_p.setText("—")
            self.lbl_pkg.setText("—"); self.lbl_actual_i.setText("—")
            return

        r_ideal, _ = led_resistor(vs, total_vf, i_f)
        series = self.w_series.currentText()
        r_e = closest_eseries(r_ideal, series, 1)
        r_chosen = r_e[0] if r_e else r_ideal
        actual_i = drop / r_chosen
        p = actual_i * actual_i * r_chosen
        _, smd, _ = recommend_package(p, 0.6)

        self.lbl_drop.setText(fmt_eng(drop, "V"))
        self.lbl_r_ideal.setText(fmt_ohm(r_ideal))
        self.lbl_r_e.setText(fmt_ohm(r_chosen))
        self.lbl_actual_i.setText(f"{fmt_eng(actual_i, 'A')}  "
                                    f"({(actual_i - i_f)/i_f*100:+.1f}%)")
        self.lbl_p.setText(fmt_eng(p, "W"))
        self.lbl_pkg.setText(f"{smd[0]} — rated {fmt_eng(smd[2],'W')}" if smd else
                             "> 1 W — use through-hole / power resistor")
        if not smd:
            self.lbl_pkg.setStyleSheet(f"color:{C.ORANGE}; font-weight:bold;")
        else:
            self.lbl_pkg.setStyleSheet(f"color:{C.GREEN}; font-weight:bold;")

        self.status.setText(
            f"<span style='color:{C.GREEN};'>R = (Vs − {n}·Vf)/If = "
            f"({fmt_eng(vs,'V')} − {fmt_eng(total_vf,'V')})/{fmt_eng(i_f,'A')} "
            f"= {fmt_ohm(r_ideal)}.</span>  "
            f"<span style='color:{C.TEXT_DIM};'>If brightness matters, recompute "
            f"with the actual If for the chosen E-series value.</span>")


# ─── Tab: RC / RL Filter ─────────────────────────────────────────────────────

class RCFilterTab(QWidget):
    TOPOLOGIES = ["RC low-pass", "RC high-pass", "RL low-pass", "RL high-pass"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Filter Topology and Components")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Topology:"), 0, 0)
        self.w_topo = QComboBox(); self.w_topo.addItems(self.TOPOLOGIES)
        grid.addWidget(self.w_topo, 0, 1)

        grid.addWidget(QLabel("R:"), 1, 0)
        self.w_r = QLineEdit("10k"); self.w_r.setPlaceholderText("e.g. 10k, 1k")
        grid.addWidget(self.w_r, 1, 1)

        grid.addWidget(QLabel("C / L:"), 1, 2)
        self.w_c = QLineEdit("100n")
        self.w_c.setPlaceholderText("RC → 100n, 1u; RL → 10u (H), 1m (H)")
        grid.addWidget(self.w_c, 1, 3)

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 2, 1)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)

        for w in (self.w_r, self.w_c):
            w.returnPressed.connect(self._calc)
        self.w_topo.currentIndexChanged.connect(self._calc)

        rc, rg = result_card("Response")
        self.lbl_fc = big_value_label()
        self.lbl_tau = mono(color=C.ACCENT)
        self.lbl_omega = mono(color=C.TEXT)
        rg.addWidget(caption("Cutoff fc (−3 dB):"), 0, 0); rg.addWidget(self.lbl_fc, 0, 1)
        rg.addWidget(caption("Time constant τ:"),   0, 2); rg.addWidget(self.lbl_tau, 0, 3)
        rg.addWidget(caption("Angular ω₀:"),         1, 0); rg.addWidget(self.lbl_omega, 1, 1)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["Frequency", "Magnitude (dB)", "Phase (°)"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for c in range(2):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents)
        outer.addWidget(self.table, 1)
        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        topo = self.w_topo.currentText()
        r = parse_resistance(self.w_r.text())
        if "RL" in topo:
            c_or_l = parse_inductance(self.w_c.text())
            unit = "H"
        else:
            c_or_l = parse_capacitance(self.w_c.text())
            unit = "F"
        if r is None or c_or_l is None or r <= 0 or c_or_l <= 0:
            self.status.setText(f"<span style='color:{C.RED};'>Enter a valid R and C/L.</span>")
            return

        if "RC" in topo:
            fc = rc_cutoff(r, c_or_l)
            tau = r * c_or_l
        else:
            fc = rl_cutoff(r, c_or_l)
            tau = c_or_l / r
        omega = 2 * math.pi * fc
        self.lbl_fc.setText(fmt_eng(fc, "Hz"))
        self.lbl_tau.setText(fmt_eng(tau, "s"))
        self.lbl_omega.setText(fmt_eng(omega, "rad/s"))

        is_high = "high" in topo
        decades = [-3, -2, -1, -0.5, 0, 0.5, 1, 2, 3]
        self.table.setRowCount(len(decades))
        for row, d in enumerate(decades):
            f = fc * (10 ** d)
            # First-order Bode for LPF: |H| = 1/√(1+(f/fc)²); HPF: (f/fc)/√(...)
            ratio = f / fc
            mag = 1.0 / math.sqrt(1 + ratio * ratio)
            if is_high:
                mag = ratio * mag
            mag_db = 20 * math.log10(mag) if mag > 0 else -120
            phase = -math.degrees(math.atan(ratio)) if not is_high else (
                90 - math.degrees(math.atan(ratio)))
            cells = [fmt_eng(f, "Hz"), f"{mag_db:+.2f}", f"{phase:+.1f}"]
            for col, t in enumerate(cells):
                it = QTableWidgetItem(t)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if abs(d) < 1e-6:
                    it.setForeground(QColor(C.GOLD))
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                else:
                    it.setForeground(QColor(C.TEXT))
                    it.setFont(QFont("Consolas", 11))
                self.table.setItem(row, col, it)
        self.table.resizeColumnsToContents()

        formula = ("fc = 1 / (2π·R·C)" if "RC" in topo else "fc = R / (2π·L)")
        self.status.setText(
            f"<span style='color:{C.GREEN};'>{formula} → {fmt_eng(fc, 'Hz')}.</span>  "
            f"<span style='color:{C.TEXT_DIM};'>First-order roll-off is "
            f"−20 dB/decade past fc. The −3 dB row is highlighted.</span>")


# ─── Tab: Capacitor Sizing (hold-up & ripple) ────────────────────────────────

class CapSizingTab(QWidget):
    MODES = ["Hold-up time (bulk cap)", "Buck output ripple",
             "Energy storage", "Voltage on charged cap"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Mode and Inputs")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Mode:"), 0, 0)
        self.w_mode = QComboBox(); self.w_mode.addItems(self.MODES)
        self.w_mode.setMinimumWidth(220)
        grid.addWidget(self.w_mode, 0, 1, 1, 3)

        grid.addWidget(QLabel("A:"), 1, 0); self.w_a = QLineEdit(); grid.addWidget(self.w_a, 1, 1)
        grid.addWidget(QLabel("B:"), 1, 2); self.w_b = QLineEdit(); grid.addWidget(self.w_b, 1, 3)
        grid.addWidget(QLabel("C:"), 2, 0); self.w_c = QLineEdit(); grid.addWidget(self.w_c, 2, 1)
        self.lbl_a = QLabel(); self.lbl_b = QLabel(); self.lbl_c = QLabel()
        grid.addWidget(self.lbl_a, 1, 4); grid.addWidget(self.lbl_b, 1, 5); grid.addWidget(self.lbl_c, 2, 5)
        for l in (self.lbl_a, self.lbl_b, self.lbl_c):
            l.setStyleSheet(f"color:{C.TEXT_DIM}; font-size:11px;")

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 2, 3)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)

        for w in (self.w_a, self.w_b, self.w_c):
            w.returnPressed.connect(self._calc)
        self.w_mode.currentIndexChanged.connect(self._reset_mode)

        rc, rg = result_card("Result")
        self.lbl_main = big_value_label()
        self.lbl_aux  = mono(color=C.ACCENT)
        self.lbl_energy = mono(color=C.TEXT_DIM)
        rg.addWidget(caption("Primary result:"), 0, 0); rg.addWidget(self.lbl_main, 0, 1)
        rg.addWidget(caption("Detail:"),         0, 2); rg.addWidget(self.lbl_aux, 0, 3)
        rg.addWidget(caption("Energy at full V:"), 1, 0); rg.addWidget(self.lbl_energy, 1, 1, 1, 3)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)

        outer.addStretch(1)
        self.status = status_label()
        outer.addWidget(self.status)
        self._reset_mode()

    def _reset_mode(self):
        m = self.w_mode.currentText()
        cfg = {
            "Hold-up time (bulk cap)":  (("Load current",  "e.g. 500m",   "A"),
                                         ("Hold-up time",  "e.g. 20m, 1", "s"),
                                         ("Allowed ΔV",    "e.g. 1, 2V",  "V")),
            "Buck output ripple":       (("Inductor ΔI",   "e.g. 200m",   "A"),
                                         ("Fsw",           "e.g. 500k, 1M","Hz"),
                                         ("Target ΔV",     "e.g. 50m, 10m","V")),
            "Energy storage":           (("Capacitance",   "e.g. 100u",    "F"),
                                         ("Voltage",       "e.g. 12, 24",  "V"),
                                         ("",              "",             "")),
            "Voltage on charged cap":   (("Capacitance",   "e.g. 1u",      "F"),
                                         ("Charge",        "e.g. 1u",      "C"),
                                         ("",              "",             "")),
        }
        a, b, c = cfg[m]
        for lab, edit, w in ((a, self.w_a, self.lbl_a),
                             (b, self.w_b, self.lbl_b),
                             (c, self.w_c, self.lbl_c)):
            name, ph, unit = lab
            edit.setPlaceholderText(ph)
            edit.setEnabled(bool(name))
            w.setText(f"  [{unit}]" if unit else "")
            # rename the labels next to the edits
        # rename the row labels in the grid
        # (easy: just change their text via mapping the row labels):
        grid = self.w_a.parentWidget().layout()
        labels = [grid.itemAtPosition(1, 0).widget(),
                  grid.itemAtPosition(1, 2).widget(),
                  grid.itemAtPosition(2, 0).widget()]
        labels[0].setText(f"{cfg[m][0][0]}:" if cfg[m][0][0] else "—")
        labels[1].setText(f"{cfg[m][1][0]}:" if cfg[m][1][0] else "—")
        labels[2].setText(f"{cfg[m][2][0]}:" if cfg[m][2][0] else "—")
        # sensible defaults per mode
        defaults = {
            "Hold-up time (bulk cap)":  ("500m", "10m", "1"),
            "Buck output ripple":       ("200m", "500k", "20m"),
            "Energy storage":           ("100u", "12", ""),
            "Voltage on charged cap":   ("1u",   "1u", ""),
        }
        da, db, dc = defaults[m]
        self.w_a.setText(da); self.w_b.setText(db); self.w_c.setText(dc)
        self._calc()

    def _calc(self):
        m = self.w_mode.currentText()
        try:
            if m == "Hold-up time (bulk cap)":
                i = parse_current(self.w_a.text())
                t = _parse_si(self.w_b.text(), "s")
                dv = parse_voltage(self.w_c.text())
                if None in (i, t, dv) or dv <= 0:
                    raise ValueError
                c = cap_holdup_f(i, t, dv)
                self.lbl_main.setText(fmt_eng(c, "F"))
                self.lbl_aux.setText(f"holds {fmt_eng(i,'A')} for {fmt_eng(t,'s')} "
                                       f"with {fmt_eng(dv,'V')} droop")
                self.lbl_energy.setText(fmt_eng(cap_energy_j(c, dv), "J") + "  (across ΔV)")
                self.status.setText(
                    f"<span style='color:{C.GREEN};'>C = I·t/ΔV → choose at least "
                    f"{fmt_eng(c,'F')}.</span>  "
                    f"<span style='color:{C.TEXT_DIM};'>Pick 1.5–2× headroom for cap "
                    f"tolerance + temperature/age derating (ceramic X7R loses ~50% at "
                    f"rated V).</span>")
            elif m == "Buck output ripple":
                di = parse_current(self.w_a.text())
                fsw = parse_freq(self.w_b.text())
                dv = parse_voltage(self.w_c.text())
                if None in (di, fsw, dv) or dv <= 0 or fsw <= 0:
                    raise ValueError
                c = cap_for_ripple_buck(di, fsw, dv)
                self.lbl_main.setText(fmt_eng(c, "F"))
                self.lbl_aux.setText(f"limits ripple to {fmt_eng(dv,'V')}p-p at "
                                       f"{fmt_eng(fsw,'Hz')}")
                # ESR contribution at this ΔV is dv = di·ESR → ESR ≤ dv/di
                self.lbl_energy.setText(
                    f"max permitted ESR ≈ {fmt_eng(dv/di, 'Ω')} (ceramic typically OK)")
                self.status.setText(
                    f"<span style='color:{C.GREEN};'>C ≥ ΔI / (8·fsw·ΔV) for a "
                    f"continuous-mode buck.</span>  "
                    f"<span style='color:{C.TEXT_DIM};'>If you use electrolytics, ESR "
                    f"dominates ripple — pick C so ESR·ΔI ≤ ΔV.</span>")
            elif m == "Energy storage":
                c = parse_capacitance(self.w_a.text())
                v = parse_voltage(self.w_b.text())
                if c is None or v is None or c <= 0:
                    raise ValueError
                e = cap_energy_j(c, v)
                self.lbl_main.setText(fmt_eng(e, "J"))
                self.lbl_aux.setText(f"= ½·C·V² with {fmt_eng(c,'F')}, {fmt_eng(v,'V')}")
                self.lbl_energy.setText(f"≈ {fmt_eng(e/3600, 'Wh')} (Wh equivalent)")
                self.status.setText(
                    f"<span style='color:{C.GREEN};'>E = ½·C·V² = {fmt_eng(e,'J')}.</span>")
            else:  # voltage on charged cap
                c = parse_capacitance(self.w_a.text())
                q = _parse_si(self.w_b.text(), "C")
                if c is None or q is None or c <= 0:
                    raise ValueError
                v = q / c
                self.lbl_main.setText(fmt_eng(v, "V"))
                self.lbl_aux.setText(f"V = Q/C with {fmt_eng(q,'C')} on {fmt_eng(c,'F')}")
                self.lbl_energy.setText(fmt_eng(cap_energy_j(c, v), "J"))
                self.status.setText(
                    f"<span style='color:{C.GREEN};'>V = Q / C.</span>")
        except (TypeError, ValueError):
            self.status.setText(f"<span style='color:{C.RED};'>Check the input fields.</span>")


# ─── Tab: Crystal Load Capacitance ───────────────────────────────────────────

class CrystalLoadTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Crystal Spec and Stray Capacitance")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Datasheet CL:"), 0, 0)
        self.w_cl = QLineEdit("12p"); self.w_cl.setPlaceholderText("e.g. 8p, 12p, 18p, 20p")
        grid.addWidget(self.w_cl, 0, 1)

        grid.addWidget(QLabel("Stray Cstray (each leg):"), 0, 2)
        self.w_cs = QLineEdit("3p")
        self.w_cs.setPlaceholderText("Typical FR-4 trace + pin: 2–5 pF")
        grid.addWidget(self.w_cs, 0, 3)

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)

        for w in (self.w_cl, self.w_cs):
            w.returnPressed.connect(self._calc)

        rc, rg = result_card("Matched Load Capacitors  (C1 = C2)")
        self.lbl_c = big_value_label()
        self.lbl_e = mono(bold=True, color=C.GOLD)
        self.lbl_note = mono(color=C.TEXT_DIM, size=11)
        rg.addWidget(caption("C1 = C2 (ideal):"),  0, 0); rg.addWidget(self.lbl_c, 0, 1)
        rg.addWidget(caption("Nearest E12 cap:"),  0, 2); rg.addWidget(self.lbl_e, 0, 3)
        rg.addWidget(self.lbl_note, 1, 0, 1, 4)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)

        outer.addStretch(1)
        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        cl = parse_capacitance(self.w_cl.text())
        cs = parse_capacitance(self.w_cs.text())
        if cl is None or cs is None or cl <= 0 or cs < 0:
            self.status.setText(f"<span style='color:{C.RED};'>Enter valid CL and Cstray.</span>")
            return
        if cs >= cl:
            self.status.setText(
                f"<span style='color:{C.RED};'>Cstray ({fmt_eng(cs,'F')}) ≥ CL — your "
                f"layout adds more than the crystal needs. Tighten the routing or pick a "
                f"crystal with a larger CL.</span>")
            self.lbl_c.setText("—"); self.lbl_e.setText("—"); self.lbl_note.setText("")
            return
        c = crystal_matched_caps(cl, cs)
        # Snap to E12 values in pF (5p6, 6p8, 8p2, 10p, 12p, 15p, 18p, 22p, 27p, 33p)
        e12 = [3.3e-12, 3.9e-12, 4.7e-12, 5.6e-12, 6.8e-12, 8.2e-12,
                10e-12, 12e-12, 15e-12, 18e-12, 22e-12, 27e-12, 33e-12, 39e-12]
        nearest = min(e12, key=lambda v: abs(v - c))
        self.lbl_c.setText(fmt_eng(c, "F"))
        self.lbl_e.setText(fmt_eng(nearest, "F"))
        # back-calculate the CL you'd actually present with the nearest E12
        cl_actual = (nearest * nearest) / (nearest + nearest) + cs
        err = (cl_actual - cl) / cl * 100
        self.lbl_note.setText(
            f"With 2× {fmt_eng(nearest,'F')} you present CL ≈ {fmt_eng(cl_actual,'F')} "
            f"({err:+.1f}% vs spec). Pick NP0/C0G dielectric; tolerance directly shifts "
            f"the oscillator pull (~ppm).")
        self.status.setText(
            f"<span style='color:{C.GREEN};'>C1 = C2 = 2·(CL − Cstray) "
            f"= 2·({fmt_eng(cl,'F')} − {fmt_eng(cs,'F')}) = {fmt_eng(c,'F')}.</span>  "
            f"<span style='color:{C.TEXT_DIM};'>Cstray includes pad, trace and pin "
            f"capacitance for one side of the crystal — 2–5 pF is typical for FR-4.</span>")


# ─── Tab: Trace Width (IPC-2221) ─────────────────────────────────────────────

class TraceWidthTab(QWidget):
    LOCATION = {
        "External (k=0.048)": 0.048,
        "Internal (k=0.024)": 0.024,
    }
    DELTA_T = {"10 °C rise": 10.0, "20 °C rise": 20.0, "30 °C rise": 30.0}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Target Current & Trace Conditions")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Current:"), 0, 0)
        self.w_i = QLineEdit("2"); self.w_i.setPlaceholderText("e.g. 500m, 2, 10")
        grid.addWidget(self.w_i, 0, 1)

        grid.addWidget(QLabel("Copper weight:"), 0, 2)
        self.w_cu = QComboBox()
        self.w_cu.addItems(list(COPPER_THICKNESS_MIL.keys()))
        self.w_cu.setCurrentText("1 oz (35 µm)")
        grid.addWidget(self.w_cu, 0, 3)

        grid.addWidget(QLabel("Temp rise:"), 1, 0)
        self.w_dt = QComboBox(); self.w_dt.addItems(list(self.DELTA_T.keys()))
        grid.addWidget(self.w_dt, 1, 1)

        grid.addWidget(QLabel("Layer location:"), 1, 2)
        self.w_loc = QComboBox(); self.w_loc.addItems(list(self.LOCATION.keys()))
        grid.addWidget(self.w_loc, 1, 3)

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 2, 1)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)
        self.w_i.returnPressed.connect(self._calc)
        for w in (self.w_cu, self.w_dt, self.w_loc):
            w.currentIndexChanged.connect(self._calc)

        rc, rg = result_card("Required Width")
        self.lbl_w_mm = big_value_label()
        self.lbl_w_mil = mono(bold=True, color=C.GOLD)
        self.lbl_capacity = mono(color=C.ACCENT)
        rg.addWidget(caption("Width (mm):"),    0, 0); rg.addWidget(self.lbl_w_mm, 0, 1)
        rg.addWidget(caption("Width (mil):"),   0, 2); rg.addWidget(self.lbl_w_mil, 0, 3)
        rg.addWidget(caption("Cap. at that width:"), 1, 0); rg.addWidget(self.lbl_capacity, 1, 1)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Width (mm)", "Width (mil)", "Capacity (A)", "Margin"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for c in range(3):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents)
        outer.addWidget(self.table, 1)

        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        i = parse_current(self.w_i.text())
        if i is None or i <= 0:
            self.status.setText(f"<span style='color:{C.RED};'>Enter a valid current.</span>")
            return
        t_mil = COPPER_THICKNESS_MIL[self.w_cu.currentText()]
        dt = self.DELTA_T[self.w_dt.currentText()]
        k = self.LOCATION[self.w_loc.currentText()]

        w_mil = trace_required_width_mil(i, dt, k, t_mil)
        w_mm = w_mil * MM_PER_MIL
        self.lbl_w_mm.setText(f"{w_mm:.3f} mm")
        self.lbl_w_mil.setText(f"{w_mil:.1f} mil")
        self.lbl_capacity.setText(f"{trace_capacity_a(w_mil, t_mil, dt, k):.2f} A "
                                    f"@ ΔT {dt:.0f} °C")

        widths_mil = [5, 8, 10, 12, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]
        self.table.setRowCount(len(widths_mil))
        for row, ww in enumerate(widths_mil):
            cap = trace_capacity_a(ww, t_mil, dt, k)
            margin = (cap - i) / i * 100 if i > 0 else 0
            cells = [f"{ww * MM_PER_MIL:.3f}", f"{ww}", f"{cap:.2f}",
                     f"{margin:+.0f}%" if cap > 0 else "—"]
            ok = cap >= i
            for col, t in enumerate(cells):
                it = QTableWidgetItem(t)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                    it.setForeground(QColor(C.GOLD))
                elif col == 2:
                    it.setForeground(QColor(C.ACCENT))
                    it.setFont(QFont("Consolas", 12))
                elif col == 3:
                    it.setForeground(QColor(C.GREEN if ok else C.RED))
                    it.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
                else:
                    it.setForeground(QColor(C.TEXT))
                self.table.setItem(row, col, it)
        self.table.resizeColumnsToContents()

        self.status.setText(
            f"<span style='color:{C.GREEN};'>IPC-2221: I = k·ΔT<sup>0.44</sup>·"
            f"A<sup>0.725</sup> → width {w_mm:.3f} mm ({w_mil:.1f} mil) for "
            f"{fmt_eng(i,'A')}.</span>  "
            f"<span style='color:{C.TEXT_DIM};'>For high-current traces verify with "
            f"IPC-2152 (newer, accounts for proximity and dielectric) and your fab's "
            f"copper-weight tolerance.</span>")


# ─── Tab: Trace Impedance ────────────────────────────────────────────────────

class TraceImpedanceTab(QWidget):
    MODES = ["Microstrip (outer layer)",
              "Stripline (between planes)",
              "Differential microstrip",
              "Differential stripline"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Geometry  (all dimensions in mm; converts to mil internally)")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Topology:"), 0, 0)
        self.w_mode = QComboBox(); self.w_mode.addItems(self.MODES); self.w_mode.setMinimumWidth(220)
        grid.addWidget(self.w_mode, 0, 1, 1, 3)

        grid.addWidget(QLabel("Trace width W:"), 1, 0)
        self.w_w = QLineEdit("0.18"); self.w_w.setPlaceholderText("mm — try 0.10–0.30")
        grid.addWidget(self.w_w, 1, 1)

        grid.addWidget(QLabel("Dielectric H / b:"), 1, 2)
        self.w_h = QLineEdit("0.20")
        self.w_h.setPlaceholderText("microstrip H, stripline b = total dielectric")
        grid.addWidget(self.w_h, 1, 3)

        grid.addWidget(QLabel("Copper T:"), 2, 0)
        self.w_t = QLineEdit("0.035")
        self.w_t.setPlaceholderText("0.5oz≈0.017, 1oz≈0.035, 2oz≈0.070 mm")
        grid.addWidget(self.w_t, 2, 1)

        grid.addWidget(QLabel("εr:"), 2, 2)
        self.w_er = QLineEdit("4.3"); self.w_er.setPlaceholderText("FR-4≈4.3, Rogers≈3.4")
        grid.addWidget(self.w_er, 2, 3)

        grid.addWidget(QLabel("Pair spacing S:"), 3, 0)
        self.w_s = QLineEdit("0.15")
        self.w_s.setPlaceholderText("differential only — edge to edge")
        grid.addWidget(self.w_s, 3, 1)

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 4, 1)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)

        for w in (self.w_w, self.w_h, self.w_t, self.w_er, self.w_s):
            w.returnPressed.connect(self._calc)
        self.w_mode.currentIndexChanged.connect(self._calc)

        rc, rg = result_card("Impedance & Propagation")
        self.lbl_z = big_value_label()
        self.lbl_er_eff = mono(color=C.ACCENT)
        self.lbl_delay  = mono(color=C.TEXT)
        rg.addWidget(caption("Z₀ (Ω):"),         0, 0); rg.addWidget(self.lbl_z, 0, 1)
        rg.addWidget(caption("Effective εr:"),    0, 2); rg.addWidget(self.lbl_er_eff, 0, 3)
        rg.addWidget(caption("Delay (ps/inch):"), 1, 0); rg.addWidget(self.lbl_delay, 1, 1, 1, 3)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)
        outer.addStretch(1)

        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        try:
            w = float(self.w_w.text().replace(",", "."))
            h = float(self.w_h.text().replace(",", "."))
            t = float(self.w_t.text().replace(",", "."))
            er = float(self.w_er.text().replace(",", "."))
            s = float(self.w_s.text().replace(",", ".")) if self.w_s.text().strip() else 0.0
        except ValueError:
            self.status.setText(f"<span style='color:{C.RED};'>Enter numbers in mm.</span>")
            return
        if any(v <= 0 for v in (w, h, t, er)):
            self.status.setText(f"<span style='color:{C.RED};'>W, H, T and εr must be positive.</span>")
            return

        w_mil = w * MIL_PER_MM; h_mil = h * MIL_PER_MM; t_mil = t * MIL_PER_MM; s_mil = s * MIL_PER_MM
        mode = self.w_mode.currentText()
        if mode.startswith("Microstrip"):
            z = microstrip_z0(w_mil, h_mil, t_mil, er); er_eff = microstrip_er_eff(w_mil, h_mil, er)
            formula = "Z₀ = (87/√(εr+1.41)) · ln(5.98H / (0.8W+T))"
        elif mode.startswith("Stripline"):
            z = stripline_z0(w_mil, h_mil, t_mil, er); er_eff = er
            formula = "Z₀ = (60/√εr) · ln(4b / (0.67π·(0.8W+T)))"
        elif mode.startswith("Differential microstrip"):
            z = diff_microstrip_z0(w_mil, s_mil, h_mil, t_mil, er); er_eff = microstrip_er_eff(w_mil, h_mil, er)
            formula = "Z_diff ≈ 2·Z₀ · (1 − 0.48·e<sup>−0.96 S/H</sup>)"
        else:
            z = diff_stripline_z0(w_mil, s_mil, h_mil, t_mil, er); er_eff = er
            formula = "Z_diff ≈ 2·Z₀ · (1 − 0.347·e<sup>−2.9 S/b</sup>)"

        if z <= 0:
            self.status.setText(f"<span style='color:{C.RED};'>Geometry out of range — "
                                  f"try wider trace or thicker dielectric.</span>")
            return
        self.lbl_z.setText(f"{z:.1f} Ω")
        self.lbl_er_eff.setText(f"{er_eff:.2f}")
        self.lbl_delay.setText(f"{propagation_delay_ps_per_inch(er_eff):.1f}  "
                                f"({propagation_delay_ps_per_inch(er_eff)/25.4:.2f} ps/mm)")
        self.status.setText(
            f"<span style='color:{C.GREEN};'>{formula}</span><br>"
            f"<span style='color:{C.TEXT_DIM};'>Closed-form estimates ±10%. For "
            f"production-critical stack-ups use your fab's controlled-impedance "
            f"calculator or a field solver.</span>")


# ─── Tab: Trace Resistance & Voltage Drop ────────────────────────────────────

class TraceResistanceTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Trace Geometry & Current")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Length:"), 0, 0)
        self.w_len = QLineEdit("50mm"); self.w_len.setPlaceholderText("e.g. 50mm, 5cm, 2in")
        grid.addWidget(self.w_len, 0, 1)

        grid.addWidget(QLabel("Width:"), 0, 2)
        self.w_wid = QLineEdit("0.3mm")
        self.w_wid.setPlaceholderText("e.g. 0.3mm, 12mil")
        grid.addWidget(self.w_wid, 0, 3)

        grid.addWidget(QLabel("Copper weight:"), 1, 0)
        self.w_cu = QComboBox(); self.w_cu.addItems(list(COPPER_THICKNESS_MIL.keys()))
        self.w_cu.setCurrentText("1 oz (35 µm)")
        grid.addWidget(self.w_cu, 1, 1)

        grid.addWidget(QLabel("Current:"), 1, 2)
        self.w_i = QLineEdit("1"); self.w_i.setPlaceholderText("e.g. 500m, 1, 5")
        grid.addWidget(self.w_i, 1, 3)

        grid.addWidget(QLabel("Trace temp (°C):"), 2, 0)
        self.w_temp = QLineEdit("25")
        self.w_temp.setPlaceholderText("ambient + estimated self-heating")
        grid.addWidget(self.w_temp, 2, 1)

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 3, 1)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)

        for w in (self.w_len, self.w_wid, self.w_i, self.w_temp):
            w.returnPressed.connect(self._calc)
        self.w_cu.currentIndexChanged.connect(self._calc)

        rc, rg = result_card("Resistance, Voltage Drop & Power")
        self.lbl_r = big_value_label()
        self.lbl_v = mono(bold=True, color=C.GOLD)
        self.lbl_p = mono(color=C.ACCENT)
        self.lbl_warn = mono(color=C.TEXT_DIM, size=11)
        rg.addWidget(caption("Resistance:"),   0, 0); rg.addWidget(self.lbl_r, 0, 1)
        rg.addWidget(caption("IR drop:"),      0, 2); rg.addWidget(self.lbl_v, 0, 3)
        rg.addWidget(caption("Self-heating:"), 1, 0); rg.addWidget(self.lbl_p, 1, 1)
        rg.addWidget(self.lbl_warn, 2, 0, 1, 4)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)
        outer.addStretch(1)

        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        length = parse_length_mm(self.w_len.text())
        width = parse_length_mm(self.w_wid.text())
        i = parse_current(self.w_i.text())
        try:
            temp = float(self.w_temp.text().replace(",", "."))
        except ValueError:
            temp = 25.0
        if None in (length, width, i) or length <= 0 or width <= 0 or i < 0:
            self.status.setText(f"<span style='color:{C.RED};'>Check length, width and current.</span>")
            return

        t_mil = COPPER_THICKNESS_MIL[self.w_cu.currentText()]
        t_um = t_mil * 25.4  # mil → µm
        r = trace_resistance_ohm(length, width, t_um, temp)
        v = i * r
        p = i * i * r

        # IPC-2221 sanity — current vs trace capacity at ΔT 10 °C
        cap_ext = trace_capacity_a(width * MIL_PER_MM, t_mil, 10.0, 0.048)

        self.lbl_r.setText(fmt_eng(r, "Ω"))
        self.lbl_v.setText(fmt_eng(v, "V"))
        self.lbl_p.setText(fmt_eng(p, "W"))

        if i > 0 and cap_ext > 0:
            ratio = i / cap_ext
            tag = ("low self-heating" if ratio < 0.5 else
                    "moderate self-heating — recheck ΔT" if ratio < 1.0 else
                    "above IPC-2221 10 °C-rise capacity; widen the trace")
            color = (C.GREEN if ratio < 0.5 else C.ORANGE if ratio < 1.0 else C.RED)
            self.lbl_warn.setText(
                f"<span style='color:{color};'>I / IPC-cap (ΔT 10 °C, external) "
                f"= {ratio:.2f} — {tag}.</span>")
        else:
            self.lbl_warn.setText("")

        self.status.setText(
            f"<span style='color:{C.GREEN};'>R = ρ·L/A at {temp:.0f} °C → "
            f"{fmt_eng(r,'Ω')}; V = I·R = {fmt_eng(v,'V')}.</span>  "
            f"<span style='color:{C.TEXT_DIM};'>For sense lines, watch IR drop; "
            f"for power, watch self-heating and skin effect at high frequency.</span>")


# ─── Tab: Current-Capacity Checker (bulk paste) ──────────────────────────────

class CurrentCapacityTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Net List  (one segment per line: name, width, current)")
        v = QVBoxLayout(grp)
        v.addWidget(QLabel("Width and current accept SI units — e.g. <code>0.3mm</code>, "
                              "<code>12mil</code>, <code>500m</code> (mA), <code>2.5</code> (A). "
                              "Use commas, semicolons or tabs as separators."))
        self.w_input = QPlainTextEdit(
            "VBUS_5V,    0.5mm,  2.0\n"
            "VBUS_3V3,   0.3mm,  500m\n"
            "SCL,        0.15mm, 5m\n"
            "GND_RTN,    1.0mm,  3.0\n"
            "MOTOR_PWR,  0.3mm,  4.5\n")
        self.w_input.setStyleSheet(
            f"background:{C.BG_LIGHT}; border:1px solid {C.BORDER}; "
            f"border-radius:4px; padding:6px; color:{C.TEXT};"
            f"font-family:Consolas, monospace; font-size:12px;")
        self.w_input.setMinimumHeight(140)
        v.addWidget(self.w_input)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Copper:"))
        self.w_cu = QComboBox(); self.w_cu.addItems(list(COPPER_THICKNESS_MIL.keys()))
        self.w_cu.setCurrentText("1 oz (35 µm)")
        controls.addWidget(self.w_cu)
        controls.addWidget(QLabel("Layer:"))
        self.w_loc = QComboBox(); self.w_loc.addItems(
            ["External (k=0.048)", "Internal (k=0.024)"])
        controls.addWidget(self.w_loc)
        controls.addWidget(QLabel("ΔT:"))
        self.w_dt = QComboBox(); self.w_dt.addItems(["10 °C", "20 °C", "30 °C"])
        controls.addWidget(self.w_dt)
        controls.addStretch()
        self.btn = accent_button("Check"); self.btn.clicked.connect(self._calc)
        controls.addWidget(self.btn)
        v.addLayout(controls)
        outer.addWidget(grp)

        self.w_input.textChanged.connect(self._calc)
        for w in (self.w_cu, self.w_loc, self.w_dt):
            w.currentIndexChanged.connect(self._calc)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Net / segment", "Width (mm)", "Width (mil)", "Required (A)",
             "Capacity (A)", "Verdict"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for c in range(5):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents)
        outer.addWidget(self.table, 1)
        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        import re as _re
        text = self.w_input.toPlainText()
        rows = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in _re.split(r"[,;\t]+", line) if p.strip()]
            if len(parts) < 3:
                rows.append((line, None, None))
                continue
            name = parts[0]
            w_mm = parse_length_mm(parts[1])
            i = parse_current(parts[2])
            rows.append((name, w_mm, i))

        t_mil = COPPER_THICKNESS_MIL[self.w_cu.currentText()]
        k = 0.048 if "External" in self.w_loc.currentText() else 0.024
        dt = float(self.w_dt.currentText().split()[0])

        self.table.setRowCount(len(rows))
        fails = 0
        for row, (name, w_mm, i) in enumerate(rows):
            if w_mm is None or i is None or w_mm <= 0:
                cells = [name, "—", "—", "—", "—", "parse error"]
                colors = [C.RED] * 6
                ok = False
            else:
                w_mil = w_mm * MIL_PER_MM
                cap = trace_capacity_a(w_mil, t_mil, dt, k)
                ok = cap >= i
                margin = (cap - i) / i * 100 if i > 0 else 0
                cells = [name, f"{w_mm:.3f}", f"{w_mil:.1f}",
                         fmt_eng(i, "A"), f"{cap:.2f}",
                         f"✓ +{margin:.0f}%" if ok else f"✗ short by {-margin:.0f}%"]
                colors = [C.GOLD, C.TEXT, C.TEXT_DIM, C.TEXT,
                          C.ACCENT, C.GREEN if ok else C.RED]
            if not ok:
                fails += 1
            for col, t in enumerate(cells):
                it = QTableWidgetItem(t)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                it.setForeground(QColor(colors[col]))
                if col in (0, 5):
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                else:
                    it.setFont(QFont("Consolas", 11))
                self.table.setItem(row, col, it)
        self.table.resizeColumnsToContents()

        if not rows:
            self.status.setText(f"<span style='color:{C.TEXT_DIM};'>Paste rows above.</span>")
        elif fails == 0:
            self.status.setText(
                f"<span style='color:{C.GREEN};'>✓ All {len(rows)} segments pass IPC-2221 at "
                f"ΔT {dt:.0f} °C.</span>")
        else:
            self.status.setText(
                f"<span style='color:{C.RED};'>✗ {fails} of {len(rows)} segment(s) below "
                f"capacity — widen those traces or accept a higher ΔT.</span>")


# ─── Tab: LDO Thermal ────────────────────────────────────────────────────────

class LDOThermalTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("LDO Operating Point and Package")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)
        grid.addWidget(QLabel("Vin:"), 0, 0)
        self.w_vin = QLineEdit("5"); grid.addWidget(self.w_vin, 0, 1)
        grid.addWidget(QLabel("Vout:"), 0, 2)
        self.w_vout = QLineEdit("3.3"); grid.addWidget(self.w_vout, 0, 3)
        grid.addWidget(QLabel("Iout:"), 1, 0)
        self.w_iout = QLineEdit("300m"); grid.addWidget(self.w_iout, 1, 1)
        grid.addWidget(QLabel("Iq (quiescent):"), 1, 2)
        self.w_iq = QLineEdit("0"); self.w_iq.setPlaceholderText("e.g. 50u, 1m, 0")
        grid.addWidget(self.w_iq, 1, 3)
        grid.addWidget(QLabel("θJA (°C/W):"), 2, 0)
        self.w_theta = QLineEdit("70")
        self.w_theta.setPlaceholderText("SOT-23-5≈250, SO-8≈100, DPAK on pour≈50")
        grid.addWidget(self.w_theta, 2, 1)
        grid.addWidget(QLabel("T ambient (°C):"), 2, 2)
        self.w_tamb = QLineEdit("25"); grid.addWidget(self.w_tamb, 2, 3)
        grid.addWidget(QLabel("T_J,max (°C):"), 3, 0)
        self.w_tjmax = QLineEdit("125"); grid.addWidget(self.w_tjmax, 3, 1)

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 4, 1)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)
        for w in (self.w_vin, self.w_vout, self.w_iout, self.w_iq,
                   self.w_theta, self.w_tamb, self.w_tjmax):
            w.returnPressed.connect(self._calc)

        rc, rg = result_card("Dissipation & Junction Temperature")
        self.lbl_p   = big_value_label()
        self.lbl_eff = mono(color=C.ACCENT)
        self.lbl_tj  = mono(bold=True, color=C.GOLD)
        self.lbl_margin = mono(bold=True, color=C.GREEN)
        self.lbl_imax = mono(color=C.TEXT)
        rg.addWidget(caption("Pdiss:"),         0, 0); rg.addWidget(self.lbl_p, 0, 1)
        rg.addWidget(caption("Efficiency η:"),   0, 2); rg.addWidget(self.lbl_eff, 0, 3)
        rg.addWidget(caption("Junction Tj:"),    1, 0); rg.addWidget(self.lbl_tj, 1, 1)
        rg.addWidget(caption("Margin to TJ,max:"), 1, 2); rg.addWidget(self.lbl_margin, 1, 3)
        rg.addWidget(caption("Max safe Iout:"),  2, 0); rg.addWidget(self.lbl_imax, 2, 1, 1, 3)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)
        outer.addStretch(1)
        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        try:
            vin = parse_voltage(self.w_vin.text())
            vout = parse_voltage(self.w_vout.text())
            iout = parse_current(self.w_iout.text())
            iq = parse_current(self.w_iq.text()) or 0.0
            theta = float(self.w_theta.text().replace(",", "."))
            tamb = float(self.w_tamb.text().replace(",", "."))
            tjmax = float(self.w_tjmax.text().replace(",", "."))
        except (ValueError, TypeError):
            self.status.setText(f"<span style='color:{C.RED};'>Check numeric inputs.</span>")
            return
        if None in (vin, vout, iout) or vin <= 0 or iout < 0 or theta <= 0:
            self.status.setText(f"<span style='color:{C.RED};'>Check Vin, Vout, Iout, θJA.</span>")
            return
        if vout > vin:
            self.status.setText(f"<span style='color:{C.RED};'>An LDO can't boost: Vout must be ≤ Vin.</span>")
            return

        p = ldo_dissipation_w(vin, vout, iout, iq)
        eff = (vout * iout) / (vin * (iout + iq)) if (iout + iq) > 0 else 0.0
        tj = junction_temp_c(p, theta, tamb)
        margin = tjmax - tj
        # max safe Iout: tj == tjmax → (vin-vout)·I + vin·iq == (tjmax-tamb)/theta
        budget = max(0.0, (tjmax - tamb) / theta - vin * iq)
        i_max = budget / (vin - vout) if vin > vout else float("inf")

        self.lbl_p.setText(fmt_eng(p, "W"))
        self.lbl_eff.setText(f"{eff*100:.1f}%")
        self.lbl_tj.setText(f"{tj:.1f} °C")
        if margin > 30:
            color, tag = C.GREEN, "comfortable"
        elif margin > 10:
            color, tag = C.ORANGE, "tight — add copper / lower current"
        else:
            color, tag = C.RED, "DANGER — will hit thermal shutdown"
        self.lbl_margin.setText(f"{margin:+.1f} °C  ({tag})")
        self.lbl_margin.setStyleSheet(f"color:{color}; font-weight:bold;")
        self.lbl_imax.setText(fmt_eng(i_max, "A") if math.isfinite(i_max) else "∞ (Vin = Vout)")

        self.status.setText(
            f"<span style='color:{C.GREEN};'>Pdiss = (Vin−Vout)·Iout + Vin·Iq = "
            f"{fmt_eng(p,'W')}.</span>  "
            f"<span style='color:{C.TEXT_DIM};'>Most LDO datasheets quote θJA on a "
            f"1-square-inch 2-oz pad — your real value can be 1.5–3× worse with little "
            f"copper. Use θJC + heatsink data for serious dissipation.</span>")


# ─── Tab: Copper Pour Thermal ────────────────────────────────────────────────

class CopperPourTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Copper Pour & Device Dissipation")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Pour area (cm²):"), 0, 0)
        self.w_area = QLineEdit("4")
        self.w_area.setPlaceholderText("e.g. 1 (small), 4, 10")
        grid.addWidget(self.w_area, 0, 1)

        grid.addWidget(QLabel("Copper weight (oz):"), 0, 2)
        self.w_oz = QComboBox(); self.w_oz.addItems(["0.5", "1", "2", "3"])
        self.w_oz.setCurrentText("1")
        grid.addWidget(self.w_oz, 0, 3)

        grid.addWidget(QLabel("Layers:"), 1, 0)
        self.w_layers = QComboBox(); self.w_layers.addItems(["1", "2", "3", "4"])
        grid.addWidget(self.w_layers, 1, 1)

        grid.addWidget(QLabel("Device power:"), 1, 2)
        self.w_p = QLineEdit("500m"); self.w_p.setPlaceholderText("e.g. 500m, 1, 2")
        grid.addWidget(self.w_p, 1, 3)

        grid.addWidget(QLabel("Ambient (°C):"), 2, 0)
        self.w_tamb = QLineEdit("25"); grid.addWidget(self.w_tamb, 2, 1)
        grid.addWidget(QLabel("T_J,max (°C):"), 2, 2)
        self.w_tjmax = QLineEdit("125"); grid.addWidget(self.w_tjmax, 2, 3)

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 3, 1)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)
        for w in (self.w_area, self.w_p, self.w_tamb, self.w_tjmax):
            w.returnPressed.connect(self._calc)
        for w in (self.w_oz, self.w_layers):
            w.currentIndexChanged.connect(self._calc)

        rc, rg = result_card("Estimated θJA, Rise and Maximum Power")
        self.lbl_theta = big_value_label()
        self.lbl_rise = mono(bold=True, color=C.GOLD)
        self.lbl_tj   = mono(color=C.ACCENT)
        self.lbl_pmax = mono(color=C.TEXT)
        rg.addWidget(caption("Estimated θJA:"), 0, 0); rg.addWidget(self.lbl_theta, 0, 1)
        rg.addWidget(caption("ΔT (rise):"),      0, 2); rg.addWidget(self.lbl_rise, 0, 3)
        rg.addWidget(caption("Junction Tj:"),    1, 0); rg.addWidget(self.lbl_tj, 1, 1)
        rg.addWidget(caption("Max device power:"),1, 2); rg.addWidget(self.lbl_pmax, 1, 3)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)

        # Sweep table over pour areas
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Pour area (cm²)", "θJA (°C/W)", "Tj at P"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for c in range(2):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents)
        outer.addWidget(self.table, 1)
        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        try:
            area = float(self.w_area.text().replace(",", "."))
            oz = float(self.w_oz.currentText())
            layers = float(self.w_layers.currentText())
            p = _parse_si(self.w_p.text(), "W")
            tamb = float(self.w_tamb.text().replace(",", "."))
            tjmax = float(self.w_tjmax.text().replace(",", "."))
        except (ValueError, TypeError):
            self.status.setText(f"<span style='color:{C.RED};'>Check numeric inputs.</span>")
            return
        if area <= 0 or p is None or p < 0:
            self.status.setText(f"<span style='color:{C.RED};'>Pour area and power must be valid.</span>")
            return

        theta = copper_pour_theta_ja(area, oz, layers)
        rise = p * theta
        tj = tamb + rise
        p_max = max(0.0, (tjmax - tamb) / theta)
        self.lbl_theta.setText(f"{theta:.1f} °C/W")
        self.lbl_rise.setText(f"{rise:+.1f} °C")
        self.lbl_tj.setText(f"{tj:.1f} °C")
        self.lbl_pmax.setText(fmt_eng(p_max, "W"))

        areas = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
        self.table.setRowCount(len(areas))
        for row, a in enumerate(areas):
            th = copper_pour_theta_ja(a, oz, layers)
            tj_at = tamb + p * th
            ok = tj_at < tjmax
            cells = [f"{a:g}", f"{th:.1f}", f"{tj_at:.1f}"]
            for col, t in enumerate(cells):
                it = QTableWidgetItem(t)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    it.setForeground(QColor(C.GOLD))
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                elif col == 2:
                    it.setForeground(QColor(C.GREEN if ok else C.RED))
                    it.setFont(QFont("Consolas", 12))
                else:
                    it.setForeground(QColor(C.TEXT))
                    it.setFont(QFont("Consolas", 12))
                self.table.setItem(row, col, it)
        self.table.resizeColumnsToContents()
        self.status.setText(
            f"<span style='color:{C.TEXT_DIM};'>Heuristic θJA ≈ 60/√(A·oz·layers) + 25. "
            f"Real boards vary 2–3× with vias-down, neighbouring components, airflow and "
            f"orientation — use this for first-pass sizing only and confirm with thermal "
            f"imaging or vendor app notes.</span>")


# ─── Tab: Buck / Boost Quick-Calc ────────────────────────────────────────────

class BuckBoostTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Switching Regulator Operating Point")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Topology:"), 0, 0)
        self.w_topo = QComboBox(); self.w_topo.addItems(["Buck (Vin > Vout)", "Boost (Vout > Vin)"])
        grid.addWidget(self.w_topo, 0, 1)

        grid.addWidget(QLabel("Vin:"), 1, 0)
        self.w_vin = QLineEdit("12"); grid.addWidget(self.w_vin, 1, 1)
        grid.addWidget(QLabel("Vout:"), 1, 2)
        self.w_vout = QLineEdit("3.3"); grid.addWidget(self.w_vout, 1, 3)
        grid.addWidget(QLabel("Iout:"), 2, 0)
        self.w_iout = QLineEdit("1"); grid.addWidget(self.w_iout, 2, 1)
        grid.addWidget(QLabel("Fsw:"), 2, 2)
        self.w_fsw = QLineEdit("500k"); self.w_fsw.setPlaceholderText("e.g. 100k, 500k, 1M, 2.2M")
        grid.addWidget(self.w_fsw, 2, 3)
        grid.addWidget(QLabel("Inductor L:"), 3, 0)
        self.w_l = QLineEdit("10u"); self.w_l.setPlaceholderText("e.g. 4.7u, 10u, 22u")
        grid.addWidget(self.w_l, 3, 1)
        grid.addWidget(QLabel("Target ΔV ripple:"), 3, 2)
        self.w_dv = QLineEdit("20m"); grid.addWidget(self.w_dv, 3, 3)

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 4, 1)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)
        self.w_topo.currentIndexChanged.connect(self._calc)
        for w in (self.w_vin, self.w_vout, self.w_iout, self.w_fsw, self.w_l, self.w_dv):
            w.returnPressed.connect(self._calc)

        rc, rg = result_card("Duty, Inductor & Capacitor")
        self.lbl_d  = big_value_label()
        self.lbl_di = mono(bold=True, color=C.GOLD)
        self.lbl_ipk = mono(color=C.ACCENT)
        self.lbl_l_min = mono(color=C.TEXT)
        self.lbl_c = mono(bold=True, color=C.ACCENT)
        self.lbl_pin = mono(color=C.TEXT)
        rg.addWidget(caption("Duty cycle D:"),      0, 0); rg.addWidget(self.lbl_d, 0, 1)
        rg.addWidget(caption("Inductor ΔI (p-p):"),  0, 2); rg.addWidget(self.lbl_di, 0, 3)
        rg.addWidget(caption("Inductor I_peak:"),    1, 0); rg.addWidget(self.lbl_ipk, 1, 1)
        rg.addWidget(caption("Min L for 30% ripple:"),1, 2); rg.addWidget(self.lbl_l_min, 1, 3)
        rg.addWidget(caption("Cout for target ΔV:"),  2, 0); rg.addWidget(self.lbl_c, 2, 1)
        rg.addWidget(caption("Pin (η=100%):"),       2, 2); rg.addWidget(self.lbl_pin, 2, 3)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)

        outer.addStretch(1)
        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        vin = parse_voltage(self.w_vin.text())
        vout = parse_voltage(self.w_vout.text())
        iout = parse_current(self.w_iout.text())
        fsw = parse_freq(self.w_fsw.text())
        l = parse_inductance(self.w_l.text())
        dv = parse_voltage(self.w_dv.text())
        if None in (vin, vout, iout, fsw, l, dv) or min(vin, vout, iout, fsw, l, dv) <= 0:
            self.status.setText(f"<span style='color:{C.RED};'>All fields must be positive numbers.</span>")
            return

        is_buck = self.w_topo.currentText().startswith("Buck")
        if is_buck and vout >= vin:
            self.status.setText(f"<span style='color:{C.ORANGE};'>For buck topology Vout must be &lt; Vin. "
                                  f"Switch to boost or swap Vin/Vout.</span>")
            return
        if not is_buck and vout <= vin:
            self.status.setText(f"<span style='color:{C.ORANGE};'>For boost topology Vout must be &gt; Vin.</span>")
            return

        if is_buck:
            d = buck_duty(vin, vout)
            di = buck_inductor_ripple_a(vin, vout, l, fsw)
            iin = iout * d
            l_min = vout * (1 - d) / (0.3 * iout * fsw)   # 30% ripple
        else:
            d = boost_duty(vin, vout)
            di = boost_inductor_ripple_a(vin, vout, l, fsw)
            iin = iout / max(1e-9, 1 - d)
            l_min = vin * d / (0.3 * iin * fsw)

        i_peak = (iout if is_buck else iin) + di / 2
        c = cap_for_ripple_buck(di, fsw, dv)
        pin = vin * iin

        self.lbl_d.setText(f"{d*100:.1f}%")
        self.lbl_di.setText(f"{fmt_eng(di, 'A')}  ({di/(iout if is_buck else iin)*100:.0f}% of "
                              f"{'Iout' if is_buck else 'Iin'})")
        self.lbl_ipk.setText(fmt_eng(i_peak, "A"))
        self.lbl_l_min.setText(fmt_eng(l_min, "H"))
        self.lbl_c.setText(fmt_eng(c, "F"))
        self.lbl_pin.setText(f"{fmt_eng(pin, 'W')}  (Iin ≈ {fmt_eng(iin, 'A')})")

        self.status.setText(
            f"<span style='color:{C.GREEN};'>{'Buck' if is_buck else 'Boost'}: D = "
            f"{d*100:.1f}%; inductor ripple ΔI = "
            f"{di/(iout if is_buck else iin)*100:.0f}% of "
            f"{'Iout' if is_buck else 'Iin'}.</span>  "
            f"<span style='color:{C.TEXT_DIM};'>First-pass numbers — real designs need "
            f"the controller's slope-compensation, ESR, dead-time and efficiency map.</span>")


# ─── Tab: Annular Ring / Drill Checker ───────────────────────────────────────

class AnnularRingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Pad / Drill Geometry")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Pad diameter:"), 0, 0)
        self.w_pad = QLineEdit("1.0mm")
        self.w_pad.setPlaceholderText("e.g. 1.0mm, 40mil")
        grid.addWidget(self.w_pad, 0, 1)

        grid.addWidget(QLabel("Drill (finished):"), 0, 2)
        self.w_drill = QLineEdit("0.5mm")
        self.w_drill.setPlaceholderText("e.g. 0.3mm, 20mil")
        grid.addWidget(self.w_drill, 0, 3)

        grid.addWidget(QLabel("Drill tolerance:"), 1, 0)
        self.w_tol = QLineEdit("0.075mm")
        self.w_tol.setPlaceholderText("typical fab: 0.05–0.10 mm")
        grid.addWidget(self.w_tol, 1, 1)

        grid.addWidget(QLabel("IPC class:"), 1, 2)
        self.w_cls = QComboBox(); self.w_cls.addItems(list(IPC_CLASS_AR_MM.keys()))
        self.w_cls.setCurrentText("Class 2 (general)")
        grid.addWidget(self.w_cls, 1, 3)

        self.btn = accent_button("Check"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 2, 1)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)
        for w in (self.w_pad, self.w_drill, self.w_tol):
            w.returnPressed.connect(self._calc)
        self.w_cls.currentIndexChanged.connect(self._calc)

        rc, rg = result_card("Annular Ring")
        self.lbl_ar = big_value_label()
        self.lbl_min = mono(bold=True, color=C.GOLD)
        self.lbl_verdict = mono(bold=True, color=C.GREEN, size=14)
        rg.addWidget(caption("Annular ring (worst-case):"), 0, 0); rg.addWidget(self.lbl_ar, 0, 1)
        rg.addWidget(caption("IPC minimum:"),               0, 2); rg.addWidget(self.lbl_min, 0, 3)
        rg.addWidget(caption("Verdict:"),                   1, 0); rg.addWidget(self.lbl_verdict, 1, 1, 1, 3)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)

        # Sweep table: pad ↔ recommended drill
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Pad (mm)", "Max drill (mm)", "Resulting AR (mm)", "Notes"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for c in range(3):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents)
        outer.addWidget(self.table, 1)

        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        pad = parse_length_mm(self.w_pad.text())
        drill = parse_length_mm(self.w_drill.text())
        tol = parse_length_mm(self.w_tol.text())
        if pad is None or drill is None or tol is None or pad <= 0 or drill <= 0:
            self.status.setText(f"<span style='color:{C.RED};'>Check pad and drill values.</span>")
            return
        min_ar = IPC_CLASS_AR_MM[self.w_cls.currentText()]
        ar = annular_ring_mm(pad, drill, tol)
        self.lbl_ar.setText(f"{ar*1000:.0f} µm  ({ar:.3f} mm)")
        self.lbl_min.setText(f"{min_ar*1000:.0f} µm  ({min_ar:.2f} mm)")
        if ar < 0:
            self.lbl_verdict.setText("✗ HOLE LARGER THAN PAD")
            self.lbl_verdict.setStyleSheet(f"color:{C.RED}; font-weight:bold;")
            color = C.RED
        elif ar < min_ar:
            self.lbl_verdict.setText(f"✗ FAIL — short by {(min_ar-ar)*1000:.0f} µm")
            self.lbl_verdict.setStyleSheet(f"color:{C.RED}; font-weight:bold;")
            color = C.RED
        elif ar < min_ar * 1.5:
            self.lbl_verdict.setText(f"⚠ TIGHT — passes but only {(ar-min_ar)*1000:.0f} µm spare")
            self.lbl_verdict.setStyleSheet(f"color:{C.ORANGE}; font-weight:bold;")
            color = C.ORANGE
        else:
            self.lbl_verdict.setText(f"✓ PASS — {(ar-min_ar)*1000:.0f} µm margin")
            self.lbl_verdict.setStyleSheet(f"color:{C.GREEN}; font-weight:bold;")
            color = C.GREEN

        # Recommended drill for each common pad size, at the chosen class.
        pads_mm = [0.5, 0.7, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0]
        self.table.setRowCount(len(pads_mm))
        for row, p in enumerate(pads_mm):
            max_drill = p - 2 * min_ar - tol
            ar_at = annular_ring_mm(p, max_drill, tol) if max_drill > 0 else -1
            notes = "below fab minimum" if max_drill < 0.20 else (
                "common signal via" if max_drill < 0.40 else "power / mounting")
            cells = [f"{p:.2f}", f"{max(0, max_drill):.2f}",
                     f"{max(0, ar_at)*1000:.0f} µm", notes]
            for col, t in enumerate(cells):
                it = QTableWidgetItem(t)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                    it.setForeground(QColor(C.GOLD))
                elif col == 1:
                    it.setFont(QFont("Consolas", 12))
                    it.setForeground(QColor(C.ACCENT))
                else:
                    it.setForeground(QColor(C.TEXT_DIM))
                    it.setFont(QFont("Consolas", 11))
                self.table.setItem(row, col, it)
        self.table.resizeColumnsToContents()

        self.status.setText(
            f"<span style='color:{color};'>AR = (pad − finished_drill − tol) / 2.</span>  "
            f"<span style='color:{C.TEXT_DIM};'>Internal annular rings are typically "
            f"smaller — check your fab's capability sheet (Class 3 is the conservative "
            f"choice for high-rel work).</span>")


# ─── Tab: IPC-7351 Land Pattern Reference ────────────────────────────────────

class PadReferenceTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        info = QLabel(
            "<b>IPC-7351 Nominal (N) land patterns</b> — quick reference for common "
            "two-terminal and small IC packages. Values are <i>approximate</i> — verify "
            "the exact dimensions in your library tool (KiCad's IPC calculator, "
            "Library Loader, your CAD suite) before laying out a footprint.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color:{C.TEXT}; padding:4px;")
        outer.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Package", "Density", "Pad W (mm)", "Pad H (mm)",
             "Pitch (mm)", "Court W", "Court H", "Notes"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        for c in range(7):
            self.table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setRowCount(len(IPC7351_LANDS))
        for row, entry in enumerate(IPC7351_LANDS):
            cells = [entry[0], entry[1],
                     f"{entry[2]:.2f}", f"{entry[3]:.2f}",
                     f"{entry[4]:.3f}",
                     f"{entry[5]:.2f}", f"{entry[6]:.2f}",
                     entry[7]]
            for col, text in enumerate(cells):
                it = QTableWidgetItem(text)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    it.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                    it.setForeground(QColor(C.GOLD))
                elif col == 1:
                    it.setForeground(QColor(C.ACCENT))
                    it.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
                elif col == 7:
                    it.setForeground(QColor(C.TEXT_DIM))
                    it.setFont(QFont("Consolas", 11))
                else:
                    it.setForeground(QColor(C.TEXT))
                    it.setFont(QFont("Consolas", 12))
                self.table.setItem(row, col, it)
        self.table.resizeColumnsToContents()
        outer.addWidget(self.table, 1)

        footer = status_label()
        footer.setText(
            f"<span style='color:{C.TEXT_DIM};'>Density classes: <b>M</b>ost = larger "
            f"courtyards / better hand-rework. <b>N</b>ominal = balanced (shown here). "
            f"<b>L</b>east = density-first, hot-air rework only. Adjust paste-mask aperture "
            f"with a 5–10% reduction for fine-pitch parts.</span>")
        outer.addWidget(footer)


# ─── Tab: Panelisation ───────────────────────────────────────────────────────

class PanelisationTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(8)

        grp = QGroupBox("Board and Panel  (millimetres)")
        grid = QGridLayout(grp); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Board X:"), 0, 0)
        self.w_bx = QLineEdit("50"); grid.addWidget(self.w_bx, 0, 1)
        grid.addWidget(QLabel("Board Y:"), 0, 2)
        self.w_by = QLineEdit("80"); grid.addWidget(self.w_by, 0, 3)

        grid.addWidget(QLabel("Panel X:"), 1, 0)
        self.w_px = QLineEdit("305"); self.w_px.setPlaceholderText("V-score / tab default 305 mm")
        grid.addWidget(self.w_px, 1, 1)
        grid.addWidget(QLabel("Panel Y:"), 1, 2)
        self.w_py = QLineEdit("457"); grid.addWidget(self.w_py, 1, 3)

        grid.addWidget(QLabel("Spacing between boards:"), 2, 0)
        self.w_s = QLineEdit("2"); self.w_s.setPlaceholderText("V-score≈0, tab-rout≈2–3")
        grid.addWidget(self.w_s, 2, 1)
        grid.addWidget(QLabel("Edge rail (each side):"), 2, 2)
        self.w_r = QLineEdit("5"); self.w_r.setPlaceholderText("typical 5–10 mm")
        grid.addWidget(self.w_r, 2, 3)

        grid.addWidget(QLabel("Panel cost (optional):"), 3, 0)
        self.w_cost = QLineEdit("")
        self.w_cost.setPlaceholderText("e.g. 25  (per panel; any currency)")
        grid.addWidget(self.w_cost, 3, 1)

        self.btn = accent_button("Calculate"); self.btn.clicked.connect(self._calc)
        grid.addWidget(self.btn, 0, 4, 4, 1)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        outer.addWidget(grp)
        for w in (self.w_bx, self.w_by, self.w_px, self.w_py,
                   self.w_s, self.w_r, self.w_cost):
            w.returnPressed.connect(self._calc)

        rc, rg = result_card("Panel Yield")
        self.lbl_n = big_value_label()
        self.lbl_orient = mono(color=C.ACCENT)
        self.lbl_grid = mono(color=C.TEXT)
        self.lbl_util = mono(bold=True, color=C.GOLD)
        self.lbl_cost = mono(color=C.TEXT)
        rg.addWidget(caption("Boards per panel:"), 0, 0); rg.addWidget(self.lbl_n, 0, 1)
        rg.addWidget(caption("Orientation:"),       0, 2); rg.addWidget(self.lbl_orient, 0, 3)
        rg.addWidget(caption("Grid (× × y):"),       1, 0); rg.addWidget(self.lbl_grid, 1, 1)
        rg.addWidget(caption("Utilisation:"),        1, 2); rg.addWidget(self.lbl_util, 1, 3)
        rg.addWidget(caption("Cost per board:"),     2, 0); rg.addWidget(self.lbl_cost, 2, 1, 1, 3)
        rg.setColumnStretch(4, 1)
        outer.addWidget(rc)
        outer.addStretch(1)
        self.status = status_label()
        outer.addWidget(self.status)
        self._calc()

    def _calc(self):
        try:
            bx = float(self.w_bx.text().replace(",", "."))
            by = float(self.w_by.text().replace(",", "."))
            px = float(self.w_px.text().replace(",", "."))
            py = float(self.w_py.text().replace(",", "."))
            s = float(self.w_s.text().replace(",", "."))
            r = float(self.w_r.text().replace(",", "."))
        except ValueError:
            self.status.setText(f"<span style='color:{C.RED};'>Enter numbers in mm.</span>")
            return
        if min(bx, by, px, py) <= 0:
            self.status.setText(f"<span style='color:{C.RED};'>Board and panel dimensions must be &gt; 0.</span>")
            return

        n1, n2, nx1, ny1, nx2, ny2 = boards_per_panel(bx, by, px, py, s, r)
        if n2 > n1:
            n, ox, oy, orient = n2, nx2, ny2, "rotated 90°"
            board_area_used = nx2 * by * ny2 * bx
        else:
            n, ox, oy, orient = n1, nx1, ny1, "as drawn"
            board_area_used = nx1 * bx * ny1 * by

        panel_area = px * py
        util = (n * bx * by) / panel_area * 100 if panel_area > 0 else 0
        self.lbl_n.setText(f"{n}")
        self.lbl_orient.setText(orient)
        self.lbl_grid.setText(f"{ox} × {oy}")
        self.lbl_util.setText(f"{util:.1f}%")

        cost_text = self.w_cost.text().strip()
        if cost_text and n > 0:
            try:
                c = float(cost_text.replace(",", "."))
                self.lbl_cost.setText(f"{c/n:.3f}  per board  (panel = {c:.2f})")
            except ValueError:
                self.lbl_cost.setText("— (invalid cost)")
        else:
            self.lbl_cost.setText("—  (enter panel cost above)")

        if n == 0:
            self.status.setText(
                f"<span style='color:{C.RED};'>No boards fit — usable area "
                f"{px - 2*r:.0f} × {py - 2*r:.0f} mm too small for "
                f"{bx:.0f} × {by:.0f} board(s) plus spacing.</span>")
        else:
            self.status.setText(
                f"<span style='color:{C.GREEN};'>{n} boards/panel — "
                f"{util:.0f}% utilisation, {orient}.</span>  "
                f"<span style='color:{C.TEXT_DIM};'>Adds-on (fiducials, tooling holes, "
                f"breakaway tabs) typically eat 5–10 mm of rail per edge — increase if "
                f"your fab requires more.</span>")


# ─── Main Window ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCB Design Toolkit")
        self.setMinimumSize(1100, 720)
        self._build()

    def _build(self):
        mb = self.menuBar()
        fm = mb.addMenu("File")
        fm.addAction("Quit", self.close)
        hm = mb.addMenu("Help")
        hm.addAction("About", self._about)

        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(8, 8, 8, 4)

        title = QLabel(
            f"<span style='font-size:18px; font-weight:bold; color:{C.ACCENT};'>"
            f"PCB Design Toolkit</span>"
            f"<span style='font-size:12px; color:{C.TEXT_DIM};'>"
            f"   Calculators &amp; checkers for everyday board design</span>")
        title.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(title)
        lay.addSpacing(4)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        def _add_category(label, children):
            sub = QTabWidget()
            for w, name in children:
                sub.addTab(w, name)
            self.tabs.addTab(sub, f"  {label}  ")

        _add_category("Voltage Dividers", [
            (DividerCalcTab(),       "Calculator"),
            (DividerFinderTab(),     "Resistor Finder"),
        ])
        _add_category("Resistors", [
            (ResistorPowerTab(),     "Power Dissipation"),
            (SeriesParallelTab(),    "Series / Parallel Solver"),
            (LEDResistorTab(),       "LED Series Resistor"),
        ])
        _add_category("Traces", [
            (TraceWidthTab(),        "Width (IPC-2221)"),
            (TraceImpedanceTab(),    "Impedance"),
            (TraceResistanceTab(),   "Resistance & Vdrop"),
            (CurrentCapacityTab(),   "Capacity Check"),
        ])
        _add_category("Vias & Drill", [
            (ViaCurrentTab(),        "Via Current"),
            (AnnularRingTab(),       "Annular Ring"),
        ])
        _add_category("Filters & Caps", [
            (RCFilterTab(),          "RC / RL Filter"),
            (CapSizingTab(),         "Capacitor Sizing"),
            (CrystalLoadTab(),       "Crystal Load Caps"),
        ])
        _add_category("Power & Thermal", [
            (LDOThermalTab(),        "LDO Thermal"),
            (CopperPourTab(),        "Copper Pour Thermal"),
            (BuckBoostTab(),         "Buck / Boost"),
        ])
        _add_category("Manufacturing", [
            (PadReferenceTab(),      "IPC-7351 Land Patterns"),
            (PanelisationTab(),      "Panelisation"),
        ])

        lay.addWidget(self.tabs)

        sb = QStatusBar()
        sb.showMessage("Enter values and press Enter, or click the calculate button on each tab.")
        self.setStatusBar(sb)

    def _about(self):
        QMessageBox.about(
            self, "About",
            "PCB Design Toolkit v1.1\n\n"
            "Calculators and checkers grouped by category:\n"
            "  • Voltage dividers — calculator + E-series finder\n"
            "  • Resistors — power, series/parallel solver, LED resistor\n"
            "  • Traces — IPC-2221 width, impedance, R / IR-drop, capacity check\n"
            "  • Vias & drill — via current, annular ring\n"
            "  • Filters & caps — RC/RL filter, capacitor sizing, crystal load\n"
            "  • Power & thermal — LDO, copper-pour θJA, buck/boost first-pass\n"
            "  • Manufacturing — IPC-7351 land patterns, panelisation\n\n"
            "All results are engineering estimates. Always confirm critical\n"
            "values against component datasheets, IPC standards and your\n"
            "PCB manufacturer's capabilities. Use at your own risk.")


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    win = MainWindow()
    win.show()
    win.raise_()
    win.activateWindow()
    sys.exit(app.exec())