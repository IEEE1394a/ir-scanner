import time
import utime
import ujson
import network
import ntptime
from machine import Pin
from dump import IR_DUMP
from Formatter import Formatter

class IrScanner:
    _IR_RECEIVER_PIN = 15

    def __init__(self):
        self._dump = None
        self._config = None

    def run(self):
        self._load_config()
        self._activate_wifi()
        self._load_time()
        self._dump = IR_DUMP(Pin(IrScanner._IR_RECEIVER_PIN, Pin.IN), self.receive_ir_signal)

        while True:
            try:
                time.sleep_ms(1000)
            except KeyboardInterrupt:
                break

    def receive_ir_signal(self, data, addr, ctrl):
        pass

    def _load_config(self):
        with open("../resources/config.json", "r") as f:
            self._config = ujson.load(f)

    def _activate_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        print("connect")
        wlan.connect(self._config["wlan"]["ssid"], self._config["wlan"]["password"])
        max_wait = 10
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)
        
        if wlan.status() != 3:
            raise RuntimeError('network connection failed')

    def _load_time(self):
        ntptime.settime()
        print("current time:", Formatter.format_localtime(utime.localtime()))
