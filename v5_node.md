# v5 "The I2S Strikes Back" module — design notes

Status: **layout concept agreed**. Remaining: pin table, a few parts (buck),
per-cell current ceilings, labeling.

Numbering note: revisions are 1-based and the current board is **v4, "a new
hope"**. The next version documented here is **v5, "The I2S Strikes Back"**.
The filename still says `v2_module.md` because that is what it was created
as; rename once convenient.

Context: the node is a small ESP32 board that owns exactly one puzzle. It
gathers input and drives output, and talks MQTT (small, event-driven
payloads) to a Raspberry Pi broker that is dedicated to the game. Each
puzzle gets one ESP. The board should stay **universal**: one design,
populated as needed, so a spoon box and a metallophone can use the same PCB.

## why v5 exists (from v4)

v4 "a new hope" = ESP32-C3-SuperMini on a daughterboard socket. Pros: maglock drive
(boolean out), power regulation, opto-isolated boolean in. Cons:

- running out of IO pins
- no bus for modules (I2C) and no standard for audio (I2S)
- USB-C unreachable once the board is fully populated (BO2 in the way)
- no screw holes
- weak C3 PCB antenna

## decisions so far

### compute

- **XIAO ESP32-S3 Plus, soldered flat onto the carrier** (20 breakout pads
  D0-D19; Seeed specs it as **18 GPIO (PWM)** usable). The
  nine extra pads (D11-D19) are 0.9 mm SMD castellations with **no header
  holes** — only reachable by soldering the board flat. So the module is
  **fixed, not socketed**; a radio change means a respin. Accepted.
- Benefit: no socket height, which helps USB-C clearance.
- Standard 14 edge pads keep the usual XIAO positions (board is 21 x 17.8 mm).
- Useful defaults: I2S trio on the Plus pads = `I2S_SD`=D11/GPIO38,
  `I2S_SCK`=D12/GPIO39, `I2S_WS`=D13/GPIO40.
- Caveats: D12-D15 (GPIO39-42) are **strapping / JTAG** (MTCK/MTDO/MTDI/MTMS);
  avoid external JTAG if used as I2S. D17-D19 are **ADC2** (shared with Wi-Fi),
  fine as digital only.
- MQTT small/event-driven does **not** need Thread/Zigbee, so C6 is not
  required. S3 chosen for ecosystem maturity, more GPIO headroom, USB-OTG.
- Module sits at a **board edge** so its USB-C is reachable with a fully
  populated board.
- **Module is soldered flat, not socketed** (see above). No screw holes on it.
- **Mainboard has screw holes** in the corners.

### bus contract to the compute

The compute header carries only low-voltage logic. Nothing 12V touches it.

- Role-shared pins: `SDA/SCL` (I2C) and `BCLK/WS/SD1/SD2` (I2S).
- `INT` (from I2C module)
- spares: `1-Wire` / boot / status
- power: 3V3, GND (no 5V on bus ports)

Compute pin budget with two I2S terminals and native RS-485:

| function            | pins |
| ------------------- | ---- |
| I2C `SDA`, `SCL`    | 2    |
| I2S `BCLK`,`WS`,`SD1`,`SD2` | 4 |
| UART `TX`,`RX` (native RS-485) | 2 |
| `INT`               | 1    |
| **subtotal**        | **9**|

Against the **Plus's 18 usable GPIO** that leaves ~9 for local cells (5) and
spares (~4). (Auto-direction transceiver assumed, so no `DE` pin.)

### local cell capacity (module is the exception)

Module usage is the exception, so local opto cells are driven from **direct MCU
pins** and consume compute pins. Need 5 (3 in + 2 out):

- **XIAO ESP32-S3 Plus soldered flat:** 18 usable GPIO (20 pads). After
  bus+UART+INT (9), ~**9 free**. Local cells need 5 (3 in + 2 out) ->
  **~4 spares** remain.
- **Area** is not the limit for this small a cell count.
- **Power** is fine: only 2-3 local outputs, all on the 2A rail, leave ample
  headroom. Remote driver boards are self-powered (see LED / dimming), so they
  do not load this fuse.

=> With this design there is **real headroom**: pins, area, and current all
have slack. Nothing is the binding limit at the chosen dimensions.

### bus terminals (shared-port idea dropped)

The "universal I2C-or-I2S shared footprint" idea was **dropped**. Reason: at
least **two I2S terminals** are required, and a single shared footprint can
only ever be one of I2C *or* I2S — it cannot provide two I2S ports. Area was
also not a real constraint (~370 mm² / 3-4% of a 10x10 board, more than repaid
by the SMD conversion).

Final terminal set, all **optional / unpopulated by default**:

- **1 x I2C terminal** — `3V3 GND SDA SCL`
- **2 x I2S terminals** — `3V3 GND BCLK WS SD`

I2S clock sharing:

- `BCLK` and `WS` are **shared across both I2S terminals** (one ESP pin each,
  fanned out).
- Each terminal gets its **own `SD`** (`SD1`, `SD2`).
- => two I2S modules cost **4 pins**, not 6.
- Valid only if both modules are **slaves at the same sample rate / format**
  (a mic + speaker, or two mics, can share). Independent differing-rate
  streams would need separate clock pairs and more pins.

### module / terminal count

- **I2C: one module.** The single I2C terminal hosts **one I2C module**
  (MCP23017 or PCA9685 with screw terminals); that module carries the many
  field channels. No mux — nothing to mux to with only one module.
- **I2S: up to two modules at once**, on the two terminals, sharing
  `BCLK`/`WS` and using `SD1`/`SD2`.
- All terminals are optional footprints; the default build populates none.

### default build = no modules

- Most puzzles end up just driving a **maglock** — one boolean output. That
  needs **no module at all**.
- Default populate: XIAO socket + power + the **local** I/O cells (3 in /
  2 out). No I2C terminal, no I2S terminal, no cables except the field wires.
- The current I/O set is not a hard limit; it is the pragmatic default that
  covers the common case while keeping the board module-free.

### field IO (12V domain, on-board)

- Keep the 12V section on the mainboard (as v4).
- Baseline populate: **3 opto-isolated boolean in, 2 opto-isolated boolean out**.
- One universal board, **populate as needed** for the rest.
- Default build has **no wires**; wire terminals only appear where a puzzle
  needs a field connection.
- **No jumper wires anywhere.** All build-time selection is soldered
  (0Ω links / solder bridges).

### spare pins + power breakout

- **Free pins:** Plus has 18 usable GPIO; bus+UART+INT uses 9 -> **9 free**.
  Local blocks (3 in + 2 out = 5) leave **4**. Excluding strapping (`D2`/GPIO3)
  and JTAG trims this further. The UART pair stays on the Plus's default
  `D6`/`D7` (GPIO43/44) for the native RS-485 transceiver.
- **Local I/O blocks (final): 2 opto out + 3 opto in, MCU-driven.**
- **Safe spares + power: 2.54 mm Dupont-spaced through-holes** (not screw
  terminals). Makes them **~10x smaller** and accepts a pin header, a female
  socket, or a soldered wire — maximum flexibility. Target pin set below.
- **Field cables** (opto in/out, I2C, I2S, RS-485) keep **screw
  terminals** — cable that lives in the installation needs strain relief;
  spares/power are build-time.
- **Excluded from spares:** strapping and JTAG pins (avoid boot/debug hazards).
- Label spares with the **actual GPIO number**, not a friendly name.

### terminal / hole set (target)

| item             | qty      | type              |
| ---------------- | -------- | ----------------- |
| opto in          | 3        | 2-pos screw term  |
| opto out         | 2        | 2-pos screw term  |
| I2C              | 1        | 4-pos screw term  |
| I2S              | 2        | 5-pos screw term  |
| RS-485 (A/B/GND) | 1        | 3-4 pos screw term |
| safe spares      | ~7 pins  | 2.54 mm holes     |
| power (2x3V3, 4xGND, 2x5V) | 8 pins | 2.54 mm holes |

### RS-485 (native, on-board transceiver)

Purpose: a **wired fallback from a node to the RPi** when its WiFi/MQTT path
fails. Laying a single cable from the RPi to the troubled node recovers it.

- **Native, not a module**: the transceiver chip lives **on our board**; the
  terminal carries the differential pair, not a UART.
- **Terminal:** `A`, `B`, `GND` (+ optional shield) = 3-4 pos screw terminal.
- **Transceiver: MAX13487EESA+** (explicit choice, SOIC-8). Auto-direction
  (AutoDirection), so **no DE pin** and no firmware direction bugs. Single
  footprint only; MAX3485 (manual DE/RE) **not** carried — two footprints for
  one function is the sprawl this doc rejects elsewhere.
  - **Non-isolated** (explicit choice): the bus shares GND with the RPi end.
    ADM2582-class isolation is the fallback if a field ground ever differs.
  - `D6`/`D7` = GPIO43/44 (Plus default UART); **no spare GPIO burned**.
- **DI idle-definition: 10k pull-up from DI to 3V3.** MAX13487 keys the driver
  off *transitions* on DI, so a Hi-Z MCU (reset, bootloader, deep sleep) must
  not be misread as a transmit. **Do not leave DI floating** — an unpulled DI
  can let a node in reset wedge the whole bus.
- **Termination:** 120Ω **behind a 0Ω link** at our end; only the two physical
  bus ends terminate, so a mid-drop node leaves its link open.
- **Bias:** fail-safe pair (e.g. ~560Ω pull-up on A / pull-down on B) behind
  the 0Ω link. **One bias pair per bus only**, normally at the master (RPi)
  end — do **not** bias at every node.
- **Line protection:** series **10Ω** on `A`/`B` at the connector, plus
  **TVS to GND** on each (`P6KE6.8A` class, consistent with v4's TVS parts).
- **3V3-only** — no 5V, per the bus-port power rule.
- **Costs:** 1 IC + ~6 passives (10k DI, 120Ω, 2x bias, 2x TVS, 2x 10Ω) +
  1 terminal.
- **Unpopulated by default**; populate per install where redundancy is wanted.
  The transceiver footprint stays on the board regardless.
- **Receive echo (firmware note):** autodirection solves *driver* direction
  only — the node still hears its own transmission (driver output couples to
  RO). Non-isolated RS-485 handles this by **ignoring RX while TX-ing** in
  firmware. Hardware cannot fix this on the auto part; not a defect.
- **Protocol / addressing (open):** Modbus RTU is the obvious candidate; each
  node needs an address (GPIO strap or a small ID chip). The RPi is master; its
  end needs the same transceiver + termination (and the single bias pair).
- **Note:** WiFi/MQTT stays the primary path; RS-485 is a **second transport to
  the same broker**. Failover semantics are a firmware decision (not hardware).

### area check (10x10 = 10 000 mm²)

- screw terminals (field only) ~3150 mm² (adds the 3-4 pos RS-485)
- Dupont holes (spares + power) ~185 mm² (vs ~1720 as screw terminals)
- compute + power + cells + passives + routing ~3300-3800 mm²
- **~70-75% used -> still comfortable** on 10x10, even with some THT. SMD cells
  free further room. Soft limit holds.

### final count summary

Field terminals / cells:

| item            | qty |
| --------------- | --- |
| I2C terminal    | 1   |
| I2S terminal    | 2   |
| RS-485 terminal | 1 |
| opto boolean in | 3   |
| opto boolean out| 2   |

Compute: **XIAO ESP32-S3 Plus, soldered flat** (18 usable GPIO, 20 pads). See compute section.

### expander modules — bought breakouts on the I2C terminal

- Do **not** place MCP23017 / PCA9685 chips on the board. The **I2C terminal**
  feeds a bought module (many are sold with screw terminals).
- I2C addresses are set **on the module** (its solder jumpers).
- Watch out: module pull-ups collide with the board pair — see I2C pull-ups
  above. Keep one pair only.
- Watch out: the module is on a cable, not stacked on the board, so height is
  no longer a concern here.

### bus port power rule (safety)

- **Bus terminals (I2C, I2S) are 3V3-only.** No 5V pin on them.
- Rationale: the bus terminals are **not opto-isolated**, so the ESP pins are
  electrically continuous with the module. Offering 5V is the most likely way
  to fry the ESP; leaving it off removes the hazard.
- 5V stays on the isolated field/signal side where it is a deliberate choice.

### bus terminal component cost

- **I2C terminal:** terminal + 2× pull-up + series R + 1× 100nF cap.
- **I2S terminal:** terminal + 3× series R + 1× 100nF cap (×2 terminals).
- All tiny (0805 parts). The connectors and the wires dominate the cost, not
  the passives — so the second I2S terminal is cheap.

### modules are cabled, not on-board

The I2C/I2S modules are **remote**, connected by a **screw-terminal cable**
(same box or nearby). Consequences:

- **Bus terminals, not on-board module headers.** Pinout on each terminal is
  `3V3 GND SDA SCL` (I2C) or `3V3 GND BCLK WS SD` (I2S), 4–5 positions.
  One I2C terminal, two I2S terminals (see bus terminals above).
- **Cable protection is part of the design** (explicit choice):
  - series resistors on `SDA`/`SCL`, and on `BCLK`/`WS`/`SD` (e.g. 22–33Ω)
  - **ESD/TVS** on the signal lines at the terminal (a pluggable cable sees
    ESD; an on-board module does not)
  - **selectable pull-ups** (2.2k–4.7k) behind 0Ω links, because cable
    capacitance slows edges
  - solid **GND return** on the terminal
- **3V3-only stands**, and matters more: a cable is a better fault antenna.
- **Distance policy:** I2C cable runs are **same-box only** (short). Plain I2C
  + series R + moderate pull-ups is sufficient; no differential I2C
  (PCA9615) / RS-485 needed. I2S over a short box cable is fine with series R;
  keep `BCLK` away from noisy lines and pair signals with a ground return.
- If a future install ever needs a room-scale bus, that is a *new* board
  decision (differential I2C / RS-485 / 1-Wire), not this terminal.

### I2C pull-ups

- **Pull-ups are an I2C-only requirement** (I2S is push-pull and needs none).
- They live on the **I2C port side**, behind **0Ω links**, so the board always
  has the capability but a build can include or exclude them.
- I2C is open-drain, so the bus floats without them.
- **One pull-up pair per bus, never duplicated.** MCP23017/PCA9685 modules ship
  with their own pull-ups; chaining several gives too-strong (too-low) parallel
  resistance. Policy: keep **either** the board pair **or** one module's pair.
  The 0Ω link is what makes that a build-time choice.
- Practical default: board pull-ups left unpopulated, relying on the single
  connected module's pull-ups — but the option is on the board for the
  universal case.

### I/O coverage (local + remote)

- **On-node I/O** -> the local reusable cells (opto in / MOSFET out), **3 in /
  2 out**. Fallback for puzzles that want I/O on the node.
- **Remote I/O** -> MCP23017 / PCA9685 modules on the I2C terminal (many are
  sold with screw terminals, so the field wiring lands on the module).
- **Audio** -> I2S modules on the two I2S terminals.
- **Wired fallback** -> RS-485 to the RPi's broker, same as the WiFi/MQTT path.
- Both local and remote kept (explicit choice) — the bus terminals do not
  replace the local cells.

### I2S audio ports

- **Two I2S terminals**, each `3V3 GND BCLK WS SD`, with `BCLK`/`WS` shared
  across both and `SD` per terminal (`SD1`, `SD2`).
- Direction per module: **mic** (`SD` = input) or **speaker** (`SD` = output).
  The same 3 signal pins serve either; the module and firmware set direction.
- **No duplex per link** — a puzzle needs record *or* playback per module, not
  both at once on one link. Two modules = two one-direction links.
- No 5V on these terminals (see power rule above). Verify per module that the
  codec/amp logic is 3.3V; level-shift only if a module is genuinely 5V.

### native I2S — considered, NOT chosen

Kept at **2x I2S terminals** for now. Native (chip on our board) was
brainstormed; recorded so it is not re-litigated from scratch.

What native would add:

- **Speaker site:** 1x I2S Class-D amp (MAX98357A class) + 2-3 decoupling caps
  + optional LC/RC output filter + a 2-pos **speaker terminal**. Replaces the
  5-pos I2S terminal.
- **Mic site:** 1x I2S MEMS mic (INMP441 / ICS-43434 class) + decoupling.
  Placed on-board; no field connector.
- Same 3 I2S pins (`BCLK`/`WS`/`SD`) either way.

Why not (drawbacks):

- **No single "native I2S".** A mic and a speaker are **different chips**, so
  each audio site becomes an **amp-or-mic build choice** (two alternative
  footprints). Two I2S sites x two types = footprint sprawl.
- **Part commitment.** Picking MAX98357A / a specific mic bakes a part into
  every board (or leaves it unpopulated). Amps/mics vary in gain, mono/stereo,
  class-D vs AB, sensitivity.
- **5V tension (softened).** MAX98357A wants ~5V for volume; the **bus
  terminals** are 3V3-only. But an **on-board** amp can tap the internal 5V
  rail directly (no 5V on a user-facing pin), which is **not** the bus hazard.
  Since v5 has a 5V rail that is otherwise underused, this is arguably an
  argument *for* native audio — not against it. Watch the **R-78E5.0-1.0's
  1A** budget and keep the amp clean of converter noise.
- **Mic wants acoustic placement**, not a wired module — native only helps if
  the mic physically belongs on the node.
- **Modules are genuinely empty** (the chip *is* the breakout), so the only
  thing native saves is one connector + the convenience of hot-swap.

Possible middle path (if audio becomes common): keep the I2S terminals **and**
add an **unpopulated on-board amp footprint** for the common playback case.
Revisit after real puzzles show the mic/speaker split.

### terminology cheat-sheet (I2S)

- `BCLK` = bit clock = SCK/SCLK — one pulse per bit (fast).
- `WS` = Word Select = LRCK/LRCLK/FS — one pulse per sample/frame (slow);
  level selects left/right channel.
- `SD` = serial data = DIN/DOUT/SDATA — the sample bits.
- One **master** per clock pair generates `BCLK`+`WS`; devices are **slaves**.
  A mic and an amp are both slaves, so they share one clock pair.
- Each I2S data line is one direction. Two modules on the two terminals = two
  independent `SD` lines sharing one `BCLK`/`WS` pair.

### per-cell logic-source selection

- Each field cell has a **0Ω / solder-jumper** that selects whether its logic
  side comes from an MCU pin or from the I2C module (MCP23017/PCA9685).
- Soldered, not a movable shunt: cannot shake loose inside an installation.
- Field side keeps screw terminals for the actual wires.

### reusable cell designs

One sub-circuit per kind, instantiated N times:

- **input cell**: `terminal -> 3.3k -> opto (SOP-4) -> 10k pull-up -> [0R link: MCU pin | I2C module]`
- **output cell**: `[0R link: MCU pin | I2C module] -> 330R -> opto -> gate -> logic-level MOSFET -> terminal` (+ flyback + bulk cap)
- **LED cell** (only if an LED must live *on the node*): `[0R link: MCU PWM | I2C module PWM] -> 10k pull-up -> gate R -> low-side logic-level MOSFET -> 12V LED` (+ bulk cap). For remote arrays the driver lives on the module instead (see LED / dimming).

Per-cell current ceiling is enforced by the cell's own parts. The ~2A
polyfuse is the aggregate backstop (kept at ~2A, per an explicit choice).

### LED / dimming

- Dimming is done over I2C with a **PCA9685** (12-bit hardware PWM, 16 ch).
  This is the answer to "can an I2C module dim a LED" — yes.
- **PCA9685 channel = 25 mA max**, so it drives the **dimming signal**, not the
  LED current. Power LEDs need a driver per channel:
  - **12V LED module (current-limited)** -> PCA9685 -> logic-level MOSFET ->
    LED. Simple. SOT-23 FET (`AO3400` class) is fine for switched 500 mA.
  - **bare 500 mA emitter** -> PCA9685 -> buck constant-current driver
    (PT4115/AL8860), PWM the driver's `DIM` pin. A series resistor would burn
    ~4.4 W per LED as heat.
- PCA9685 outputs are open-drain -> **10k pull-up to VCC per output**, and use
  a **logic-level** MOSFET.
- **Where the driver lives: remote, on the module** (explicit choice). The
  driver cells sit with the PCA9685 at the far end; the board only supplies
  `3V3 GND SDA SCL`. So a 500 mA array needs a **purpose-built remote driver
  board** (PCA9685 + N driver cells), not a plain PCA9685 breakout.
- **Remote driver board is self-powered** (explicit choice): it takes its own
  12V/supply, so the 500 mA LED currents do **not** pass through the universal
  board's ~2A fuse — only the logic link (`3V3 SDA SCL`, mA) crosses. This
  resolves the earlier fuse squeeze.

### audio

- Audio runs on the **I2S terminals** (remote mic/speaker modules on cables).
- MQTT carries only events/commands ("play tone X", "loud sound detected"),
  never the audio stream.

### power

- 12V in -> polyfuse (~2A) -> Schottky -> TVS -> R-78 5V (as v4).
- **Add a 3V3 buck** so the logic rail does not depend on the module LDO.

### assembly / fab

- SMD where easy to hand-solder with a Pinecil (no heat gun):
  **0805 passives**, **SOIC / SOP-4 / SOT-23** chips. Avoid QFN/DFN/BGA.
- Keep **THT** for screw terminals, the R-78, and bulk caps.
- The **Plus is soldered flat** to the carrier; spares/power are 2.54 mm holes.
- Target 10x10 (soft). Area estimate ~68-73% used — comfortable.
- v4 silk reads "on 28.08.2026"; kept only as historical context, no timing
  decision here.

## puzzle examples this must cover

- rotary phone: call a number, a message plays to the handset speaker
- knock-knock box: button plays a morse-like sequence; matching knocks open
- metallophone: sequence in, playback + door + room lights (LED array)
- spoon box: spoon removed -> door opens

## standards to evaluate next (data handling & beyond)

Not committed; a survey to run before finalising the bus. Ordered roughly by
relevance to a puzzle node.

### data buses / links
- **1-Wire (Dallas/Maxim)** — 1 data + GND (+ parasitic power). Unique 64-bit
  ROM per device, so no addressing hassle. Great for **many simple switches,
  buttons, iButton keys, temperature sensors**. Already flagged in
  `i2c_bus.md`. Low speed, but ideal for a chain of contacts.
  - **No footprint needed** (decision): it needs one GPIO + a 4.7k pull-up, so
    it can be soldered to a **spare Dupont hole**. One pull-up per bus.
- **UART / serial** — 2 wires, **asynchronous, no clock**, point-to-point.
  Both ends agree a baud rate; the start bit re-syncs each byte. Good for
  talking to an outboard MCU (e.g. an Arduino running a specific puzzle) or a
  second ESP.
- **RS-485 (physical) / Modbus RTU (protocol)** — **differential, no clock**,
  multi-drop, **~1200 m**, noise-immune. This is **the standard long-distance
  wired link**. Modbus is the message format riding on it; RS-485 is the wire.
  - **Not just a terminal:** needs a transceiver (MAX485/MAX3485/AUT-direction
    class), a terminal (`A`, `B`, `GND`, +shield), 120Ω termination at each
    end, bias/common-mode resistors, and a **DE/RE direction pin** (1 GPIO) or
    an auto-direction part.
  - **Relevance check:** RS-485 pays off for **hundreds of metres** or
    **multi-drop**. Current nodes sit at their own puzzle and talk MQTT to the
    RPi, so it is insurance for a puzzle class not yet present. Counterpoint:
    a **UART pair on a spare Dupont hole** already gives short/medium serial
    to an outboard board at ~zero cost; RS-485 is only worth it for real
    distance or true multi-drop.
  - **Resolved: native RS-485, on-board transceiver, MAX13487E** (explicit
    choice). The transceiver chip lives on our board so a single cable from the
    RPi to a troubled node recovers its link. The board exposes the
    **differential pair** (`A`, `B`, `GND`) on a 3-4 pos screw terminal — not a
    UART. **Half-duplex** (2 wires A/B) is the choice. **Non-isolated**; auto-
    direction -> no DE pin.
    - Direction: **auto-direction MAX13487E** -> no extra GPIO.
    - Natural pin fit: the Plus's default UART on `D6`/`D7` (GPIO43/44).
    - Board cost: 1 IC + ~6 passives + 1 terminal, on **every** board even when
      unpopulated — accepted as cheap insurance for a wired fallback.
    - Full block detail (DI pull-up, termination, bias, TVS): see the
      **RS-485 (native, on-board transceiver)** section above.
- **SPI** — clocked, 4 wires (`SCK`, `MOSI`, `MISO`, `CS`), point-to-point.
  Overkill for most puzzles; useful for SD/display/fast ADC. Plus exposes a
  second SPI bus.
- **CAN bus** — differential, multi-drop, arbitration. Heavier than needed;
  the gold standard for noisy/long multi-node links.
- **Differential I2C (PCA9615)** — extends I2C over cable; only if I2C must run
  room-scale (currently not needed).

### clock vs. no clock (quick reference)
- **Clocked:** I2C (`SCL`), I2S (`BCLK`+`WS`), SPI (`SCK`).
- **Clockless / async:** UART, RS-485/Modbus, 1-Wire (self-timed by protocol).

### audio
- **I2S** (chosen) — digital audio, 3 wires, covered.
- **PDM** — 2 wires (clock + data), used by many cheap MEMS mics. Simpler than
  I2S for a single mic; the ESP32-S3 supports it. Worth knowing as a mic
  alternative.
- **analog audio (line / speaker)** — what v4 effectively did on its signal
  port. Keep in mind for simple "play a tone" puzzles where a codec is overkill
  (a DAC pin or PWM + filter).

### addressable / smart outputs
- **WS2812 / WS2811 / WS2815** — 1 wire, addressable RGB. Chosen *against* for
  the PWM LED bank, but still useful where individually-coloured LEDs matter.
- **NeoPixel over 5V vs 12V (WS2815)** — 12V variants fit the node's rail.

### power / safety
- **PoE (802.3af/at)** — if a node ever sits at the end of a Cat5 run, PoE
  carries power + data on one cable. Changes the connector and power design;
  worth knowing if installs get structured-cable-based.
- **USB-C PD / power negotiation** — relevant only if a puzzle gets power over
  USB-C rather than the 12V rail.
- **e-Fuse / hot-swap controllers** — cleaner than a polyfuse if you want
  per-rail limits + telemetry.

### identity / discovery
- **I2C EEPROM ID (AT24C02)** per module, or **1-Wire ID (DS2431)** — lets the
  node auto-discover what is plugged into a port. Nice-to-have; revisit if
  modules become many.

### protocols on top (software)
- **MQTT** (chosen) — the node <-> RPi broker link. Evaluate **MQTT topics
  schema / retained state / LWT** conventions, and whether **mqtt-tls** or
  plain local broker is enough.
- **ESP-NOW** — direct ESP-to-ESP, no AP. Only if nodes ever need to talk to
  each other rather than through the RPi.
- **mDNS / discovery** — if the RPi broker address is dynamic.
- **OTA update strategy** — how the node firmware gets updated once installed.

### the question to answer
Which of these, if any, deserve a **footprint / terminal** on v5 *now*
(cheap insurance), vs. a future revision. **1-Wire: resolved** — solder to a
spare hole, no footprint. **RS-485: resolved** — native on-board MAX13487E,
half-duplex, non-isolated, `A`/`B`/`GND` terminal, unpopulated by default.
Others remain future options.

## open items

- **pin table** — which GPIO carries what (bus + UART + local cells + spares),
  respecting the Plus's strapping/JTAG caveats
- **field current / fuse budget** — keep ~2A; local cells only (~2-3 outputs).
  Remote driver boards are **self-powered**, so their current does not pass
  through this fuse. Largely resolved; confirm per-cell ceilings.
- exact 3V3 buck part
- per-cell current ceiling numbers
- port-keying / labeling so the v4 signal terminals and the new bus terminals
  cannot be confused
- I2C bus trace routing (star vs. daisy) — minor, same-box only

## superseded / not chosen

- **universal shared I2C-or-I2S port** — dropped; at least two I2S terminals
  are needed and one shared footprint cannot provide them. Now: 1 I2C + 2 I2S
  independent terminals.
- **TCA9548A mux site** — dropped; only ever one I2C module, nothing to mux.
- bare WROOM module + custom carrier (wanted to keep a socketed daughterboard)
- on-board expander chips (chose bought breakouts on the I2C terminal)
- XIAO ESP32-C6 (no Thread need; fewer useful pins than S3 for this use)
- standard XIAO ESP32-S3 (11 GPIO, too few for MCU-driven local cells; → Plus)
- socketed mounting (Plus extra pads are solder-flat only; module is fixed)
- screw terminals for spares/power (chose 2.54 mm Dupont holes, ~10x smaller)
- movable jumper shunts (chose soldered links)
