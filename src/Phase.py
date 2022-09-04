#! python3

from dataclasses import dataclass
from typing import Iterable

from Move import Move


@dataclass(frozen=True)
class Phase:
    node: int
    type: int
    seq: int
    red: int
    yellow: int
    green: int
    num_moves: int
    moves: set[Move]    # list(from_link -> to_link)

    @property
    def total_time(self) -> float:
        """Returns the total time for the phase"""
        return self.red + self.yellow + self.green

    def __len__(self):
        return self.num_moves

    def __repr__(self):
        return f"<Phase=({self.moves})"

    def __iter__(self) -> Iterable[Move]:
        for move in self.moves:
            yield move

    def __hash__(self):
        return hash((self.node, self.seq, self.green, len(self.moves)))