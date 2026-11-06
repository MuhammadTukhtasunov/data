#!/usr/bin/env python3
"""Bootstrap the four drone KiCad projects (PDB, HAT, LGT, SNS).

Run with a Python that can import both `pcbnew` (KiCad 7) and `kiutils`:

    python3 hardware/tools/gen_kicad.py            # all boards
    python3 hardware/tools/gen_kicad.py pdb hat    # selected boards

Circuit intent comes from docs/electrical/README.md. Values written as "TBD"
must be calculated from the part datasheet before layout.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kigen import (C, C0603, C0805, C1206, C1210, CONN, CP, HOLE, HW, LED, R, R0603,  # noqa: E402
                   Board, generate, drc)

FP_XT60 = "Connector_AMASS:AMASS_XT60PW-M_1x02_P7.20mm_Horizontal"
FP_XT30 = "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal"
FP_MFIT2 = "Connector_Molex:Molex_Micro-Fit_3.0_43650-0210_1x02-1MP_P3.00mm_Horizontal"
FP_GH4 = "Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal"
FP_SH4 = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
FP_PH2 = "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal"
FP_XH4 = "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"
FP_SOIC14 = "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
FP_R2512 = "Resistor_SMD:R_2512_6332Metric"
FP_R1206 = "Resistor_SMD:R_1206_3216Metric"
FP_L12 = "Inductor_SMD:L_Bourns_SRP1245A"
FP_CP10 = "Capacitor_SMD:CP_Elec_10x10.5"
FP_CP8 = "Capacitor_SMD:CP_Elec_8x10.5"
FP_PTC = "Fuse:Fuse_1206_3216Metric"

TBD_NOTE = "Values marked TBD must be calculated from the part datasheet before layout"
GEN_NOTE = "Bootstrapped by hardware/tools/gen_kicad.py; edit in KiCad from here on"


# --------------------------------------------------------------------------
# Project symbol library (Teensy 4.1)
# --------------------------------------------------------------------------
TEENSY_LEFT = ["GND", "D0/RX1", "D1/TX1", "D2", "D3", "D4", "D5", "D6", "D7/RX2", "D8/TX2",
               "D9", "D10", "D11", "D12", "3V3", "D24/TX6", "D25/RX6", "D26", "D27",
               "D28/RX7", "D29/TX7", "D30", "D31", "D32"]          # DIP pins 1..24, top to bottom
TEENSY_RIGHT = ["D33", "D34/RX8", "D35/TX8", "D36", "D37", "D38", "D39", "D40", "D41", "GND",
                "D13/LED", "D14/TX3", "D15/RX3", "D16/RX4", "D17/TX4", "D18/SDA", "D19/SCL",
                "D20/TX5", "D21/RX5", "D22", "D23", "3V3", "GND", "VIN"]  # DIP pins 25..48, bottom to top


def write_project_symbols():
    def pin(num, name, etype, x, y, ang):
        return (f'      (pin {etype} line (at {x} {y} {ang}) (length 5.08)\n'
                f'        (name "{name}" (effects (font (size 1.27 1.27))))\n'
                f'        (number "{num}" (effects (font (size 1.27 1.27))))\n      )\n')

    def etype(num, name):
        if name == "GND" or name == "VIN":
            return "power_in"
        if name == "3V3":
            return "power_out" if num == 46 else "passive"
        return "bidirectional"

    pins = ""
    top = 29.21
    for i, name in enumerate(TEENSY_LEFT):
        n = i + 1
        pins += pin(n, name, etype(n, name), -20.32, round(top - 2.54 * i, 2), 0)
    for j, name in enumerate(TEENSY_RIGHT):
        n = 25 + j
        row = 23 - j
        pins += pin(n, name, etype(n, name), 20.32, round(top - 2.54 * row, 2), 180)
    text = f'''(kicad_symbol_lib (version 20220914) (generator gen_kicad)
  (symbol "Teensy_4.1" (in_bom yes) (on_board yes)
    (property "Reference" "U" (at -15.24 33.02 0)
      (effects (font (size 1.27 1.27)) (justify left))
    )
    (property "Value" "Teensy_4.1" (at 15.24 33.02 0)
      (effects (font (size 1.27 1.27)) (justify right))
    )
    (property "Footprint" "Package_DIP:DIP-48_W15.24mm_Socket" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "https://www.pjrc.com/store/teensy41.html" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "ki_description" "PJRC Teensy 4.1 on 2x24 0.1in sockets. Pin numbers follow DIP-48 numbering (1-24 down the left edge, 25-48 up the right edge, USB at the top). Verify against the PJRC pinout card." (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "ki_keywords" "teensy imxrt1062 mcu module" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (symbol "Teensy_4.1_0_1"
      (rectangle (start -15.24 31.75) (end 15.24 -31.75)
        (stroke (width 0.254) (type default))
        (fill (type background))
      )
      (text "USB" (at 0 29.21 0)
        (effects (font (size 1.27 1.27)))
      )
    )
    (symbol "Teensy_4.1_1_1"
{pins}    )
  )
)
'''
    path = HW / "lib" / "drone.kicad_sym"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def teensy_pin(name):
    names = {i + 1: n for i, n in enumerate(TEENSY_LEFT)}
    names.update({25 + j: n for j, n in enumerate(TEENSY_RIGHT)})
    hits = [num for num, n in names.items() if n == name or n.split("/")[0] == name]
    assert len(hits) == 1, (name, hits)
    return str(hits[0])


# --------------------------------------------------------------------------
# PDB
# --------------------------------------------------------------------------
def pdb() -> Board:
    b = Board("pdb", "PDB - Power Distribution Board", size=(100, 80), layers=4, paper="A2",
              comments=["Battery in; 19 V Jetson, 5 V aux, 5 V servo rails; current + voltage sense to FC",
                        TBD_NOTE, GEN_NOTE, "Rev A bootstrap"],
              flags=["PWR_VBAT", "GND", "PWR_5V_AUX", "VCC_19V"],
              zones=[("In1.Cu", "GND"), ("B.Cu", "GND")])
    b.notes = [
        "TBD values: calculate from the LM5176 and TPS54560B datasheets (Detailed Design sections) or TI WEBENCH before layout.",
        "FB dividers R25/R26 and R31/R32 assume a 0.8 V reference. Verify against the TPS54560B datasheet.",
        "AGND and PGND share the GND net. Join them under U2's thermal pad and keep each power loop compact.",
        "R1 is a 4-terminal shunt. Route ISNS_P / ISNS_N as a tight Kelvin pair from R1's sense pads to U1.",
        "Check J1/J2/J3 pad 1 = + against the AMASS drawing before ordering.",
        "Scale factors for the FC: FC_CURR_SNS = 25 mV/A (40 A/V), FC_VBAT_SNS = VBAT / 11.",
    ]

    k = b.block("Battery input & protection")
    CONN(k, "J1", "XT60PW-M BATT_IN", FP_XT60, ["VBAT_RAW", "GND"])
    k.add("D1", "Device:D_Zener_Small", "SMBJ28A", "Diode_SMD:D_SMB", {"1": "VBAT_RAW", "2": "GND"})
    CP(k, "C1", "470uF 50V", "VBAT_RAW", "GND", FP_CP10)
    CP(k, "C2", "470uF 50V", "VBAT_RAW", "GND", FP_CP10)
    C(k, "C3", "1uF 50V", "VBAT_RAW", "GND", C1206)

    k = b.block("Current & voltage sense")
    k.add("R1", "Device:R_Shunt", "0.25mR BVR", "Resistor_SMD:R_Shunt_Isabellenhuette_BVR4026",
          {"1": "VBAT_RAW", "2": "ISNS_P", "3": "ISNS_N", "4": "PWR_VBAT"})
    k.add("U1", "Amplifier_Current:INA240A3D", "INA240A3D", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
          {"8": "ISNS_P", "1": "ISNS_N", "6": "3V3_SNS", "2": "GND", "3": "GND", "7": "GND", "5": "CURR_RAW"})
    C(k, "C4", "100nF", "3V3_SNS", "GND")
    R(k, "R4", "100R", "CURR_RAW", "FC_CURR_SNS")
    C(k, "C5", "1nF", "FC_CURR_SNS", "GND")
    R(k, "R2", "100k 0.1%", "PWR_VBAT", "FC_VBAT_SNS")
    R(k, "R3", "10k 0.1%", "FC_VBAT_SNS", "GND")
    C(k, "C6", "100nF", "FC_VBAT_SNS", "GND")
    k.add("U5", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
          {"1": "PWR_5V_AUX", "3": "PWR_5V_AUX", "2": "GND", "5": "3V3_SNS"})
    C(k, "C7", "1uF", "PWR_5V_AUX", "GND")
    C(k, "C8", "1uF", "3V3_SNS", "GND")
    CONN(k, "J9", "FC_SNS JST-GH", FP_GH4, ["FC_CURR_SNS", "FC_VBAT_SNS", "GND", None])

    k = b.block("Battery outputs")
    CONN(k, "J2", "XT60PW-M ESC_OUT", FP_XT60, ["PWR_VBAT", "GND"])
    k.add("F1", "Device:Fuse_Small", "3A >=32V", "Fuse:Fuse_1206_3216Metric",
          {"1": "PWR_VBAT", "2": "PWR_VBAT_LGT"})
    CONN(k, "J3", "XT30PW-M LGT_PWR", FP_XT30, ["PWR_VBAT_LGT", "GND"])

    k = b.block("19 V Jetson rail - LM5176 control")
    k.add("U2", "Regulator_Switching:LM5176PWP", "LM5176PWP", "Package_SO:HTSSOP-28-1EP_4.4x9.7mm_P0.65mm_EP3.4x9.5mm_ThermalVias",
          {"1": "EN_19V", "2": "PWR_VBAT", "3": "PWR_VBAT", "4": "MODE_19V", "5": "GND", "6": "RT_19V",
           "7": "SLOPE_19V", "8": "SS_19V", "9": "COMP_19V", "10": "GND", "11": "FB_19V",
           "12": "PWR_19V_JET", "13": "PWR_19V_JET", "14": "VOUT_PRE_19V", "15": "GND",
           "16": "LS_SRC_19V", "17": "PG_19V", "18": "SW2_19V", "19": "HO2_19V", "20": "BOOT2_19V",
           "21": "LO2_19V", "22": "GND", "23": "VCC_19V", "24": "PWR_VBAT", "25": "LO1_19V",
           "26": "BOOT1_19V", "27": "HO1_19V", "28": "SW1_19V", "29": "GND"})
    R(k, "R10", "TBD", "PWR_VBAT", "EN_19V")
    R(k, "R11", "TBD", "EN_19V", "GND")
    R(k, "R12", "TBD", "MODE_19V", "GND")
    R(k, "R13", "TBD", "RT_19V", "GND")
    C(k, "C10", "TBD", "SLOPE_19V", "GND")
    C(k, "C11", "TBD", "SS_19V", "GND")
    R(k, "R14", "TBD", "COMP_19V", "COMP_RC_19V")
    C(k, "C12", "TBD", "COMP_RC_19V", "GND")
    C(k, "C13", "TBD", "COMP_19V", "GND")
    R(k, "R15", "TBD", "PWR_19V_JET", "FB_19V")
    R(k, "R16", "TBD", "FB_19V", "GND")
    R(k, "R19", "100k", "VCC_19V", "PG_19V")
    C(k, "C14", "100nF 50V", "BOOT1_19V", "SW1_19V")
    C(k, "C15", "100nF 50V", "BOOT2_19V", "SW2_19V")
    C(k, "C16", "4.7uF 16V", "VCC_19V", "GND", C0805)
    C(k, "C17", "100nF 50V", "PWR_VBAT", "GND")

    k = b.block("19 V Jetson rail - power stage")
    fet = "Transistor_FET:CSD18540Q5B"
    fpq = "Package_TO_SOT_SMD:TDSON-8-1"
    k.add("Q1", fet, "CSD18540Q5B", fpq, {"4": "HO1_19V", "5": "PWR_VBAT", "1": "SW1_19V"})
    k.add("Q2", fet, "CSD18540Q5B", fpq, {"4": "LO1_19V", "5": "SW1_19V", "1": "LS_SRC_19V"})
    k.add("Q3", fet, "CSD18540Q5B", fpq, {"4": "LO2_19V", "5": "SW2_19V", "1": "LS_SRC_19V"})
    k.add("Q4", fet, "CSD18540Q5B", fpq, {"4": "HO2_19V", "5": "VOUT_PRE_19V", "1": "SW2_19V"})
    k.add("L1", "Device:L", "6.8uH >=10A TBD", FP_L12, {"1": "SW1_19V", "2": "SW2_19V"})
    R(k, "R17", "5mR TBD", "LS_SRC_19V", "GND", FP_R2512)
    R(k, "R18", "TBD (0R if unused)", "VOUT_PRE_19V", "PWR_19V_JET", FP_R2512)
    C(k, "C18", "10uF 50V", "PWR_VBAT", "GND", C1210)
    C(k, "C19", "10uF 50V", "PWR_VBAT", "GND", C1210)
    C(k, "C20", "22uF 35V", "PWR_19V_JET", "GND", C1210)
    C(k, "C21", "22uF 35V", "PWR_19V_JET", "GND", C1210)
    CP(k, "C22", "100uF 35V", "PWR_19V_JET", "GND", FP_CP8)
    CONN(k, "J4", "JET_PWR Micro-Fit", FP_MFIT2, ["PWR_19V_JET", "GND"])
    R(k, "R20", "10k", "PWR_19V_JET", "LED_19V_A")
    LED(k, "D2", "green", "LED_19V_A", "GND")

    for tag, rail, refs in (("5VA", "PWR_5V_AUX", dict(u="U3", r=21, c=23, d=3, l="L2", led=4, j=["J5", "J6", "J7"])),
                            ("5VS", "PWR_5V_SERVO", dict(u="U4", r=28, c=31, d=5, l="L3", led=6, j=["J8"]))):
        title = "5 V aux rail - TPS54560B" if tag == "5VA" else "5 V servo rail - TPS54560B"
        k = b.block(title)
        r, c = refs["r"], refs["c"]
        k.add(refs["u"], "Regulator_Switching:TPS54560BDDA", "TPS54560BDDA",
              "Package_SO:Texas_R-PDSO-G8_EP2.95x4.9mm_Mask2.4x3.1mm_ThermalVias",
              {"1": f"BOOT_{tag}", "2": "PWR_VBAT", "3": f"EN_{tag}", "4": f"RT_{tag}",
               "5": f"FB_{tag}", "6": f"COMP_{tag}", "7": "GND", "8": f"SW_{tag}"})
        R(k, f"R{r}", "TBD", "PWR_VBAT", f"EN_{tag}")
        R(k, f"R{r + 1}", "TBD", f"EN_{tag}", "GND")
        R(k, f"R{r + 2}", "TBD", f"RT_{tag}", "GND")
        R(k, f"R{r + 3}", "TBD", f"COMP_{tag}", f"COMP_RC_{tag}")
        C(k, f"C{c}", "TBD", f"COMP_RC_{tag}", "GND")
        C(k, f"C{c + 1}", "TBD", f"COMP_{tag}", "GND")
        R(k, f"R{r + 4}", "52.3k", rail, f"FB_{tag}")
        R(k, f"R{r + 5}", "10k", f"FB_{tag}", "GND")
        C(k, f"C{c + 2}", "100nF 16V", f"BOOT_{tag}", f"SW_{tag}")
        k.add(f"D{refs['d']}", "Device:D_Schottky_Small", "B560C", "Diode_SMD:D_SMC",
              {"1": f"SW_{tag}", "2": "GND"})
        k.add(refs["l"], "Device:L", "10uH >=7A TBD", FP_L12, {"1": f"SW_{tag}", "2": rail})
        C(k, f"C{c + 3}", "10uF 50V", "PWR_VBAT", "GND", C1210)
        C(k, f"C{c + 4}", "47uF 10V", rail, "GND", C1210)
        C(k, f"C{c + 5}", "47uF 10V", rail, "GND", C1210)
        names = {"J5": "HAT_5V", "J6": "SNS_5V", "J7": "USBHUB_5V", "J8": "SERVO_5V"}
        for j in refs["j"]:
            CONN(k, j, f"{names[j]} Micro-Fit", FP_MFIT2, [rail, "GND"])
        R(k, f"R{r + 6}", "1k", rail, f"LED_{tag}_A")
        LED(k, f"D{refs['led']}", "green", f"LED_{tag}_A", "GND")

    k = b.block("Mechanical", cols=4)
    for i in range(1, 5):
        HOLE(k, f"H{i}", "M3")
    return b


# --------------------------------------------------------------------------
# HAT
# --------------------------------------------------------------------------
def hat() -> Board:
    b = Board("hat", "HAT - Jetson I/O HAT", size=(65, 56.5), layers=2, paper="A3", holes="M2.5",
              comments=["Jetson 40-pin header: I2S amp, buffered PWM (3.3 V to 5 V), safe-at-boot enable",
                        "Enable PWM and I2S pins with jetson-io.py before use", GEN_NOTE, "Rev A bootstrap"],
              flags=["PWR_5V_AUX", "GND"], zones=[("B.Cu", "GND")],
              # Raspberry-Pi-HAT style: header centred along the top edge, holes 3.5 mm in
              fixed={"J1": (90, 32.5, 3.5)}, hole_inset=3.5, pack_margin=(2.0, 8.5, 2.0, 7.0))
    b.notes = [
        "Header pins 2 and 4 (Jetson 5 V) are intentionally unconnected: the HAT runs from PWR_5V_AUX on J2.",
        "R1 sets the MAX98357A SD_MODE level with the amp's internal pull-down; 634k from 3.3 V targets (L+R)/2. Verify against the SD_MODE table.",
        "U2 uses the 74LVC125 symbol (same pinout); fit a 74AHCT125 so 3.3 V inputs give 5 V outputs.",
        "OUT_EN low (boot/reset): Q1 off, OUT_EN_N high, U2 outputs Hi-Z and pulled low. Lights off, no servo pulses.",
        "R17/R18 I2C pull-ups are DNP. Fit only if the carrier has none on pins 3/5.",
    ]
    k = b.block("Jetson 40-pin header", cols=1)
    hdr = {"1": "3V3_JET", "17": "3V3_JET", "3": "I2C_SDA", "5": "I2C_SCL", "7": "SPARE_3V3",
           "8": "FC_UART_TX_J", "10": "FC_UART_RX_J", "12": "I2S_BCLK", "15": "PWM_GIMBAL_3V3",
           "29": "AMP_SD", "31": "OUT_EN", "32": "PWM_FLASH_3V3", "33": "PWM_IR_3V3",
           "35": "I2S_LRCLK", "40": "I2S_DOUT"}
    for g in ("6", "9", "14", "20", "25", "30", "34", "39"):
        hdr[g] = "GND"
    k.add("J1", "Connector_Generic:Conn_02x20_Odd_Even", "Jetson 40-pin",
          "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical", hdr)

    k = b.block("Power inputs", cols=3)
    CONN(k, "J2", "5V_AUX_IN Micro-Fit", FP_MFIT2, ["PWR_5V_AUX", "GND"])
    CONN(k, "J3", "5V_SERVO_IN Micro-Fit", FP_MFIT2, ["PWR_5V_SERVO", "GND"])
    CP(k, "C5", "220uF 10V", "PWR_5V_SERVO", "GND", FP_CP8)

    k = b.block("I2S speaker amplifier", cols=5)
    k.add("U1", "Audio:MAX98357A", "MAX98357A", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm",
          {"1": "I2S_DOUT", "16": "I2S_BCLK", "14": "I2S_LRCLK", "4": "SD_MODE_AMP", "7": "PWR_5V_AUX",
           "3": "GND", "17": "GND", "9": "SPK_P", "10": "SPK_N"})
    R(k, "R1", "634k", "AMP_SD", "SD_MODE_AMP")
    C(k, "C1", "10uF 10V", "PWR_5V_AUX", "GND", C0805)
    C(k, "C2", "100nF", "PWR_5V_AUX", "GND")
    CONN(k, "J4", "SPEAKER JST-PH", FP_PH2, ["SPK_P", "SPK_N"])

    k = b.block("PWM buffer & enable", cols=6)
    ins = [("PWM_GIMBAL", "1", "2", "3"), ("PWM_FLASH", "4", "5", "6"), ("PWM_IR", "10", "9", "8"), ("SPARE", "13", "12", "11")]
    for unit, (sig, oe, a, y) in enumerate(ins, start=1):
        k.add("U2", "74xx:74LVC125", "74AHCT125", FP_SOIC14,
              {oe: "OUT_EN_N", a: f"{sig}_3V3", y: f"{sig}_BUF"}, unit=unit)
    k.add("U2", "74xx:74LVC125", "74AHCT125", FP_SOIC14, {"14": "PWR_5V_AUX", "7": "GND"}, unit=5)
    C(k, "C3", "100nF", "PWR_5V_AUX", "GND")
    outs = {"PWM_GIMBAL": "PWM_GIMBAL", "PWM_FLASH": "PWM_FLASH", "PWM_IR": "PWM_IR", "SPARE": "SPARE_OUT"}
    for i, (sig, *_rest) in enumerate(ins):
        R(k, f"R{3 + i}", "100k", f"{sig}_3V3", "GND")
        R(k, f"R{7 + i}", "100R", f"{sig}_BUF", outs[sig])
        R(k, f"R{11 + i}", "10k", outs[sig], "GND")
    k.add("Q1", "Transistor_FET:2N7002", "2N7002", "Package_TO_SOT_SMD:SOT-23",
          {"1": "OUT_EN", "2": "GND", "3": "OUT_EN_N"})
    R(k, "R15", "100k", "OUT_EN", "GND")
    R(k, "R16", "10k", "PWR_5V_AUX", "OUT_EN_N")

    k = b.block("Output connectors", cols=4)
    CONN(k, "J5", "GIMBAL servo", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
         ["GND", "PWR_5V_SERVO", "PWM_GIMBAL"])
    CONN(k, "J6", "LIGHT_CTRL JST-GH", FP_GH4, ["PWM_FLASH", "PWM_IR", "SPARE_OUT", "GND"])
    CONN(k, "J7", "I2C Qwiic JST-SH", FP_SH4, ["GND", "3V3_JET", "I2C_SDA", "I2C_SCL"])
    R(k, "R17", "4.7k", "I2C_SDA", "3V3_JET", dnp=True)
    R(k, "R18", "4.7k", "I2C_SCL", "3V3_JET", dnp=True)
    CONN(k, "J8", "FC_UART JST-GH", FP_GH4, [None, "FC_UART_TX", "FC_UART_RX", "GND"])
    R(k, "R19", "100R", "FC_UART_TX_J", "FC_UART_TX")
    R(k, "R20", "100R", "FC_UART_RX", "FC_UART_RX_J")

    k = b.block("Mechanical", cols=4)
    for i in range(1, 5):
        HOLE(k, f"H{i}", "M2.5")
    return b


# --------------------------------------------------------------------------
# LGT
# --------------------------------------------------------------------------
def lgt() -> Board:
    b = Board("lgt", "LGT - Lighting Driver Board", size=(70, 50), layers=2, paper="A3",
              comments=["Two AL8860 constant-current LED drivers: flashlight (CH1) and IR (CH2)",
                        "PWM dimming via CTRL; NTC on the emitter heatsink derates current", GEN_NOTE,
                        "Rev A bootstrap"],
              flags=["PWR_VBAT_LGT", "GND"], zones=[("B.Cu", "GND")])
    b.notes = [
        "LED current = 0.1 V / R_SENSE (R5, R11): 0.068R is about 1.5 A. Set to the emitter's rating and verify the AL8860 sense voltage.",
        "CTRL network: R3/R9 4.7k from the PWM input, R4/R10 100k to GND, NTC (10k B3950) from CTRL to GND at the emitter. Hot NTC pulls CTRL down and reduces current.",
        "Check the AL8860 CTRL voltage range and internal pull-up, then adjust R3/R4 (R9/R10).",
        "C2/C6 (DNP) turn high-frequency PWM into smooth analog dimming when fitted.",
        "On 4S packs the LED string's forward voltage must stay below about 11 V.",
    ]
    k = b.block("Power input", cols=4)
    CONN(k, "J1", "XT30PW-M LGT_PWR", FP_XT30, ["PWR_VBAT_LGT", "GND"])
    k.add("D1", "Device:D_Zener_Small", "SMBJ28A", "Diode_SMD:D_SMB", {"1": "PWR_VBAT_LGT", "2": "GND"})
    CP(k, "C1", "47uF 50V", "PWR_VBAT_LGT", "GND", FP_CP8)

    k = b.block("Control input", cols=3)
    CONN(k, "J2", "LIGHT_CTRL JST-GH", FP_GH4, ["PWM_FLASH", "PWM_IR", "SPARE_OUT", "GND"])
    k.add("TP1", "Connector:TestPoint", "SPARE_OUT", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "SPARE_OUT"})

    for ch, (sig, led, ntc, sw, u, base, d0, l, j) in enumerate(
            [("PWM_FLASH", "LED_FLASH", "NTC_FLASH", "SW_FLASH", "U1", 1, 2, "L1", "J3"),
             ("PWM_IR", "LED_IR", "NTC_IR", "SW_IR", "U2", 7, 4, "L2", "J4")], start=1):
        name = "Flashlight channel (CH1)" if ch == 1 else "IR channel (CH2)"
        k = b.block(name, cols=7)
        r = base
        c = 2 if ch == 1 else 6
        R(k, f"R{r}", "100R", sig, f"{sig}_IN")
        R(k, f"R{r + 1}", "10k", f"{sig}_IN", "GND")
        k.add(f"D{d0}", "Device:D_TVS", "PESD5V0S1BB", "Diode_SMD:D_SOD-323", {"1": f"{sig}_IN", "2": "GND"})
        R(k, f"R{r + 2}", "4.7k", f"{sig}_IN", ntc)
        R(k, f"R{r + 3}", "100k", ntc, "GND")
        C(k, f"C{c}", "10nF", ntc, "GND", dnp=True)
        k.add(u, "Driver_LED:AL8860MP", "AL8860MP", "Package_SO:MSOP-8-1EP_3x3mm_P0.65mm_EP1.5x1.8mm",
              {"8": "PWR_VBAT_LGT", "1": f"{led}_P", "4": ntc, "5": sw, "2": "GND"})
        R(k, f"R{r + 4}", "0.068R 1%", "PWR_VBAT_LGT", f"{led}_P", FP_R1206)
        C(k, f"C{c + 1}", "10uF 50V", "PWR_VBAT_LGT", "GND", C1210)
        C(k, f"C{c + 2}", "100nF 50V", "PWR_VBAT_LGT", "GND")
        k.add(l, "Device:L", "47uH >=2A TBD", "Inductor_SMD:L_12x12mm_H6mm", {"1": f"{led}_N", "2": sw})
        k.add(f"D{d0 + 1}", "Device:D_Schottky_Small", "B360A", "Diode_SMD:D_SMA",
              {"1": "PWR_VBAT_LGT", "2": sw})
        CONN(k, j, f"{led}_LED JST-XH", FP_XH4, [f"{led}_P", f"{led}_N", ntc, "GND"])

    k = b.block("Mechanical", cols=4)
    for i in range(1, 5):
        HOLE(k, f"H{i}", "M3")
    return b


# --------------------------------------------------------------------------
# SNS
# --------------------------------------------------------------------------
def sns() -> Board:
    b = Board("sns", "SNS - Sensor Hub", size=(90, 60), layers=2, paper="A2",
              comments=["Teensy 4.1 carrier: 8 fused UART sensor ports with 5 V-tolerant RX buffers",
                        "Cut the Teensy VUSB-VIN trace; VIN is fed from J1", GEN_NOTE, "Rev A bootstrap"],
              flags=["PWR_5V_AUX", "GND"], zones=[("B.Cu", "GND")])
    b.notes = [
        "Teensy pins use DIP-48 numbering (1-24 down the left, 25-48 up the right, USB at top). Verify against the PJRC Teensy 4.1 pinout card.",
        "Cut the VUSB-VIN trace on the Teensy so the Jetson's USB 5 V and PWR_5V_AUX never connect.",
        "U2/U3 use 74LVC125A at 3.3 V: inputs accept 5 V, so each RX line is safe for 3.3 V or 5 V sensors.",
        "Trigger/echo sensors use the same ports: TXn becomes TRIG, RXn becomes ECHO.",
        "R41/R42 I2C pull-ups on J10 are DNP.",
    ]
    tx = {1: "D1", 2: "D8", 3: "D14", 4: "D17", 5: "D20", 6: "D24", 7: "D29", 8: "D35"}
    rx = {1: "D0", 2: "D7", 3: "D15", 4: "D16", 5: "D21", 6: "D25", 7: "D28", 8: "D34"}

    k = b.block("Power input", cols=3)
    CONN(k, "J1", "5V_IN Micro-Fit", FP_MFIT2, ["PWR_5V_AUX", "GND"])
    CP(k, "C1", "100uF 10V", "PWR_5V_AUX", "GND", FP_CP8)
    C(k, "C2", "10uF 10V", "PWR_5V_AUX", "GND", C0805)

    k = b.block("Teensy 4.1", cols=1)
    tp = {teensy_pin("VIN"): "PWR_5V_AUX", "1": "GND", "34": "GND", "47": "GND",
          "15": "3V3_T", "46": "3V3_T",
          teensy_pin("D18"): "SNS_SDA", teensy_pin("D19"): "SNS_SCL",
          teensy_pin("D2"): "GPIO2", teensy_pin("D3"): "GPIO3"}
    for n in range(1, 9):
        tp[teensy_pin(tx[n])] = f"TX{n}"
        tp[teensy_pin(rx[n])] = f"RX{n}_B"
    k.add("U1", "drone:Teensy_4.1", "Teensy_4.1", "Package_DIP:DIP-48_W15.24mm_Socket", tp)

    k = b.block("RX level buffers (5 V-tolerant)", cols=5)
    chans = [("1", "2", "3"), ("4", "5", "6"), ("10", "9", "8"), ("13", "12", "11")]
    for ui, u in enumerate(("U2", "U3")):
        for unit, (oe, a, y) in enumerate(chans, start=1):
            n = ui * 4 + unit
            k.add(u, "74xx:74LVC125", "74LVC125A", FP_SOIC14,
                  {oe: "GND", a: f"SENS{n}_RX", y: f"RX{n}_B"}, unit=unit)
        k.add(u, "74xx:74LVC125", "74LVC125A", FP_SOIC14, {"14": "3V3_T", "7": "GND"}, unit=5)
    C(k, "C3", "100nF", "3V3_T", "GND")
    C(k, "C4", "100nF", "3V3_T", "GND")

    for half in (0, 1):
        title = "Sensor ports 1-4 (rangefinders)" if half == 0 else "Sensor ports 5-8 (echo sensors)"
        k = b.block(title, cols=8)
        for n in range(1 + 4 * half, 5 + 4 * half):
            k.add(f"F{n}", "Device:Polyfuse_Small", "300mA hold", FP_PTC, {"1": "PWR_5V_AUX", "2": f"SENS{n}_5V"})
            R(k, f"R{n}", "220R", f"TX{n}", f"SENS{n}_TX")
            R(k, f"R{8 + n}", "47k", f"SENS{n}_RX", "3V3_T")
            label = f"RANGE{n}" if n <= 4 else f"ECHO{n - 4}"
            CONN(k, f"J{n + 1}", f"{label} JST-GH", FP_GH4, [f"SENS{n}_5V", f"SENS{n}_TX", f"SENS{n}_RX", "GND"])

    k = b.block("Expansion", cols=3)
    CONN(k, "J10", "EXP", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
         ["3V3_T", "GND", "SNS_SDA", "SNS_SCL", "GPIO2", "GPIO3"])
    R(k, "R41", "4.7k", "SNS_SDA", "3V3_T", dnp=True)
    R(k, "R42", "4.7k", "SNS_SCL", "3V3_T", dnp=True)

    k = b.block("Mechanical", cols=4)
    for i in range(1, 5):
        HOLE(k, f"H{i}", "M3")
    return b


BOARDS = {"pdb": pdb, "hat": hat, "lgt": lgt, "sns": sns}

if __name__ == "__main__":
    write_project_symbols()
    names = sys.argv[1:] or list(BOARDS)
    failed = False
    for name in names:
        board = BOARDS[name]()
        sch, pcb, netlist, problems = generate(board)
        n_parts = len([r for r in netlist["components"] if not r.startswith("#")])
        print(f"[{name}] {n_parts} parts, {len(netlist['nets'])} nets -> {sch.name}, {pcb.name}")
        if problems:
            failed = True
            for p in problems:
                print(f"  ! {p}")
        report = drc(pcb)
        print("  DRC summary:", " | ".join(l.strip() for l in report.splitlines() if l.startswith("**")))
    sys.exit(1 if failed else 0)
