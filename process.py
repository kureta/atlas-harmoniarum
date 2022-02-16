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
    'major': np.arange(12, dtype=int),
    'melodic_minor': np.arange(12, dtype=int),
    'harmonic_major': np.arange(12, dtype=int),
    'harmonic_minor': np.arange(12, dtype=int),
    'wholetone': np.arange(2, dtype=int),
    'octatonic': np.arange(3, dtype=int),
    'augmented': np.arange(4, dtype=int),
}

pc_to_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


# Where a certain chord appears in a scale family
def _locate_chord(family, chord):
    locations = np.correlate(np.pad(family, (0, len(chord) - 1), 'wrap'), chord, mode='valid') == np.sum(chord)
    return np.sort((len(family) - np.argwhere(locations).flatten()) % len(family))


# Where a chord appears in all scale families
def locate_chord(chord):
    if len(chord) == 0:
        return default_locations

    locations = {}
    for family, values in scale_families.items():
        locations[family] = _locate_chord(values, chord)
    return locations
