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

SINKS_TO_ID = None

WPCTL_TYPES = ["Audio", "Devices", "Sinks", "Sources", "Filters", "Streams"]



def main():
    ser = serial.Serial('/dev/serial/by-id/usb-FIREPHX_USB_SER_FX2348N-if00', 115200)
    time.sleep(2) 
    if not SINKS:
        map_sliders_to_channel_ids()
    while True:

        try:    
            line = ser.readline().decode().strip()

            print(line)

            slider, value = line.split(':')

            slider = int(slider)
            value = int(value)

            volume = round(value / 1023, 2)

            if slider in SINKS:
                set_volume(SINKS[slider], volume)
                print(f"Slider {slider} -> {volume}")
                
        except Exception as e:
            print(f"Error: {e}")


def set_volume(sink_id, volume):
    subprocess.run([
        "wpctl",
        "set-volume",
        sink_id,
        str(volume)
    ])

def get_channels():
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

    
def map_sliders_to_channel_ids():
    channels = get_channels()
    for slider_num, channel_name in SLIDER_TO_SINK_NAME.items():
        for channel_id, name in channels.items():
            if name == channel_name:
                SINKS[slider_num] = channel_id
                print(f"Mapped slider {slider_num} to channel ID {channel_id} for '{channel_name}'")
                break

    return

if __name__ == "__main__":
    main()


'''
 wpctl status

 Audio
 ├─ Devices:
 │      63. Radeon High Definition Audio Controller [alsa]
 │      67. Navi 31 HDMI/DP Audio               [alsa]
 │      68. Ryzen HD Audio Controller           [alsa]
 │      69. Razer Audio Mixer                   [alsa]
 │  
 ├─ Sinks:
 │      39. Game_Audio                          [vol: 0.10]
 │      41. Chat_Audio                          [vol: 0.32]
 │      42. Music_Audio                         [vol: 0.30]
 │  *   75. Razer Audio Mixer Analog Stereo     [vol: 1.00]
 │  
 ├─ Sources:
 │  *   76. Razer Audio Mixer Analog Stereo     [vol: 0.26]
 │  
 ├─ Filters:
 │  
 └─ Streams:

'''