# PCB Design Toolkit

A tabbed PyQt6 desktop app collecting the calculators and checkers I reach for on most PCB designs.

## Tools

- **Voltage Divider Calculator** — Vout, divider current and per-resistor power, with optional load across R2.
- **Voltage Divider Resistor Finder** — best E-series (E6 … E96) R1/R2 pairs for a target Vout, ranked by voltage error.
- **Resistor Power Dissipation** — I²R, voltage drop, required rating after derating, and the smallest SMD package (0201 → 2512) plus through-hole rating that fits.
- **Via Current Calculator** — IPC-2221 current per via across standard finished hole sizes (0.20 → 1.00 mm) and the number of vias needed for a target current.
- **More Tools** — roadmap of additional calculators to add (trace width, impedance, LDO thermal, etc.).

## Requirements

- Python 3.10+
- PyQt6 (see [requirements.txt](requirements.txt))

## Install & Run

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python pcb-design-toolkit.py
```

## Input Conventions

Resistor and SI fields accept the shorthand most schematics use:

- Resistance: `100`, `4.7k`, `10K`, `2M2`, `4k7`, `0R1`, `1.5MΩ`
- Voltage / current: `3.3`, `3.3V`, `50m`, `500mA`, `1.2A`, `10u`

Press `Enter` in any input to recalculate the current tab.

## ⚠️ AI Disclaimer

This project — both the source code and this README — was generated with the assistance of AI (Claude). It has **not** been independently audited and may contain bugs, incorrect formulas, or unsafe defaults.

All outputs (resistor pairs, package recommendations, via current estimates, etc.) are **engineering estimates** based on textbook formulas (IPC-2221 for vias, I²R for power, ideal-divider math). Real-world behavior depends on copper pour, thermal relief, plating quality, datasheet derating curves, and your fab's actual capabilities.

**Use at your own risk.** Always verify critical values against component datasheets, the relevant IPC standards (IPC-2152 for traces, IPC-7351 for footprints, etc.), and your PCB manufacturer before committing to a design. The authors accept no liability for damage, failed boards, or any other consequences arising from use of this software.

## License

No license specified yet — treat as "all rights reserved" until one is added.
