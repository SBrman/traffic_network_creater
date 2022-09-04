#! python3

import os
import logging
from copy import deepcopy
from typing import Iterable, Any, Union
from ast import literal_eval

from Node import Node
from Link import Link
from Move import Move
from Phase import Phase
from Path import Path

OD = tuple[Node, Node]


logging.disable(logging.CRITICAL)
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


class Graph:
    def __init__(self, path, name="Untitled"):

        self.dir_path: str = os.path.abspath(path)
        self.name: str = name

        self._nodes: dict[int, Node] = self.__load_nodes()                                              # Nodes
        self._zones: dict[int, Node] = {node.id: node for node in self.nodes if node.centroid}          # Zones
        self._links: dict[int, Link] = self.__load_links()

        self._centroid_connectors: dict[int, Link] = {link.id: link for link in self.links if link.centroid_connector}
        self._entry_links: dict[int, Link] = self.__load_entry_links(self.centroid_connectors)
        self._exit_links: dict[int, Link] = self.__load_exit_links(self.centroid_connectors)

        self.internal_links: set[Link] = self.links - self.entry_links - self.exit_links
        self._internal_links: dict[int, Link] = {link.id: link for link in self.internal_links}
        # self.N, self.Z, self.A, self.AZ  etc are created when required. Read __getattr__ method.

        self.origins: dict[int, Node] = {link.tail.id: link.tail for link in self.entry_links if link.tail.centroid}
        self.destinations: dict[int, Node] = {link.head.id: link.head for link in self.exit_links if link.head.centroid}

        self.demand: dict[tuple[Node, Node], float] = self.__load_demands()
        self.phases: dict[int, dict[int, Phase]] = self.__load_phases()  # dict[node_id, dict[seq, Phase]]

        self._signal_nodes: dict[int, Node] = self.__load_signal_nodes()

        self.exogenous_demands: dict[Link, float]
        self.exogenous_demands, self.paths = self.__load_exogenous_demands_and_paths()

        self.turn_proportions: dict[tuple[Link, Link], float] = self.load_turn_proportions(demand_scaler=1)

        # self.exogenous_demands = {k: v * demand_scaler for k, v in self.exogenous_demands.items()}

    def __repr__(self):
        return f"<Graph of {self.name}>"

    def __getattr__(self, attr):
        """
        If any attribute is not initialized then attribute will be set to set(_attribute.values()) and returned.
        Failing would raise AttributeError
        """
        if attr in self.__dict__:
            return self.__dict__[attr]                           # if attribute is already present return attribute
        elif f"_{attr}" in self.__dict__:
            setattr(self, attr, set(self.__dict__[f"_{attr}"].values()))

        return self.__dict__[attr]

    def __getitem__(self, ij: tuple[Any, Any]) -> Link:
        """Returns the link from the nodes"""

        if '__A' not in self.__dict__:
            self.__A: dict[tuple[int, int], Link] = {(link.tail.id, link.head.id): link for link in self.links}

        i, j = ij
        if type(i) == type(j) == int:
            return self.__A[(i, j)]
        elif type(i) == type(j) == Node:
            return self.__A[(i.id, j.id)]
        else:
            raise TypeError

    def __load_nodes(self) -> dict[int, Node]:
        """Returns the nodes loaded from nodes.txt in the given dir_path."""
        nodes_dir = os.path.join(self.dir_path, "nodes.txt")

        nodes_data = {}
        with open(nodes_dir) as nodes_file:
            next(nodes_file)
            for line in nodes_file:
                # node, type_, x, y, z = line.split()
                node = Node(*[literal_eval(arg) for arg in line.split()])
                nodes_data[node.id] = node
        return nodes_data

    def __load_links(self) -> dict[int, Link]:
        """Returns the links loaded from the links.txt in the given dir_path."""
        link_dir = os.path.join(self.dir_path, "links.txt")

        links_data = {}
        with open(link_dir) as links_file:
            next(links_file)
            for line in links_file:
                # link, type_, source, dest, length, ffspd, w, capacity, num_lanes = line.split()
                link_id, type_, i, j, *other_args = [literal_eval(arg) for arg in line.split()]
                node_i, node_j = [self._zones.get(node, self._nodes[node]) for node in [i, j]]
                links_data[link_id] = Link(link_id, type_, node_i, node_j, *other_args)
        return links_data

    @staticmethod
    def __load_entry_links(links: set[Link]) -> dict[int, Link]:
        return {link.id: link for link in links if link.tail.centroid}

    @staticmethod
    def __load_exit_links(links: set[Link]) -> dict[int, Link]:
        return {link.id: link for link in links if link.head.centroid}

    def __load_demands(self) -> dict[tuple[Node, Node], float]:
        """Returns the zone nodes and the od demand (demand/hour)."""
        static_od_dir = os.path.join(self.dir_path, "static_od.txt")

        static_od_data = {}
        with open(static_od_dir) as static_od_file:
            next(static_od_file)
            for line in static_od_file:
                *_, origin, destination, demand = [literal_eval(arg) for arg in line.split()]
                r, s = self._zones[origin], self._zones[destination]
                static_od_data.setdefault((r, s), 0)
                static_od_data[(r, s)] += float(demand)
        return static_od_data

    def __load_phases(self) -> dict[int, dict[int, Phase]]:
        """Returns the phases"""
        phase_dir = os.path.join(self.dir_path, "phases.txt")

        all_phases = {}
        with open(phase_dir) as phases:
            next(phases)
            for line in phases:
                *others, link_from, link_to = line.split()
                node_id, type_, seq, red, yellow, green, num_moves = [int(val) for val in others]
                link_from = literal_eval(link_from.replace('{', '[').replace('}', ']'))
                link_to = literal_eval(link_to.replace('{', '[').replace('}', ']'))
                moves: set[Move] = {Move(self._links[i], self._links[j]) for i, j in list(zip(link_from, link_to))}
                all_phases.setdefault(node_id, {})
                all_phases[node_id][seq] = Phase(node_id, type_, seq, red, yellow, green, num_moves, moves)

        return all_phases

    def __load_exogenous_demands_and_paths(self) -> tuple[dict[Link, float], dict[OD, list[Path]]]:
        """Loads the turning proportions for each move"""
        paths_dir = os.path.join(self.dir_path, 'paths.txt')

        paths: dict[tuple[Node, Node], list[Path]] = {}
        with open(paths_dir) as path_file:
            next(path_file)
            for line in path_file:
                path_id, num_links, path_proportion, *path_of_link_ids = [literal_eval(arg) for arg in line.split()]
                path_of_links = [self._links[link] for link in path_of_link_ids]

                path: Path = Path(path_id, path_of_links, path_proportion, num_links)
                path.flow = path.proportion * self.demand[path.origin, path.destination]

                r, s = path.origin, path.destination
                paths.setdefault((r, s), [])
                paths[(r, s)].append(path)

        exogenous_demand = {}
        for entry_link in self.entry_links:
            exogenous_demand.setdefault(entry_link, 0)
            for r, s in self.all_od_pairs:
                if not self.demand.get((r, s), 0) or r != entry_link.tail:
                    continue
                total_path_proportion = 0
                for path in paths.get((r, s), []):
                    if entry_link == path[0]:
                        total_path_proportion += path.proportion
                exogenous_demand[entry_link] += total_path_proportion * self.demand[r, s]

        return exogenous_demand, paths

    def __star(self, node: Node, method: str, force: bool = False) -> Iterable[Link]:
        """Forward_star if method=='i' else Reverse_star"""
        if node.centroid and not force:
            return None
        assert len(self.links) > 0, "No links found in the graph."

        for link in self.links:  # implement adjacency matrix later
            node_check = getattr(link, method)
            if node == node_check:
                yield link

    def load_turn_proportions(self, demand_scaler: float) -> dict[tuple[Link, Link], float]:
        """Returns the turn proportions from path values obtained from the path file."""
        turn_proportions: dict[tuple[Link, Link], float] = {}
        all_paths = {p for pp in self.paths.values() for p in pp}
        for node in self.signal_nodes:
            for move in self.allowed_moves(node):
                for path in all_paths:
                    upstream_index: Union[int, None] = path.get_index(move.in_link)
                    if upstream_index is not None:
                        move.denominator += path.flow * demand_scaler
                        if upstream_index + 1 <= len(path) and path[upstream_index + 1] == move.out_link:
                            move.numerator += path.flow * demand_scaler

                assert move.numerator <= move.denominator, f"{move.numerator = } > {move.denominator = }"
                i, j = move
                turn_proportions[(i, j)] = move.numerator / move.denominator if move.denominator > 0 else 0

        return turn_proportions

    def forward_star(self, node: Node, force: bool = False) -> Iterable[Link]:
        """Returns the forward star of the node"""
        return self.__star(node, 'tail', force)

    def reverse_star(self, node: Node, force: bool = False) -> Iterable[Link]:
        """Returns the reverse star of the node"""
        return self.__star(node, 'head', force)

    def outgoing_links(self, link: Link) -> Iterable[Link]:
        """Returns the outgoing links from the input link"""
        return self.forward_star(link.head)

    def incoming_links(self, link: Link) -> Iterable[Link]:
        """Returns the incoming links from the input link"""
        return self.reverse_star(link.tail)

    @property
    def all_od_pairs(self) -> Iterable[tuple[Node, Node]]:
        """Yields the origin and destinations of the network"""

        for r, s in self.demand:
            yield r, s

    @property
    def _all_possible_moves(self) -> Iterable[Move]:
        """Returns all possible moves that can be made in this network"""

        # if all moves attribute does not exist then it is calculated
        if "all_moves" not in self.__dict__:
            self.all_moves = set()
            for node in self.signal_nodes:
                for move in self.allowed_moves(node):
                    self.all_moves.add(move)

        for move in self.all_moves:
            yield move

    @staticmethod
    def is_same_link_diff_direction(link1, link2):
        if link1.head == link2.tail and link1.tail == link2.head:
            return True
        else:
            return False

    def all_paths(self, source: Link, destination: Link) -> list[Node]:
        """Returns all possible paths from source to destination"""

        paths = []

        queue = [[source]]

        while queue:
            curr_path = queue.pop(0)
            last_edge = curr_path[-1]

            if last_edge == destination:
                paths.append(curr_path)
            elif last_edge.centroid_connector and len(curr_path) > 1:
                continue
            else:
                for link in self.outgoing_links(last_edge):
                    if not self.is_same_link_diff_direction(link, last_edge) and \
                            link.head not in {edge.head for edge in curr_path}:
                        new_path = curr_path.copy() + [link]
                        queue.append(new_path)

        return paths

    def allowed_phases(self, node: Node) -> Iterable[Phase]:
        """Yields all allowed moves from a given node"""

        for phase in set(self.phases[node.id].values()):
            yield phase

    def allowed_moves(self, node: Node) -> Iterable[Move]:
        """Yields the allowed moves for the input node."""

        moves = set()
        for phase in self.allowed_phases(node):
            for move in phase:
                if move not in moves:
                    yield move
                    moves.add(move)

    def __load_signal_nodes(self) -> dict[int, Node]:
        """
        Returns the signal nodes. Signal nodes are nodes where the moves have less than hundred percent of
        active green time. Can't be called before initializing self.phases
        """
        assert hasattr(self, 'phases'), "Signal nodes can't be determined before initializing self.phases."

        signal_nodes = {}

        for node_id in self.phases:
            node = self._nodes[node_id]

            for phase in self.allowed_phases(node):
                if phase.yellow != 0 and phase.red != 0:
                    signal_nodes[node_id] = node
                    break

        self.__update_default_signal_control()

        return signal_nodes

    def __update_default_signal_control(self) -> None:
        """
        Updates the default signal control. Can't be called before self.phases is created.
        """

        if not hasattr(self, 'phases'):
            raise AttributeError("move green time can not be updated before self.phases is created.")

        for node_id in self.phases.keys():
            node = self._nodes[node_id]
            cycle_length = sum(phase.total_time for phase in self.allowed_phases(node))

            moves = {}
            for phase in self.allowed_phases(node):
                for move in phase:
                    moves.setdefault(move, 0)
                    moves[move] += (phase.green / cycle_length)

            for phase in self.allowed_phases(node):
                for move in phase:
                    move.active_green = moves[move]


if __name__ == "__main__":
    G = Graph(r"F:\LimitedDeployment\code\data")
