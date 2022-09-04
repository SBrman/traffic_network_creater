#! python3
from typing import Iterable

from Node import Node
from Link import Link


class Move:
    def __init__(self, in_link, out_link):
        if in_link.head != out_link.tail:
            raise ConnectionError(f"Links {in_link} and {out_link} are not connected by {in_link.head}")

        self.in_link: Link = in_link                # upstream link
        self.out_link: Link = out_link              # downstream link
        self.node: Node = self.in_link.head         # signal node
        self.active_green: float = 0                # just initializing here.
        self.mp_green: float = 0                    # Initializing here.
        self.numerator: float = 0
        self.denominator: float = 0

    def __eq__(self, other) -> bool:
        """Checks equality of two moves based on in and out links id and coordinates."""
        check_links_by_ids = self.in_link.id == other.in_link.id and self.out_link.id == other.out_link.id
        check_links_by_coordinates = self.in_link == other.in_link and self.out_link == other.out_link
        if check_links_by_ids or check_links_by_coordinates:
            return True
        else:
            return False

    def __repr__(self) -> str:
        return f"Move<N{self.in_link.tail.id}><N{self.in_link.head.id}><N{self.out_link.head.id}>"

    def __str__(self) -> str:
        return f"({self.in_link}, {self.out_link})"

    def __iter__(self) -> Iterable[Link]:
        yield self.in_link
        yield self.out_link

    def __len__(self):
        return 2

    def __hash__(self) -> int:
        """Hashing by tuple of coordinates of all three nodes of the move."""
        return hash((self.in_link.id, self.out_link.id))
