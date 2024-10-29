import tuke_openlab
import pygame
from audio_analizer import AudioAnalyzer
from tuke_openlab.lights import Color
from bar import Bar


def get_controller():
    return tuke_openlab.Controller(tuke_openlab.simulation_env('os228mz'))


def get_lights():
    return [
        [i for i in range(70, 82)],
        [i for i in range(43, 55)],
        [i for i in range(16, 28)],

        list(reversed([i for i in range(55, 70)])),
        list(reversed([i for i in range(28, 43)])),
        list(reversed([i for i in range(1, 16)])),
    ]


def get_bars(color, controller, lights):
    return [
        # bass bars
        Bar(controller, lights[-1], {"start": 20, "stop": 60}, color),
        Bar(controller, lights[-2], {"start": 61, "stop": 250}, color),

        # heavy_area
        Bar(controller, lights[-3], {"start": 251, "stop": 500}, color),

        # low
        Bar(controller, lights[-4], {"start": 501, "stop": 2000}, color),

        # high
        Bar(controller, lights[-5],
            {"start": 2000, "stop": 4000}, color),
        Bar(controller, lights[-6], {"start": 4000, "stop": 6000}, color)
    ]


def play(bars, controller, a, file):
    a.load(file)
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()
    while True:

        for bar in bars:
            bar.update(a, pygame.mixer.music.get_pos() / 1000.0)

        if pygame.mixer.music.get_pos() / 1000.0 <= 0:
            break


def main(file: str):
    a = AudioAnalyzer()
    a.load(file)

    controller = get_controller()
    controller.lights.turn_off()
    lights = get_lights()

    # pulse(Color(r=255), controller)
    bars = get_bars(Color(w=255), controller, lights)

    pygame.mixer.init()
    play(bars, controller, a, file)
    controller.lights.turn_off()


if __name__ == "__main__":
    main('AC-DC - Thunderstruck.mp3')
