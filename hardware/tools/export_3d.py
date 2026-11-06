#!/usr/bin/env python3
"""Export each board to VRML (board + component models) for 3D previews.

KiCad 7's 3D library lacks models for a few footprints used here, so this script
swaps in a close stand-in model, or a simple coloured box sized from the
footprint, *in memory only*. The .kicad_pcb files are not changed.

    python3 hardware/tools/export_3d.py <kicad 3dmodels dir> <output dir>
"""
import os
import sys
from pathlib import Path

MODELS = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
os.environ["KICAD6_3DMODEL_DIR"] = str(MODELS)
os.environ["KICAD7_3DMODEL_DIR"] = str(MODELS)
os.environ.setdefault("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
import pcbnew  # noqa: E402

HW = Path(__file__).resolve().parent.parent
FPDIR = Path("/usr/share/kicad/footprints")

# footprint model -> stand-in model with the same body
STAND_IN = {
    "TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm.wrl": "Package_DFN_QFN.3dshapes/TQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.wrl",
    "MSOP-8-1EP_3x3mm_P0.65mm_EP1.5x1.8mm.wrl": "Package_SO.3dshapes/MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm.wrl",
    "Texas_R-PDSO-G8_EP2.95x4.9mm_Mask2.4x3.1mm.wrl": "Package_SO.3dshapes/HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm.wrl",
    "L_Bourns_SRP1245A.wrl": "Inductor_SMD.3dshapes/L_Bourns_SRR1260.wrl",
    "L_12x12mm_H6mm.wrl": "Inductor_SMD.3dshapes/L_Bourns_SRR1260.wrl",
}
# footprint model -> (height mm, rgb) for a box sized from the footprint outline
BOX = {
    "AMASS_XT60PW-M_1x02_P7.20mm_Horizontal.wrl": (8.3, (0.93, 0.76, 0.12)),
    "AMASS_XT30PW-M_1x02_P2.50mm_Horizontal.wrl": (5.5, (0.93, 0.76, 0.12)),
    "Molex_Micro-Fit_3.0_43650-0210_1x02-1MP_P3.00mm_Horizontal.wrl": (9.9, (0.12, 0.12, 0.13)),
    "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal.wrl": (2.9, (0.92, 0.90, 0.84)),
    "R_Shunt_Isabellenhuette_BVR4026.wrl": (2.6, (0.78, 0.78, 0.80)),
}


def box_wrl(path: Path, x1, y1, x2, y2, h, rgb):
    """Box in KiCad's WRL convention (1 unit = 0.1 inch, Y up)."""
    s = 1 / 2.54
    X1, X2, Y1, Y2, Z = x1 * s, x2 * s, -y2 * s, -y1 * s, h * s
    pts = [(X1, Y1, 0), (X2, Y1, 0), (X2, Y2, 0), (X1, Y2, 0), (X1, Y1, Z), (X2, Y1, Z), (X2, Y2, Z), (X1, Y2, Z)]
    faces = "0,3,2,1,-1,4,5,6,7,-1,0,1,5,4,-1,1,2,6,5,-1,2,3,7,6,-1,3,0,4,7,-1"
    path.write_text(f"""#VRML V2.0 utf8
Shape {{
  appearance Appearance {{ material Material {{ diffuseColor {rgb[0]} {rgb[1]} {rgb[2]} specularColor 0.3 0.3 0.3 shininess 0.4 }} }}
  geometry IndexedFaceSet {{
    coord Coordinate {{ point [ {", ".join(f"{a:.4f} {b:.4f} {c:.4f}" for a, b, c in pts)} ] }}
    coordIndex [ {faces} ]
  }}
}}
""")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    boxdir = OUT / "boxes"
    boxdir.mkdir(exist_ok=True)
    for name in ("pdb", "hat", "lgt", "sns"):
        brd = pcbnew.LoadBoard(str(HW / name / f"{name}.kicad_pcb"))
        for fp in brd.GetFootprints():
            # fp.Models() hands back copies in the Python binding: rebuild the list instead
            models = list(fp.Models())
            if not any(Path(m.m_Filename).name in STAND_IN or Path(m.m_Filename).name in BOX for m in models):
                continue
            fp.Models().clear()
            for m in models:
                base = Path(m.m_Filename).name
                nm = pcbnew.FP_3DMODEL()
                nm.m_Filename, nm.m_Offset, nm.m_Rotation, nm.m_Scale = m.m_Filename, m.m_Offset, m.m_Rotation, m.m_Scale
                nm.m_Show, nm.m_Opacity = True, 1.0
                if base in STAND_IN:
                    nm.m_Filename = str(MODELS / STAND_IN[base])
                elif base in BOX:
                    h, rgb = BOX[base]
                    lib, fpname = fp.GetFPIDAsString().split(":", 1)
                    ref_fp = pcbnew.FootprintLoad(str(FPDIR / f"{lib}.pretty"), fpname)
                    bb = ref_fp.GetBoundingBox(False, False)
                    tgt = boxdir / base
                    box_wrl(tgt, pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                            pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()), h, rgb)
                    nm.m_Filename = str(tgt)
                    nm.m_Offset = pcbnew.VECTOR3D(0, 0, 0)
                    nm.m_Rotation = pcbnew.VECTOR3D(0, 0, 0)
                    nm.m_Scale = pcbnew.VECTOR3D(1, 1, 1)
                fp.Add3DModel(nm)
        out = OUT / f"{name}.wrl"
        ok = pcbnew.EXPORTER_VRML(brd).ExportVRML_File(brd.GetProject(), "", str(out), 1.0,
                                                        False, False, "", 0.0, 0.0)
        print(name, "ok" if ok else "FAILED", out.stat().st_size if out.exists() else 0)


if __name__ == "__main__":
    main()
