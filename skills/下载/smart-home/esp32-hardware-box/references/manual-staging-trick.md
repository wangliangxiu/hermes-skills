# Manual Staging Trick: Installing ESP32 Packages Without Internet

## Problem

Arduino IDE's Boards Manager downloads toolchain zips from GitHub releases. On networks where GitHub is blocked or slow (common in China), the 400MB+ downloads timeout with errors like:

```
Platform installation failed: 'esp32:3.3.10' 13 INTERNAL: Download failed:
performing HEAD request: Head "https://github.com/espressif/crosstool-NG/
releases/download/esp-14.2.0_20260121/xtensa-esp-elf-14.2.0_20260121-x86_64-w64-mingw32.zip":
read tcp ...->20.205.243.166:443: wsarecv: A connection attempt failed
```

This happens because the actual toolchain binaries are on GitHub releases, not on any mirror. Changing the Board Manager URL only affects the package **index**, not the binary downloads.

## Solution: Pre-populate the staging directory

The IDE stores partially-downloaded packages in `~/AppData/Local/Arduino15/staging/packages/`. If a file with the expected name already exists there, the IDE skips the download and uses the cached copy.

### Which files you need (ESP32 v3.3.10 for Windows)

These are the toolchain zip files the IDE needs. Only download the ones relevant to your board:

| File | Size | Needed for |
|------|------|------------|
| `riscv32-esp-elf-14.2.0_20260121-x86_64-w64-mingw32.zip` | ~673 MB | ESP32-S3, ESP32-C6, ESP32-C5, ESP32-P4 |
| `xtensa-esp-elf-14.2.0_20260121-x86_64-w64-mingw32.zip` | ~395 MB | ESP32, ESP32-S2, ESP32-S3 |
| `esp32c6-libs-3.3.10.zip` | ~63 MB | ESP32-C6 only |
| `esp32c5-libs-3.3.10.zip` | ~63 MB | ESP32-C5 only |
| `esp32c3-libs-3.3.10.zip` | ~53 MB | ESP32-C3 only |
| `esp32-libs-3.3.10.zip` | ~42 MB | Classic ESP32 only |

Total (all packages): ~1.3 GB. For YD-ESP32-23 (S3), the minimum is riscv32 (~673MB) + xtensa (~395MB) = ~1GB.

### Method 1: Download via phone VPN

1. Phone: enable VPN → open the GitHub download URLs in browser
2. Download the required zip files (takes a few minutes on mobile data)
3. Transfer to PC via WeChat File Transfer, QQ, USB cable, or cloud drive

### Method 2: Placeholder trick (for board-specific libs you don't need)

If only small board-specific libs fail (e.g., `esp32c6-libs-3.3.10.zip` for a S3 board), create empty zips:

```python
import zipfile
import os

staging = r'C:\Users\用户名\AppData\Local\Arduino15\staging\packages'
fake_files = [
    'esp32c6-libs-3.3.10.zip',
    'esp32c5-libs-3.3.10.zip',
]

for fname in fake_files:
    dst = os.path.join(staging, fname)
    if not os.path.exists(dst):
        with zipfile.ZipFile(dst, 'w') as zf:
            zf.writestr('placeholder.txt', 'placeholder')
        print(f"Created placeholder: {fname}")
```

⚠️ Only safe for board variants your chip doesn't need. The IDE will extract the zip and fail silently for those library variants, but your board's variant should still compile.

### After placing files

1. Verify they're in staging:
   ```bash
   python3 -c "import os; p=r'C:\Users\用户名\AppData\Local\Arduino15\staging\packages'; [print(f'{f} ({os.path.getsize(os.path.join(p,f))/1024/1024:.1f} MB)') for f in os.listdir(p)]"
   ```
2. Close and reopen Arduino IDE
3. Go to `Tools → Board → Boards Manager → search ESP32 → Install`
4. IDE detects local files, skips download, extracts and installs

## Post-install verification

Check that the package was actually extracted:

```bash
python3 -c "import os; p=r'C:\Users\用户名\AppData\Local\Arduino15\packages'; [print(os.path.join(r,d)) for r,ds,fs in os.walk(p) for d in ds if 'esp32' in d.lower() or 'esp' in d.lower()]"
```

If empty, the install didn't complete — IDE may still be downloading other packages.

## YD-ESP32-23 board: chip confirmed as ESP32-S3

esptool chip-id output from actual hardware:

```
Detecting chip type... ESP32-S3
Chip type:          ESP32-S3 (QFN56) (revision v0.2)
Features:           Wi-Fi, BT 5 (LE), Dual Core + LP Core, 240MHz, Embedded PSRAM 8MB (AP_3v3)
Crystal frequency:  40MHz
Flash:              16MB (quad, 3.3V)
```

In Arduino IDE, select: `Tools → Board → ESP32 Arduino → ESP32S3 Dev Module`
