---
title: Installation
nav_order: 2
---

# Installation

## Supported Device

- Xteink X4 Pro

## Download the verified firmware

Download `CrossDiTo-x4-pro-v1.5.1.bin` from the [CrossDiTo 1.5.1 release](https://github.com/dito94/CrossDiTo/releases/tag/v1.5.1).

The verified application image is 6,137,264 bytes and has this SHA-256 checksum:

```text
be7afe4ea3e55bfbd46a7935715872b864a6df14ddc2f521918d2c69e3e65463
```

The release image was flashed to an X4 Pro and read back in full with an exact checksum match.

## SD Card Firmware Update

Use this method for an existing CrossDiTo installation. It also works when USB data transfer is unavailable.

1. Place the downloaded `CrossDiTo-x4-pro-v1.5.1.bin` file anywhere on the SD card.
2. Go to `Settings > System > SD Card Firmware Update`.
3. Select the `.bin` file and confirm the update.

## USB-locked devices

Use the SD Card Firmware Update method above. It does not require USB data access.

## Command Line

These instructions are for macOS and Linux. Windows users should use the web installer.

Install `esptool`:

```sh
pip3 install esptool
```

esptool v5 renamed its subcommands to hyphenated form (`write_flash` became
`write-flash`, `read_flash` became `read-flash`). The commands below use the v5
names; on esptool v4 and earlier, use the underscore spelling instead.

Download `CrossDiTo-x4-pro-v1.5.1.bin` from the [CrossDiTo releases page](https://github.com/dito94/CrossDiTo/releases), then connect the X4 Pro with USB-C.

Find the device port:

```sh
# Linux
dmesg | grep tty

# macOS
ls /dev/cu.*
```

Flash the firmware using the X4 Pro's `esp32s3` target:

```sh
# Linux
esptool --chip esp32s3 --port /dev/ttyACM0 --baud 921600 write-flash 0x10000 /path/to/CrossDiTo-x4-pro.bin

# macOS
esptool --chip esp32s3 --port /dev/cu.usbmodem2101 --baud 921600 write-flash 0x10000 /path/to/CrossDiTo-x4-pro.bin
```

Replace the port and firmware path with your actual values.

### If the device still boots the old firmware

`0x10000` is the `app0` slot. The device has two app slots and a small `otadata`
area that decides which one the bootloader starts. A unit that last took an
update over the air, or from the SD card, may be running from `app1` — and then
writing `app0` succeeds while changing nothing on screen.

Write both slots and it no longer matters which one is selected:

```sh
esptool --chip esp32s3 --port /dev/ttyACM0 --baud 921600 write-flash 0x10000 /path/to/CrossDiTo-x4-pro.bin 0x7f0000 /path/to/CrossDiTo-x4-pro.bin
```

`0x7f0000` is where `app1` sits on the stock X4 Pro partition table. **That table
is not the one in this repository's `partitions.csv`**, which places `app1` at
`0x650000` and gives the slots a different size. We never flash a partition
table, so what the device uses is whatever the factory wrote; `partitions.csv`
only bounds the build. Read the real table off a device before trusting either:

```sh
esptool --chip esp32s3 --port /dev/ttyACM0 read-flash 0x8000 0x1000 parttable.bin
```

To see which slot is selected, read `otadata` — the entry with the higher
`ota_seq` wins, and `(ota_seq - 1) % 2` is the slot number:

```sh
esptool --chip esp32s3 --port /dev/ttyACM0 read-flash 0xe000 0x2000 otadata.bin
```

### If the device boot-loops after flashing

A unit that shows nothing new on screen and ignores the power button is usually
stuck in a reset loop rather than bricked. Attach a serial terminal at 115200
and power-cycle; the ESP-IDF bootloader always prints, even on release builds
where the app's own serial log is disabled.

```sh
python -m serial.tools.miniterm /dev/ttyACM0 115200
```

A loop that looks like this is the 64KB-boundary landmine described in
[Build-time image check](#build-time-image-check) — the image is intact and
correctly written, but it cannot start:

```
entry 0x403c8870
E (941) cpu_start: Invalid app image header
abort() was called at PC 0x... on core 0
Rebooting...
```

**Recovery is over USB only.** The power + down-button route into the SD card
update screen lives inside the app, and a loop like this never reaches it.
Write a known-good release to both slots:

```sh
esptool --chip esp32s3 --port /dev/ttyACM0 --baud 460800 write-flash 0x10000 /path/to/good.bin 0x7f0000 /path/to/good.bin
```

Confirm `Hash of data verified.` appears twice. Do **not** run `erase-flash`:
it wipes the second-stage bootloader at `0x0` and the partition table at
`0x8000`, and this project ships neither, so the unit would stop responding to
anything but a factory image.

### Build-time image check

On the ESP32-S3 the flash rodata segment and PSRAM share one address region, so
ESP-IDF's linker script reserves room for rodata by skipping `SIZEOF(.flash.text)`
and rounding up to the MMU page size. The region starts at `0x3C000020` — 0x20
past a 64KB boundary — so when `.flash.text` lands in the last 0x20 bytes before
a boundary, the reservation comes up one MMU page short. Instruction and data
mappings share the page table, so the data mapping shifts by a page and the
image-header read during early startup fails. **The link and the build both
succeed; only a flashed device shows the problem.**

`scripts/check_image_mmu_split.py` compares the pages the instruction segment
needs against the pages reserved before rodata, and fails when they do not add
up. CI and the release workflow both run it, so an image that cannot boot never
reaches a release. Run it by hand against any locally built binary:

```sh
python scripts/check_image_mmu_split.py .pio/build/x4-pro/CrossDiTo-*.bin
```

When it fails, grow `crossditoMmuSplitPad` in `src/main.cpp` so `.flash.text`
crosses the boundary instead of stopping just short of it. Crossing it is what
buys headroom: the reservation then runs to the next page.
