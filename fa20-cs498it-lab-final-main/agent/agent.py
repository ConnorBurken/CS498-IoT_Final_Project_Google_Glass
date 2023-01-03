import sys
import time
import websocket
import requests

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

host_url = "54.89.189.153:8080"
device_name = "TheIoTeamGlass"
ble = BLERadio()
ble_msg_chunk_size = 16
ble_pause_size = 64
ble_pause_time = 5
ble_msg_hard_stop = 64

uart_connection = None
finished = False
hasUART = False

message_queue = []

try:
    import thread
except ImportError:
    import _thread as thread


def on_message(ws, message):
    print("msg: " + message + "\n")

    global message_queue
    message_queue.append(message)

    # global uart_connection
    # if not uart_connection:
    #     try:
    #         uart_connection[UARTService].write(str.encode("Hello"))
    #     except:
    #         print("Unexpected error:", sys.exc_info()[0])


def on_error(ws, error):
    print(error)


def on_close(ws):
    global uart_connection
    if not uart_connection:
        uart_connection.disconnect()
        uart_connection = None

    print("exiting agent due to websocket close")


def on_open(ws):
    def run(*args):
        global uart_connection
        while True:
            cmd = input("outgoing msg/cmd: ")

            if cmd == 'exit':
                print('exiting agent...')
                if not uart_connection:
                    uart_connection.disconnect()
                    uart_connection = None
                break

            ws.send(cmd)
        # ws.close()
        # print("thread terminating...")

    thread.start_new_thread(run, ())


def start_ws_client():
    print('connecting to messaging server...')
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://{0}/client".format(host_url),
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()


if __name__ == "__main__":
    # TheIoTeamGlass
    print("Scanning for \"{0}\"...".format(device_name))

    if not uart_connection:
        for adv in ble.start_scan(ProvideServicesAdvertisement, timeout=5):
            print(adv)
            if adv.complete_name == 'TheIoTeamGlass':
                print("found TheIoTeamGlasses!")

                if UARTService in adv.services:
                    print("found a UARTService advertisement inside")
                    hasUART = True
                else:
                    print("didn't a UARTService advertisement inside")
                    raise Exception("device is not working properly")
                    hasUART = False

                support_services = adv.services
                uart_connection = ble.connect(adv)
                break

        ble.stop_scan()

    if not uart_connection:
        raise Exception("can't connect to target device")

    # message server
    reg_req = requests.post('http://{0}/reg'.format(host_url), json={"src": "test01",
                                                                     "topic": "test"})
    print('reg_req.status_code = {0}'.format(reg_req.status_code))
    thread.start_new_thread(start_ws_client, ())

    # start agent
    print('agent started!')
    uart_connection[UARTService].write(str.encode("Hello\n"))

    while uart_connection and uart_connection.connected:
        while len(message_queue) > 0:
            current_msg = message_queue.pop()

            # current_msg_chunks = []
            current_msg_pos = 0
            accumulate_msg_pos = 0

            if len(current_msg) >= ble_msg_hard_stop - 1:
                current_msg = current_msg[0:ble_msg_hard_stop - 1]

            print('sending message to device: {0}'.format(current_msg))

            while current_msg_pos < len(current_msg) - 1:
                current_msg_chunk = current_msg[current_msg_pos:current_msg_pos + ble_msg_chunk_size]
                # current_msg_chunks.append(current_msg_chunk)
                print('sending chunk: {0}'.format(current_msg_chunk))
                uart_connection[UARTService].write(str.encode(current_msg_chunk))
                current_msg_pos += ble_msg_chunk_size
                accumulate_msg_pos += ble_msg_chunk_size

                if accumulate_msg_pos > ble_pause_size:
                    accumulate_msg_pos -= ble_pause_size
                    time.sleep(ble_pause_time)

            uart_connection[UARTService].write(str.encode("\n"))

        time.sleep(1)
