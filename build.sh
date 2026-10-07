#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="$ROOT/.archiso-profile"
WORK="$ROOT/work"
OUT="$ROOT/out"
need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing host command: $1" >&2; exit 2; }; }
for c in mkarchiso rsync sudo pacman; do need "$c"; done
[[ "$(id -u)" -ne 0 ]] || { echo "Run build.sh as a normal Arch user." >&2; exit 2; }
[[ -d /usr/share/archiso/configs/releng ]] || { echo "Install archiso: /usr/share/archiso/configs/releng is missing." >&2; exit 2; }
rm -rf "$PROFILE"
mkdir -p "$PROFILE"
RELENG=/usr/share/archiso/configs/releng
rsync -a --delete "$RELENG/" "$PROFILE/"
# profiledef: upstream releng first (keeps the modes it sets for its own files), NovaOS overrides after.
{ cat "$RELENG/profiledef.sh"; printf '\n# ---- NovaOS overrides ----\n'; sed '1{/^#!/d}' "$ROOT/profiledef.sh"; } > "$PROFILE/profiledef.sh"
cp "$ROOT/packages.x86_64" "$PROFILE/packages.x86_64"
cp "$ROOT/pacman.conf" "$PROFILE/pacman.conf"
rsync -a "$ROOT/airootfs/" "$PROFILE/airootfs/"
# releng enables systemd-networkd (DHCP on every NIC), which fights NetworkManager; it also ships
# sshd/cloud-init/mirror-selection units for an installer medium that NovaOS does not install.
find "$PROFILE/airootfs/etc/systemd" -depth \( -name '*networkd*' -o -name 'dbus-org.freedesktop.network1.service' \
  -o -name 'sshd*' -o -name 'cloud-init*' -o -name 'choose-mirror*' -o -name 'reflector*' \) -exec rm -rf {} \; 2>/dev/null || true
rm -rf "$PROFILE/airootfs/etc/systemd/network" "$PROFILE/airootfs/etc/ssh/sshd_config.d"
rm -rf "$OUT"
mkdir -p "$OUT"
sudo mkarchiso -v -r -w "$WORK" -o "$OUT" "$PROFILE"
ISO="$(find "$OUT" -maxdepth 1 -type f -name '*.iso' -print -quit)"
[[ -n "$ISO" ]] || { echo "No ISO generated." >&2; exit 1; }
sha256sum "$ISO" > "$ISO.sha256"
printf 'ISO=%s\nSHA256=' "$ISO"
cut -d' ' -f1 "$ISO.sha256"
printf '\n'
