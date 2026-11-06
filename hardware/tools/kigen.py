"""Small KiCad 7 project generator used to bootstrap the drone boards.

A board is described as blocks of parts; each part maps symbol pin numbers to
net names. The generator writes:

* a flat schematic where every used pin gets a short wire stub and a net label
  (global labels for nets that cross boards), unused pins get no-connect flags;
* a project file with net classes;
* a PCB with the outline, mounting holes, every footprint (with nets assigned
  from the schematic's exported netlist) placed in block clusters, and a GND pour.

It is a one-time bootstrap: once the boards are being edited in KiCad, edit the
KiCad files directly.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from kiutils.items.common import (Effects, Font, Justify, PageSettings, Position,
                                  Property, Stroke, TitleBlock)
from kiutils.items.schitems import (Connection, GlobalLabel, HierarchicalSheetInstance,
                                    LocalLabel, NoConnect, Rectangle, SchematicSymbol,
                                    SymbolProjectInstance, SymbolProjectPath, Text)
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib

SYMDIR = Path("/usr/share/kicad/symbols")
FPDIR = Path("/usr/share/kicad/footprints")
HW = Path(__file__).resolve().parent.parent
PROJECT_SYMLIB = HW / "lib" / "drone.kicad_sym"
NS = uuid.UUID("6f1c2a52-6a7e-4c1e-9d55-1a2b3c4d5e6f")
GRID = 1.27
STUB = 2.54
DATE = "2026-11-06"

# Nets that cross boards: drawn as global labels (see docs/electrical/README.md §3)
GLOBAL_NETS = {
    "PWR_VBAT", "PWR_VBAT_LGT", "PWR_19V_JET", "PWR_5V_AUX", "PWR_5V_SERVO", "GND",
    "FC_CURR_SNS", "FC_VBAT_SNS", "I2S_BCLK", "I2S_LRCLK", "I2S_DOUT", "AMP_SD", "OUT_EN",
    "PWM_GIMBAL", "PWM_FLASH", "PWM_IR", "SPARE_OUT", "I2C_SDA", "I2C_SCL",
    "FC_UART_TX", "FC_UART_RX", "SPK_P", "SPK_N", "LED_FLASH_P", "LED_FLASH_N",
    "LED_IR_P", "LED_IR_N", "NTC_FLASH", "NTC_IR",
} | {f"SENS{i}_{s}" for i in range(1, 9) for s in ("5V", "TX", "RX")}


def uid(*parts) -> str:
    return str(uuid.uuid5(NS, "/".join(map(str, parts))))


def snap(v: float, g: float = GRID) -> float:
    return round(round(v / g) * g, 4)


# --------------------------------------------------------------------------
# Symbol libraries
# --------------------------------------------------------------------------
_libs: dict[str, dict] = {}


def _lib(nick: str) -> dict:
    if nick not in _libs:
        path = PROJECT_SYMLIB if nick == "drone" else SYMDIR / f"{nick}.kicad_sym"
        lib = SymbolLib.from_file(str(path))
        _libs[nick] = {s.entryName: s for s in lib.symbols}
    return _libs[nick]


_flat: dict[str, object] = {}


def flat_symbol(lib_id: str):
    """Return a flattened (no `extends`) deep copy of a library symbol."""
    if lib_id in _flat:
        return _flat[lib_id]
    nick, name = lib_id.split(":", 1)
    by = _lib(nick)
    s = by[name]
    if s.extends:
        base = copy.deepcopy(flat_symbol(f"{nick}:{s.extends}"))
        props = {p.key: p for p in base.properties}
        for p in s.properties:
            props[p.key] = copy.deepcopy(p)
        base.properties = list(props.values())
        out = base  # derived symbols inherit in_bom / on_board from their parent
    else:
        out = copy.deepcopy(s)
    out.entryName = name
    out.libraryNickname = nick
    out.extends = None
    for u in out.units:
        u.entryName = name
        u.libraryNickname = None
    _flat[lib_id] = out
    return out


_DIR = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}


@dataclass
class PinGeo:
    number: str
    name: str
    etype: str
    hidden: bool
    x: float  # endpoint relative to symbol origin, schematic coords (y down)
    y: float
    ox: int   # outward direction, schematic coords
    oy: int


def symbol_pins(lib_id: str, unit: int) -> list[PinGeo]:
    sym = flat_symbol(lib_id)
    pins = []
    for u in sym.units:
        if u.unitId not in (0, unit) or u.styleId not in (0, 1):
            continue
        for p in u.pins:
            a = int(round(p.position.angle or 0)) % 360
            vx, vy = _DIR[a]
            pins.append(PinGeo(p.number, p.name, p.electricalType, bool(p.hide),
                               float(p.position.X), -float(p.position.Y), -vx, vy))
    return pins


def unit_count(lib_id: str) -> int:
    return max([u.unitId for u in flat_symbol(lib_id).units] + [1])


# --------------------------------------------------------------------------
# Board description
# --------------------------------------------------------------------------
@dataclass
class Part:
    ref: str
    lib_id: str
    value: str
    footprint: str
    pins: dict
    unit: int = 1
    dnp: bool = False
    fields: dict = field(default_factory=dict)


@dataclass
class Block:
    title: str
    parts: list = field(default_factory=list)
    cols: int = 6

    def add(self, *a, **k) -> Part:
        p = Part(*a, **k)
        self.parts.append(p)
        return p


@dataclass
class Board:
    name: str
    title: str
    size: tuple            # PCB outline (w, h) in mm
    layers: int = 2
    paper: str = "A3"
    holes: str = "M3"
    comments: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    blocks: list = field(default_factory=list)
    flags: list = field(default_factory=list)  # nets that need a PWR_FLAG
    zones: list = field(default_factory=list)  # (layer name, net)
    fixed: dict = field(default_factory=dict)  # ref -> (rotation deg, centre x, centre y) in board mm
    hole_inset: float = 4.0
    pack_margin: tuple = None                  # (left, top, right, bottom) mm; default keeps holes clear

    def block(self, title: str, cols: int = 6) -> Block:
        b = Block(title, cols=cols)
        self.blocks.append(b)
        return b

    def parts(self):
        return [p for b in self.blocks for p in b.parts]


# Handy part constructors -------------------------------------------------
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
C1210 = "Capacitor_SMD:C_1210_3225Metric"
LED0603 = "LED_SMD:LED_0603_1608Metric"


def R(blk, ref, val, a, b, fp=R0603, **k):
    return blk.add(ref, "Device:R_Small", val, fp, {"1": a, "2": b}, **k)


def C(blk, ref, val, a, b, fp=C0603, **k):
    return blk.add(ref, "Device:C_Small", val, fp, {"1": a, "2": b}, **k)


def CP(blk, ref, val, plus, minus, fp="Capacitor_SMD:CP_Elec_8x10.5", **k):
    return blk.add(ref, "Device:C_Polarized_Small", val, fp, {"1": plus, "2": minus}, **k)


def LED(blk, ref, val, anode, cathode, fp=LED0603):
    return blk.add(ref, "Device:LED_Small", val, fp, {"2": anode, "1": cathode})


def CONN(blk, ref, val, fp, nets: list, **k):
    n = len(nets)
    return blk.add(ref, f"Connector_Generic:Conn_01x{n:02d}", val, fp,
                   {str(i + 1): net for i, net in enumerate(nets) if net is not None}, **k)


def HOLE(blk, ref, size):
    fp = {"M3": "MountingHole:MountingHole_3.2mm_M3",
          "M2.5": "MountingHole:MountingHole_2.7mm_M2.5"}[size]
    return blk.add(ref, "Mechanical:MountingHole", f"{size} hole", fp, {})


# --------------------------------------------------------------------------
# Schematic writer
# --------------------------------------------------------------------------
def _font(h=1.27):
    return Font(height=h, width=h)


def _label_len(text: str) -> float:
    return 1.0 * len(text) + 3.0


def _part_extent(p: Part):
    """Bounding box (relative to symbol origin) including stubs and labels."""
    pins = [g for g in symbol_pins(p.lib_id, p.unit)]
    xs, ys = [-3.81, 3.81], [-3.81, 3.81]
    for g in pins:
        xs.append(g.x)
        ys.append(g.y)
        net = p.pins.get(g.number)
        if net is None:
            continue
        ex, ey = g.x + g.ox * STUB, g.y + g.oy * STUB
        ll = _label_len(net)
        if g.oy == 0:          # horizontal pin: label continues outward
            xs.append(ex + g.ox * ll)
            ys += [ey - 1.5, ey + 1.5]
        else:                  # vertical pin: label reads left-to-right from the stub end
            xs.append(ex + ll)
            ys.append(ey + g.oy * 2.0)
    # room for reference/value text
    return min(xs) - 1.5, min(ys) - 2.5, max(xs) + 1.5, max(ys) + 2.5


class SchematicBuilder:
    def __init__(self, board: Board, outdir: Path):
        self.b = board
        self.out = outdir
        self.sch = Schematic.create_new()
        self.sch.version = 20230121
        self.sch.generator = "eeschema"
        self.root = uid(board.name, "root")
        self.sch.uuid = self.root
        self.lib_ids = []
        self.flag_n = 0

    # -- primitives -----------------------------------------------------
    def _wire(self, x1, y1, x2, y2, key):
        self.sch.graphicalItems.append(Connection(
            type="wire", points=[Position(x1, y1), Position(x2, y2)],
            stroke=Stroke(width=0, type="default"), uuid=uid(self.b.name, "w", key)))

    def _label(self, net, x, y, ox, oy, key):
        ang = 180 if (ox, oy) == (-1, 0) else 0
        just = "left" if ang == 0 else "right"
        eff = Effects(font=_font(), justify=Justify(horizontally=just))
        if net in GLOBAL_NETS:
            gl = GlobalLabel(text=net, shape="passive", fieldsAutoplaced=True,
                             position=Position(x, y, ang), effects=eff,
                             uuid=uid(self.b.name, "gl", key))
            gl.properties = [Property(key="Intersheetrefs", value="${INTERSHEET_REFS}", id=0,
                                      position=Position(x, y, ang),
                                      effects=Effects(font=_font(), hide=True))]
            self.sch.globalLabels.append(gl)
        else:
            eff.justify.vertically = "bottom"
            self.sch.labels.append(LocalLabel(text=net, position=Position(x, y, ang),
                                              effects=eff, fieldsAutoplaced=True,
                                              uuid=uid(self.b.name, "ll", key)))

    def _text(self, s, x, y, size=1.27, bold=False, key=None):
        f = _font(size)
        f.bold = bold
        self.sch.texts.append(Text(text=s, position=Position(x, y, 0),
                                   effects=Effects(font=f, justify=Justify(horizontally="left", vertically="bottom")),
                                   uuid=uid(self.b.name, "t", key or s)))

    def _symbol(self, p: Part, X, Y, ref_override=None):
        sym = flat_symbol(p.lib_id)
        if p.lib_id not in self.lib_ids:
            self.lib_ids.append(p.lib_id)
        ref = ref_override or p.ref
        nick, name = p.lib_id.split(":", 1)
        ss = SchematicSymbol()
        ss.libraryNickname, ss.entryName = nick, name
        ss.position = Position(X, Y, 0)
        ss.unit = p.unit
        ss.inBom = bool(sym.inBom) and not ref.startswith("#")
        ss.onBoard = bool(sym.onBoard) and not ref.startswith("#")
        ss.dnp = p.dnp
        ss.fieldsAutoplaced = True
        ss.uuid = uid(self.b.name, "sym", ref, p.unit)
        props = []
        for i, lp in enumerate(sym.properties):
            if lp.key.startswith("ki_"):
                continue
            val = {"Reference": ref, "Value": p.value, "Footprint": p.footprint}.get(lp.key, lp.value)
            pos = lp.position
            np = Property(key=lp.key, value=val, id=len(props),
                          position=Position(snap(X + pos.X, 0.01), snap(Y - pos.Y, 0.01), 0),
                          effects=copy.deepcopy(lp.effects) if lp.effects else Effects(font=_font()))
            if lp.key in ("Footprint", "Datasheet"):
                np.effects.hide = True
            props.append(np)
        for k, v in p.fields.items():
            props.append(Property(key=k, value=v, id=len(props), position=Position(X, Y, 0),
                                  effects=Effects(font=_font(), hide=True)))
        ss.properties = props
        ss.pins = {g.number: uid(self.b.name, "pin", ref, p.unit, g.number)
                   for g in symbol_pins(p.lib_id, p.unit)}
        ss.instances = [SymbolProjectInstance(name=self.b.name, paths=[
            SymbolProjectPath(sheetInstancePath=f"/{self.root}", reference=ref, unit=p.unit)])]
        self.sch.schematicSymbols.append(ss)
        return ss

    def _connect(self, p: Part, X, Y, ref=None):
        ref = ref or p.ref
        pins = symbol_pins(p.lib_id, p.unit)
        known = {g.number for g in pins}
        bad = set(p.pins) - known
        if bad:
            raise ValueError(f"{self.b.name} {ref} ({p.lib_id} unit {p.unit}): unknown pins {sorted(bad)}")
        done_pos = {}
        for g in pins:
            if g.number in p.pins:
                done_pos[(g.x, g.y)] = p.pins[g.number]
        for g in pins:
            ex, ey = snap(X + g.x), snap(Y + g.y)
            net = p.pins.get(g.number)
            if net is None:
                if g.etype == "no_connect" or (g.x, g.y) in done_pos:
                    continue
                if g.hidden and g.etype in ("passive", "power_in"):
                    continue
                self.sch.noConnects.append(NoConnect(position=Position(ex, ey),
                                                     uuid=uid(self.b.name, "nc", ref, p.unit, g.number)))
                continue
            sx, sy = snap(ex + g.ox * STUB), snap(ey + g.oy * STUB)
            key = (ref, p.unit, g.number)
            self._wire(ex, ey, sx, sy, key)
            self._label(net, sx, sy, g.ox, g.oy, key)

    # -- layout -----------------------------------------------------------
    def build(self):
        b = self.b
        papers = {"A4": (297, 210), "A3": (420, 297), "A2": (594, 420), "A1": (841, 594)}
        W, H = papers[b.paper]
        margin_x, top = 20.32, 22.86
        x0, y0 = margin_x, top
        shelf_h = 0.0
        usable_w = W - 2 * margin_x
        for bi, blk in enumerate(b.blocks):
            # lay parts out in rows of `cols`
            cells = []
            for p in blk.parts:
                x1, y1, x2, y2 = _part_extent(p)
                cells.append((p, x1, y1, x2, y2))
            rows, row = [], []
            for c in cells:
                row.append(c)
                if len(row) == blk.cols:
                    rows.append(row)
                    row = []
            if row:
                rows.append(row)
            bw = max(sum(c[3] - c[1] for c in r) for r in rows) + 7.62
            bh = sum(max(c[4] - c[2] for c in r) for r in rows) + 11.43
            if x0 + bw > W - margin_x and x0 > margin_x:
                x0 = margin_x
                y0 += shelf_h + 5.08
                shelf_h = 0
            bx, by = snap(x0, 2.54), snap(y0, 2.54)
            self.sch.shapes.append(Rectangle(start=Position(bx, by), end=Position(snap(bx + bw, 2.54), snap(by + bh, 2.54)),
                                             stroke=Stroke(width=0.25, type="dash"),
                                             uuid=uid(b.name, "blk", bi)))
            self._text(blk.title.upper(), bx + 2.54, by + 5.08, size=2.0, bold=True, key=("bt", bi))
            cy = by + 7.62
            for r in rows:
                cx = bx + 3.81
                rh = max(c[4] - c[2] for c in r)
                for (p, x1, y1, x2, y2) in r:
                    X, Y = snap(cx - x1, 2.54), snap(cy - y1, 2.54)
                    self._symbol(p, X, Y)
                    self._connect(p, X, Y)
                    cx += (x2 - x1)
                cy += rh
            x0 += bw + 5.08
            shelf_h = max(shelf_h, bh)
        if y0 + shelf_h > H - 45:  # keep blocks clear of the title block band
            raise ValueError(f"{b.name}: schematic content ({y0 + shelf_h:.0f} mm) does not fit {b.paper}")
        # power flags
        fy = y0 + shelf_h + 10.16
        fx = margin_x + 5.08
        self._text("POWER FLAGS (ERC)", fx - 2.54, fy - 5.08, size=1.5, bold=True, key="flags")
        for net in b.flags:
            self.flag_n += 1
            ref = f"#FLG{self.flag_n:02d}"
            p = Part(ref, "power:PWR_FLAG", "PWR_FLAG", "", {"1": net})
            X, Y = snap(fx, 2.54), snap(fy, 2.54)
            self._symbol(p, X, Y)
            self._connect(p, X, Y)
            fx += 7.62 + _label_len(net)
        # notes
        ny = fy + 10.16
        if b.notes:
            self._text("NOTES", margin_x, ny, size=1.8, bold=True, key="notes")
            for i, n in enumerate(b.notes):
                self._text(f"{i + 1}. {n}", margin_x, ny + 3.81 * (i + 1), key=("note", i))
            ny += 3.81 * (len(b.notes) + 1)
        if ny > H - 12:
            raise ValueError(f"{b.name}: schematic content ({ny:.0f} mm) does not fit {b.paper}")
        # header blocks
        self.sch.paper = PageSettings(paperSize=b.paper)
        self.sch.titleBlock = TitleBlock(title=b.title, date=DATE, revision="A",
                                         company="Jetson drone electronics",
                                         comments={i + 1: c for i, c in enumerate(b.comments[:4])})
        self.sch.libSymbols = [flat_symbol(l) for l in self.lib_ids]
        self.sch.sheetInstances = [HierarchicalSheetInstance(instancePath="/", page="1")]
        path = self.out / f"{b.name}.kicad_sch"
        self.sch.to_file(str(path))
        return path


# --------------------------------------------------------------------------
# Netlist (via kicad-cli) and verification
# --------------------------------------------------------------------------
def _sexpr(text: str):
    tokens = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text)
    stack, cur = [], []
    for t in tokens:
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return cur[0]


def _find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def export_netlist(sch_path: Path) -> dict:
    out = sch_path.with_suffix(".net")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr",
                    "-o", str(out), str(sch_path)], check=True, capture_output=True)
    tree = _sexpr(out.read_text())
    out.unlink()
    comps = {}
    for c in _find(_find(tree, "components")[0], "comp"):
        ref = _find(c, "ref")[0][1]
        fp = _find(c, "footprint")
        comps[ref] = {"value": _find(c, "value")[0][1], "footprint": fp[0][1] if fp else "",
                      "tstamp": _find(c, "tstamps")[0][1]}
    nets = {}
    for n in _find(_find(tree, "nets")[0], "net"):
        name = _find(n, "name")[0][1]
        nets[name] = [(_find(nd, "ref")[0][1], _find(nd, "pin")[0][1]) for nd in _find(n, "node")]
    return {"components": comps, "nets": nets}


def verify(board: Board, netlist: dict) -> list[str]:
    """Check every intended pin→net assignment made it into KiCad's netlist."""
    problems = []
    actual = {}
    for net, nodes in netlist["nets"].items():
        clean = net.lstrip("/")
        for ref, pin in nodes:
            actual[(ref, pin)] = clean
    for p in board.parts():
        for pin, net in p.pins.items():
            got = actual.get((p.ref, pin))
            if got != net:
                problems.append(f"{p.ref}.{pin}: expected {net}, KiCad has {got}")
    # single-node nets usually mean a typo
    for net, nodes in netlist["nets"].items():
        if len(nodes) == 1 and not net.startswith("unconnected-"):
            ref, pin = nodes[0]
            if not ref.startswith("#"):
                problems.append(f"net {net} has only one connection ({ref}.{pin})")
    return problems


# --------------------------------------------------------------------------
# Project file
# --------------------------------------------------------------------------
NETCLASS_KEYS = dict(bus_width=12, diff_pair_gap=0.25, diff_pair_via_gap=0.25, diff_pair_width=0.2,
                     line_style=0, microvia_diameter=0.3, microvia_drill=0.1, pcb_color="rgba(0, 0, 0, 0.000)",
                     schematic_color="rgba(0, 0, 0, 0.000)", wire_width=6)


def write_project(board: Board, outdir: Path):
    tmpl = json.loads(Path("/usr/share/kicad/template/kicad.kicad_pro").read_text())
    tmpl["meta"]["filename"] = f"{board.name}.kicad_pro"

    def nc(name, clearance, track, via_d, via_drill):
        d = dict(NETCLASS_KEYS)
        d.update(name=name, clearance=clearance, track_width=track, via_diameter=via_d, via_drill=via_drill)
        return d

    tmpl["net_settings"] = {
        "classes": [nc("Default", 0.2, 0.25, 0.6, 0.3),
                    nc("Power", 0.2, 1.0, 0.8, 0.4),
                    nc("HighCurrent", 0.2, 3.0, 1.0, 0.5)],
        "meta": {"version": 3},
        "net_colors": None,
        "netclass_assignments": None,
        "netclass_patterns": [
            {"netclass": "HighCurrent", "pattern": "PWR_VBAT"},
            {"netclass": "HighCurrent", "pattern": "VBAT_RAW"},
            {"netclass": "Power", "pattern": "PWR_*"},
            {"netclass": "Power", "pattern": "SW*"},
            {"netclass": "Power", "pattern": "LED_*"},
            {"netclass": "Power", "pattern": "SPK_*"},
            {"netclass": "Power", "pattern": "VOUT_*"},
            {"netclass": "Power", "pattern": "LS_SRC_*"},
            {"netclass": "Power", "pattern": "SENS*_5V"},
        ],
    }
    (outdir / f"{board.name}.kicad_pro").write_text(json.dumps(tmpl, indent=2) + "\n")
    (outdir / "sym-lib-table").write_text(
        '(sym_lib_table\n  (version 7)\n'
        '  (lib (name "drone")(type "KiCad")(uri "${KIPRJMOD}/../lib/drone.kicad_sym")(options "")(descr "Drone project symbols"))\n)\n')


# --------------------------------------------------------------------------
# PCB
# --------------------------------------------------------------------------
def build_pcb(board: Board, outdir: Path, netlist: dict, sch_name: str):
    import pcbnew
    from pcbnew import FromMM, VECTOR2I

    W, H = board.size
    ox, oy = 100.0, 100.0  # board origin on the PCB canvas (mm)
    brd = pcbnew.BOARD()
    brd.SetCopperLayerCount(board.layers)
    tb = brd.GetTitleBlock()
    tb.SetTitle(board.title)
    tb.SetRevision("A")
    tb.SetDate(DATE)
    tb.SetCompany("Jetson drone electronics")

    # outline
    rect = pcbnew.PCB_SHAPE(brd)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(VECTOR2I(FromMM(ox), FromMM(oy)))
    rect.SetEnd(VECTOR2I(FromMM(ox + W), FromMM(oy + H)))
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(FromMM(0.1))
    brd.Add(rect)

    # nets
    netinfo = {}
    pad_net = {}
    for name, nodes in netlist["nets"].items():
        clean = name.lstrip("/")
        if clean.startswith("unconnected-"):
            continue
        ni = pcbnew.NETINFO_ITEM(brd, clean)
        brd.Add(ni)
        netinfo[clean] = ni
        for ref, pin in nodes:
            pad_net[(ref, pin)] = ni

    # footprints, clustered by schematic block
    part_block = {}
    for bi, blk in enumerate(board.blocks):
        for p in blk.parts:
            part_block.setdefault(p.ref, bi)
    groups: dict[int, list] = {}
    for ref, c in netlist["components"].items():
        if ref.startswith("#") or not c["footprint"]:
            continue
        lib, name = c["footprint"].split(":", 1)
        fp = pcbnew.FootprintLoad(str(FPDIR / f"{lib}.pretty"), name)
        if fp is None:
            raise ValueError(f"{board.name}: footprint not found {c['footprint']}")
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetFPIDAsString(c["footprint"])
        fp.SetPath(pcbnew.KIID_PATH(f"/{c['tstamp']}"))
        if hasattr(fp, "SetSheetname"):
            fp.SetSheetname("Root")
            fp.SetSheetfile(sch_name)
        for pad in fp.Pads():
            ni = pad_net.get((ref, pad.GetNumber()))
            if ni is not None:
                pad.SetNet(ni)
        brd.Add(fp)
        groups.setdefault(part_block.get(ref, 99), []).append(fp)

    # holes go in the corners
    inset = board.hole_inset
    corners = [(inset, inset), (W - inset, inset), (inset, H - inset), (W - inset, H - inset)]
    holes = sorted([f for g in groups.values() for f in g if f.GetReference().startswith("H")],
                   key=lambda f: f.GetReference())
    for f, (hx, hy) in zip(holes, corners):
        f.SetPosition(VECTOR2I(FromMM(ox + hx), FromMM(oy + hy)))
        f.Reference().SetVisible(False)
        f.Value().SetVisible(False)

    # Pack each schematic block into a tight cluster (saved as a KiCad group),
    # then pack the clusters onto the board; clusters that don't fit are staged
    # to the right of the outline.
    import rectpack

    def box(f):
        """Physical extent plus the visible reference text (values live on F.Fab)."""
        bb = f.GetBoundingBox(False, False)
        if f.Reference().IsVisible():
            bb.Merge(f.Reference().GetBoundingBox())
        return bb

    def bbox_mm(f):
        bb = box(f)
        return bb, pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())

    def move_to(f, x, y):
        bb = box(f)
        pos = f.GetPosition()
        f.SetPosition(VECTOR2I(pos.x + FromMM(x) - bb.GetX(), pos.y + FromMM(y) - bb.GetY()))

    gap = 0.8
    if board.pack_margin:
        m_x, m_y, m_r, m_b = board.pack_margin
    else:
        reserve_lr = W >= H              # keep the corner holes clear along the shorter side
        m_x = m_r = 8.0 if reserve_lr else 1.5
        m_y = m_b = 1.5 if reserve_lr else 8.0
    area_w, area_h = W - m_x - m_r, H - m_y - m_b

    for ref, (rot, cx, cy) in board.fixed.items():
        f = brd.FindFootprintByReference(ref)
        f.SetOrientationDegrees(rot)
        bb = f.GetBoundingBox(False, False)
        pos = f.GetPosition()
        f.SetPosition(VECTOR2I(pos.x + FromMM(ox + cx) - bb.GetCenter().x,
                               pos.y + FromMM(oy + cy) - bb.GetCenter().y))
        for bi in groups:
            groups[bi] = [g for g in groups[bi] if g.GetReference() != ref]
        # edge-mounted connectors: solid zone connection, thermal spokes would be cut by the edge
        for pad in f.Pads():
            pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    movable = {bi: [f for f in fps if not f.GetReference().startswith("H")] for bi, fps in groups.items()}
    for fps in movable.values():
        for f in fps:  # lay parts longer than the board on their side
            _, w, h = bbox_mm(f)
            if h > area_h and w < h:
                f.SetOrientationDegrees(90)
    sizes = {f.GetReference(): bbox_mm(f)[1:] for fps in movable.values() for f in fps}
    byref = {f.GetReference(): f for fps in movable.values() for f in fps}

    def pack(rects, bins, sort_algo):
        """rects: [(rid, w, h)], bins: [(bid, w, h)] -> {rid: (bid, x, y)}"""
        pk = rectpack.newPacker(rotation=False, sort_algo=sort_algo)
        for bid, w, h in bins:
            pk.add_bin(w + 0.01, h + 0.01, bid=bid)
        for rid, w, h in rects:
            pk.add_rect(w, h, rid=rid)
        pk.pack()
        return {rid: (pk[b].bid, x, y) for (b, x, y, w, h, rid) in pk.rect_list()}

    # 1) tight cluster per block, clusters onto the board
    clusters = {}
    for bi, fps in movable.items():
        if not fps:
            continue
        total = sum((sizes[f.GetReference()][0] + gap) * (sizes[f.GetReference()][1] + gap) for f in fps)
        widest = max(sizes[f.GetReference()][0] for f in fps) + gap
        bin_w = max(widest, min(area_w, (total * 1.5) ** 0.5))
        got = pack([(f.GetReference(), sizes[f.GetReference()][0] + gap, sizes[f.GetReference()][1] + gap) for f in fps],
                   [("c", bin_w, 10000)], rectpack.SORT_AREA)
        cw = max(x + sizes[r][0] for r, (_, x, y) in got.items()) + gap
        ch = max(y + sizes[r][1] for r, (_, x, y) in got.items()) + gap
        clusters[bi] = (cw, ch, got)
    at = pack([(bi, cw, ch) for bi, (cw, ch, _) in clusters.items()], [("board", area_w, area_h)], rectpack.SORT_AREA)
    final = {}
    if len(at) == len(clusters):
        for bi, (cw, ch, got) in clusters.items():
            _, bx, by = at[bi]
            for r, (_, x, y) in got.items():
                final[r] = (ox + m_x + bx + x, oy + m_y + by + y)
    else:
        # 2) clusters don't all fit: pack individual parts, block by block, largest first
        order = [f.GetReference() for bi in sorted(movable)
                 for f in sorted(movable[bi], key=lambda f: -sizes[f.GetReference()][0] * sizes[f.GetReference()][1])]
        rects = [(r, sizes[r][0] + gap, sizes[r][1] + gap) for r in order]
        best = {}
        for algo in (rectpack.SORT_NONE, rectpack.SORT_AREA, rectpack.SORT_PERI):
            got = pack(rects, [("board", area_w, area_h)], algo)
            if len(got) > len(best):
                best = got
            if len(best) == len(rects):
                break
        for r, (_, x, y) in best.items():
            final[r] = (ox + m_x + x, oy + m_y + y)
        rest = [rr for rr in rects if rr[0] not in best]
        if rest:  # stage what still doesn't fit to the right of the outline
            got = pack(rest, [(f"s{i}", 150, max(H, 120.0)) for i in range(6)], rectpack.SORT_AREA)
            for r, (bid, x, y) in got.items():
                final[r] = (ox + W + 10.0 + 160.0 * int(bid[1:]) + x, oy + y)
    for r, (x, y) in final.items():
        move_to(byref[r], x, y)
    titles = {bi: blk.title for bi, blk in enumerate(board.blocks)}
    for bi, fps in movable.items():
        if not fps:
            continue
        grp = pcbnew.PCB_GROUP(brd)
        grp.SetName(titles.get(bi, "Other"))
        brd.Add(grp)
        for f in fps:
            grp.AddItem(f)

    # ground pours
    for layer_name, net in board.zones:
        z = pcbnew.ZONE(brd)
        z.SetLayer(brd.GetLayerID(layer_name))
        z.SetNet(netinfo[net])
        z.SetLocalClearance(FromMM(0.3))
        z.SetMinThickness(FromMM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        ol = z.Outline()
        ol.NewOutline()
        m = 0.5
        for (x, y) in [(m, m), (W - m, m), (W - m, H - m), (m, H - m)]:
            ol.Append(FromMM(ox + x), FromMM(oy + y))
        brd.Add(z)

    path = outdir / f"{board.name}.kicad_pcb"
    pcbnew.SaveBoard(str(path), brd, True)  # skip settings: keep our .kicad_pro net classes
    # zone filling and design rules need the board loaded with its project
    loaded = pcbnew.LoadBoard(str(path))
    ds = loaded.GetDesignSettings()
    ds.m_MinThroughDrill = FromMM(0.2)   # thermal-via footprints (TI PowerPAD) use 0.2 mm drills
    ds.m_HoleClearance = FromMM(0.25)
    ds.m_CopperEdgeClearance = FromMM(0.3)
    pcbnew.ZONE_FILLER(loaded).Fill(loaded.Zones())
    pcbnew.SaveBoard(str(path), loaded)  # also writes the rules into the .kicad_pro
    return path


def drc(pcb_path: Path) -> str:
    import os
    os.environ.setdefault("KICAD7_FOOTPRINT_DIR", str(FPDIR))
    os.environ.setdefault("KICAD7_SYMBOL_DIR", str(SYMDIR))
    import pcbnew
    brd = pcbnew.LoadBoard(str(pcb_path))
    rpt = pcb_path.with_suffix(".drc.rpt")
    pcbnew.WriteDRCReport(brd, str(rpt), pcbnew.EDA_UNITS_MILLIMETRES, True)
    text = rpt.read_text()
    rpt.unlink()
    return text


# --------------------------------------------------------------------------
def generate(board: Board):
    outdir = HW / board.name
    outdir.mkdir(parents=True, exist_ok=True)
    write_project(board, outdir)
    order = ["A4", "A3", "A2", "A1"]
    for paper in order[order.index(board.paper):]:
        board.paper = paper
        try:
            sch = SchematicBuilder(board, outdir).build()
            break
        except ValueError as e:
            if "does not fit" not in str(e) or paper == order[-1]:
                raise
    netlist = export_netlist(sch)
    problems = verify(board, netlist)
    pcb = build_pcb(board, outdir, netlist, sch.name)
    return sch, pcb, netlist, problems
