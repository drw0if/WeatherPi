#!/usr/bin/env python

from typing import List, Dict

from threading import Thread, Event
import subprocess
import sys
import json
import time
from datetime import datetime
import os

import requests
import logging
from dotenv import load_dotenv

load_dotenv()

RTL_CMD: str | None =       os.getenv("RTL_CMD")
UPLOAD_URL: str | None =    os.getenv("UPLOAD_URL")
API_KEY: str | None =       os.getenv("API_KEY")


def _require(value: str | None, name: str) -> str:
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


RTL_CMD = _require(RTL_CMD, "RTL_CMD")
UPLOAD_URL = _require(UPLOAD_URL, "UPLOAD_URL")
API_KEY = _require(API_KEY, "API_KEY")


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger


DATA : Dict[str, int|float] = {}


class Uploader(Thread):

    def __init__(self, log):
        Thread.__init__(self)
        self.stop_event = Event()
        self.log = log


    def run(self):
        global DATA

        self.log.info("Starting Uploader thread...")

        while len(DATA) != len(Collector.REMOTE2LOCAL_FIELD) and not self.stop_event.is_set():
            self.stop_event.wait(timeout=1)


        while not self.stop_event.is_set():
            try:
                self.log.debug(f"Uploading: {json.dumps(DATA)}")
                r = requests.post(UPLOAD_URL,
                    json = DATA,
                    headers = {
                        "X-Api-Key": API_KEY
                    }
                )
                self.log.info(f"Result: {r.status_code} - {r.text}")
            except BaseException as e:
                tb = sys.exception().__traceback__
                self.log.error(e.with_traceback(tb))

            self.stop_event.wait(timeout=60)

        self.log.info("Stopping Uploader thread...")


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


    def __init__(self, log, cmd):
        Thread.__init__(self)
        self.log = log
        self.cmd : List[str] = cmd.split(" ")
        self.process : subprocess.Popen | None = None


    def stop(self):
        self.process.kill()
        self.process.wait()
        self.join()


    def run(self):
        global DATA

        self.log.info("Starting Collector thread...")

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

                self.log.debug(f"Got: {json.dumps(DATA)}")
            except json.JSONDecodeError:
                pass
            except BaseException as e:
                tb = sys.exception().__traceback__
                self.log.error(e.with_traceback(tb))

        self.log.info("Stopping Collector thread...")


if __name__ == "__main__":
    log = setup_logger("weather-pi")
    log.info("Service started")

    UPLOAD_THREAD = Uploader(log)
    COLLECTOR_THREAD = Collector(log, RTL_CMD)

    try:
        COLLECTOR_THREAD.start()
        UPLOAD_THREAD.start()

        while True:
            if not COLLECTOR_THREAD.is_alive():
                log.error("Collector thread quit")
                break

            if not UPLOAD_THREAD.is_alive():
                log.error("Upoad thread quit")
                break

            time.sleep(1)

    except KeyboardInterrupt as e:
        pass
    finally:
        log.info("Cleaning up...")

        if COLLECTOR_THREAD.is_alive():
            COLLECTOR_THREAD.stop()

        if UPLOAD_THREAD.is_alive():
            UPLOAD_THREAD.stop()

        log.info("Quitting...")

        sys.exit(0)