from time import sleep_ms, ticks_diff, ticks_ms

from machine import Pin

from wavplayer import WavPlayer


BUTTON_PIN = 26
AUDIO_PIN = 27

SINGLE_PRESS_SOUND = "single.wav"
DOUBLE_PRESS_SOUND = "double.wav"
DOUBLE_PRESS_WINDOW_MS = 350
DEBOUNCE_MS = 30

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
player = WavPlayer(AUDIO_PIN)


def wait_for_release():
    while button.value() == 0:
        sleep_ms(10)


def wait_for_press():
    while button.value() == 1:
        sleep_ms(5)

    sleep_ms(DEBOUNCE_MS)
    if button.value() != 0:
        return False

    wait_for_release()
    return True


def second_press_detected():
    started_at = ticks_ms()

    while ticks_diff(ticks_ms(), started_at) < DOUBLE_PRESS_WINDOW_MS:
        if button.value() == 0:
            sleep_ms(DEBOUNCE_MS)
            if button.value() == 0:
                wait_for_release()
                return True
        sleep_ms(5)

    return False


while True:
    if not wait_for_press():
        continue

    if second_press_detected():
        player.play(DOUBLE_PRESS_SOUND)
    else:
        player.play(SINGLE_PRESS_SOUND)
