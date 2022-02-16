import mido
import numpy as np
import pyglet

from process import default_locations, locate_chord


# From "origin at center, top = 1, bottom = -1,
# left and right are whatever the aspect ratio dictates" coordinates
def to_pyglet_coordinates(x, y, w, h):
    transform = np.array([[h / 2, 0.], [0, h / 2]])
    coordinates = np.array([x, y])
    return coordinates @ transform + np.array([w / 2, h / 2])


def to_piglet_length(r, h):
    return r * h / 2


class DebugLabel(pyglet.text.Label):
    def __init__(self, width, height, font_size=20):
        super().__init__('',
                         font_name='Times New Roman',
                         font_size=font_size,
                         x=0, y=height,
                         anchor_x='left', anchor_y='top',
                         width=width,
                         multiline=True)

    def update_text(self, locations):
        # Update debug text
        text = []
        for family, loc in locations.items():
            if len(loc) > 0:
                text.append(f'{family}: {" ".join(str(n) for n in loc)}')
            else:
                text.append(f'{family}: ')

        n_scales = sum([len(pl) for pl in locations.values()])
        text.append('')
        text.append(f'n possibilities: {n_scales}')
        self.text = '\n'.join(text)


class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show FPS for debugging purposes.
        self.fps_display = pyglet.window.FPSDisplay(window=self)

        # Show some parameters for debugging.
        self.label = DebugLabel(self.width, self.height)

        # State variables for calculating currently playing notes
        self.down_keys = np.zeros(12, dtype=int)
        self.pedal_state = np.zeros(1, dtype=int)
        self.playing_keys = np.zeros(12, dtype=int)

        # Location of currently played notes in all scale families, if they are contained.
        self.locations = default_locations

        # Just a test circle
        self.circle = pyglet.shapes.Circle(
            *to_pyglet_coordinates(0, 1, self.width, self.height),
            to_piglet_length(0.2, self.height))
        self.t = 0.

    def on_draw(self):
        self.clear()
        self.label.draw()
        self.circle.draw()
        self.fps_display.draw()

    def update(self, dt):
        self.label.update_text(self.locations)

        # Move circle
        w = 0.5
        self.t += dt
        x = np.sin(w * self.t)
        y = np.cos(w * self.t)
        self.circle.x, self.circle.y = to_pyglet_coordinates(x, y, self.width, self.height)
        self.circle.color = (255, (x + 1) / 2 * 255, (y + 1) / 2 * 255)

    def on_midi_event(self, message):
        # Calculate which notes are currently played, factoring in the hold pedal.
        if message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0):
            self.down_keys[message.note % 12] = 0
            if self.pedal_state[0] == 0:
                self.playing_keys[message.note % 12] = 0
        elif message.type == 'note_on' and message.velocity > 0:
            self.down_keys[message.note % 12] = 1
            self.playing_keys[message.note % 12] = 1
        elif message.type == 'control_change' and message.control == 64:
            self.pedal_state[0] = message.value
            if self.pedal_state[0] == 0:
                self.playing_keys[:] = self.down_keys[:]

        # Process midi event
        self.locations = locate_chord(self.playing_keys)


def main():
    config = pyglet.gl.Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True)
    window = Window(width=1920, height=1080, caption='Harmony Helper',
                    style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS,
                    config=config)
    pyglet.clock.schedule_interval(window.update, 1 / 60.)
    with mido.open_input(mido.get_input_names()[2], callback=window.on_midi_event) as port:
        pyglet.app.run()


if __name__ == '__main__':
    main()
