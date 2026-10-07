# NovaOS V20 “Sao Mai”

NovaOS V20 is a freshly structured Arch Linux + archiso + XFCE live desktop for low-end x86_64 hardware. It is designed around the actual constraints of the target class: 4 GB RAM, HDD storage, Intel integrated graphics, and a demand for a Windows/Zorin-like desktop that does not waste rendering work on cosmetic effects.

## V20 is a new source tree

This release is intentionally reconstructed as a new project tree. It is not a renamed V7/V10 archive and it does not depend on files copied from an older NovaOS ZIP at build time. The build script starts from the installed Archiso `releng` profile and overlays only the V20 source tree.

## Core design

- Arch Linux live ISO, x86_64.
- BIOS + UEFI boot targets.
- XFCE desktop.
- Live account `nova` with direct LightDM autologin.
- **Instant desktop defaults:** XFWM4 compositor off, Picom off, GTK animations off, menu delays set to zero, no visual polling daemon.
- Liquid Glass is strictly manual through `novaos-glass on` and is never started by an app watcher.
- zram + earlyoom + low-memory tuning.
- Windows `.exe` / `.msi` support through Wine.
- Game Hub with per-game prefixes, WineD3D default, Winetricks, Wine Mono/Gecko and GameMode integration.
- Intel/Mesa/VA-API stack, hardware diagnostics and storage diagnostics.
- ClamAV on-demand security scanner without a permanently running FreshClam updater.
- Real GTK3 NovaOS Center with live state and real commands.
- SQLite account metadata database; passwords are never written to it.

## Build

Build on an Arch Linux host with `archiso`, `rsync`, `sudo` and the normal Arch package repositories available.

```bash
./build.sh
```

The build script checks for the upstream Archiso releng profile, copies it into a temporary build profile, overlays V20, and invokes `mkarchiso`.

## Source audit

Run:

```bash
./scripts/audit-source.sh
```

This checks the complete V20 tree for shell/Python syntax, XML validity, duplicate package entries, suspicious paths, special files, executable permissions, Debian/live-build leakage, Windows-game wiring, zero-animation wiring, account database wiring and documentation consistency.

## Windows games

The baseline runner is Wine. It creates a separate Wine prefix per executable path:

```text
~/.local/share/novaos/wine-prefixes/<stable-id>/
```

Run directly:

```bash
novaos-game-run /path/to/Game.exe
novaos-game-run /path/to/installer.msi
```

The default graphics path is **WineD3D**, not DXVK. The target Pentium G2030/Intel HD class machine is not assumed to provide a suitable Vulkan implementation, so V20 does not make Vulkan a hidden prerequisite. `vkd3d` is installed for compatibility work, but it is not forced into every prefix.

GameMode is used temporarily when the game runner starts a game. Arch currently ships GameMode as a small daemon/library combination intended to apply temporary optimisations to game processes.

Wine, Wine Mono, Wine Gecko and Winetricks are current Arch packages; Wine is the Windows compatibility layer, while Winetricks installs common redistributable/runtime components.

## Reality check

This source package does **not** claim a successful physical boot, a measured idle RAM value, or guaranteed compatibility with every Windows game. Those need a real ISO build and boot test on the target machine.
