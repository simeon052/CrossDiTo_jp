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
