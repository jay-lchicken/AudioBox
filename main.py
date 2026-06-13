import struct
from time import sleep_ms,sleep_us, ticks_diff,ticks_ms
from machine import Pin, PWM


BUTTON_PIN=26
AUDIO_PIN = 27

SINGEL_PRESS_SOUND = "single.wav"
DOUBLE_PRESS_SOUND="double.wav"
DOUBLE_PRESS_WINDOw_MS = 350
DEBOUNCE_MS=30
PWM_SILENCE =32768

button=Pin(BUTTON_PIN,Pin.IN, Pin.PULL_UP)

audio = PWM(Pin(AUDIO_PIN))
audio.freq(62500)
audio.duty_u16(PWM_SILENCE)


def read_wav_hedar(wav_file):
  if wav_file.read(4) != b"RIFF":
      raise ValueError("Not WAV")

  wav_file.read(4)
  if wav_file.read(4)!=b"WAVE":
      raise ValueError("Not WAV")

  sample_rate=None
  bits_per_sample = None
  channles = None


  while True:
      chunk_id=wav_file.read(4)
      if len(chunk_id)<4:
          raise ValueError("No data chunk")

      chunk_size_bytes = wav_file.read(4)
      if len(chunk_size_bytes) < 4:
          raise ValueError("Invalid WAV chunk")

      chunk_size=struct.unpack("<I",chunk_size_bytes)[0]

      if chunk_id == b"fmt ":
          formatt_data = wav_file.read(chunk_size)
          if len(formatt_data)<16:
              raise ValueError("Invalid WAV format")

          audio_format,channles,sample_rate, _, _,bits_per_sample = (
              struct.unpack("<HHIIHH",formatt_data[:16])
          )
          if audio_format != 1:
              raise ValueError("Only PCM WAV supported")

      elif chunk_id==b"data":
          if sample_rate is None:
              raise ValueError("WAV format chunk missing")
          return sample_rate,bits_per_sample,channles,chunk_size
      else:
          wav_file.seek(chunk_size,1)


def play_8_bit_sampels(chunk, channles, sample_delay_us):
    if channles==1:
       for sampl in chunk:
          audio.duty_u16(sampl*257)
          sleep_us(sample_delay_us)
       return

    for i in range(0,len(chunk)-1,2):
       sampl=(chunk[i]+chunk[i+1])//2
       audio.duty_u16(sampl * 257)
       sleep_us(sample_delay_us)



def play_16_bit_samples(chunk,channles, sample_delay_us):
   frame_size=2 if channles == 1 else 4

   for i in range(0, len(chunk)-frame_size+1,frame_size):
      left=struct.unpack("<h",chunk[i:i+2])[0]
      sampl = left

      if channles==2:
         right = struct.unpack("<h",chunk[i+2:i+4])[0]
         sampl=(left+right)//2

      audio.duty_u16(sampl+PWM_SILENCE)
      sleep_us(sample_delay_us)


def play_wav(filename):
    try:
      with open(filename,"rb") as wav_file:
         sample_rate,bits_per_sample,channles,bytes_left=read_wav_hedar(wav_file)
         sample_deley_us=1_000_000//sample_rate

         while bytes_left:
            chunk=wav_file.read(min(512,bytes_left))
            if not chunk:
               break
            bytes_left -= len(chunk)

            if bits_per_sample==8:
               play_8_bit_sampels(chunk,channles,sample_deley_us)
            elif bits_per_sample == 16:
               play_16_bit_samples(chunk,channles,sample_deley_us)
            else:
               raise ValueError("Use 8-bit or 16-bit WAV")
    finally:
      audio.duty_u16(PWM_SILENCE)



def wait_for_relase():
   while button.value()==0:
       sleep_ms(10)


def wait_for_press():
    while button.value() == 1:
      sleep_ms(5)

    sleep_ms(DEBOUNCE_MS)

    if button.value()==0:
      wait_for_relase()
      return True
    return False


def secound_press_detected():
  started_at=ticks_ms()

  while ticks_diff(ticks_ms(),started_at)<DOUBLE_PRESS_WINDOw_MS:
     if button.value()==0:
        sleep_ms(DEBOUNCE_MS)
        if button.value() == 0:
           wait_for_relase()
           return True

     sleep_ms(5)

  return False



while True:
  if not wait_for_press():
     continue

  if secound_press_detected():
      play_wav(DOUBLE_PRESS_SOUND)
  else:
      play_wav(SINGEL_PRESS_SOUND)
