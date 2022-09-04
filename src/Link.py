from dataclasses import dataclass
from Node import Node


@dataclass
class Link:
    id: int
    type: int           # 1000 if centroid_connector else 100
    tail: Node  # tail node
    head: Node  # head node
    length: float       # in ft
    ffspd: float        # in mph
    w: float            # in mph
    capacity: float
    num_lanes: int

    __unit = {"length": "ft", "ffspd": "mph", "w": "mph"}

    def __repr__(self):
        return f"<Link=({self.tail.id}, {self.head.id})>"

    # def __str__(self):
    #     return f"Link(id={self.id}, type={self.type}, i=<Node={self.tail.id}>, j=<Node={self.head.id}>, " \
    #             + f"length={self.length}, ffspd={self.ffspd}, w={self.w}, capacity={self.capacity}, " \
    #             + f"num_lanes={self.num_lanes}, centroid_connector={self.centroid_connector})"

    def __eq__(self, other):
        return True if self.tail == other.tail and self.head == other.head else False

    def __hash__(self):
        return hash((self.tail.x, self.tail.y, self.tail.z, self.head.x, self.head.y, self.head.z))

    def unit(self, attr):
        """Returns the type of attribute"""
        return self.__unit[attr] if attr in self.__unit else type(getattr(self, attr))

    @property
    def centroid_connector(self):
        return True if self.type == 1000 else False
