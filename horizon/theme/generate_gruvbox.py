#!/usr/bin/env python3
"""Generate Horizon EDA colour presets from the KiCad Gruvbox theme.

Source of truth: ~/.local/share/kicad/*/colors/gruvbox.json (fallback: config dir)
Output: gruvbox.schematic.json (layer_colors, layered=false)
        gruvbox.board.json     (layer_colors, layered=true)

Horizon stores colours as floats 0..1 and keys layers by their integer id.
KiCad stores them as "rgb(r, g, b)" / "rgba(r, g, b, a)" strings with layer names.
"""

import json
import re
import sys
from pathlib import Path

KIcad_THEME = Path.home() / ".config/kicad/10.0/colors/gruvbox.json"
OUT_DIR = Path(__file__).resolve().parent

# Gruvbox canonical palette; also the fallback if the KiCad theme is missing.
GRUVBOX = {
    "bg0_h": "1d2021",
    "bg0": "282828",
    "bg1": "3c3836",
    "bg2": "504945",
    "bg3": "665c54",
    "bg4": "7c6f64",
    "fg0": "fbf1c7",
    "fg1": "ebdbb2",
    "fg2": "d5c4a1",
    "fg3": "bdae93",
    "fg4": "a89984",
    "red": "fb4934",
    "green": "b8bb26",
    "yellow": "fabd2f",
    "blue": "83a598",
    "purple": "d3869b",
    "aqua": "8ec07c",
    "orange": "fe8019",
}


def hex_to_rgb(h):
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def rgb_float(r, g, b):
    return {"b": round(b / 255, 4), "g": round(g / 255, 4), "r": round(r / 255, 4)}


def palette(name):
    return rgb_float(*hex_to_rgb(GRUVBOX[name]))


def parse_kicad_color(value):
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", value)
    if not m:
        raise ValueError(f"cannot parse colour {value!r}")
    return rgb_float(*(int(x) for x in m.groups()))


def load_kicad():
    for cand in [
        KIcad_THEME,
        Path.home() / ".local/share/kicad/10.0/colors/gruvbox.json",
    ]:
        if cand.exists():
            return json.loads(cand.read_text()), cand
    return None, None


# --- schematic mapping: KiCad schematic keys -> Horizon palette entries ---
SCHEMATIC_MAP = {
    "BACKGROUND": "background",
    "GRID": "grid",
    "FRAME": "worksheet",
    "NET": "wire",
    "BUS": "bus",
    "JUNCTION": "junction",
    "PIN": "pin",
    "PIN_HIDDEN": "hidden",
    "CURSOR_NORMAL": "cursor",
    "CURSOR_TARGET": "anchor",
    "ERROR": "erc_error",
    "MARKER_BORDER": "erc_warning",
    "SELECTABLE_PRELIGHT": "brightened",
    "SELECTABLE_ALWAYS": "aux_items",
    "SELECTION_LINE": "brightened",
    "SELECTION_BOX": "drag_net_collision",
    "TEXT_OVERLAY": "note",
    "AIRWIRE": "no_connect",
    "AIRWIRE_ROUTER": "bus_junction",
}

# --- board mapping: KiCad board keys -> Horizon palette entries ---
BOARD_MAP = {
    "BACKGROUND": "background",
    "GRID": "grid",
    "FRAME": "worksheet",
    "NET": "ratsnest",
    "AIRWIRE": "ratsnest",
    "CONNECTION_LINE": "ratsnest",
    "BUS": "bus",
    "JUNCTION": "points",
    "PIN": "pad_through_hole",
    "PIN_HIDDEN": "footprint_text_invisible",
    "CURSOR_NORMAL": "cursor",
    "CURSOR_TARGET": "anchor",
    "ERROR": "drc_error",
    "MARKER_BORDER": "drc_warning",
    "SELECTABLE_PRELIGHT": "aux_items",
    "SELECTABLE_ALWAYS": "aux_items",
    "SELECTION_LINE": "points",
    "SELECTION_BOX": "conflicts_shadow",
    "TEXT_OVERLAY": "f_silks",
    "SHADOW": "outline_area",
    "AIRWIRE_ROUTER": "drc_warning",
    "DIFFPAIR": "eco2_user",
    "ORIGIN": "grid_axes",
    "DIMENSION": "f_fab",
    "FRAG_ORPHAN": "no_connect",
    "SEARCH": "eco1_user",
    "SEARCH_CURRENT": "eco2_user",
}

# Horizon layer ids -> KiCad key, board preset
BOARD_LAYERS = {
    0: "copper.f",           # TOP_COPPER
    -1: "copper.in1",        # IN1_COPPER
    -2: "copper.in2",
    -3: "copper.in3",
    -4: "copper.in4",
    -100: "copper.b",        # BOTTOM_COPPER
    10: "f_mask",            # TOP_MASK
    -110: "b_mask",          # BOTTOM_MASK
    20: "f_silks",           # TOP_SILKSCREEN
    -120: "b_silks",         # BOTTOM_SILKSCREEN
    30: "f_paste",           # TOP_PASTE
    -130: "b_paste",         # BOTTOM_PASTE
    40: "f_fab",             # TOP_PACKAGE
    -140: "b_fab",           # BOTTOM_PACKAGE
    50: "f_fab",             # TOP_ASSEMBLY
    -150: "b_fab",           # BOTTOM_ASSEMBLY
    60: "f_crtyd",           # TOP_COURTYARD
    -160: "b_crtyd",         # BOTTOM_COURTYARD
    100: "edge_cuts",        # L_OUTLINE
    110: "edge_cuts",        # OUTLINE_NOTES
    200: "user_1",           # TOP_NOTES
    -200: "user_1",          # BOTTOM_NOTES
}

# Horizon layer ids -> palette name, schematic preset
SCHEMATIC_LAYERS = {
    -1: "orange",   # IN1
    -2: "purple",
    -3: "aqua",
    -4: "blue",
    -100: "green",  # BOTTOM_COPPER
    10: "yellow",
    -110: "yellow",
    20: "fg1",
    -120: "fg1",
    30: "fg4",
    -130: "fg4",
    40: "bg3",
    -140: "bg3",
    50: "bg3",
    -150: "bg3",
    60: "bg3",
    -160: "bg3",
    100: "orange",
    110: "orange",
    200: "fg3",
    -200: "fg3",
}


def kicad_get(section, key, default_palette_key="fg1"):
    """Fetch a KiCad colour by "a.b" path with palette fallback."""
    obj = section
    for part in key.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return palette(default_palette_key)
        obj = obj[part]
    try:
        return parse_kicad_color(obj)
    except ValueError:
        return palette(default_palette_key)


def build(preset_map, layer_map, layered, kicad_section):
    colors = {}
    for hz_key, kicad_key in preset_map.items():
        colors[hz_key] = kicad_get(kicad_section, kicad_key)
    layer_colors = {str(layer): kicad_get(kicad_section, k) for layer, k in []}
    return {"colors": colors, "layer_colors": layer_colors, "layered": layered}


def main():
    kicad, source = load_kicad()
    if kicad:
        print(f"source: {source}", file=sys.stderr)
        sch = kicad.get("schematic", {})
        brd = kicad.get("board", {})
    else:
        print("KiCad theme not found, using built-in Gruvbox hex values", file=sys.stderr)
        sch = brd = {}

    schematic = build(SCHEMATIC_MAP, {}, False, sch)
    schematic["layer_colors"] = {
        str(k): palette(v) for k, v in SCHEMATIC_LAYERS.items()
    }
    board = build(BOARD_MAP, {}, True, brd)
    board["layer_colors"] = {str(k): kicad_get(brd, v) for k, v in BOARD_LAYERS.items()}

    (OUT_DIR / "gruvbox.schematic.json").write_text(
        json.dumps(schematic, indent=2, sort_keys=True) + "\n"
    )
    (OUT_DIR / "gruvbox.board.json").write_text(
        json.dumps(board, indent=2, sort_keys=True) + "\n"
    )
    print("wrote gruvbox.schematic.json and gruvbox.board.json", file=sys.stderr)


if __name__ == "__main__":
    main()