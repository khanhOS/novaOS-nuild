#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
PY="$(command -v python3 || command -v python)"

pass=0
fail=0
not_tested=0
ok(){ echo "PASS: $1"; pass=$((pass+1)); }
bad(){ echo "FAIL: $1"; fail=$((fail+1)); }
note(){ echo "NOT TESTED: $1"; not_tested=$((not_tested+1)); }

if bash -n build.sh && bash -n airootfs/root/customize_airootfs.sh && \
   for f in airootfs/usr/local/bin/novaos-session-setup airootfs/usr/local/bin/novaos-game-run airootfs/usr/local/bin/novaos-gamehub airootfs/usr/local/bin/novaos-gamemode airootfs/usr/local/bin/novaos-glass airootfs/usr/local/sbin/novaos-account-db airootfs/usr/local/sbin/novaos-antivirus airootfs/usr/local/sbin/novaos-auto-boost airootfs/usr/local/sbin/novaos-diagnostics airootfs/usr/local/sbin/novaos-maint airootfs/usr/local/sbin/novaos-memcheck airootfs/usr/local/sbin/novaos-user-setup airootfs/usr/local/sbin/novaos-zram; do bash -n "$f" || exit 1; done; then
  ok 'all NovaOS shell files: bash -n'
else
  bad 'shell syntax'
fi

if "$PY" -m compileall -q tests airootfs/usr/local/sbin && "$PY" -m py_compile airootfs/usr/local/bin/novaos-center; then
  ok 'Python compile/py_compile'
else
  bad 'Python syntax'
fi

if "$PY" tests/test_static.py; then
  ok 'project static test suite'
else
  bad 'project static test suite'
fi

if "$PY" - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path('airootfs')
xs=list((root/'etc').rglob('*.xml'))+list((root/'usr/share/mime/packages').rglob('*.xml'))
for p in xs: ET.parse(p)
print('XML_COUNT='+str(len(xs)))
PY
then
  ok 'XML parse'
else
  bad 'XML parse'
fi

if "$PY" - <<'PY'
from pathlib import Path
p=[]
for line in Path('packages.x86_64').read_text().splitlines():
    s=line.strip()
    if s and not s.startswith('#'): p.append(s)
assert len(p)==len(set(p))
print('PACKAGE_COUNT='+str(len(p)))
PY
then
  ok 'package uniqueness'
else
  bad 'package uniqueness'
fi

if ! grep -RInE 'novaos-visuals-daemon|wmctrl -lx|sleep 3' --exclude-dir=.git airootfs build.sh profiledef.sh packages.x86_64 pacman.conf >/tmp/novaos-v20-stale.txt; then
  ok 'no legacy visual watcher/polling code'
else
  cat /tmp/novaos-v20-stale.txt
  bad 'legacy visual watcher/polling code found'
fi

if ! grep -RInE '/etc/apt/|/var/lib/dpkg/|debootstrap|live-boot|live-config|apt-get|dpkg -i|/usr/share/live/config' --exclude-dir=.git airootfs build.sh profiledef.sh packages.x86_64 pacman.conf >/tmp/novaos-v20-debian.txt; then
  ok 'no Debian/live-build runtime leakage'
else
  cat /tmp/novaos-v20-debian.txt
  bad 'Debian/live-build runtime leakage found'
fi

if "$PY" tests/test_center_smoke.py >/dev/null; then
  ok 'NovaOS Center logic smoke test (stubbed GTK, all 12 pages)'
else
  bad 'NovaOS Center logic smoke test'
fi

note 'NovaOS Center / NovaOS-Dark theme rendering on a real GTK3 session is not tested (no GTK typelib in the audit environment).'
note 'Archiso ISO build in this non-Arch environment is not performed by this audit.'
note 'Physical boot, Pentium G2030 Intel HD graphics, Wi-Fi/Bluetooth/audio and real idle-RAM measurement require target hardware.'
note 'Windows game compatibility requires installing and actually running individual games; source files only prove runner wiring.'

printf '\nSUMMARY PASS=%d FAIL=%d NOT_TESTED=%d\n' "$pass" "$fail" "$not_tested"
[[ "$fail" -eq 0 ]]
