# The MIT License (MIT)
# Copyright (c) 2022 Mike Teachman
# https://opensource.org/licenses/MIT
#
# MicroPython Class used to control playing a WAV file using an I2S amplifier or DAC module
# - control playback with 5 methods:
#     - play()
#     - pause()
#     - resume()
#     - stop()
#     - isplaying()
# Example:
#    wp = WavPlayer(id=I2S_ID,
#                   sck_pin=Pin(SCK_PIN),
#                   ws_pin=Pin(WS_PIN),
#                   sd_pin=Pin(SD_PIN),
#                   ibuf=BUFFER_LENGTH_IN_BYTES)
#    wp.play("YOUR_WAV_FILE.wav", loop=True)
#
# All methods are non-blocking.
# The WAV file header is parsed in the play() method to get audio parameters



## Some code was modified to be used with rp2040

import struct
from time import sleep_us

from machine import Pin, PWM


class WavPlayer:
    """Play uncompressed 8-bit or 16-bit PCM WAV files through PWM."""

    PWM_FREQUENCY = 62_500
    PWM_SILENCE = 32_768
    BUFFER_SIZE = 512

    def __init__(self, audio_pin):
        self.audio = PWM(Pin(audio_pin))
        self.audio.freq(self.PWM_FREQUENCY)
        self.audio.duty_u16(self.PWM_SILENCE)
        self._stop_requested = False

    @staticmethod
    def _read_header(wav_file):
        if wav_file.read(4) != b"RIFF":
            raise ValueError("Not a RIFF WAV file")

        wav_file.read(4)
        if wav_file.read(4) != b"WAVE":
            raise ValueError("Not a WAVE file")

        wav_format = None

        while True:
            chunk_id = wav_file.read(4)
            chunk_size_bytes = wav_file.read(4)
            if len(chunk_id) != 4 or len(chunk_size_bytes) != 4:
                raise ValueError("WAV data chunk not found")

            chunk_size = struct.unpack("<I", chunk_size_bytes)[0]

            if chunk_id == b"fmt ":
                format_data = wav_file.read(chunk_size)
                if len(format_data) < 16:
                    raise ValueError("Invalid WAV format chunk")

                (
                    audio_format,
                    channels,
                    sample_rate,
                    _byte_rate,
                    _block_align,
                    bits_per_sample,
                ) = struct.unpack("<HHIIHH", format_data[:16])

                if audio_format != 1:
                    raise ValueError("Only uncompressed PCM WAV files are supported")
                if channels not in (1, 2):
                    raise ValueError("Only mono or stereo WAV files are supported")
                if bits_per_sample not in (8, 16):
                    raise ValueError("Only 8-bit or 16-bit WAV files are supported")

                wav_format = (sample_rate, bits_per_sample, channels)
            elif chunk_id == b"data":
                if wav_format is None:
                    raise ValueError("WAV format chunk missing")
                return wav_format + (chunk_size,)
            else:
                wav_file.seek(chunk_size, 1)

            # RIFF chunks are padded to an even byte boundary.
            if chunk_size & 1:
                wav_file.seek(1, 1)

    def _play_8_bit(self, data, channels, sample_delay_us):
        frame_size = channels
        for offset in range(0, len(data), frame_size):
            if self._stop_requested:
                return

            sample = data[offset]
            if channels == 2:
                sample = (sample + data[offset + 1]) // 2

            self.audio.duty_u16(sample * 257)
            sleep_us(sample_delay_us)

    def _play_16_bit(self, data, channels, sample_delay_us):
        frame_size = channels * 2
        for offset in range(0, len(data), frame_size):
            if self._stop_requested:
                return

            sample = struct.unpack("<h", data[offset : offset + 2])[0]
            if channels == 2:
                right = struct.unpack("<h", data[offset + 2 : offset + 4])[0]
                sample = (sample + right) // 2

            self.audio.duty_u16(sample + self.PWM_SILENCE)
            sleep_us(sample_delay_us)

    def play(self, filename):
        self._stop_requested = False

        try:
            with open(filename, "rb") as wav_file:
                sample_rate, bits_per_sample, channels, bytes_left = (
                    self._read_header(wav_file)
                )
                frame_size = channels * (bits_per_sample // 8)
                sample_delay_us = max(1, 1_000_000 // sample_rate)

                while bytes_left and not self._stop_requested:
                    read_size = min(self.BUFFER_SIZE, bytes_left)
                    read_size -= read_size % frame_size
                    if read_size == 0:
                        break

                    data = wav_file.read(read_size)
                    if len(data) < frame_size:
                        break

                    complete_size = len(data) - (len(data) % frame_size)
                    data = data[:complete_size]
                    bytes_left -= len(data)

                    if bits_per_sample == 8:
                        self._play_8_bit(data, channels, sample_delay_us)
                    else:
                        self._play_16_bit(data, channels, sample_delay_us)
        finally:
            self.audio.duty_u16(self.PWM_SILENCE)

    def stop(self):
        self._stop_requested = True
        self.audio.duty_u16(self.PWM_SILENCE)

    def deinit(self):
        self.stop()
        self.audio.deinit()
