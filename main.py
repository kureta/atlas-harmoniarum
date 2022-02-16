from ctypes import c_int8

import mido
import numpy as np
import pyglet

from process import default_locations, locate_chord, to_binary


def to_pyglet(x, y, w=640, h=480):
    transform = np.array([[h / 2, 0.], [0, h / 2]])
    coordinates = np.array([x, y])
    return coordinates @ transform + np.array([w / 2, h / 2])


class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fps_display = pyglet.window.FPSDisplay(window=self)

        self.label = pyglet.text.Label('Hello, world',
                                       font_name='Times New Roman',
                                       font_size=20,
                                       x=0, y=self.height,
                                       anchor_x='left', anchor_y='top',
                                       width=self.width,
                                       multiline=True)

        self.down_keys = set()
        self.pedal_state = c_int8(0)
        self.playing_keys = set()

        self.locations = default_locations

        self.circle = pyglet.shapes.Circle(
            *to_pyglet(0, 1, self.width, self.height),
            0.2 * self.height / 2)
        self.t = 0.

    def on_draw(self):
        self.clear()
        self.label.draw()
        self.circle.draw()
        self.fps_display.draw()

    def update(self, dt):
        text = []
        for family, locations in self.locations.items():
            if locations:
                text.append(f'{family}: {" ".join(str(n) for n in locations)}')

        n_scales = sum([len(pl) for pl in self.locations.values()])
        text.append('')
        text.append(f'n possibilities: {n_scales}')

        self.label.text = '\n'.join(text)
        w = 0.5
        self.t += dt
        x = np.sin(w * self.t)
        y = np.cos(w * self.t)
        self.circle.x, self.circle.y = to_pyglet(x, y, self.width, self.height)
        self.circle.color = (255, (x + 1) / 2 * 255, (y + 1) / 2 * 255)

    def on_midi_event(self, message):
        # Calculate which notes are currently played, factoring in the hold pedal.
        if message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0):
            self.down_keys.remove(message.note)
            if self.pedal_state.value == 0:
                self.playing_keys.remove(message.note)
        elif message.type == 'note_on' and message.velocity > 0:
            self.down_keys.add(message.note)
            self.playing_keys.add(message.note)
        elif message.type == 'control_change' and message.control == 64:
            self.pedal_state.value = message.value
            if self.pedal_state.value == 0:
                self.playing_keys.intersection_update(self.down_keys)

        # Process midi event
        binary = to_binary(self.playing_keys)
        self.locations = locate_chord(binary)


def main():
    window = Window(width=1920, height=1080, caption='Harmony Helper',
                    style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
    pyglet.clock.schedule_interval(window.update, 1 / 60.)
    with mido.open_input(mido.get_input_names()[2], callback=window.on_midi_event) as port:
        pyglet.app.run()


if __name__ == '__main__':
    main()
