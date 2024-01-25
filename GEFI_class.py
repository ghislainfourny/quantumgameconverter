import json
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from jsonschema import validate   
import copy
import utils as utils
    
class GEFI:
    """GEFI class containing json_GEFI, matrix T, number_of_measurement_options array 
    """
    def __init__(self):
        """Initializes the GEFI class in order to always be using the same schema"""
        with open(str("0_Oxygen/GEFI/" + "GEFI_schema.jschema"), "r") as GEFI_schema:
            self.GEFI_schema = json.load(GEFI_schema)
        self.informationset_increment_bis = -1
        
    def build_CS_graph(self, EPMF_json, file_name, PLOT=False):
        """Build a networkx DiGraph called CS_graph given the PMF_json"""
        # Get the Labs and Wires arrays
        data_dictionary = utils.extract_PMF_data(EPMF_json)
        Labs_array = data_dictionary["Labs_array"] 
        Wires_array = data_dictionary["Wires_array"] 
        # Get nodes and edges for graph
        nodes = []
        edges = []
        map_playeridx2labidx = {"a":{},"x":{}}
        nodes_color = []
        nodes_labels = {}
        player_index = 0
        for lab in Labs_array: # for each lab
            # if start or end lab ignore
            lab_idx = lab["Index"]
            if lab_idx == 0 or lab_idx == 1:
                pass
            else:
                # Add classical decision node
                player_a = player_index
                number_of_measurement_axes = len(lab["Measurements"]) # Get the number of possible measurement axes that (scientist)player can choose
                nodes.append( (player_a, {"number_of_measurement_options": number_of_measurement_axes}) )
                nodes_color.append((144/256,238/256,144/256))
                nodes_labels[player_a] = "a" + str(lab_idx)
                map_playeridx2labidx["a"][lab_idx] = player_a
                # Add classical outcome node
                player_x = player_index + 1
                number_of_measurement_outcomes = len(lab["Measurements"][0]["CPMaps"]) # Get the number of possible measurement outcomes that (nature)player can choose
                nodes.append((player_x, {"number_of_measurement_options": number_of_measurement_outcomes}))
                nodes_color.append((255/256,99/256,71/256))
                nodes_labels[player_x] = "x" + str(lab_idx)
                map_playeridx2labidx["x"][lab_idx] = player_x
                # Add edge between both classicals of the same lab
                edges.append((player_a,player_x))
                # Increment player_idx by 2
                player_index += 2

        edges.extend([
            (map_playeridx2labidx["x"][wire["From"]["LabIdx"]], map_playeridx2labidx["x"][wire["To"]["LabIdx"]])
            for wire in Wires_array if wire["From"]["LabIdx"] > 1 and wire["To"]["LabIdx"] > 1
        ])
        
        # Graph plot with networkx
        self.CS_graph = nx.DiGraph()
        self.CS_graph.add_nodes_from(nodes)
        self.CS_graph.add_edges_from(edges)
        # Plot graph
        if PLOT == True:
            plt.figure()
            graph_options = {
                "font_size": 32,
                "node_size": 3000,
                "node_color": nodes_color, # "white",
                "labels": nodes_labels,
                "edgecolors": "black",
                "linewidths": 4,
                "width": 4,
            }
            # Draw in the causal order
            pos = nx.planar_layout(self.CS_graph)
            nx.draw_networkx(self.CS_graph, pos, **graph_options)
            # Set margins for the axes so that nodes aren't clipped
            ax = plt.gca()
            ax.margins(0.20)
            plt.axis("off")
            #plt.show()
            plt.savefig(str(file_name + "_CS_graph"))
        return 0  
    
    def build_LO_order(self):
        """
        Get the LO order and set the mapping from the LO order indices to CS indices.
        Additionaly create the dictionary of predecessors for each node in LO order
        """
        # Get linearisation of CS graph
        self.LO = nx.lexicographical_topological_sort(self.CS_graph)
        # maping (as a list) from a LO index to a CS index for players
        self.map_LOplayer2CSplayer = list(self.LO)
        # LO order indices # HERE maybe recall ancestors descendants
        self.predecessors = {}
        for i, player in enumerate(self.map_LOplayer2CSplayer):
            self.predecessors[i] = [self.map_LOplayer2CSplayer.index(CS_player) 
                                    for CS_player in list(nx.transitive_closure(self.CS_graph).predecessors(player))]
        self.successors = {}
        for i, player in enumerate(self.map_LOplayer2CSplayer):
            self.successors[i] = [self.map_LOplayer2CSplayer.index(CS_player) 
                                  for CS_player in list(nx.transitive_closure(self.CS_graph).successors(player))] 
        
             
    def map_PMF2GEFI(self, PMF_json, file_name, PLOT=False):
        """Map from the EPMF object to the GEFI JSON object
        """
        # Get CS graph including number of classical decisions/outcomes from a EPMF json dictionary 
        self.build_CS_graph(PMF_json, file_name=file_name, PLOT=PLOT)
        # dictionary from CS_graph nodes to the number of decisions there # HERE recall possible_decisions to actions
        self.possible_decisions = dict(self.CS_graph.nodes(data="number_of_measurement_options",default=1))
        # Set LO_order, the mapping LO to CS as well as the dictionary of predecessors and one for successorsfor each LO node
        self.build_LO_order()
        # total number of players 
        self.number_of_players = len(self.map_LOplayer2CSplayer)
        # Build matrix T
        self.build_T()
        # Initialise GEFI tree
        assert self.number_of_players >= 1, f"Error: there is no lab to be used in map_EPMF2GEFI"
        # Call GEFI_recursion
        root_history = np.atleast_1d(np.full((self.number_of_players),fill_value=-1))
        self.GEFI = self.GEFI_recursion(root_history)
        # Validate dictionary to GEFI json schema
        self.GEFI_validate(self.GEFI, True)
        # Return json_GEFI
        return self.GEFI
    
    def build_T(self):
        """Build the matrix map T in LO order mapping an incomplete history to an information-set or a complete history
        to a payoff array."""
        def T_recursion(player, temp_history):
            """Lets first define the recursions"""
            # HERE deepcopy history first
            history = copy.deepcopy(temp_history)
            # Get the array of unseen predecessors first
            unseen_predecessors = [predecessor for predecessor in self.predecessors[player] if history[predecessor] == -1]
            if len(unseen_predecessors) > 0:
                next_predecessor = unseen_predecessors[0]
                # got over each possible outcome of the predecessor and enter further layer of recursion
                for outcome in range(0, self.possible_decisions[self.map_LOplayer2CSplayer[next_predecessor]]):
                    history[next_predecessor] = outcome
                    T_recursion(player, history)
            else:
                self.T.append((player,history,self.informationset_increment))
                self.informationset_increment += 1
                # If the current player is a leaf node i.e. has no other successors in the CS graph add the payoff node
                if len(self.successors[player]) == 0:
                    for outcome in range(0, self.possible_decisions[self.map_LOplayer2CSplayer[player]]):
                        payoff_history = copy.deepcopy(history)
                        payoff_history[player] = outcome
                        self.T.append((-1, payoff_history,self.payoffcount_increment))
                        self.payoffcount_increment += 1
            return 0
        # Now start with the actual function build_T()
        self.T = []
        self.informationset_increment = 0
        self.payoffcount_increment = 0
        for player in range(0, self.number_of_players):
            T_recursion(player, np.atleast_1d(np.full((self.number_of_players),fill_value=-1)))
        return 0

    def infoset_from_T(self,player,history):
        """player is an LO player, history gets transformed into a LO compatible one"""
        if player != -1: # Player node
            LO_history = np.atleast_1d(np.full((self.number_of_players),fill_value=-1))
            predecessors = self.predecessors[player]
            LO_history[predecessors] = history[predecessors]
        else: # Payoff node
            LO_history = history
        #print(player, LO_history)
        informationset = [tuple[2] for tuple in self.T if (tuple[0] == player and (tuple[1] == LO_history).all())]
        assert len(informationset) == 1, f"Error: information-set is not a single value. I.e. there exist more than one tuple for the same information-set"
        return informationset[0]
        
    def GEFI_recursion(self, temp_history):
        """GEFI_recursion given tree object
        NB: in here player corresponds to the index in LO
        """
        # First deepcopy history
        history = copy.deepcopy(temp_history)
        # Get player
        unseen_players = np.argwhere(history == -1)
        if (len(unseen_players) > 0): # Player
            player = unseen_players[0][0] # first unseen one
            children = []
            for i in range(0,self.possible_decisions[self.map_LOplayer2CSplayer[player]]):
                updated_history = history
                updated_history[player] = i
                children.append(self.GEFI_recursion(updated_history))
            return {"children" : children, "kind" : "choice", "information-set" : int(self.infoset_from_T(player, history)), "player" : int(player)}
        else: # Payoff
            self.informationset_increment_bis += 1
            return {"payoffs" : self.informationset_increment_bis , "kind" : "outcome"} # int(self.infoset_from_T(-1, history))
      
    def GEFI_validate(self, GEFI_json_dict, message=False):
        """Validates a given GEFI_json_dict with respect to the schema used when GEFI was initialized.
            Bool message indicates if the function should print that the tested object is valid."""  
        validate(instance=GEFI_json_dict,schema=self.GEFI_schema)
        if message:
            print("GEFI is valid")
        return 0
    
    def visualize_GEFI(self, output_GEFI, file_name, PLOT=False):
        """Visualizes the given spacetime game in extensive form with imperfect information."""
        # Initialize nodes and edges for graph
        nodes = []
        edges = []
        nodes_color = []
        nodes_labels = {}
        self.node_index = 0
        
        # Fill nodes and edges from current 
        def gefi_to_nodesNedges_reccursion(gefi):
            this_index = self.node_index
            if gefi["kind"] == "choice":
                nodes.append((this_index)) #, {gefi["information-set"], gefi["player"]}
                self.node_index += 1
                nodes_labels[this_index] = str(gefi["information-set"])
                nodes_color.append("white") #(255/256,99/256,71/256)
                for child in gefi["children"]:
                    node_index = gefi_to_nodesNedges_reccursion(child)
                    edges.append((this_index, node_index))
            elif gefi["kind"] == "outcome":
                nodes.append((this_index)) #, (gefi["payoffs"])
                self.node_index += 1
                nodes_labels[this_index] = str(gefi["payoffs"])
                nodes_color.append("red") # (144/256,238/256,144/256)
            else:
                assert False, f"Error: nor choice nor payoff node"
            return this_index
        """nodes.append((0))
        nodes_labels[0] = str(0)
        nodes_color.append("white")
        edges.append((0,1))"""
        gefi_to_nodesNedges_reccursion(output_GEFI)
        
        # Graph plot with networkx
        GEFI_graph = nx.DiGraph()
        GEFI_graph.add_nodes_from(nodes)
        GEFI_graph.add_edges_from(edges)
        # Plot graph
        if PLOT == True:
            plt.figure()
            graph_options = {
                "font_size": 10,
                "node_size": 500,
                "node_color": nodes_color, # "white",
                "labels": nodes_labels,
                "edgecolors": "black",
                "alpha": 0.75,
                "linewidths": 0.1,
                #"width": 3,
                #"margins": (10,10)
            }
            # Draw in the causal order
            pos = nx.planar_layout(GEFI_graph, scale=2)
            pos = nx.kamada_kawai_layout(GEFI_graph, pos=pos)
            nx.draw_networkx(GEFI_graph, pos, **graph_options)
            
            # Set margins for the axes so that nodes aren't clipped
            ax = plt.gca()
            ax.margins(0.2)
            plt.axis("off")
            #plt.show()
            plt.savefig(str(file_name + "_GEFI_graph"))


def main():
    """This function has been left as is here, in order to give future implementors the tools to directly test their implementation here."""
    # Initialise GEFI and run the mapping algorithm
    gefi = GEFI()
    # Load JSON    
    with open(str("0_Oxygen/EPMF/" + "instance_EPR_A2B.json"), "r") as PMF_1:
        PMF_json = json.load(PMF_1)
    # Load a GEFI example and check that it is valid
    GEFI_example = utils.load_GEFI_json("example.json") # HERE if only I were able to go from GEFI_example to DiGraph...
    gefi.GEFI_validate(GEFI_example)
    # Run mapping
    output_GEFI = gefi.map_PMF2GEFI(PMF_json,file_name="test", PLOT=False)
    # Save GEFI
    utils.save_to_json(output_GEFI,"0_Oxygen/GEFI/PMF2GEFI_1.json")
    # Visualize
    gefi.visualize_GEFI(output_GEFI, file_name="test", plot=False) # FAIL -> want a tree like representation
    
if __name__ == "__main__":
    main()
