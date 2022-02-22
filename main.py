import argparse

import mido
import networkx as nx
import numpy as np
import pyglet

from process import connections, radii, scale_families, short_names


def build_graph():
    graph = nx.Graph()
    for name, pattern in scale_families.items():
        for step in range(len(pattern)):
            _pattern = np.roll(pattern, step)
            n_steps = len(pattern)
            graph.add_node((name, step), pattern=_pattern, n_steps=n_steps)

    for name, step in graph.nodes:
        lines = connections[name]
        for next_name, step_diff in lines:
            next_step = (step + step_diff) % len(graph.nodes[next_name, 0]['pattern'])
            graph.add_edge((name, step), (next_name, next_step))

    return graph


def has_chord(data, chord):
    # This return a float in [0, 1], not bool. For later use in decay or fuzzy matching/scoring.
    padded = np.pad(data['pattern'], (0, 12 - data['n_steps']), 'wrap')
    return (padded @ chord) == np.count_nonzero(chord)


def has_avoid_notes(data, chord):
    # are there notes in np.roll(chord, 1) in scale but not in chord
    avoid_notes = np.roll(chord, 1)
    avoid_notes = np.logical_and(avoid_notes, np.logical_not(chord))
    padded = np.pad(data['pattern'], (0, 12 - data['n_steps']), 'wrap')
    return avoid_notes @ padded > 0


class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # length scale from polar coordinates to pyglet coordinates
        self.scale = self.height / 2

        # Show FPS for debugging purposes.
        self.fps_display = pyglet.window.FPSDisplay(window=self)

        # State variables for calculating currently playing notes
        self.pedal_state = np.zeros(1, dtype=int)
        self.down_keys = np.zeros(12 * 12, dtype=int)
        self.playing_keys = np.zeros(12 * 12, dtype=int)
        self.playing_pitch_classes = np.zeros(12, dtype=int)
        self.changed = True

        # Graph of harmonic relationships
        self.graph = build_graph()

        # TODO: color decay time
        self.has_chord = (0, 0, 255)
        self.avoid = (255, 0, 0)
        self.other = (255, 255, 255)

        # Background
        bg_color = (100, 100, 100, 255)
        self.background = pyglet.image.SolidColorImagePattern(bg_color).create_image(self.width, self.height)

        # Circle layout
        self.circles_batch = pyglet.shapes.Batch()
        for (name, step), data in self.graph.nodes(data=True):
            x, y = self.from_polar_coordinates(radii[name] / 8,
                                               2 * np.pi * ((step * 7) % data['n_steps']) / data['n_steps'])
            r = 0.06 * self.scale
            data['circle'] = pyglet.shapes.Circle(x, y, r, batch=self.circles_batch)

        self.lines_batch = pyglet.shapes.Batch()
        for a, b, data in self.graph.edges(data=True):
            a = self.graph.nodes[a]['circle']
            b = self.graph.nodes[b]['circle']
            data['line'] = pyglet.shapes.Line(a.x, a.y, b.x, b.y, batch=self.lines_batch)

        self.labels_batch = pyglet.shapes.Batch()
        for (name, step), data in self.graph.nodes(data=True):
            a = data['circle']
            data['label'] = pyglet.text.Label(f'{short_names[name]} {step}',
                                              color=(0, 0, 0, 255),
                                              font_name='Noto Sans',
                                              font_size=14,
                                              x=a.x, y=a.y,
                                              anchor_x='center', anchor_y='center',
                                              batch=self.labels_batch)

    def from_polar_coordinates(self, r, theta):
        x = r * self.scale * np.sin(theta) + (self.width / 2)
        y = r * self.scale * np.cos(theta) + (self.height / 2)

        return x, y

    def on_draw(self):
        self.clear()
        self.background.blit(0, 0)
        self.lines_batch.draw()
        self.circles_batch.draw()
        self.labels_batch.draw()
        self.fps_display.draw()

    def update(self, _dt):
        if self.changed:
            self.changed = False
            for _, data in self.graph.nodes(data=True):
                shit = has_chord(data, self.playing_pitch_classes)
                if shit:
                    data['circle'].color = self.has_chord
                    avoid = has_avoid_notes(data, self.playing_pitch_classes)
                    if False:
                        data['circle'].color = self.avoid
                else:
                    data['circle'].color = self.other

    def on_midi_event(self, message):
        # TODO: pedal problem
        self.changed = True
        # Calculate which notes are currently played, factoring in the hold pedal.
        if message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0):
            self.down_keys[message.note] = 0
            if self.pedal_state[0] == 0:
                self.playing_keys[message.note] = 0
        elif message.type == 'note_on' and message.velocity > 0:
            self.down_keys[message.note] = 1
            self.playing_keys[message.note] = 1
        elif message.type == 'control_change' and message.control == 64:
            self.pedal_state[0] = message.value
            if self.pedal_state[0] == 0:
                self.playing_keys[:] = self.down_keys[:]

        self.playing_pitch_classes = np.any(self.playing_keys.reshape(12, 12), axis=0)


def main():
    parser = argparse.ArgumentParser(description='Atlas Harmoniarum')
    parser.add_argument('--index', type=int, help='MIDI input device number.')

    args = parser.parse_args()
    inputs = mido.get_input_names()
    if not args.index:
        for i, name in enumerate(inputs):
            print(f'[{i + 1}]: {name}')
        selected = None
        while not selected:
            try:
                index = int(input('Please enter MIDI input number:'))
                selected = inputs[index - 1]
            except (IndexError, ValueError):
                print('Invalid number!')
    else:
        selected = inputs[args.index - 1]

    config = pyglet.gl.Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True)
    window = Window(fullscreen=True, caption='Atlas Harmoniarum', config=config)
    pyglet.clock.schedule_interval(window.update, 1 / 60.)
    with mido.open_input(selected, callback=window.on_midi_event):
        pyglet.app.run()


if __name__ == '__main__':
    main()
