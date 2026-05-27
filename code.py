import time
import adafruit_datetime

from adafruit_magtag.magtag import MagTag

magtag = MagTag()

def nametag():
    magtag.remove_all_text()
    magtag.add_text(
        text_position=(
            5,
            20,
        ),
        text_scale = 2
    )

    magtag.add_text(
        text_position=(
            5,
            72,
        ),
        text_scale = 6,
    )

    magtag.set_text("Hello, my name is:", 0)
    magtag.set_text("Carlisle", 1)

def clock():
    magtag.remove_all_text()
    magtag.add_text(
        text_position=(
            5,
            72,
        ),
        text_scale = 6,
    )

    magtag.set_text("clock", 0)

clock()

nametag_or_clock = False
while True:
    if not magtag.peripherals.buttons[0].value:
        print("Button a pressed")
        magtag.peripherals.neopixel_disable = False
        magtag.peripherals.neopixels.fill((240, 0, 255))
        magtag.peripherals.play_tone(1318, 0.3)
    elif not magtag.peripherals.buttons[1].value:
        print("Button b pressed")
        magtag.peripherals.neopixel_disable = True
        magtag.peripherals.play_tone(900, 0.3)
    elif not magtag.peripherals.buttons[2].value:
        print("Button c pressed")
        if nametag_or_clock:
            nametag_or_clock = not nametag_or_clock
            nametag()
        else:
            nametag_or_clock = not nametag_or_clock
            clock()
