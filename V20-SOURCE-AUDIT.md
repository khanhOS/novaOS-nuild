# NovaOS V20 source audit (review of 2026-10-07)

This is a **source-level** audit. It separates what was verified statically from what needs a real Arch build and real hardware. Nothing here claims the ISO builds or boots.

## Result of the review

The previous audit reported all-PASS, but its checks did not look at what `mkarchiso` actually requires. A review against archiso's documentation and the current Arch repositories found the defects below. All are fixed in this tree and covered by `tests/test_static.py` (the new tests fail on the previous tree: 33 failures).

### Would stop the ISO from building or booting

| # | Defect | Evidence | Fix |
|---|--------|----------|-----|
| 1 | `mkinitcpio-archiso` (and `syslinux` for BIOS) missing from `packages.x86_64` | archiso `README.profile.rst`: mkinitcpio and mkinitcpio-archiso are mandatory | added, plus `edk2-shell`, `memtest86+`, `memtest86+-efi` used by the releng boot entries |
| 2 | `mesa-amber` / `lib32-mesa-amber` listed together with `mesa` / `lib32-mesa` | Arch package pages: `mesa-amber` has `Conflicts: mesa` (frozen at 21.3.9) | removed; modern Mesa (crocus) covers Gen 4-7 Intel |
| 3 | `mesa-vdpau` listed | Mesa 25.3 removed VDPAU; the split package no longer exists | removed |
| 4 | `clamav-freshclam` listed | not an Arch package; `freshclam` ships inside `clamav` (file list checked) | removed |
| 5 | `novaos-user-setup` missing from `file_permissions` | archiso resets airootfs modes to 644; `customize_airootfs.sh` executes it | added; test now cross-checks every `#!` script |
| 6 | Deprecated boot modes (`bios.syslinux.mbr`, `uefi-x64.systemd-boot.esp`, ...) | archiso 86 changelog replaced them with `bios.syslinux` / `uefi.systemd-boot` | updated |
| 7 | Own `file_permissions` replaced releng's, so inherited scripts lost their exec bit | archiso docs on airootfs modes | `build.sh` now composes releng's `profiledef.sh` + NovaOS overrides (`file_permissions+=`) |

### Would break at runtime on the live system

- releng's systemd-networkd (DHCP on every NIC) ran alongside NetworkManager: `build.sh` now removes those units/configs, plus releng's sshd/cloud-init/mirror units.
- LightDM autologin: `lightdm.conf` is read last and overrode `lightdm.conf.d`, so `novaos-maint autologin on/off` had no effect; and Arch's autologin PAM needs the user in group `autologin`, which was never created. Both fixed; the autologin drop-in is now a static file. The root-run `session-setup-script` (wrong `$HOME`) was removed; the autostart entry already runs it as the user.
- No font package was listed (Vietnamese UTF-8 text needs one): added `ttf-dejavu`, `ttf-liberation`.
- `accounts.db` used SQLite WAL while being read by the unprivileged Center from a root-owned directory: switched to rollback journal, Center opens it read-only.
- `novaos-antivirus update` ran a root-only action without `sudo`; Center's "Scan Home" used `sudo` for a command not in sudoers and its terminals closed immediately (now `--hold`, scan runs as the user).
- `picom.conf` had `animations = false;` (a list option in picom 12): removed.
- NovaOS-Dark GTK3 theme contained only colour definitions, so GTK drew an unstyled UI: now imports Adwaita-dark first (see NOT TESTED).
- `/etc/earlyoom.conf` was a dead file (the systemd drop-in is authoritative): removed.
- Game Hub exited whenever Wine/a game returned non-zero (`set -e`): fixed. `.exe` association now includes the current `application/vnd.microsoft.portable-executable` type and a default `mimeapps.list`.
- Game runner now refuses to create a Wine prefix with < 1 GiB free (archiso's overlay is RAM-backed, 256 MiB by default) and says how to use `--prefix` on a disk.
- NovaOS Center spawned `wine --version` every 2 s, built all pages (including `inxi`) before showing the window and gave no feedback for maintenance actions: pages are lazy, Wine version cached, `inxi` runs in a thread, results of privileged actions are shown in a status line.
- `linux-headers` removed (not needed on a live image, adds weight).

### Findings that were checked and are NOT defects

CRLF line endings, the Thunar `uca.xml` element names, and the manifest hashes/modes were verified correct.

## Automated checks (`./scripts/audit-source.sh`)

`bash -n` on every shell file, `py_compile`, static test suite (incl. the regression checks above), XML parse, package uniqueness, legacy/Debian leakage scans, and a stubbed-GTK smoke test of NovaOS Center that builds all 12 pages. Result at the time of writing: **8 PASS / 0 FAIL / 4 NOT TESTED**.

Measured: 68 files (incl. the manifest), 37 directories, 115 package entries, 6 XML files, 7 desktop files.

## NOT TESTED (needs an Arch host and/or the target PC)

1. A real `mkarchiso` build. Package names were verified against Arch pages and docs, but only a build proves the full list resolves today.
2. BIOS and UEFI boot (HP Compaq Pro 6300 SFF / QEMU).
3. NovaOS Center and the NovaOS-Dark theme rendering on real GTK3 (the smoke test uses stubs and does not render).
4. That `systemd-networkd` pruning and the `autologin` group behave as expected on the final image.
5. Idle RAM, Intel HD acceleration, Wi-Fi/Bluetooth/audio, and real Windows game compatibility.

Known limitations that are design choices, not fixed here: `xf86-video-intel` is kept although the Arch wiki recommends the modesetting driver (test both on the target); `customize_airootfs.sh` is deprecated in archiso (still executed with a warning); root has an empty password and tty1 autologins as root (inherited from releng); the boot menu still carries Arch branding.
