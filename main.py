import mido
import numpy as np
import pyglet

from process import default_locations, locate_chord, scale_families


# From "origin at center, top = 1, bottom = -1,
# left and right are whatever the aspect ratio dictates" coordinates
def to_pyglet_coordinates(x, y, w, h):
    transform = np.array([[h / 2, 0.], [0, h / 2]])
    coordinates = np.array([x, y]).T
    return transform @ coordinates + np.array([w / 2, h / 2])


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


radii = {
    'major': 3,
    'melodic_minor': 2,
    'harmonic_major': 4,
    'harmonic_minor': 5,
    'wholetone': 1,
    'octatonic': 6,
    'augmented': 7,
}

short_names = {
    'major': 'M',
    'melodic_minor': 'm',
    'harmonic_major': 'H',
    'harmonic_minor': 'h',
    'wholetone': 'w',
    'octatonic': 'o',
    'augmented': 'a',
}


class Graph:
    def __init__(self, transform, offset, scale):
        graph_scale = 0.1
        graph_offset = 2.0
        graph_phase = 0.0

        centers = {}
        for name, value in scale_families.items():
            steps = len(value)
            base_r = radii[name]
            for idx in range(steps):
                centers[(name, idx)] = (
                    (graph_offset + base_r) * graph_scale * np.sin(2 * np.pi * ((idx * 7) % 12) / steps + graph_phase),
                    (graph_offset + base_r) * graph_scale * np.cos(2 * np.pi * ((idx * 7) % 12) / steps + graph_phase))

        self.batch = pyglet.graphics.Batch()
        self.labels_batch = pyglet.graphics.Batch()
        self.circles = {}
        self.labels = {}
        for (name, idx), coord in centers.items():
            coord = np.array(coord).T
            coord = transform @ coord + offset
            self.circles[(name, idx)] = pyglet.shapes.Circle(*coord, 0.04 * scale, batch=self.batch,
                                                             color=(255, 0, 25))
            self.labels[(name, idx)] = pyglet.text.Label(f'{short_names[name]} {idx}',
                                                         font_name='Times New Roman',
                                                         font_size=14,
                                                         x=coord[0], y=coord[1],
                                                         anchor_x='center', anchor_y='center',
                                                         batch=self.labels_batch)

    def draw(self):
        self.batch.draw()
        self.labels_batch.draw()

    def update(self, locations):
        for circle in self.circles.values():
            circle.color = (255, 0, 25)
        for key, locs in locations.items():
            for loc in locs:
                self.circles[(key, loc)].color = (0, 25, 255)


class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Transformation matrix from origin at center, unit size coordinates to pyglet coordinates
        self.transform = np.array([[self.height / 2, 0.], [0, self.height / 2]])
        # Center offset
        self.offset = np.array([self.width / 2, self.height / 2])
        # Scaling factor
        self.scale = self.height / 2

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

        self.graph = Graph(self.transform, self.offset, self.scale)

    def to_pyglet_coordinates(self, x, y):
        coordinates = np.array([x, y]).T
        return self.transform @ coordinates + self.offset

    def on_draw(self):
        self.clear()
        self.label.draw()
        self.graph.draw()
        self.fps_display.draw()

    def update(self, _dt):
        self.label.update_text(self.locations)
        self.graph.update(self.locations)

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
