# Smoke test for novaos-center logic with a stubbed GTK (no display needed). It does NOT test rendering.
import sys, types, threading, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
from unittest.mock import MagicMock

class Widget(MagicMock): pass
class Window:
    def __init__(self, *a, **k): self._m = MagicMock()
    def __getattr__(self, n): return getattr(self.__dict__['_m'], n)
Gtk = MagicMock(); Gtk.Window = Window
GLib = MagicMock(); GLib.idle_add = lambda f, *a: f(*a)
repo = types.ModuleType('gi.repository'); repo.Gtk = Gtk; repo.GLib = GLib
gi = types.ModuleType('gi'); gi.require_version = lambda *a: None; gi.repository = repo
sys.modules.update({'gi': gi, 'gi.repository': repo})

ns = {'__name__': 'harness'}
exec(compile((ROOT/'airootfs/usr/local/bin/novaos-center').read_text(encoding='utf-8'), 'novaos-center', 'exec'), ns)
win = ns['win']
class Row:
    def __init__(s, n): s.n = n
    def get_name(s): return s.n
# stack.get_visible_child_name is a mock; make Home visible
win.__dict__['stack'] = MagicMock(); win.stack.get_visible_child_name.return_value = 'Home'
for key in ['Home','Performance','Appearance','Network','Games','Security','Accounts','Hardware','Startup','Storage','Maintenance','About']:
    win.select_page(None, Row(key)); print('built OK:', key)
time.sleep(0.5)
assert len(win.built) == 12, win.built
print('wine cached:', repr(win._wine))
n = len(win.built); win.select_page(None, Row('Home')); assert len(win.built) == n
# maint(): fake sudo missing -> must report an error via callback, not crash
win.maint('profile','low'); time.sleep(1.0)
assert win.refresh_home() is True
print('ns capture of missing tool ->', ns['capture'](['definitely-not-installed']))

print('CENTER_SMOKE_PASS')
