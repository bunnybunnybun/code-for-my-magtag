import asyncio
import time as og_time
import adafruit_requests
import os
import wifi
import adafruit_connection_manager

from adafruit_datetime import date, datetime, time
from adafruit_magtag.magtag import MagTag

magtag = MagTag()
day = 0

# Stuff that's too complex for my brain but is needed apparently:
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)

async def clock():
    global day
    while True:
        now = datetime.now()
        print(now)
        if day != now.day:
            magtag.set_text(f"{now.year}-{now.month}-{now.day}", 0, auto_refresh=False)
        if now.minute < 10:
            magtag.set_text(f"{now.hour}:0{now.minute}", 1, auto_refresh=False)
        else:
            magtag.set_text(f"{now.hour}:{now.minute}", 1, auto_refresh=False)
        magtag.refresh()
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

async def nametag():
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

    magtag.set_text("Hello, my name is:", 0, auto_refresh=False)
    magtag.set_text("Carlisle", 1, auto_refresh=False)
    magtag.refresh()

async def weather():
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    try:
        wifi.radio.connect(ssid, password)
    except OSError as e:
        magtag.add_text(
            text_position=(
                10,
                30,
            ),
            text_scale=1,
        )
        magtag.set_text(f"Could not connect to wifi.\nError: {e}", 0)
        print(f"❌ OSError: {e}")

    magtag.network.connect()
    weather_url = "https://api.open-meteo.com/v1/forecast?latitude=45.8207&longitude=-120.8217&daily=temperature_2m_max,temperature_2m_min,cloud_cover_mean&current=temperature_2m,apparent_temperature&timezone=auto&forecast_days=3&wind_speed_unit=mph&temperature_unit=fahrenheit&precipitation_unit=inch"

    weather_response = requests.get(weather_url).json()
    try:
        temperature_unit = weather_response["current_units"]["temperature_2m"]
        current_temp = weather_response["current"]["temperature_2m"]
        current_apparent_temp = weather_response["current"]["apparent_temperature"]
        today_max_temp = weather_response["daily"]["temperature_2m_max"][0]
        today_min_temp = weather_response["daily"]["temperature_2m_min"][0]
    except (KeyError, TypeError):
        print("Something went wrong :(")
    print(f"Response: {weather_response}")
    magtag.remove_all_text()
    magtag.add_text(
        text_position=(
            15,
            35,
        ),
        text_scale=5,
    )
    magtag.add_text(
        text_position=(
            10,
            70,
        ),
        text_scale=2,
    )
    magtag.add_text(
        text_position=(
            210,
            20,
        ),
        text_scale=2,
    )
    magtag.add_text(
        text_position=(
            210,
            50,
        ),
        text_scale=2,
    )
    magtag.set_text(f"{current_temp}{temperature_unit}", 0, auto_refresh=False)
    magtag.set_text(f"Feels like {current_apparent_temp}{temperature_unit}", 1, auto_refresh=False)
    magtag.set_text(f"Max:{today_max_temp}",2, auto_refresh=False)
    magtag.set_text(f"Min:{today_min_temp}",3, auto_refresh=False)
    magtag.refresh()

magtag.peripherals.neopixel_disable = True

async def listen_for_button_presses():
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

        elif not magtag.peripherals.buttons[1].value:
            print("Button b pressed")
            weather_task = asyncio.create_task(weather())
            try:
                clock_task.cancel()
                print("Cancelled clock_task")
            except Exception as exception:
                print(f"Could not cancel clock_task because: {exception}")

        elif not magtag.peripherals.buttons[2].value:
            print("Button c pressed")
            await start_clock()
            try:
                clock_task.cancel()
                print("Cancelled clock_task")
            except Exception as exception:
                print(f"Could not cancel clock_task because: {exception}")
            clock_task = asyncio.create_task(clock())

        elif not magtag.peripherals.buttons[3].value:
            print("Button d pressed")
            nametag_task = asyncio.create_task(nametag())
            try:
                clock_task.cancel()
                print("Cancelled clock_task")
            except Exception as exception:
                print(f"Could not cancel clock_task because: {exception}")

        await asyncio.sleep(0.05)


async def main():
    weather_task = asyncio.create_task(weather())
    listen_for_button_presses_task = asyncio.create_task(listen_for_button_presses())
    await asyncio.gather(weather_task, listen_for_button_presses_task)


asyncio.run(main())
