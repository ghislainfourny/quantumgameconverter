import json
import jsonschema
import networkx as nx
import matplotlib.pyplot as plt
from src import utils

class PMF:
    """Process Matrix Framework (PMF) class
    """
    def __init__(self, PATH_TO_PMF_JSONS, PMF_json, PMF_name, PATH_TO_FIGURES, plot_PMF=False):
        """Initializes a Process Matrix Framework (PMF) object by building the
        PMF graph and W.

        Args:
            PMF_json (dict): dict read directly from a valid JSON document
            PMF_name (string): name of this PMF object
            PATH_TO_FIGURES (string): 
            plot_PMF (bool, optional): If True, stores a visual representation
            of the PMF graph. Defaults to False.
        """
        # First, checks that the PMF JSON object is valid and well-formed
        with open(str(PATH_TO_PMF_JSONS + "PMF_schema.jschema"), "r", encoding="utf-8") as PMF_schema:
            self.PMF_schema = json.load(PMF_schema)
        self.validate_PMF(PMF_json, message=True)
        self.PMF_name = PMF_name
        self.PMF_graph = self._build_PMF_graph(PMF_json)
        if plot_PMF:
            self.plot_PMF_graph(PATH_TO_FIGURES)

    def _build_PMF_graph(self, PMF_json):
        """Build the PMF graph containing all information from the JSON file.

        Args:
            PMF_json (dict): dict representation of the PMF json

        Returns:
            nx.MultiDiGraph: the PMF graph
        """
        # Get the two basic array labs and wires.
        data_dictionary = utils.extract_PMF_data(PMF_json)
        labs_array = data_dictionary["Labs_array"]
        wires_array = data_dictionary["Wires_array"]
        # Get all nodes and their dictionary of properties.
        nodes = []
        for lab in labs_array:
            nodes.append((lab["Index"], lab))

        # Get all edges and their dictionary of properties.
        wires = []
        for wire in wires_array:
            wires.append((wire["From"]["LabIdx"], wire["To"]["LabIdx"], wire))

        # Build the PMF graph.
        self.PMF_graph = nx.MultiDiGraph()
        self.PMF_graph.add_nodes_from(nodes)
        self.PMF_graph.add_edges_from(wires)

        return self.PMF_graph

    def plot_PMF_graph(self,path):
        """Saves a matplotlib plot of the PMF graph

        Args:
            path (string): path to figures folder
        """
        plt.figure()
        graph_options = {
            "font_size": 32,
            "node_size": 3000,
            "node_color": "white",
            "edgecolors": "black",
            "linewidths": 4,
            "width": 4,
        }
        # Draw in the causal order.
        pos = nx.planar_layout(self.PMF_graph)
        nx.draw_networkx(self.PMF_graph, pos, **graph_options)
        # Set margins for the axes so that nodes aren't clipped.
        ax = plt.gca()
        ax.margins(0.20)
        plt.axis("off")
        #plt.show()
        plt.savefig(str(path+self.PMF_name+"_PMF_graph"))

    def validate_PMF(self, PMF_json, message=False):
        """Validates the member variable PMF_json with respect to the schema
        given while initializing this PMF.

        Args:
            message (bool, optional): If True, prints whether the underlying
            PMF dictionary is well-formed and valid. Defaults to False.
        """
        jsonschema.validate(instance=PMF_json,schema=self.PMF_schema)
        if message:
            print("PMF is valid")