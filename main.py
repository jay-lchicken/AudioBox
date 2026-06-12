from machine import Pin, PWM
from time import sleep_ms, sleep_us, ticks_ms, ticks_diff
import struct

BUTTON_PIN = 26
AUDIO_PIN = 27

SINGLE_WAV = "single.wav"
DOUBLE_WAV = "double.wav"

DOUBLE_PRESS_MS = 350

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

audio = PWM(Pin(AUDIO_PIN))
audio.freq(62500)
audio.duty_u16(32768)


def find_data_chunk(f):
    if f.read(4) != b"RIFF":
        raise ValueError("Not WAV")
    f.read(4)
    if f.read(4) != b"WAVE":
        raise ValueError("Not WAV")

    while True:
        chunk_id = f.read(4)
        if len(chunk_id) < 4:
            raise ValueError("No data chunk")

        chunk_size = struct.unpack("<I", f.read(4))[0]

        if chunk_id == b"fmt ":
            fmt = f.read(chunk_size)
            audio_format, channels, sample_rate, _, _, bits = struct.unpack("<HHIIHH", fmt[:16])
            if audio_format != 1:
                raise ValueError("Only PCM WAV supported")

        elif chunk_id == b"data":
            return sample_rate, bits, channels, chunk_size

        else:
            f.seek(chunk_size, 1)


def play_wav(filename):
    with open(filename, "rb") as f:
        sample_rate, bits, channels, data_size = find_data_chunk(f)

        delay = int(1_000_000 / sample_rate)
        remaining = data_size

        while remaining > 0:
            raw = f.read(min(512, remaining))
            remaining -= len(raw)

            if bits == 8:
                if channels == 1:
                    for s in raw:
                        audio.duty_u16(s * 257)
                        sleep_us(delay)
                else:
                    for i in range(0, len(raw) - 1, 2):
                        s = (raw[i] + raw[i + 1]) // 2
                        audio.duty_u16(s * 257)
                        sleep_us(delay)

            elif bits == 16:
                if channels == 1:
                    for i in range(0, len(raw) - 1, 2):
                        s = struct.unpack("<h", raw[i:i+2])[0]
                        audio.duty_u16(s + 32768)
                        sleep_us(delay)
                else:
                    for i in range(0, len(raw) - 3, 4):
                        l = struct.unpack("<h", raw[i:i+2])[0]
                        r = struct.unpack("<h", raw[i+2:i+4])[0]
                        s = ((l + r) // 2) + 32768
                        audio.duty_u16(s)
                        sleep_us(delay)
            else:
                raise ValueError("Use 8-bit or 16-bit WAV")

    audio.duty_u16(32768)


def wait_release():
    while button.value() == 0:
        sleep_ms(10)


def pressed_once():
    while button.value() == 1:
        sleep_ms(5)

    sleep_ms(30)

    if button.value() == 0:
        wait_release()
        return True

    return False


while True:
    if pressed_once():
        start = ticks_ms()
        double_pressed = False

        while ticks_diff(ticks_ms(), start) < DOUBLE_PRESS_MS:
            if button.value() == 0:
                sleep_ms(30)
                if button.value() == 0:
                    wait_release()
                    double_pressed = True
                    break

            sleep_ms(5)

        if double_pressed:
            play_wav(DOUBLE_WAV)
        else:
            play_wav(SINGLE_WAV)