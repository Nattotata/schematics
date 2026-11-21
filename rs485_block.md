# RS-485 block — v5

Native, on-board, half-duplex.
Auto-direction, non-isolated.
Unpopulated by default;
footprint resident.
See `v5_node.md`,
section "RS-485 (native, on-board transceiver)".

Sheet: `rs485.kicad_sch`,
instantiated once.

## hierarchical pins

| pin      | shape         | to                |
| -------- | ------------- | ----------------- |
| UART_TX  | input         | ESP D7 / GPIO44   |
| UART_RX  | output        | ESP D6 / GPIO43   |
| 3V3      | input         | logic rail        |
| GND      | input         | ground            |
| A        | bidirectional | field terminal    |
| B        | bidirectional | field terminal    |

## wiring

```
       3V3                          3V3
        |                            |
      [10k] R_RS485_DI            [560R] R_RS485_BIASA
        |                            |
  UART_TX -- DI              (0R) R_RS485_BIASLINK_A
  UART_RX -- RO   MAX13487E         |
                    VCC -- 3V3     A --+-- R_RS485_SA -- J.1 (A)
                    GND -- GND      |        |
                    A --------------+      TVS_A
                    B --+                  D_RS485_TVSA
                        |                   |
        R_RS485_TERMLINK(0R)               GND
              |
           R_RS485_TERM (120R)
              |
             B --+-- R_RS485_SB -- J.2 (B)
                 |        |
               TVS_B   (0R) R_RS485_BIASLINK_B
           D_RS485_TVSB        |
                 |        [560R] R_RS485_BIASB
                GND            |
                              GND

  VCC bypass: C_RS485_1 (100nF), C_RS485_2 (1uF) to GND
  RE#/SHDN: tie to GND (receiver enabled, auto-direction on)

  J.3 (GND) -- GND
  J.4 (SHIELD) -- GND via optional RC, else NC
```

## component checklist

| ref                 | part                     | value  | default        |
| ------------------- | ------------------------ | ------ | -------------- |
| U_RS485             | MAX13487EESA+ (SOIC-8)   | —      | DNP (resident) |
| J_RS485             | Screw_Terminal_01x04     | —      | DNP (resident) |
| R_RS485_DI          | Device:R                 | 10k    | populate       |
| R_RS485_TERM        | Device:R                 | 120R   | DNP            |
| R_RS485_TERMLINK    | Device:R                 | 0R     | populate       |
| R_RS485_BIASA       | Device:R                 | 560R   | DNP            |
| R_RS485_BIASB       | Device:R                 | 560R   | DNP            |
| R_RS485_BIASLINK_A  | Device:R                 | 0R     | populate       |
| R_RS485_BIASLINK_B  | Device:R                 | 0R     | populate       |
| R_RS485_SA          | Device:R                 | 10R    | DNP (resident) |
| R_RS485_SB          | Device:R                 | 10R    | DNP (resident) |
| D_RS485_TVSA        | P6KE6.8A                 | —      | DNP (resident) |
| D_RS485_TVSB        | P6KE6.8A                 | —      | DNP (resident) |
| C_RS485_1           | Device:C                 | 100nF  | DNP (resident) |
| C_RS485_2           | Device:C                 | 1uF    | DNP (resident) |

"resident" means `on_board yes`, `in_bom no`, `dnp yes`:
the copper stays,
but no part is placed.
Populate per install,
where a wired fallback is wanted.

## notes

- **DI pull-up (10k) is mandatory.**
  MAX13487 keys the driver off DI transitions;
  a Hi-Z MCU (reset/bootloader/deep sleep),
  without the pull-up,
  can be misread as a transmit,
  and jam the bus.
- **Termination:** 120R across A/B,
  behind the 0R link.
  Only the two physical bus ends terminate;
  a mid-drop node leaves its link open.
- **Bias:** one pair per bus,
  normally at the master (RPi) end.
  Do not bias at every node.
- **Protection:** 10R series + P6KE6.8A TVS,
  to GND on each line.
- **3V3 only** — no 5V on this terminal,
  per the bus-port power rule.
- **Receive echo:** autodirection gates the driver,
  not the receiver;
  the node hears its own TX.
  Firmware must ignore RX while transmitting.
- **RE#/SHDN** is active-low;
  tie low to keep the receiver enabled,
  and the part out of shutdown.
