import asyncio
import time as og_time
import adafruit_requests
import os
import wifi
import adafruit_connection_manager

from adafruit_datetime import date, datetime, time
from adafruit_magtag.magtag import MagTag

magtag = MagTag()
nametag_or_clock = False
day = 0

# Stuff that's too complex for my brain but is needed apparently:
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)

async def clock():
    global day
    while not nametag_or_clock:
        now = datetime.now()
        print(now)
        if day != now.day:
            magtag.set_text(f"{now.year}-{now.month}-{now.day}", 0)
        if now.minute < 10:
            magtag.set_text(f"{now.hour}:0{now.minute}", 1)
        else:
            magtag.set_text(f"{now.hour}:{now.minute}", 1)
        await asyncio.sleep(300)
        day = now.day

async def start_clock():
    magtag.remove_all_text()
    magtag.add_text(
        text_position=(
            10,
            20,
        ),
        text_scale=3,
    )

    magtag.add_text(
        text_position=(
            10,
            80,
        ),
        text_scale=9,
    )

    try:
        magtag.network.connect()
        magtag.get_local_time()
    except Exception as error:
        print(error)

    clock_task = asyncio.create_task(clock())
    await asyncio.gather(clock_task)

def nametag():
    magtag.remove_all_text()
    magtag.add_text(
        text_position=(
            5,
            20,
        ),
        text_scale=2,
    )

    magtag.add_text(
        text_position=(
            5,
            72,
        ),
        text_scale=6,
    )

    magtag.set_text("Hello, my name is:", 0)
    magtag.set_text("Carlisle", 1)

async def weather():
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    try:
        # Connect to the Wi-Fi network
        wifi.radio.connect(ssid, password)
    except OSError as e:
        print(f"❌ OSError: {e}")

    magtag.network.connect()
    weather_url = "https://api.open-meteo.com/v1/forecast?latitude=45.8207&longitude=-120.8217&temperature_unit=fahrenheit&timezone=auto&current=temperature,apparent_temperature"

    weather_response = requests.get(weather_url).json()
    try:
        temperature_unit = weather_response["current_units"]["temperature"]
        current_temp = weather_response["current"]["temperature"]
        apparent_temp = weather_response["current"]["apparent_temperature"]
    except (KeyError, TypeError):
        print("Something went wrong :(")
    print(f"Response: {weather_response}")
    magtag.remove_all_text()
    magtag.add_text(
        text_position=(
            30,
            60,
        ),
        text_scale=7,
    )
    magtag.set_text(f"{current_temp}{temperature_unit}", 0)

magtag.peripherals.neopixel_disable = True


async def listen_for_button_presses():
    global nametag_or_clock
    while True:
        if not magtag.peripherals.buttons[0].value:
            print("Button a pressed")
            if not magtag.peripherals.neopixel_disable:
                magtag.peripherals.neopixel_disable = True
                await asyncio.sleep(0.5)
            else:
                magtag.peripherals.neopixel_disable = False
                magtag.peripherals.neopixels.fill((240, 0, 255))
                await asyncio.sleep(0.5)

        elif not magtag.peripherals.buttons[2].value:
            print("Button c pressed")
            if nametag_or_clock:
                nametag_or_clock = not nametag_or_clock
                asyncio.run(start_clock())
            else:
                nametag_or_clock = not nametag_or_clock
                nametag()
        elif not magtag.peripherals.buttons[3].value:
            print("Button d pressed")
            magtag.refresh()

        await asyncio.sleep(0.05)


async def main():
    start_clock_task = asyncio.create_task(weather())
    listen_for_button_presses_task = asyncio.create_task(listen_for_button_presses())
    await asyncio.gather(start_clock_task, listen_for_button_presses_task)


asyncio.run(main())
