"""
Demonstration of a Bluefruit BLE Central for Circuit Playground Bluefruit. Connects to the first BLE
UART peripheral it finds. Sends Bluefruit ColorPackets, read from three accelerometer axis, to the
peripheral.
"""

import time

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService


def scale(value):
    """Scale an value from  (acceleration range) to 0-255 (RGB range)"""
    value = abs(value)
    value = max(min(19.6, value), 0)
    return int(value / 19.6 * 255)


ble = BLERadio()

uart_connection = None
# See if any existing connections are providing UARTService.
if ble.connected:
    for connection in ble.connections:
        if UARTService in connection:
            uart_connection = connection
        break

finished = False
hasUART = False

while not finished:
    if not uart_connection:
        print("Scanning...")
        for adv in ble.start_scan(ProvideServicesAdvertisement, timeout=5):
            # if UARTService in adv.services:
            #     print("found a UARTService advertisement")
            #     uart_connection = ble.connect(adv)
            #     break
            print(adv)
            if adv.complete_name == 'TheIoTeamGlass':
                print("found TheIoTeamGlasses!")

                if UARTService in adv.services:
                    print("found a UARTService advertisement inside")
                    hasUART = True
                else:
                    print("didn't a UARTService advertisement inside")
                    hasUART = False

                support_services = adv.services
                uart_connection = ble.connect(adv)
                break
        # Stop scanning whether or not we are connected.
        ble.stop_scan()

    counter = 0

    while uart_connection and uart_connection.connected:
        # r, g, b = map(scale, accelerometer.acceleration)
        #
        # color = (r, g, b)
        # neopixels.fill(color)
        # color_packet = ColorPacket(color)
        # try:
        #     uart_connection[UARTService].write(color_packet.to_bytes())
        # except OSError:
        #     try:
        #         uart_connection.disconnect()
        #     except:  # pylint: disable=bare-except
        #         pass
        #     uart_connection = None

        # try:
        #     uart_connection[UARTService].read
        # except:
        #     print('some error happens...');
        #     pass

        print('counter = {0}'.format(counter))
        counter += 1

        if hasUART:
            uart_connection[UARTService].write(str.encode("Hello World {0}\n".format(counter)))

        if counter > 3:
            uart_connection.disconnect()
            finished = True
            break

        # do nothing
        time.sleep(1)
