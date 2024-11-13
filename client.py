import json
import logging
import tempfile
import threading

import pygame.mixer
import tuke_openlab
from paho.mqtt.client import Client
from tuke_openlab.lights import Color

from audio_analizer import AudioAnalyzer
from bar import Bar
import ctypes


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AudioThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self):
        try:
            self._target(*self._args)
        finally:
            return

    def get_id(self):
        if hasattr(self, "_thread_id"):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def kill(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            thread_id, ctypes.py_object(SystemExit)
        )

        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print("Exception raiise failrule")


class AudioVisualizerClient:
    OPEN_LAB_AUDIO_TOPIC = "openlab/audio"

    def __init__(self, host: str, port: str, is_production: bool = True) -> None:
        self._host = host
        self._port = port
        self._id = "audio-visualizer"
        self._is_production = is_production

        self.controller = tuke_openlab.Controller(
            tuke_openlab.production_env()
            if is_production
            else tuke_openlab.simulation_env("os228mz")
        )
        self.controller.lights.turn_off()
        self.lights = self._get_lights()
        self.bars = self._get_bars(Color(w=255))

        self._topic = "openlab/audio-visualizer"

        self._client = Client(client_id=self._id)

        self._client.on_message = self.on_message
        # self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect

        self._client.connect(self._host)

        self._client.subscribe(self._topic)

    def main_loop(self) -> None:
        self._client.loop_forever()

    def on_message(self, client, userdata, message):
        logger.info(
            f"Received message from topic {message.topic}: {message.payload.decode()}"
        )
        data = json.loads(message.payload.decode())

        if data.get("play"):
            if data["play"] == "stop":
                pygame.mixer.music.stop()
                self._thread.join()
            self._thread = AudioThread(target=self.play, args=[data["play"]])
            self._thread.start()

    def on_connect(
        self, client, userdata, connect_flags, reason_code, properties
    ) -> None:
        logger.info("MQTT client connected")
        client.subscribe(self._topic)

    def on_disconnect(self) -> None:
        logger.info("MQTT client disconnected")

    def play(self, file_url: str) -> None:
        analizer = AudioAnalyzer()
        analizer.load(file_url)

        pygame.mixer.init()

        with tempfile.NamedTemporaryFile(
            suffix=f".{analizer.file_type}", delete=False
        ) as temp_file:
            analizer.file.seek(0)
            temp_file.write(analizer.file.read())
            temp_file_path = temp_file.name

        pygame.mixer.music.load(temp_file_path)
        pygame.mixer.music.set_volume(1)

        if self._is_production:
            self._client.publish(
                self.OPEN_LAB_AUDIO_TOPIC,
                json.dumps({"play": f"{file_url}"}),
            )

            pygame.mixer.music.set_volume(0)

        analizer.file.close()

        pygame.mixer.music.play()

        while True:
            for bar in self.bars:
                bar.update(analizer, pygame.mixer.music.get_pos() / 1000.0)

            if not pygame.mixer.music.get_busy():
                self.controller.lights.turn_off()
                break

        analizer.file.seek(0)
        del analizer
        pygame.mixer.music.stop()

    def _get_lights(self) -> list[list[int]]:
        return [
            [i for i in range(70, 82)],
            [i for i in range(43, 55)],
            [i for i in range(16, 28)],
            list(reversed([i for i in range(55, 70)])),
            list(reversed([i for i in range(28, 43)])),
            list(reversed([i for i in range(1, 16)])),
        ]

    def _get_bars(self, color: Color) -> list[Bar]:
        return [
            # bass bars
            Bar(self.controller, self.lights[-1], {"start": 20, "stop": 60}, color),
            Bar(self.controller, self.lights[-2], {"start": 61, "stop": 250}, color),
            # heavy_area
            Bar(self.controller, self.lights[-3], {"start": 251, "stop": 500}, color),
            # low
            Bar(self.controller, self.lights[-4], {"start": 501, "stop": 2000}, color),
            # high
            Bar(self.controller, self.lights[-5], {"start": 2000, "stop": 4000}, color),
            Bar(self.controller, self.lights[-6], {"start": 4000, "stop": 6000}, color),
        ]
