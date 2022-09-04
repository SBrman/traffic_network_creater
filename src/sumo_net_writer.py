#! python3

__author__ = 'Simanta Barman'
__email__ = 'barma017@umn.edu'


import os
import shutil
import time

from Graph import *


# Extra SUMO scripts
SUMO_SCRIPTS_PATH = r'F:\LimitedDeployment\code\sumo_scripts'


class SumoNetworkBuilder:

    def __init__(self, net: Graph, scale: float, folder_name: str):
        """
        :param net: network object.
        :param scale: if x, y, z coordinates are too small then sumo causes problems.
        """
        self.G = net
        self.scale = scale
        self.directory = folder_name
        os.makedirs(fr'.\{folder_name}', exist_ok=True)

        self.node_path = ""
        self.edge_path = ""
        self.net_path = ""

    @staticmethod
    def ft_to_m(distance):
        """Returns data converted from feet to meter"""
        return distance * 0.3048

    @staticmethod
    def m_to_ft(distance):
        """Returns data converted from meter to ft"""
        return distance / 0.3048

    @staticmethod
    def mph_to_mps(speed):
        """Returns the speed converted from miles per hour to meter per second."""
        return speed * 0.44704

    @staticmethod
    def mps_to_mph(speed):
        """Returns the speed converted from miles per hour to meter per second."""
        return speed / 0.44704

    def write_node_file(self, name: str = None):
        """Writes the nodes xml for sumo."""

        name = name if name else self.G.name
        self.node_path = fr".\{self.directory}\{name}.nod.xml"
        with open(self.node_path, 'w') as node_xml_file:
            node_xml_file.write(f"<nodes>\n")
            for node in self.G.nodes:
                if node in self.G.signal_nodes:
                    node_type = "traffic_light"
                # elif node.centroid:
                #     node_type = "unregulated"
                else:
                    node_type = "unregulated"
                    # node_type = "priority"

                line = f'    <node id="{node.id}" x="{node.x * self.scale}" y="{node.y * self.scale}" z="{node.z}" '\
                       f'type="{node_type}"/>\n'

                node_xml_file.write(line)

            node_xml_file.write("</nodes>")

    def write_edge_file(self, name: str = None):
        """Writes the edge xml for sumo"""

        name = name if name else self.G.name
        self.edge_path = fr".\{self.directory}\{name}.edg.xml"
        with open(self.edge_path, 'w') as edge_xml_file:
            edge_xml_file.write(f"<edges>\n")
            for edge in self.G.links:

                line = f'    <edge id="{edge.id}" from="{edge.tail.id}" to="{edge.head.id}" '\
                       f'numLanes="{edge.num_lanes}" speed="{self.mph_to_mps(edge.ffspd)}" '\
                       f' length="{self.ft_to_m(edge.length)}"/>\n'
                edge_xml_file.write(line)
            edge_xml_file.write("</edges>")

    def write_net_file(self, name: str = None):
        """Writes the network xml for sumo"""

        name = name if name else self.G.name

        if self.node_path == "":
            self.write_node_file(name)
        if self.edge_path == "":
            self.write_edge_file(name)

        self.net_path = fr".\{self.directory}\{name}.net.xml"

        os.system(fr"netconvert -n {self.node_path} -e {self.edge_path} --no-turnarounds -o {self.net_path}")

    def generate_routes(self, name: str = None):
        """Generates the route file using the paths"""

        name = name if name else self.G.name

        # with open(fr'.\{self.directory}\{name}_{self.G.demand_scaler}_routes.rou.xml', 'w') as routesFile:
        with open(fr'.\{self.directory}\{name}_routes.rou.xml', 'w') as routesFile:
            routesFile.write('<routes>')
            for paths in self.G.paths.values():
                for path in paths:
                    edge_path = [link for link in path._path]
                    assert edge_path[0].tail == path.origin and edge_path[-1].head == path.destination, "rs did not match."
                    edge_path = " ".join([str(link.id) for link in edge_path])
                    routesFile.write(fr'    <route id="{path.id}" edges="{edge_path}"/>' + '\n')
            routesFile.write('</routes>')

    def generate_trips(self, simulation_period: int, name: str = None, demand_scaler: float = 1):
        """
        Generates trips.
        :param simulation_period: time in minutes
        :param name: name of the network
        """

        name = name if name else self.G.name

        simulation_period = simulation_period / 3600    # converting to hours
        od_matrix_path = fr'.\{self.directory}\{name}_{simulation_period}h_{demand_scaler}_od_edge_relation.xml'
        with open(od_matrix_path, 'w') as od_matrix:
            print(od_matrix_path)
            id_count = 1
            od_matrix.write(f'<interval id="tripsGen" begin="0" end="{int(simulation_period * 3600)}">\n')
            for (r, s), counts in self.G.demand.items():
                if counts == 0:
                    continue
                for path in self.G.paths.get((r, s), []):
                    first_centroid_connector, last_centroid_connector = path._path[0], path._path[-1]
                    path_trip_count = counts * simulation_period * path.proportion * demand_scaler
                    od_matrix.write(f'    <edgeRelation id="{path.id}" from="{first_centroid_connector.id}" '
                                    f'to="{last_centroid_connector.id}" count="{round(path_trip_count)}"/>\n')
                id_count += 1
            od_matrix.write(fr'</interval>')

        self._generate_demand_file(int(simulation_period * 3600), name, demand_scaler)

    def _generate_demand_file(self, simulation_period: int, name: str = None, demand_scaler: float = 1):
        """Generates the demand files using randomTrips.py, routeSampler.py and generateTurnRatios.py"""

        name = name if name else self.G.name
        os.chdir(fr'.\{self.directory}')

        demand_file = f'{name}_simTime_{simulation_period}s_{demand_scaler}.rou.xml'
        edge_relation_file = f'{name}_{simulation_period/3600}h_{demand_scaler}_od_edge_relation.xml'

        shutil.copy(f'{name}_routes.rou.xml', demand_file)

        # os.system(fr'randomTrips.py -n {name}.net.xml -r randomRoutes.rou.xml -e 50000')
        os.system(fr'routeSampler.py -r {name}_routes.rou.xml --od-files {edge_relation_file}' 
                  fr' -o {demand_file} -b 0 -e {simulation_period}')
        os.system(fr'generateTurnRatios.py -r {demand_file} -p -o {name}_{demand_scaler}_turn_ratios.xml')
        os.system(fr'{SUMO_SCRIPTS_PATH}\routecheck.py -n {name}.net.xml -f {demand_file} -v -i')

        os.chdir('..')

    def generate_demand_files_and_turn_ratios(self):
        pass


if __name__ == "__main__":
    # demand_scale = 0.20
    net_name = f'austin_3_dua'
    G = Graph(r"..\data", name=net_name)
    sumo_net_builder = SumoNetworkBuilder(G, scale=3e5, folder_name=net_name)
    # sumo_net_builder.write_net_file()
    # sumo_net_builder.generate_routes()

    # for demand_scale in [0.1, 0.15, 0.20, 0.25, 0.30]:
    for demand_scale in range(23, 36):
        if demand_scale in {25, 30}:
            continue

        demand_scale = round(demand_scale / 100, 2)
        # sumo_net_builder.G.update_turn_proportions(demand_scaler=demand_scale)
        sumo_net_builder.generate_trips(3600 * 3, demand_scaler=demand_scale)
        # sumo_net_builder.generate_demand_files_and_turn_ratios()
        time.sleep(0.1)
