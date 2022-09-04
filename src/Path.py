from copy import deepcopy
from Node import Node
from Link import Link


class Path:
    def __init__(self, id: int, path: list[Link], proportion: float, num_links: int):

        assert len(path) == num_links, f"Error in path {id}: Path length = {len(path)} does not match number of links " \
                                       f"{num_links}. \n{path}"

        self.id: int = id
        self.proportion: float = proportion
        self._path: tuple[Link] = tuple(path)
        self.origin: Node = path[0].tail
        self.destination: Node = path[-1].head

    def __repr__(self):
        return f"Path <{self.id=}>"

    def __iter__(self):
        for upstream, downstream in zip(self._path[:-1], self._path[1:]):
            yield upstream, downstream

    def __getitem__(self, item: int):
        return self._path[item]

    def __hash__(self):
        return hash(self.id)

    def __len__(self):
        return len(self._path)

    def get_index(self, link: Link):
        """Returns the index of input link in path"""
        for i, edge in enumerate(self._path):
            if link.id == edge.id:
                return i
        return None
