import numpy as np

scale_families = {
    # All proper scales have 12 transpositions
    'major': np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], dtype=int),
    'melodic_minor': np.array([1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1], dtype=int),
    'harmonic_major': np.array([1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1], dtype=int),
    'harmonic_minor': np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1], dtype=int),
    # Harmonic modes of limited transposition
    'wholetone': np.array([1, 0], dtype=int),  # 2 transpositions
    'octatonic': np.array([1, 0, 1], dtype=int),  # 3 transpositions
    'augmented': np.array([1, 0, 0, 1], dtype=int),  # 4 transpositions
}

radii = {
    'major': 3,
    'melodic_minor': 2,
    'harmonic_major': 4,
    'harmonic_minor': 5,
    'wholetone': 1,
    'octatonic': 6,
    'augmented': 7,
}
connections = {
    'major': [('major', 7), ('melodic_minor', 2), ('harmonic_minor', 9)],
    'melodic_minor': [('major', 0), ('harmonic_major', 7), ('octatonic', 0), ('wholetone', 1)],
    'harmonic_major': [('major', 0), ('octatonic', 1), ('augmented', 0)],
    'harmonic_minor': [('melodic_minor', 0), ('harmonic_major', 0), ('octatonic', 0), ('augmented', 0)],
    'wholetone': [],
    'octatonic': [],
    'augmented': []
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
