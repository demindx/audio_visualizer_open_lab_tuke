from tuke_openlab.lights import Color
from tuke_openlab import Controller


class Bar:
    def __init__(self, lights_controller: Controller,
                 controled_lights: list[int], freq: dict, color: Color,
                 max_decibel: int = 0, min_decibel: int = -80) -> None:

        self.controller = lights_controller
        self.main_color = color
        self.lights = controled_lights
        self.height = 0
        self.max_height = len(self.lights)
        self.min_decibel, self.max_decibel = min_decibel, max_decibel

        self.freq_rng = [i for i in range(freq['start'], freq['stop'])]

        self.__height_decibel_ratio = self.max_height / (
            self.max_decibel - self.min_decibel)

    def draw(self, old_height: int) -> None:
        if old_height > self.height:
            self.controller.lights.set_color(
                self.lights[self.height: old_height], Color(), 100
            )
        else:
            self.controller.lights.set_color(
                self.lights[0:self.height], self.main_color, 100)

    def update(self, analizer, time) -> None:
        avg = 0
        for i in self.freq_rng:
            avg += analizer.get_decibel(time, i)

        avg /= len(self.freq_rng)

        old_height = self.height
        self.height = int(avg * self.__height_decibel_ratio)
        self.draw(old_height)
