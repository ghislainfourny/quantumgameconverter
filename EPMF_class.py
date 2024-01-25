import utils as utils
import networkx as nx
import matplotlib.pyplot as plt

class EPMF:
    def __init__(self, PMF_json, file_name, PLOT=False):
        # Build PMF graph
        self.PMF_graph = self.build_PMF_graph(PMF_json,file_name, PLOT=True)
        # Build W
        self.W = self.build_W()
        
    def build_PMF_graph(self, PMF_json, file_name, PLOT=False):
        """Build the PMF graph containing all information from the JSON file.
        PLOT: True to show the graph"""
        # Get the two basic array labs and wires
        data_dictionary = utils.extract_PMF_data(PMF_json)
        Labs_array = data_dictionary["Labs_array"]
        Wires_array = data_dictionary["Wires_array"]
        # Get all nodes and their dictionary of properties
        nodes = []
        for lab in Labs_array:
            # TODO deal with Start and End specially
            nodes.append((lab["Index"], lab))   
        
        # Get all edges and their dictionary of properties
        wires = []
        for wire in Wires_array:
            wires.append((wire["From"]["LabIdx"], wire["To"]["LabIdx"], wire))
        
        # Enforce constraints 
        # TODO check that every wire has existing labs and that every qubit is used 
        # exactly once
        # TODO enforce indices uniqueness?
        
        # Build PMF graph
        self.PMF_graph = nx.MultiDiGraph()
        self.PMF_graph.add_nodes_from(nodes)
        self.PMF_graph.add_edges_from(wires)
        
        # Visualize PMF graph
        if PLOT == True:
            plt.figure()
            graph_options = {
                "font_size": 32,
                "node_size": 3000,
                "node_color": "white",
                "edgecolors": "black",
                "linewidths": 4,
                "width": 4,
            }
            # Draw in the causal order
            pos = nx.planar_layout(self.PMF_graph)
            nx.draw_networkx(self.PMF_graph, pos, **graph_options)
            # Set margins for the axes so that nodes aren't clipped
            ax = plt.gca()
            ax.margins(0.20)
            plt.axis("off")
            #plt.show()
            plt.savefig(str(file_name + "_PMF_graph"))
        # Return graph
        return self.PMF_graph
    
    def build_W(self):
        """TODO Builds W"""
        # Get the number of qubits/wires
        pass
        # Initialize W
        self.W = 0
        # Iterate through every combination and sum up
        
        return self.W
    
    def get_epmf_frequencies(self, measurement_axes, measurement_outcomes):
        """Return the frequencies for the given measurement properties"""
        # Check that the properties are correct TODO
        #assert
        # calc tr(W(MxMxM))
        