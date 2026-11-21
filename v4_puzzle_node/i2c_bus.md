# shared I2C bus — idea for the universal puzzle node

Motivation: the node runs out of pins once you add anything beyond boolean
I/O (e.g. an I2S microphone, an LED flicker bank). A shared bus moves the
pin-hungry stuff off the MCU and onto two wires, and makes module ports
plug-and-play instead of hand-wired.

## the idea

- **2 wires** (`SDA`/`SCL`) + power. Nearly every small breakout (sensors,
  OLED, PWM driver, I/O expander) already speaks I2C, so modules become
  swappable.
- **Address conflicts / port isolation** -> `TCA9548A` I2C mux (8 channels).
  Each physical module port becomes its own I2C channel. Bonus: the mux
  tells us *which port* is populated.
- **Not enough I/O** -> `MCP23017` (16 I/O over I2C) for boolean banks,
  `74HC595`/`74HC165` for cheap one-direction shift banks.
- **Many simple switches** -> 1-Wire (1 data + power, unique 64-bit ROM per
  device, no addressing needed). Fits the existing "1 data + power" port.
- **Many indicator outputs** -> WS2812 class (1 wire) where a discrete PWM
  per channel does not pay off.
- **Module identity** -> a tiny I2C EEPROM (or 1-Wire ID) per module so the
  node can auto-discover what is plugged into each port.

## worked example: the microphone / maglock / candle node

- input: I2S microphone (sound puzzle)
- output: boolean trigger for an external Arduino
- output: maglock powered from the node's 12V
- output: several 1W LEDs in a candle "flower", 12V, individual flicker

### pin budget on the C3 (13 GPIO on the SuperMini)

| function                         | signals           | pins |
| -------------------------------- | ----------------- | ---- |
| I2S mic                          | BCLK, WS, SD      | 3    |
| shared I2C (PWM driver / ID)     | SDA, SCL          | 2    |
| maglock switch                   | gate              | 1    |
| boolean trigger -> Arduino       | out               | 1    |
| **subtotal**                     |                   | **7**|
| candle flicker (direct LEDC)     | up to 6x PWM      | 6    |
| **total**                        |                   | 13   |

So it only fits if the flicker channels come from the **PCA9685 over I2C**
(2 pins for up to 16 channels) rather than straight off the MCU. Same for
any future growth.

### the 1W candle LEDs

Fork depending on what the lamp actually is:

- **bare 1W emitter (~3.2V, ~300mA)**: series resistor off 12V would burn
  ~2.7W *per lamp* as heat — bad inside a candle. Use a small **buck
  constant-current driver per lamp** (PT4115 / AL8860 class) and PWM its
  `DIM` pin for the flicker.
- **12V LED module (already current-limited)**: simplest — one logic-level
  MOSFET (IRLZ44N class) per lamp, PWM'd directly.

Either way, drive the flicker from the **PCA9685** (or the C3 LEDC if <= 6)
and give each lamp its own bulk cap so one current step does not dip the
shared 12V and couple into the mic.

### maglock

Low-side switch (IRLZ44N + gate resistor + pull-down + flyback diode across
the coil). 12V is already on the node; size for inrush. NB: the current
**2A polyfuse** is the sum of maglock + LEDs + logic — likely too small.

### boolean trigger -> Arduino

Keep it opto-isolated (PC817) so there is no ground loop to the other
controller. Open-collector with a pull-up on the Arduino side is the most
flexible contract; a relay only if it must be floating.

### I2S microphone

Standard I2S digital mic (INMP441 / ICS-43434 class), not PDM. C3 GPIO
matrix routes BCLK/WS/SD to any pins. Keep the mic 3V3 clean (RC/ferrite),
keep its ground away from the LED/maglock return, and keep the clocks away
from the 12V switching nodes.

## proposed module port

Physical separation matters more than the protocol:

- logic / signal domain: `3V3`, `GND`, `SDA`, `SCL` (+ spare `INT`/`DATA`)
- power domain: `12V`, `5V`, `GND` on a separate connector/traces

Keep both domains on one board but star-ground them; do not route
LED/maglock return currents under the mic.

## caveats

- **I2C is short-range** (bus capacitance): fine on-node, but for cable runs
  across a room use **RS-485 / Modbus** or 1-Wire, or differential I2C
  (PCA9615). Keep the existing opto isolation on the field side.
- The board grows in the **12V area** (MOSFETs, CC drivers, inductors,
  connectors), not the logic area.
- Add the **3V3 buck** (as planned) so the logic domain is not on the
  SuperMini's weak LDO.

## candidate parts

- `PCA9685` — 16-ch PWM over I2C (flicker / dimming)
- `TCA9548A` — 8-ch I2C mux (port isolation, address conflicts)
- `MCP23017` — 16-ch I/O over I2C (boolean banks)
- `PT4115` / `AL8860` — buck constant-current LED driver (PWM DIM)
- `IRLZ44N` — logic-level N-MOSFET (already in BOM)
- `PC817` — opto (already in BOM)
- `INMP441` / `ICS-43434` — I2S microphone
- `AT24C02` (I2C) / `DS2431` (1-Wire) — per-module ID
- `WS2815` / `WS2811` — 12V addressable LED alternative (if lamps can change)
