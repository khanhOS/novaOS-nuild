# NovaOS V20 status

## Release identity

- Name: NovaOS
- Codename: Sao Mai
- Version: 20.0
- Base: Arch Linux + Archiso + XFCE
- Architecture: x86_64
- Boot: BIOS + UEFI
- Default UI: instant/no-effects
- Windows app/game layer: Wine

## V20 acceptance rules

V20 is considered complete only when the full source tree is audited. A version string, a new ZIP name and a handful of edited files are not sufficient evidence of a new release.

## Runtime status at source-package creation

- Source audit: required and generated with the package.
- Arch ISO build: not performed in this environment.
- Physical boot on HP Compaq Pro 6300 SFF: not performed.
- Idle RAM measurement: not performed.
- Windows game compatibility benchmark: not performed.

## Defect review (2026-10-07)

A static review fixed 7 build/boot blockers and a set of runtime defects; see `V20-SOURCE-AUDIT.md`. The Arch ISO build, BIOS/UEFI boot and real-GTK rendering of NovaOS Center are still **NOT TESTED**.
