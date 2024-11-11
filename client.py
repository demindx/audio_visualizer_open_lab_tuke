import json
import logging
import tempfile

import pygame.mixer
import tuke_openlab
from paho.mqtt.client import Client
from tuke_openlab.lights import Color

from audio_analizer import AudioAnalyzer
from bar import Bar


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AudioVisualizerClient:
    def __init__(self, host: str, port: str, is_production: bool = True) -> None:
        self._host = host
        self._port = port
        self._id = "audio-visualizer"

        self.controller = tuke_openlab.Controller(
            tuke_openlab.production_env()
            if is_production
            else tuke_openlab.simulation_env("os228mz")
        )
        self.lights = self._get_lights()
        self.bars = self._get_bars(Color(w=255))

        self.analizer = AudioAnalyzer()

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
            self.play(data["play"])

    def on_connect(
        self, client, userdata, connect_flags, reason_code, properties
    ) -> None:
        logger.info("MQTT client connected")
        client.subscribe(self._topic)

    def on_disconnect(self) -> None:
        logger.info("MQTT client disconnected")

    def play(self, file_url: str) -> None:
        self.analizer.load(file_url)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            self.analizer.file.seek(0)
            temp_file.write(self.analizer.file.read())
            temp_file_path = temp_file.name

        pygame.mixer.init()
        pygame.mixer.music.load(temp_file_path)
        pygame.mixer.music.play()

        while True:
            for bar in self.bars:
                bar.update(self.analizer, pygame.mixer.music.get_pos() / 1000.0)

            if pygame.mixer.music.get_pos() / 1000.0 <= 0:
                break

        self.analizer.file.seek(0)
        pygame.mixer.music.stop()

    def _get_lights(self) -> list[list[int]]:
        return [
            [i for i in range(70, 82)],
            [i for i in range(43, 55)],
            [i for i in range(16, 28)],
            [i for i in range(55, 70)],
            [i for i in range(28, 43)],
            [i for i in range(16, 1)],
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
