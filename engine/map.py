"""
2D grid map + safe zone management.
The map itself is just a coordinate space [0, size-1] x [0, size-1].
The zone is a rectangle that shrinks every ZONE_SHRINK_INTERVAL ticks.
"""
from __future__ import annotations
from dataclasses import dataclass
import random


@dataclass
class Zone:
    x1: int
    y1: int
    x2: int
    y2: int

    def contains(self, x: int, y: int) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def width(self) -> int:
        return self.x2 - self.x1 + 1

    def height(self) -> int:
        return self.y2 - self.y1 + 1

    def to_dict(self) -> dict:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}

    def shrink(self, amount: int = 1) -> None:
        """Shrink each border inward by `amount`, min size 3x3."""
        new_x1 = min(self.x1 + amount, self.x2 - 1)
        new_y1 = min(self.y1 + amount, self.y2 - 1)
        new_x2 = max(self.x2 - amount, new_x1 + 2)
        new_y2 = max(self.y2 - amount, new_y1 + 2)
        self.x1, self.y1, self.x2, self.y2 = new_x1, new_y1, new_x2, new_y2


class GameMap:
    def __init__(self, size: int, rng: random.Random):
        self.size = size
        self.rng = rng
        self.zone = Zone(0, 0, size - 1, size - 1)

    def random_position(self) -> tuple[int, int]:
        return (
            self.rng.randint(self.zone.x1, self.zone.x2),
            self.rng.randint(self.zone.y1, self.zone.y2),
        )

    def clamp(self, x: int, y: int) -> tuple[int, int]:
        """Keep coordinates inside the full map boundaries."""
        return max(0, min(self.size - 1, x)), max(0, min(self.size - 1, y))

    def spawn_positions(self, count: int) -> list[tuple[int, int]]:
        """Return `count` distinct spawn positions spread across the map."""
        positions: set[tuple[int, int]] = set()
        attempts = 0
        while len(positions) < count and attempts < count * 10:
            pos = self.random_position()
            positions.add(pos)
            attempts += 1
        # Fallback: fill remaining with grid positions
        if len(positions) < count:
            for x in range(self.size):
                for y in range(self.size):
                    positions.add((x, y))
                    if len(positions) >= count:
                        break
                if len(positions) >= count:
                    break
        return list(positions)[:count]
