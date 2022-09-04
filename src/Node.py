from dataclasses import dataclass


class Node:
    def __init__(self, id, type, x, y, z):
        self.id: int = id
        self.type: int = type      # 1000 if centroid else 100
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.mp_installed = False

    def __repr__(self):
        return f"<Node={self.id}>"

    # def __str__(self):
    #     return f"Node(id={self.id}, type={self.type}, x={self.x}," \
    #            + f"y={self.y}, z={self.z}, centroid={self.centroid})"

    def __eq__(self, other) -> bool:
        for attr in ['x', 'y', 'z']:
            if getattr(self, attr) != getattr(other, attr):
                return False
        if self.id != other.id:
            return False
        return True

    def __hash__(self):
        # return hash(self.id)
        return hash((self.x, self.y, self.z))

    @property
    def centroid(self) -> bool:
        return True if self.type == 1000 else False

    @property
    def coordinates(self) -> tuple[float, float, float]:
        """Returns the tuple of x, y, z"""
        return self.x, self.y, self.z
