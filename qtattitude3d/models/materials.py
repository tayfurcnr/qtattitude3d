from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Material:
    ambient: np.ndarray
    diffuse: np.ndarray
    specular: np.ndarray
    shininess: float = 1.0
    opacity: float = 1.0

    @classmethod
    def default(cls):
        return cls(
            ambient=np.array([0.2, 0.2, 0.2], dtype=np.float32),
            diffuse=np.array([0.8, 0.8, 0.8], dtype=np.float32),
            specular=np.array([0.0, 0.0, 0.0], dtype=np.float32),
            shininess=1.0,
            opacity=1.0,
        )

    def signature(self):
        return (
            tuple(np.round(self.ambient, 6)),
            tuple(np.round(self.diffuse, 6)),
            tuple(np.round(self.specular, 6)),
            round(float(self.shininess), 6),
            round(float(self.opacity), 6),
        )
