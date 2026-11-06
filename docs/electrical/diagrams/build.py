#!/usr/bin/env python3
"""Generate the Mermaid sources for the electrical design diagrams.

Edges are declared through Diagram.edge() so link indices (needed for
Mermaid `linkStyle` colouring by signal class) are always correct.

Usage:
    python3 build.py              # writes *.mmd next to this script
Render (needs @mermaid-js/mermaid-cli):
    for f in *.mmd; do npx -p @mermaid-js/mermaid-cli mmdc -i "$f" -o "${f%.mmd}.png" -b white -s 2; done
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

INIT = (
    '%%{init: {"theme": "base", "fontFamily": "Inter, Arial, Helvetica, sans-serif", '
    '"themeVariables": {"fontFamily": "Inter, Arial, Helvetica, sans-serif", "fontSize": "14px", '
    '"primaryColor": "#ffffff", "primaryBorderColor": "#5b6b7c", "primaryTextColor": "#1d2733", '
    '"lineColor": "#5b6b7c", "clusterBkg": "#f6f8fb", "clusterBorder": "#c3ccd6", '
    '"edgeLabelBackground": "#ffffff"}, '
    '"flowchart": {"curve": "basis", "nodeSpacing": 30, "rankSpacing": 70, "padding": 12}} }%%'
)

# Signal classes -> line style. Keep in sync with the legend in README.md.
KINDS = {
    "power":  "stroke:#d62728,stroke-width:3px",
    "usb":    "stroke:#1f77b4,stroke-width:2px",
    "uart":   "stroke:#2ca02c,stroke-width:2px",
    "i2s":    "stroke:#ff7f0e,stroke-width:2px",
    "pwm":    "stroke:#9467bd,stroke-width:2px",
    "i2c":    "stroke:#b8860b,stroke-width:2px",
    "analog": "stroke:#8c564b,stroke-width:2px",
    "video":  "stroke:#e377c2,stroke-width:2px",
    "csi":    "stroke:#17becf,stroke-width:2px",
    "gpio":   "stroke:#555555,stroke-width:2px,stroke-dasharray:5 4",
    "bundle": "stroke:#333333,stroke-width:4px",
}
CLASSDEFS = """
    classDef cots fill:#eef1f5,stroke:#8a97a6,color:#1d2733
    classDef custom fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#0b2a6b
    classDef core fill:#1f3b57,stroke:#0f2233,color:#ffffff
    classDef ic fill:#ffffff,stroke:#334155,stroke-width:1.5px,color:#0f172a
    classDef conn fill:#fff8e1,stroke:#b7950b,color:#4a3b00
    classDef hdr fill:#ede9fe,stroke:#6d28d9,color:#2e1065
    classDef passive fill:#f8fafc,stroke:#94a3b8,stroke-dasharray:4 3,color:#334155
    classDef ext fill:#eef1f5,stroke:#8a97a6,stroke-dasharray:4 3,color:#475569
"""


class Diagram:
    def __init__(self, name, direction="LR"):
        self.name = name
        self.lines = [INIT, f"flowchart {direction}"]
        self.edges = []  # (text, kind)

    def raw(self, text):
        self.lines.append(text.rstrip("\n"))

    def edge(self, a, b, label=None, kind=None, arrow="-->"):
        lab = f'|"{label}"|' if label else ""
        self.edges.append((f"    {a} {arrow}{lab} {b}", kind))

    def render(self):
        out = list(self.lines)
        by_kind = {}
        idx = 0
        for text, kind in self.edges:
            if text is not None:
                out.append(text)
            if kind:
                by_kind.setdefault(kind, []).append(idx)
            idx += 1
        out.append(CLASSDEFS.rstrip())
        for kind, ids in by_kind.items():
            out.append(f"    linkStyle {','.join(map(str, ids))} {KINDS[kind]}")
        return "\n".join(out) + "\n"

    def write(self):
        (HERE / f"{self.name}.mmd").write_text(self.render())


# --------------------------------------------------------------------------
# 1a. System signal interconnect (data / control only)
# --------------------------------------------------------------------------
def system_signals():
    d = Diagram("system-signals", "LR")
    d.raw('''
    RF["4× Rangefinders"]:::cots
    ECHO["4× Echo sensors"]:::cots
    LIDAR["Lidar"]:::cots
    MIC["USB microphone"]:::cots
    HEAT["Thermal camera"]:::cots
    RGB["RGB / Night camera"]:::cots
    SNS["<b>SNS</b><br/>Sensor Hub · Teensy 4.1"]:::custom
    LBRD["Lidar USB board"]:::cots
    USBH["Powered USB hub<br/>(off-the-shelf)"]:::cots
    JET["<b>Jetson Orin Nano</b><br/>Dev Kit"]:::core
    LTE["4G LTE modem"]:::cots
    HAT["<b>HAT</b><br/>Jetson I/O HAT"]:::custom
    SPK["Speaker 4–8 Ω"]:::cots
    GIM["Gimbal servo"]:::cots
    LGT["<b>LGT</b><br/>Lighting Driver Board"]:::custom
    FLASH["Flashlight LED"]:::cots
    IRL["IR LED 850 nm"]:::cots
    FC["<b>Flight Controller</b>"]:::core
    RCAM["Radio camera"]:::cots
    GPS["GPS + compass"]:::cots
    RTR["Radio transmission<br/>receiver"]:::cots
    VTX["Radio VTX"]:::cots
    ESC["4-in-1 ESC"]:::cots
    PDB["<b>PDB</b><br/>Power Distribution Board"]:::custom''')
    e = d.edge
    e("RF", "SNS", "UART ×4", "uart", "<-->")
    e("ECHO", "SNS", "UART ×4", "uart", "<-->")
    e("LIDAR", "LBRD", "UART", "uart", "<-->")
    e("SNS", "USBH", "USB", "usb", "<-->")
    e("LBRD", "USBH", "USB", "usb", "<-->")
    e("MIC", "USBH", "USB", "usb", "<-->")
    e("USBH", "JET", "USB", "usb", "<-->")
    e("HEAT", "JET", "USB-C", "usb", "<-->")
    e("RGB", "JET", "CSI-2 · 22-pin FPC", "csi")
    e("JET", "LTE", "USB", "usb", "<-->")
    e("JET", "HAT", "40-pin header<br/>I2S · PWM ×3 · GPIO · I2C · UART", "bundle", "<-->")
    e("HAT", "SPK", "SPK± (BTL)", "power")
    e("HAT", "GIM", "PWM 50 Hz · 5 V", "pwm")
    e("HAT", "LGT", "PWM_FLASH · PWM_IR", "pwm")
    e("LGT", "FLASH", "constant current", "power")
    e("LGT", "IRL", "constant current", "power")
    e("JET", "FC", "USB · MAVLink", "usb", "<-->")
    e("HAT", "FC", "UART (optional backup)", "uart", "-.->")
    e("RCAM", "FC", "CVBS", "video")
    e("GPS", "FC", "UART + I2C", "uart")
    e("RTR", "FC", "UART · CRSF", "uart", "<-->")
    e("PDB", "FC", "CURR_SNS · VBAT_SNS", "analog")
    e("FC", "ESC", "DShot ×4", "pwm")
    e("FC", "VTX", "CVBS + OSD", "video")
    d.write()


# --------------------------------------------------------------------------
# 1b. System power distribution
# --------------------------------------------------------------------------
def system_power():
    d = Diagram("system-power", "LR")
    d.raw('''
    BATT["Battery<br/>6S LiPo · 18–25.2 V"]:::cots
    PDB["<b>PDB</b><br/>Power Distribution Board"]:::custom
    ESC["4-in-1 ESC<br/>(+ FC / VTX via ESC BEC)"]:::cots
    MOT["4× Motors"]:::cots
    JET["<b>Jetson Orin Nano</b><br/>≤ 25 W"]:::core
    LGT["<b>LGT</b><br/>Lighting Driver Board"]:::custom
    FLASH["Flashlight LED ≈ 10 W"]:::cots
    IRL["IR LED ≈ 10 W"]:::cots
    HAT["<b>HAT</b><br/>amp + buffers"]:::custom
    SPK["Speaker ≤ 3.2 W"]:::cots
    GIM["Gimbal servo<br/>stall ≈ 2 A"]:::cots
    SNS["<b>SNS</b><br/>Teensy + 8 sensors"]:::custom
    USBH["Powered USB hub<br/>mic · lidar"]:::cots
    JUSB["Jetson USB ports<br/>FC · thermal · 4G"]:::cots''')
    e = d.edge
    e("BATT", "PDB", "VBAT · XT60", "power")
    e("PDB", "ESC", "PWR_VBAT · XT60", "power")
    e("ESC", "MOT", "3-phase", "power")
    e("PDB", "LGT", "PWR_VBAT_LGT · fused 3 A", "power")
    e("LGT", "FLASH", "CC", "power")
    e("LGT", "IRL", "CC", "power")
    e("PDB", "JET", "PWR_19V_JET · 60 W", "power")
    e("JET", "JUSB", "USB 5 V", "power")
    e("PDB", "HAT", "PWR_5V_AUX", "power")
    e("HAT", "SPK", "class-D", "power")
    e("PDB", "HAT", "PWR_5V_SERVO · 3 A", "power")
    e("HAT", "GIM", "PWR_5V_SERVO", "power")
    e("PDB", "SNS", "PWR_5V_AUX", "power")
    e("PDB", "USBH", "PWR_5V_AUX", "power")
    d.write()


# --------------------------------------------------------------------------
# 2. PDB
# --------------------------------------------------------------------------
def pdb():
    d = Diagram("board-pdb", "LR")
    d.raw('''
    BATT["Battery 6S LiPo<br/>18.0–25.2 V"]:::ext
    subgraph PDBB["PDB — Power Distribution Board"]
        direction LR
        J1["J1 BATT_IN<br/>XT60PW-M"]:::conn
        PROT["Input protection<br/>D1 TVS SMBJ28A<br/>C1–C2 470 µF / 50 V low-ESR"]:::passive
        SH["R1 shunt 0.25 mΩ<br/>4-terminal, ≥ 5 W"]:::passive
        BUS(("PWR_VBAT<br/>bus"))
        U1["U1 INA240A3<br/>current-sense amp ×100<br/>25 mV/A"]:::ic
        DIV["R2/R3 100k / 10k<br/>VBAT divider ÷11"]:::passive
        F1["F1 3 A fuse"]:::passive
        U2["U2 buck-boost ctrl<br/>LM5176-class<br/>19 V / 3.2 A (60 W)"]:::ic
        U3["U3 buck<br/>TPS54560B + Schottky<br/>5 V / 5 A"]:::ic
        U4["U4 buck<br/>TPS54560B + Schottky<br/>5 V / 3 A"]:::ic
        U5["U5 LDO 3.3 V<br/>AP2112K-3.3"]:::ic
        J2["J2 ESC_OUT · XT60PW-M<br/>→ 4-in-1 ESC"]:::conn
        J3["J3 LGT_PWR · XT30PW-M<br/>→ LGT J1"]:::conn
        J4["J4 JET_PWR · Micro-Fit 2p<br/>→ Jetson DC jack"]:::conn
        J5["J5 HAT_5V · Micro-Fit 2p<br/>→ HAT J2"]:::conn
        J6["J6 SNS_5V · Micro-Fit 2p<br/>→ SNS J1"]:::conn
        J7["J7 USBHUB_5V · Micro-Fit 2p<br/>→ USB hub DC in"]:::conn
        J8["J8 SERVO_5V · Micro-Fit 2p<br/>→ HAT J3"]:::conn
        J9["J9 FC_SNS · JST-GH 4p<br/>→ FC CURR / VBAT pads"]:::conn
    end
''')
    e = d.edge
    e("BATT", "J1", "VBAT_RAW", "power")
    e("J1", "PROT", None, "power")
    e("PROT", "SH", None, "power")
    e("SH", "BUS", None, "power")
    e("SH", "U1", "Kelvin sense", "analog", "-.->")
    e("BUS", "J2", "PWR_VBAT (motors)", "power")
    e("BUS", "F1", None, "power")
    e("F1", "J3", "PWR_VBAT_LGT", "power")
    e("BUS", "U2", None, "power")
    e("U2", "J4", "PWR_19V_JET", "power")
    e("BUS", "U3", None, "power")
    e("U3", "J5", "PWR_5V_AUX", "power")
    e("U3", "J6", "PWR_5V_AUX", "power")
    e("U3", "J7", "PWR_5V_AUX", "power")
    e("U3", "U5", None, "power")
    e("U5", "U1", "3V3_SNS", "power")
    e("BUS", "U4", None, "power")
    e("U4", "J8", "PWR_5V_SERVO", "power")
    e("BUS", "DIV", None, "analog")
    e("U1", "J9", "FC_CURR_SNS", "analog")
    e("DIV", "J9", "FC_VBAT_SNS", "analog")
    d.write()


# --------------------------------------------------------------------------
# 3. Jetson I/O HAT
# --------------------------------------------------------------------------
def hat():
    d = Diagram("board-hat", "LR")
    d.raw('''
    subgraph HDR["J1 · Jetson 40-pin header (3.3 V logic)"]
        direction TB
        P_I2S["pins 12 / 35 / 40<br/>I2S SCLK / FS / DOUT"]:::hdr
        P_AMP["pin 29 · GPIO01"]:::hdr
        P_PWM["pins 15 / 32 / 33<br/>PWM"]:::hdr
        P_SP["pin 7 · GPIO09"]:::hdr
        P_EN["pin 31 · GPIO11"]:::hdr
        P_I2C["pins 3 / 5<br/>I2C SDA / SCL"]:::hdr
        P_UART["pins 8 / 10<br/>UART TXD / RXD"]:::hdr
        P_NC["pins 2 / 4 · 5 V<br/>NOT CONNECTED"]:::passive
    end
    subgraph HATB["HAT — Jetson I/O HAT"]
        direction LR
        RSD["R_SD<br/>SD_MODE resistor"]:::passive
        U1["U1 MAX98357A<br/>I2S class-D amp 3.2 W"]:::ic
        RPD["R 100k pull-downs<br/>on U2 inputs"]:::passive
        Q1["Q1 2N7002<br/>gate 100k to GND<br/>drain 10k to 5V_AUX"]:::ic
        U2["U2 74AHCT125<br/>quad buffer, VCC 5 V<br/>3.3 → 5 V, OE# per ch."]:::ic
        ROUT["R 100 Ω series +<br/>10k pull-down per output"]:::passive
        RS["R 100 Ω series"]:::passive
        J2["J2 5V_AUX in<br/>Micro-Fit 2p"]:::conn
        J3["J3 5V_SERVO in<br/>Micro-Fit 2p"]:::conn
        J4["J4 SPEAKER<br/>JST-PH 2p"]:::conn
        J5["J5 GIMBAL<br/>servo 3p 2.54"]:::conn
        J6["J6 LIGHT_CTRL<br/>JST-GH 4p"]:::conn
        J7["J7 I2C (Qwiic)<br/>JST-SH 4p"]:::conn
        J8["J8 FC_UART (opt.)<br/>JST-GH 4p"]:::conn
    end''')
    e = d.edge
    e("P_I2S", "U1", "I2S_BCLK · I2S_LRCLK · I2S_DOUT", "i2s")
    e("P_AMP", "RSD", "AMP_SD", "gpio")
    e("RSD", "U1", "SD_MODE", "gpio")
    e("U1", "J4", "SPK_P / SPK_N (BTL)", "power")
    e("P_PWM", "RPD", "PWM_GIMBAL_3V3 · PWM_FLASH_3V3 · PWM_IR_3V3", "pwm")
    e("P_SP", "RPD", "SPARE_3V3", "gpio")
    e("RPD", "U2", "1A–4A", "pwm")
    e("P_EN", "Q1", "OUT_EN", "gpio")
    e("Q1", "U2", "OUT_EN_N → 1OE#–4OE#", "gpio")
    e("U2", "ROUT", "1Y–4Y (5 V)", "pwm")
    e("ROUT", "J5", "PWM_GIMBAL", "pwm")
    e("ROUT", "J6", "PWM_FLASH · PWM_IR · SPARE_OUT", "pwm")
    e("J3", "J5", "PWR_5V_SERVO", "power")
    e("J2", "U1", None, "power")
    e("J2", "U2", "PWR_5V_AUX", "power")
    e("P_I2C", "J7", "I2C_SDA · I2C_SCL", "i2c", "<-->")
    e("P_UART", "RS", "FC_UART_TX / RX", "uart", "<-->")
    e("RS", "J8", None, "uart", "<-->")
    d.write()


# --------------------------------------------------------------------------
# 4. Lighting driver board
# --------------------------------------------------------------------------
def lighting():
    d = Diagram("board-lighting", "LR")
    d.raw('''
    PDB["PDB J3<br/>PWR_VBAT_LGT"]:::ext
    HAT["HAT J6<br/>LIGHT_CTRL"]:::ext
    subgraph LGTB["LGT — Lighting Driver Board"]
        direction LR
        J1["J1 LGT_PWR<br/>XT30PW-M"]:::conn
        J2["J2 LIGHT_CTRL<br/>JST-GH 4p"]:::conn
        CIN["Input filter<br/>bulk + ceramic caps<br/>TVS"]:::passive
        RC["Per PWM input:<br/>100 Ω series · 10k pull-down<br/>ESD diode"]:::passive
        U1["U1 AL8860<br/>constant-current buck<br/>CH1 · white"]:::ic
        U2["U2 AL8860<br/>constant-current buck<br/>CH2 · IR"]:::ic
        RS1["R5 sense<br/>sets I_FLASH"]:::passive
        RS2["R11 sense<br/>sets I_IR"]:::passive
        J3["J3 FLASH_LED<br/>JST-XH 4p"]:::conn
        J4["J4 IR_LED<br/>JST-XH 4p"]:::conn
    end
    FL["Flashlight LED<br/>+ NTC on heatsink"]:::ext
    IR["IR LED 850 nm<br/>+ NTC on heatsink"]:::ext''')
    e = d.edge
    e("PDB", "J1", None, "power")
    e("J1", "CIN", "PWR_VBAT_LGT", "power")
    e("CIN", "U1", "VIN", "power")
    e("CIN", "U2", "VIN", "power")
    e("HAT", "J2", None, "pwm")
    e("J2", "RC", "PWM_FLASH · PWM_IR", "pwm")
    e("RC", "U1", "DIM (PWM_FLASH)", "pwm")
    e("RC", "U2", "DIM (PWM_IR)", "pwm")
    e("U1", "RS1", None, "analog", "---")
    e("U2", "RS2", None, "analog", "---")
    e("U1", "J3", "LED_FLASH_P / N", "power")
    e("U2", "J4", "LED_IR_P / N", "power")
    e("J3", "FL", None, "power")
    e("J4", "IR", None, "power")
    e("J3", "U1", "NTC_FLASH → CTRL (derate)", "analog", "-.->")
    e("J4", "U2", "NTC_IR → CTRL (derate)", "analog", "-.->")
    d.write()


# --------------------------------------------------------------------------
# 5. Sensor hub
# --------------------------------------------------------------------------
def sensor_hub():
    d = Diagram("board-sensor-hub", "TB")
    d.raw('''
    subgraph BOARD["SNS — Sensor Hub · board level"]
        direction LR
        PDB["PDB J6<br/>PWR_5V_AUX"]:::ext
        J1["J1 5V_IN<br/>Micro-Fit 2p"]:::conn
        T41["U1 Teensy 4.1<br/>IMXRT1062 · 3.3 V I/O<br/>pins NOT 5 V tolerant<br/>VUSB–VIN trace CUT"]:::ic
        BUF["U2, U3 74LVC125A<br/>VCC 3.3 V · inputs 5 V-tolerant<br/>OE# tied to GND"]:::ic
        USBH["Powered USB hub<br/>→ Jetson"]:::ext
        J10["J10 EXP 1×6 2.54<br/>3V3 · GND · SDA 18 · SCL 19<br/>GPIO 2 · GPIO 3"]:::conn
        PTC["F1–F8 PTC fuses<br/>~300 mA hold"]:::passive
        PORTS["J2–J5 RANGE1–4<br/>J6–J9 ECHO1–4<br/>JST-GH 4p"]:::conn
    end
    subgraph PORT["One sensor port · repeated ×8 (n = 1…8, see port map)"]
        direction LR
        TXP["U1 Teensy<br/>TXn pin (3.3 V)"]:::ic
        RTX["R 220 Ω<br/>series"]:::passive
        JTX["Jn pin 2<br/>SENSn_TX"]:::conn
        SRX["Sensor RX in"]:::ext
        STX["Sensor TX out<br/>(3.3 V or 5 V)"]:::ext
        JRX["Jn pin 3<br/>SENSn_RX"]:::conn
        PU["R 47k pull-up<br/>to 3V3"]:::passive
        BCH["74LVC125A channel<br/>5 V in → 3.3 V out"]:::ic
        RXP["U1 Teensy<br/>RXn pin"]:::ic
        V5["PWR_5V_AUX"]:::ext
        FN["Fn PTC"]:::passive
        JV["Jn pin 1<br/>SENSn_5V"]:::conn
        SV["Sensor VCC"]:::ext
        JG["Jn pin 4<br/>GND"]:::conn
        SG["Sensor GND"]:::ext
    end''')
    e = d.edge
    e("PDB", "J1", None, "power")
    e("J1", "T41", "PWR_5V_AUX → VIN", "power")
    e("J1", "PTC", "PWR_5V_AUX", "power")
    e("PTC", "PORTS", "SENS1–8_5V", "power")
    e("T41", "BUF", "3V3", "power")
    e("T41", "PORTS", "TX1–TX8 via 220 Ω", "uart")
    e("BUF", "T41", "RX1–RX8", "uart")
    e("PORTS", "BUF", "SENS1–8_RX", "uart")
    e("T41", "USBH", "USB micro-B", "usb", "<-->")
    e("T41", "J10", "I2C + GPIO", "i2c", "<-->")
    e("TXP", "RTX", None, "uart")
    e("RTX", "JTX", None, "uart")
    e("JTX", "SRX", None, "uart")
    e("STX", "JRX", None, "uart")
    e("JRX", "BCH", "nA", "uart")
    e("PU", "BCH", None, None, "---")
    e("BCH", "RXP", "nY", "uart")
    e("V5", "FN", None, "power")
    e("FN", "JV", None, "power")
    e("JV", "SV", None, "power")
    e("JG", "SG", None, None, "---")
    e("BOARD", "PORT", None, None, "~~~")  # stack the two panels vertically
    d.write()


if __name__ == "__main__":
    for fn in (system_signals, system_power, pdb, hat, lighting, sensor_hub):
        fn()
    print("wrote", ", ".join(p.name for p in sorted(HERE.glob("*.mmd"))))
