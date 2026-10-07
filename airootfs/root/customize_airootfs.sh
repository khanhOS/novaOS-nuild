#!/usr/bin/env bash
# NOTE: archiso marks customize_airootfs.sh as deprecated (it still runs, with a warning).
# Anything that can be a static file in airootfs/ should live there instead.
set -euo pipefail

# locale
sed -i 's/^#\?en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/' /etc/locale.gen
sed -i 's/^#\?vi_VN.UTF-8 UTF-8$/vi_VN.UTF-8 UTF-8/' /etc/locale.gen
locale-gen >/dev/null 2>&1 || true

# Create live account and its metadata DB.
/usr/local/sbin/novaos-user-setup
/usr/local/sbin/novaos-account-db

# Group permissions are conditional because group names differ between package sets.
for g in video audio input storage network bluetooth; do
  getent group "$g" >/dev/null 2>&1 && usermod -aG "$g" nova || true
done

# Enable core services. These symlinks are standard systemd installation state.
systemctl enable NetworkManager.service
systemctl enable lightdm.service
systemctl enable novaos-account-db.service
systemctl enable earlyoom.service
systemctl enable novaos-auto-boost.timer
systemctl enable systemd-zram-setup@zram0.service 2>/dev/null || true

# FreshClam is deliberately not resident on the low-RAM live session.
systemctl mask clamav-freshclam.service >/dev/null 2>&1 || true

# MIME caches / desktop database.
update-mime-database /usr/share/mime >/dev/null 2>&1 || true
update-desktop-database /usr/share/applications >/dev/null 2>&1 || true

# Make directories for the live user's normal desktop workflow.
install -d -o nova -g nova /home/nova/Desktop /home/nova/Downloads /home/nova/Documents /home/nova/Pictures /home/nova/Videos /home/nova/.config
sudo -u nova xdg-user-dirs-update >/dev/null 2>&1 || true

# Configure Wine/GameMode defaults without starting them.
install -d -o nova -g nova /home/nova/.config
cat > /home/nova/.config/gamemode.ini <<'EOF'
[general]
renice=10
softrealtime=auto
gpu_performance_level=auto

[custom]
start=pkill -x picom || true
end=pkill -x picom || true
EOF
chown nova:nova /home/nova/.config/gamemode.ini

# Tighten a few idle-time settings without introducing desktop animation.
install -d -m 0755 /etc/modprobe.d
cat > /etc/modprobe.d/novaos-snd.conf <<'EOF'
# Keep ALSA power management conservative; do not force unsupported options.
EOF

# Verify the privileged helper does not accidentally become writable.
chmod 0755 /usr/local/sbin/novaos-maint /usr/local/sbin/novaos-account-db
chmod 0440 /etc/sudoers.d/20-novaos-helper
