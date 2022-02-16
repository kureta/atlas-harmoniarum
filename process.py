import numpy as np

scale_families = {
    # All proper scales have 12 transpositions
    'major': np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1]),
    'melodic_minor': np.array([1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1]),
    'harmonic_major': np.array([1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1]),
    'harmonic_minor': np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1]),
    # Harmonic modes of limited transposition
    'wholetone': np.array([1, 0]),  # 2 transpositions
    'octatonic': np.array([1, 0, 1]),  # 3 transpositions
    'augmented': np.array([1, 0, 0, 1]),  # 4 transpositions
}

default_locations = {
    'major': list(range(12)),
    'melodic_minor': list(range(12)),
    'harmonic_major': list(range(12)),
    'harmonic_minor': list(range(12)),
    'wholetone': list(range(2)),
    'octatonic': list(range(3)),
    'augmented': list(range(4)),
}

pc_to_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def to_binary(pitches, edo=12):
    if not pitches:
        return np.zeros(0)
    pitch_classes = sorted(list({n % edo for n in pitches}))

    binary = np.zeros(edo, dtype=int)
    binary[pitch_classes] = 1

    return binary


# Where a certain chord appears in a scale family
def _locate_chord(family, chord):
    locations = np.correlate(np.pad(family, (0, len(chord) - 1), 'wrap'), chord, mode='valid') == np.sum(chord)
    return list(np.sort((len(family) - np.argwhere(locations).flatten()) % len(family)))


# Where a chord appears in all scale families
def locate_chord(chord):
    if len(chord) == 0:
        return default_locations
    locations = {}
    for name, pcs in scale_families.items():
        locations[name] = _locate_chord(pcs, chord)
    return locations
