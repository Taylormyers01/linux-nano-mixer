

```
[Unit]
Description=Linux Mixer Service
After=network.target

[Service]
ExecStart=/home/tmyers/Desktop/pyton/sound_mixer/.venv/bin/python /home/tmyers/Desktop/pyton/sound_mixer/sound_mixer_tray.py
Restart=no
WorkingDirectory=/home/tmyers/Desktop/pyton/sound_mixer


[Install]
WantedBy=default.target
```


```
sudo nano /etc/udev/rules.d/99-linux-mixer.rules


ACTION=="add", SUBSYSTEM=="tty", ENV{ID_SERIAL}=="FIREPHX_USB_SER_FX2348N", TAG+="systemd", ENV{SYSTEMD_USER_WANTS}+="linux_mixer.service"

ACTION=="remove", SUBSYSTEM=="tty", ENV{ID_SERIAL}=="FIREPHX_USB_SER_FX2348N", RUN+="/usr/bin/systemctl --user stop linux_mixer.service"



sudo udevadm control --reload-rules
sudo udevadm trigger
```