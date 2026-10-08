# esptool Alternative: When Arduino IDE Can't Download Toolchains

## When to use this

Arduino IDE's ESP32 board package downloads toolchain zips from GitHub releases (~400MB total in v3.3.10). In China or restricted networks, these downloads frequently time out or fail (TCP connections to `20.205.243.166:443` drop).

When that happens, `esptool` + a precompiled `.bin` is the escape hatch.

## Install esptool

```bash
pip install esptool
```

Use Tsinghua mirror for faster download:
```bash
pip install esptool -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## Verify board connection

```bash
# Chip identification — this alone proves USB/serial/board all work
python3 -m esptool --port COM3 chip-id

# Expected output:
#   Detecting chip type... ESP32-S3   ← KEY: this tells you the actual chip
#   Chip type:          ESP32-S3 (QFN56) (revision v0.2)
#   Features:           Wi-Fi, BT 5 (LE), Dual Core + LP Core, 240MHz, Embedded PSRAM 8MB
#   Crystal frequency:  40MHz
#   MAC:                xx:xx:xx:xx:xx:xx

# Flash size check
python3 -m esptool --port COM3 flash-id
# Shows manufacturer, device ID, detected flash size
```

## Burning a precompiled .bin

```bash
# Erase first (optional but recommended for clean state)
python3 -m esptool --port COM3 erase_flash

# Write firmware
python3 -m esptool --port COM3 write_flash 0x0 path/to/firmware.bin
```

## MicroPython as alternative firmware

If you can't compile Arduino code but can download a 3MB MicroPython .bin:

1. Download `ESP32_GENERIC_S3-<date>-v<version>.bin` from micropython.org
2. Flash it:
   ```bash
   python3 -m esptool --port COM3 write_flash 0x0 ESP32_GENERIC_S3.bin
   ```
3. Connect via serial terminal (115200 baud) — you get a Python REPL
4. Use `ampy` or `mpremote` to upload Python scripts that control TFT, I2S, etc.

## YD-ESP32-23 Board Specs (esptool-verified)

Confirmed from `chip-id` and `flash-id` on an actual unit:
- **Chip**: ESP32-S3 (QFN56, rev v0.2)
- **Features**: Wi-Fi, BT 5 (LE), Dual Core + LP Core, 240MHz
- **PSRAM**: 8MB embedded (AP_3v3)
- **Flash**: 16MB (quad, 3.3V)
- **MAC**: xx:xx:xx:xx:xx:xx (per-unit)
- **USB chip**: CH343 (drives COM port)
- **esptool tested**: v5.3.0, fully compatible

This session confirmed: **esptool v5.3.0 works perfectly with the YD-ESP32-23 board on COM3.** Communication is stable, chip detection is accurate, flash detection works.

## What esptool CAN'T do

- It cannot **compile** `.ino` files — it only flashes precompiled binaries
- It cannot install Arduino libraries or board packages
- It's not a replacement for Arduino IDE's development workflow — it's a last-resort flashing tool when the IDE can't get its toolchain

## IDE Detection Notes (June 2026)

When esptool identifies the chip as ESP32-S3 but the Arduino IDE auto-selection suggests something else:
- The IDE's board selection is intentional: `ESP32S3 Dev Module` is the right choice, NOT `ESP32 Dev Board`
- If `ESP32S3 Dev Module` is selected but the IDE says the package isn't installed, you need the ESP32 board package version 3.x (not 2.x)
- The IDE may prompt: `The board needs esp32[v3.3.10] core. Install now?` — clicking Yes triggers the download chain that fails on restricted networks. Use the manual staging trick instead.

## After getting the IDE package installed

Once the IDE can compile (via manual staging or otherwise):
1. Select `ESP32S3 Dev Module` in Boards menu
2. Select `COM3` in Port menu
3. Click Upload (→)
4. The first compile takes 2-5 minutes as it resolves all dependencies
5. Watch the Output panel for: `Writing at 0x... (100%)` → `Hash of data verified` → `Hard resetting via RTS pin...`
