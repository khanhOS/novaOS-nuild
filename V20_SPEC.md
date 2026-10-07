# V20 specification

## Performance contract

1. No compositor at idle.
2. No animation launcher at login.
3. No Glass watcher or `wmctrl` polling daemon.
4. GTK3 and GTK4 animation settings disabled.
5. XFWM4 compositor disabled.
6. Menu popup delays are zero.
7. Thumbnails are disabled by default in Thunar.
8. zram uses LZ4.
9. earlyoom protects the display/session stack from accidental memory pressure termination.
10. Journald has strict size caps.

## Game contract

1. `.exe` and `.msi` can be opened through the Game Hub and MIME associations.
2. Every game gets a deterministic per-path Wine prefix unless an explicit prefix is selected.
3. `WINEDEBUG=-all` is the default for normal launches.
4. `gamemoderun` is used when installed.
5. Desktop compositor remains disabled during games.
6. WineD3D is the safe baseline for the old Intel target.
7. Vulkan/DXVK is not silently assumed.

## Security contract

The privileged helper has a finite action list. There is no “run arbitrary command” action. GUI code calls a fixed helper with validated parameters.

## Runtime boundary

A source audit proves source properties. It does not prove boot success, actual Intel driver behavior, actual RAM use, or game compatibility on a physical G2030 machine.
