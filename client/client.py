#!/usr/bin/env python

from typing import List, Dict

from threading import Thread, Event
import subprocess
import sys
import json
import time
from datetime import datetime
import requests

RTL_CMD : str = "rtl_433 -s 1M -R 172 -f 868M -F json"
UPLOAD_URL : str = "" #
API_KEY : str = "" # 

assert RTL_CMD != "", "Missing rtl_433 command"
assert UPLOAD_URL != "", "Missing upload URL"
assert API_KEY != "", "Missing API key"


DATA : Dict[str, int|float] = {}


class Uploader(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.stop_event = Event()


    def run(self):
        global DATA

        print("Starting Uploader thread...")

        while len(DATA) != len(Collector.REMOTE2LOCAL_FIELD) and not self.stop_event.is_set():
            self.stop_event.wait(timeout=1)


        while not self.stop_event.is_set():
            try:
                requests.post(UPLOAD_URL,
                    json = DATA,
                    headers = {
                        "X-Api-Key": API_KEY
                    }
                )
            except BaseException as e:
                print(e.with_traceback())

            self.stop_event.wait(timeout=60)

        print("Stopping Uploader thread...")


    def stop(self):
        self.stop_event.set()
        self.join()


class Collector(Thread):

    REMOTE2LOCAL_FIELD : Dict[str, str] = {
        "id": "broadcasted_station_id",
        "battery_ok": "battery",
        "time": "timestamp",

        "temperature_C": "temperature",

        "humidity": "humidity",

        "wind_avg_m_s": "wind_speed",
        "wind_dir_deg": "wind_dir",
        "wind_max_m_s": "wind_gust",

        "rain_mm": "rain",
    }


    def update_data(data : Dict[str, int|float|str]) -> None:
        global DATA

        for k, v in Collector.REMOTE2LOCAL_FIELD.items():
            if k in data:
                DATA[v] = data[k]


    def __init__(self, cmd):
        Thread.__init__(self)
        self.cmd : List[str] = cmd.split(" ")
        self.process : subprocess.Popen | None = None


    def stop(self):
        self.process.kill()
        self.process.wait()
        self.join()


    def run(self):
        global DATA

        print("Starting Collector thread...")

        self.process : subprocess.Popen = subprocess.Popen(
            self.cmd,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
        )

        for line in self.process.stdout:
            try:
                data = json.loads(line)

                if "time" in data:
                    data["time"] = int(datetime.strptime(data["time"], '%Y-%m-%d %H:%M:%S').timestamp()) # from 2025-10-05 19:55:21

                if "battery_ok" in data:
                    data["battery_ok"] = data["battery_ok"] == 1

                Collector.update_data(data)

                print(f"Got: {json.dumps(DATA)}")
            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"Got exception in Collector thread: {e}")

        print("Stopping Collector thread...")


if __name__ == "__main__":
    UPLOAD_THREAD = Uploader()
    COLLECTOR_THREAD = Collector(RTL_CMD)

    try:
        COLLECTOR_THREAD.start()
        UPLOAD_THREAD.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt as e:
        pass
    finally:
        print("Cleaning up...")

        COLLECTOR_THREAD.stop()
        UPLOAD_THREAD.stop()
        print("Quitting...")

        sys.exit(0)