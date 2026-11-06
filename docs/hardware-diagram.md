# Hardware Architecture Diagram

Digital version of the hand-drawn hardware wiring sketch. The **Jetson** is the
central companion computer; the **Flight Controller** runs the flight stack.

![Hardware architecture](hardware-diagram.png)

- Mermaid source: [`hardware-diagram.mmd`](hardware-diagram.mmd)
- Vector export: [`hardware-diagram.svg`](hardware-diagram.svg)

<details>
<summary>Live Mermaid version (renders on GitHub)</summary>

```mermaid
%%{init: {"theme": "base", "fontFamily": "Inter, Arial, Helvetica, sans-serif", "themeVariables": {"fontFamily": "Inter, Arial, Helvetica, sans-serif", "fontSize": "15px", "primaryColor": "#ffffff", "primaryBorderColor": "#5b6b7c", "primaryTextColor": "#1d2733", "lineColor": "#5b6b7c", "clusterBkg": "#f4f6f9", "clusterBorder": "#c3ccd6", "edgeLabelBackground": "#ffffff"}, "flowchart": {"curve": "basis", "nodeSpacing": 45, "rankSpacing": 60}} }%%
flowchart TB
    %% ---------- Audio ----------
    subgraph AUDIO["Audio"]
        direction TB
        MIC["Microphone"]
        SPK["Speaker"]
        AMP["Amplifier"]
        SPK --- AMP
    end

    %% ---------- Lighting ----------
    subgraph LIGHT["Lighting"]
        direction TB
        PWR["Power ?"]
        DRV["Drivers"]
        FLASH["Flashlight"]
        IR["IR Light"]
        PWR --> DRV
        DRV --- FLASH
        DRV --- IR
    end

    %% ---------- Vision ----------
    subgraph VISION["Vision sensors"]
        direction TB
        RGB["RGB / Night camera"]
        HEAT["Heat (thermal) camera"]
        LIDAR["Lidar"]
        LBOARD["Lidar board"]
        LIDAR -- "Pin connector" --- LBOARD
    end

    %% ---------- Companion computer ----------
    JETSON{{"Jetson"}}
    LTE["4G LTE"]
    GIMBAL["Gimbal servo"]

    %% ---------- Proximity sensing ----------
    subgraph PROX["Proximity sensing"]
        direction LR
        TEENSY["Teensy"]
        RF["4x Rangefinders"]
        ECHO["4x Echo"]
        TEENSY -- "UART" --- RF
        TEENSY -- "UART" --- ECHO
    end

    %% ---------- Flight stack ----------
    subgraph FLIGHT["Flight stack"]
        direction TB
        FC{{"Flight Controller"}}
        RCAM["Radio camera"]
        RTR["Radio transmission receiver"]
        GPS["GPS"]
        VTX["Radio VTX"]
        ESC["ESC"]
        RCAM -- "Pin connector" --> FC
        FC <--> RTR
        GPS --> FC
        FC --> VTX
        FC --> ESC
    end

    %% ---------- Connections to Jetson ----------
    AMP <-. "?" .-> PWR
    MIC -- "USB-A" --> JETSON
    AMP -- "Pin connector" --> JETSON
    DRV -- "Pin connectors" --> JETSON
    RGB -- "FPC, Pin" --> JETSON
    HEAT -- "USB-C" --> JETSON
    LBOARD -- "USB-A" --> JETSON
    JETSON -- "USB-A" --> TEENSY
    JETSON <--> LTE
    JETSON --> GIMBAL
    JETSON <-- "USB-A" --> FC

    %% ---------- Styling ----------
    classDef core fill:#1f3b57,stroke:#0f2233,color:#ffffff,font-weight:bold
    classDef unsure fill:#fff4d6,stroke:#c99700,stroke-dasharray:4 3,color:#5a4500
    class JETSON,FC core
    class PWR unsure
```

</details>

## Connections

| From | To | Interface | Notes |
|------|----|-----------|-------|
| Microphone | Jetson | USB-A | |
| Speaker | Amplifier | — | |
| Amplifier | Jetson | Pin connector | |
| Amplifier | Power | ? | Undecided in the sketch |
| Power | Drivers | — | Power source still marked "?" |
| Drivers | Flashlight, IR Light | — | |
| Drivers | Jetson | Pin connectors | |
| RGB / Night camera | Jetson | FPC, Pin | |
| Heat (thermal) camera | Jetson | USB-C | |
| Lidar | Lidar board | Pin connector | |
| Lidar board | Jetson | USB-A | |
| Jetson | Teensy | USB-A | |
| Teensy | 4x Rangefinders, 4x Echo | UART | |
| Jetson | 4G LTE | — | Bidirectional; interface not labeled in the sketch |
| Jetson | Gimbal servo | — | Interface not labeled in the sketch |
| Jetson | Flight Controller | USB-A | Bidirectional |
| Radio camera | Flight Controller | Pin connector | |
| Radio transmission receiver | Flight Controller | — | Bidirectional |
| GPS | Flight Controller | — | |
| Flight Controller | Radio VTX | — | One-way, out of the FC |
| Flight Controller | ESC | — | |

## Regenerating the images

```bash
npx -p @mermaid-js/mermaid-cli mmdc -i hardware-diagram.mmd -o hardware-diagram.png -b white -s 2
npx -p @mermaid-js/mermaid-cli mmdc -i hardware-diagram.mmd -o hardware-diagram.svg -b white
```
