import socket
import sys
import time
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QThread, Qt, pyqtSignal
import serial
import time
import subprocess
SINKS = {}

SLIDER_TO_SINK_NAME = {
    6: "Game_Audio",  # Game_Audio
    5: "Chat_Audio",  # Chat_Audio
    4: "Music_Audio",  # Music_Audio
    3: "Razer Audio Mixer Analog Stereo",  # Razer Audio Mixer Analog Stereo
    0: "Razer Audio Mixer Analog Stereo - mic"  # Razer Audio Mixer Analog Stereo (source) - > for mic volume
}

CURRENT_VOLUME = {}

SINKS_TO_ID = None

WPCTL_TYPES = ["Audio", "Devices", "Sinks", "Sources", "Filters", "Streams"]

APP = None

WINDOW = None

class BackgroundWorker(QThread):
    # Signal used to pass messages/data back to the main thread
    message_signal = pyqtSignal(str)

    def run(self):
        ser = serial.Serial('/dev/serial/by-id/usb-FIREPHX_USB_SER_FX2348N-if00', 115200)
        time.sleep(2) 
        if not SINKS:
            self.map_sliders_to_channel_ids()
        while True:
            try:    
                line = ser.readline().decode().strip()
                print(line)
                
                slider, value = line.split(':')
                slider = int(slider)
                value = int(value)
                volume = round(value / 1023, 2)       

                if slider in SINKS:
                    if slider not in CURRENT_VOLUME or (CURRENT_VOLUME[slider] > volume or CURRENT_VOLUME[slider] < volume):
                        CURRENT_VOLUME[slider] = volume
                        self.set_volume(SINKS[slider], volume)
                        self.message_signal.emit(f"{SLIDER_TO_SINK_NAME[slider]} : {volume:.0%}")

            except Exception as e:
                print(f"Error: {e}")


    def set_volume(self,sink_id, volume):
        subprocess.run([
            "wpctl",
            "set-volume",
            sink_id,
            str(volume)
        ])

    def get_channels(self):
        # Use wpctl to get the current channel IDs and names, then parse the output to create a mapping of channel name -> channel ID 
        # if the channel is a sink or source (indicated by [vol: in the line)
        result = subprocess.run(["wpctl", "status"], capture_output=True, text=True)
        lines = result.stdout.splitlines()

        channels = {}
        audio_type = "Sinks:"
        current_section = None

        for line in lines:
            line = line.strip()
            start_word = line.split(None, 1)
            if start_word and start_word[0] in WPCTL_TYPES:
                current_section = start_word[0]
            elif current_section in ["Audio"]:
                parts = line.split()
                if len(parts) >=2 and parts[1] == "Sources:":
                    audio_type = "Sources:"
                # Check line for `[vol:` to indicate that it is a sink/source  
                if len(parts) >= 2 and "[vol: " in line: 
                    if audio_type == "Sources:":
                        parts[-3] = parts[-3] + ' - mic'
                    if "*" in line:
                        channel_id = parts[2].rstrip('.')
                        channel_name = ' '.join(parts[3:-2])
                        channels[channel_id] = channel_name
                    else:
                        channel_id = parts[1].rstrip('.')
                        channel_name = ' '.join(parts[2:-2])
                        channels[channel_id] = channel_name

        return channels

        
    def map_sliders_to_channel_ids(self):
        # Restarts can change the channel IDs, so we need to dynamically map the sliders to the correct channel IDs on startup
        channels = self.get_channels()
        for slider_num, channel_name in SLIDER_TO_SINK_NAME.items():
            for channel_id, name in channels.items():
                if name == channel_name:
                    SINKS[slider_num] = channel_id
                    self.message_signal.emit(f"Mapped slider {slider_num} to channel ID {channel_id} for '{channel_name}'")
                    break

        return

class SystemTrayApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        # Prevents the app from closing when the tray is the only thing running
        APP.setQuitOnLastWindowClosed(False)

        # Create the tray icon
        scheme = APP.styleHints().colorScheme()

        if scheme == Qt.ColorScheme.Dark:
            self.tray_icon = QSystemTrayIcon(QIcon("/home/tmyers/Desktop/pyton/sound_mixer/light-bit-slider.png"))
        elif scheme == Qt.ColorScheme.Light:
            self.tray_icon = QSystemTrayIcon(QIcon("/home/tmyers/Desktop/pyton/sound_mixer/bit-slider.png"))

        self.tray_icon.setVisible(True)

        # Create Right-Click Menu
        menu = QMenu()

        # Open a terminal window that shows the logs from the background worker
        self.show_logs = QAction("Show Logs")
        self.show_logs.triggered.connect(self.start_log_terminal)
        menu.addAction(self.show_logs)

        self.quit_action = QAction("Quit")
        self.quit_action.triggered.connect(self.quit_app)
        menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(menu)

        # Start the mixer loop in a background thread
        self.worker = BackgroundWorker()
        self.worker.message_signal.connect(self.send_log_to_terminal)
        self.worker.start()

    def quit_app(self):
        self.worker.terminate() # Stop the loop thread
        APP.quit()

    def init_ui(self):
        self.setWindowTitle('Sound Mixer Logs')
        layout = QVBoxLayout()
        self.setLayout(layout)

    def start_log_terminal(self):
        # Spawns a new terminal window and runs the listener script in it
        if sys.platform == "win32":
            subprocess.Popen(['start', 'cmd', '/k', 'python', 'terminal_listener.py'], shell=True)
        elif sys.platform == "darwin": # macOS
            subprocess.Popen(['open', '-a', 'Terminal', 'terminal_listener.py'])
        else: # Linux
            subprocess.Popen(['konsole', '-e', 'python3 /home/tmyers/Desktop/pyton/sound_mixer/terminal_listener.py'])

    def send_log_to_terminal(self, message):
        # Send the log message 
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 9999))
                s.sendall(f"{message}\n".encode('utf-8'))
        except ConnectionRefusedError:
            pass

if __name__ == "__main__":
    APP = QApplication(sys.argv)
    WINDOW = SystemTrayApp()
    WINDOW.show()  # Show the main window (can be hidden if you only want the tray icon)
    WINDOW.hide()  # Start hidden since we're using the system tray <- but doesnt work?
    sys.exit(APP.exec())
