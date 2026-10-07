from __future__ import annotations
from pathlib import Path
import ast, re, stat, zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
FAIL=[]

def check(cond, msg):
    if not cond: FAIL.append(msg)

def read(rel):
    f=ROOT/rel
    if not f.is_file():
        FAIL.append(f'missing:{rel}'); return ''
    return f.read_text(encoding='utf-8')

# Required architectural files.
required=[
 'build.sh','profiledef.sh','packages.x86_64','pacman.conf','README.md','V20_SPEC.md','PROJECT_STATUS.md',
 'airootfs/root/customize_airootfs.sh',
 'airootfs/usr/local/bin/novaos-center','airootfs/usr/local/bin/novaos-game-run','airootfs/usr/local/bin/novaos-gamehub',
 'airootfs/usr/local/bin/novaos-session-setup','airootfs/usr/local/bin/novaos-glass','airootfs/usr/local/bin/novaos-gamemode',
 'airootfs/usr/local/sbin/novaos-maint','airootfs/usr/local/sbin/novaos-account-db','airootfs/usr/local/sbin/novaos-antivirus',
 'airootfs/usr/local/sbin/novaos-auto-boost','airootfs/usr/local/sbin/novaos-diagnostics','airootfs/usr/local/sbin/novaos-memcheck','airootfs/usr/local/sbin/novaos-zram',
]
for r in required: check((ROOT/r).is_file(), f'missing:{r}')

# Package list sanity.
pkgs=[]
for line in read('packages.x86_64').splitlines():
    s=line.strip()
    if s and not s.startswith('#'): pkgs.append(s)
check(len(pkgs)==len(set(pkgs)), 'duplicate package entries')
for must in ['wine','wine-mono','wine-gecko','winetricks','gamemode','lib32-gamemode','lib32-mesa','zram-generator','earlyoom','intel-ucode','mesa','lib32-libva-intel-driver','libva-intel-driver','libva-utils','mesa-utils','xf86-video-intel','nm-connection-editor','mkinitcpio','mkinitcpio-archiso','syslinux','ttf-dejavu']:
    check(must in pkgs, f'package missing:{must}')

# Source security / safety scan. Do not ban ordinary shell in shell helpers, but GUI Python may not invoke shell=True/eval/os.system.
center=read('airootfs/usr/local/bin/novaos-center')
check('shell=True' not in center, 'center uses shell=True')
check('os.system' not in center, 'center uses os.system')
check('\neval(' not in center, 'center contains eval()')
maint=read('airootfs/usr/local/sbin/novaos-maint')
check('Unknown NovaOS maintenance action' in maint, 'maintenance helper lacks fixed dispatch guard')
check('case "$ACTION" in' in maint, 'maintenance helper missing action dispatch')

# Instant UI contract.
session=read('airootfs/usr/local/bin/novaos-session-setup')
xfwm=read('airootfs/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml')
check('pkill -x picom' in session, 'session setup does not force picom off')
check('GTK_ENABLE_ANIMATIONS=0' in session, 'GTK animation env not enforced')
check('use_compositing' in xfwm and 'value="false"' in xfwm, 'xfwm compositor default is not false')
check('gtk-enable-animations=false' in read('airootfs/etc/gtk-3.0/settings.ini'), 'GTK3 animations not disabled')
check('gtk-menu-popup-delay=0' in read('airootfs/etc/gtk-3.0/settings.ini'), 'GTK menu delay not zero')
scan_files=[ROOT/'build.sh', ROOT/'profiledef.sh', ROOT/'packages.x86_64', ROOT/'pacman.conf'] + [p for p in (ROOT/'airootfs').rglob('*') if p.is_file()]
all_text='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in scan_files)
check('novaos-visuals-daemon' not in all_text, 'legacy visual watcher reference remains')
check('wmctrl -lx' not in all_text, 'visual window polling remains')

# Game wiring.
for marker in ['WINEPREFIX','WINEDEBUG=-all','wineboot','gamemoderun','WineD3D']:
    check(marker in read('airootfs/usr/local/bin/novaos-game-run') or marker in read('README.md'), f'game marker missing:{marker}')
check('*.exe' in read('airootfs/usr/share/mime/packages/novaos-windows-games.xml'), 'exe MIME missing')
check('*.msi' in read('airootfs/usr/share/mime/packages/novaos-windows-games.xml'), 'msi MIME missing')
check('novaos-game-run %f' in read('airootfs/usr/share/applications/novaos-game-run.desktop'), 'game MIME desktop handler missing')

# No Debian/live-build runtime leakage.
for bad in ['/etc/apt/','/var/lib/dpkg/','live-boot','live-config','debootstrap','apt-get','dpkg -i','/usr/share/live/config']:
    check(bad not in all_text, f'Debian/live-build leakage:{bad}')

# XML parse.
for p in list((ROOT/'airootfs/etc').rglob('*.xml'))+list((ROOT/'airootfs/usr/share/mime/packages').rglob('*.xml')):
    try: ET.parse(p)
    except Exception as e: FAIL.append(f'XML:{p}:{e}')

# Python AST parse, including the extensionless GTK Center executable.
py_files=list((ROOT/'airootfs').rglob('*.py'))+[ROOT/'airootfs/usr/local/bin/novaos-center']
for p in py_files:
    try: ast.parse(p.read_text(encoding='utf-8'))
    except Exception as e: FAIL.append(f'PY:{p}:{e}')

# Executable paths.
for p in (ROOT/'airootfs').rglob('*'):
    if p.is_file() and p.stat().st_mode & stat.S_IXUSR:
        check(p.suffix in {'.sh','.py','.desktop','.service',''} or 'usr/local' in str(p), f'suspicious executable:{p.relative_to(ROOT)}')

# No credentials/signatures in source.
for p in ROOT.rglob('*'):
    if not p.is_file() or p.stat().st_size>2_000_000: continue
    try: txt=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    for pat in [r'AKIA[0-9A-Z]{16}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'ghp_[A-Za-z0-9]{20,}']:
        check(not re.search(pat,txt), f'suspicious-secret-pattern:{p}')


# ---- Regression checks for defects found in the V20 source review (build/boot blockers first) ----
# archiso hard requirement: mkinitcpio + mkinitcpio-archiso (docs: README.profile.rst, "packages.arch").
for must in ['mkinitcpio','mkinitcpio-archiso','syslinux']:
    check(must in pkgs, f'archiso requires package:{must}')
# Packages that make pacstrap fail: hard conflicts, or names that do not exist in the Arch repos.
for a,b in [('mesa-amber','mesa'),('lib32-mesa-amber','lib32-mesa')]:
    check(not (a in pkgs and b in pkgs), f'conflicting packages both listed:{a}+{b}')
for bad in ['mesa-vdpau','lib32-mesa-vdpau','clamav-freshclam']:   # VDPAU removed from Mesa 25.3; freshclam ships inside 'clamav' on Arch
    check(bad not in pkgs, f'package not available on Arch:{bad}')
# archiso >= 86: single bootmode names; old *.mbr/*.eltorito/uefi-x64.* names are deprecated.
pd=read('profiledef.sh')
check("'bios.syslinux'" in pd and "'uefi.systemd-boot'" in pd, 'profiledef bootmodes are not bios.syslinux + uefi.systemd-boot')
check(not re.search(r"bios\.syslinux\.(mbr|eltorito)|uefi-x64\.|uefi-ia32\.", pd), 'deprecated archiso bootmode names present')
check('file_permissions+=(' in pd, 'profiledef must append to releng file_permissions')
b=read('build.sh')
check('configs/releng' in b and 'NovaOS overrides' in b, 'build.sh does not merge releng profiledef')
check('*networkd*' in b, 'build.sh does not remove releng systemd-networkd (conflicts with NetworkManager)')
# mkarchiso resets airootfs modes to 644, so every script must be listed in file_permissions.
perm=set(re.findall(r'\["(/[^"]+)"\]="0:0:\d+"', pd))
for f in (ROOT/'airootfs').rglob('*'):
    if f.is_file() and f.read_bytes()[:2]==b'#!':
        check('/'+str(f.relative_to(ROOT/'airootfs')) in perm, f'script missing from file_permissions:{f.relative_to(ROOT)}')
# LightDM: lightdm.conf is read last and overrides lightdm.conf.d, so it must not pin autologin.
ld=read('airootfs/etc/lightdm/lightdm.conf')
check('autologin' not in ld, 'lightdm.conf pins autologin (overrides conf.d / novaos-maint)')
check('session-setup-script' not in ld, 'session-setup-script runs as root with the wrong $HOME')
check('autologin-user=nova' in read('airootfs/etc/lightdm/lightdm.conf.d/50-novaos-autologin.conf'), 'static autologin drop-in missing')
check('groupadd -r autologin' in read('airootfs/usr/local/sbin/novaos-user-setup'), 'autologin group not created (lightdm PAM needs it)')
check('autologin' in maint and 'gpasswd -a' in maint, 'novaos-maint autologin does not add the user to group autologin')
# Misc defects.
check('journal_mode=WAL' not in read('airootfs/usr/local/sbin/novaos-account-db'), 'accounts.db uses WAL (unprivileged readers fail)')
check('animations' not in read('airootfs/etc/picom.conf'), 'picom.conf has an invalid boolean animations option')
check('@import' in read('airootfs/usr/share/themes/NovaOS-Dark/gtk-3.0/gtk.css'), 'GTK theme has no base import (renders unstyled)')
check(not (ROOT/'airootfs/etc/earlyoom.conf').exists(), 'dead /etc/earlyoom.conf (Arch reads /etc/default/earlyoom; drop-in is authoritative)')
check('sudo -n /usr/local/sbin/novaos-maint antivirus-update' in read('airootfs/usr/local/sbin/novaos-antivirus'), 'novaos-antivirus update needs sudo for non-root')
check('--hold' in center, 'Center terminals close before the user can read output')
check('_wine' in center, 'Center must cache the Wine version (was spawned every 2 s)')
check('threading' in center and "'inxi'" in center, 'Center must run inxi off the UI thread')
gh=read('airootfs/usr/local/bin/novaos-gamehub')
check('novaos-game-run "$FILE" || true' in gh, 'gamehub must survive non-zero exit codes from games (set -e)')
check('x-ms-dos-executable' in read('airootfs/etc/xdg/mimeapps.list'), 'no default handler for .exe')
check('portable-executable' in read('airootfs/usr/share/applications/novaos-game-run.desktop'), 'game handler lacks current MIME alias for .exe')
check('df -Pk' in read('airootfs/usr/local/bin/novaos-game-run'), 'game runner has no free-space guard (live overlay is small)')

if FAIL:
    print(f'FAIL={len(FAIL)}')
    for x in FAIL: print('FAIL:',x)
    raise SystemExit(1)
print('STATIC_TESTS_PASS')
print('PACKAGE_COUNT',len(pkgs))
print('TEXT_FILES',sum(1 for p in ROOT.rglob('*') if p.is_file() and p.suffix in {'.sh','.py','.xml','.conf','.ini','.service','.desktop','.md'}))
print('TOTAL_FILES',sum(1 for p in ROOT.rglob('*') if p.is_file()))
