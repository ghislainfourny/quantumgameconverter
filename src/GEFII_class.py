import copy
import json
import jsonschema
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from src import utils

class GEFII:
    """Game in Extensive Form with Imperfect Information (GEFII) class
    """
    def __init__(self,PATH_TO_GEFII_JSONS, PATH_TO_FIGURES, PMF_json, PMF_name, 
                 plot_CS=False, plot_GEFII=False
                 ):
        """Initializes a GEFII object by converting a PMF JSON dictionary. The
        GEFII JSON dictionary is checked for well-formedness and valid along
        the given jschema.

        Args:
            PATH_TO_GEFII_JSONS (string): Path to desired storage location for
            GEFII JSON files.
            PATH_TO_FIGURES (string): Path to desired storage location for all
            PNG figures.
            PMF_json (dict): Dict object representing a quantum experiment in
            process matrix format.
            PMF_name (string): Name of the quantum experiment. Will be used for
            sensible file naming.
            plot_CS (bool, optional): If True, stores a visual representation
            of the causal structure graph. Defaults to False.
            plot_GEFII (bool, optional): If True, stores a visual
            representation of the GEFII graph. Defaults to False.
        """
        self._PATH_TO_GEFII_JSONS = PATH_TO_GEFII_JSONS
        self._PATH_TO_FIGURES = PATH_TO_FIGURES
        self.GEFII_name = PMF_name

        self.GEFII_json: dict
        self.CS_graph: nx.DiGraph
        self.LO: nx.DiGraph
        self.GEFII_graph: nx.DiGraph
        self.map_LOplayer2CSplayer: list
        self._predecessors: dict
        self._successors: dict
        self.possible_decisions: dict
        self.number_of_players: int

        self.number_of_informationsets: int
        self.number_of_payoffs: int
        self.number_of_nodes: int
        
        self.T: list
        self._informationset_index: int
        self._payoff_index: int

        with open(str(PATH_TO_GEFII_JSONS + "GEFII_schema.jschema"), "r", encoding="utf-8") as GEFII_schema:
            self.GEFII_schema = json.load(GEFII_schema)
        self._informationset_increment_bis = -1
        
        self._convert_PMF_to_GEFII(PMF_json, plot_CS, validate_GEFII=True)
        self.number_of_nodes = self.number_of_informationsets + self.number_of_payoffs

        self.validate_GEFII(message=False)
        self.visualize_GEFII(plot_GEFII)

    def _build_CS_graph(self, PMF_json, plot_CS=False):
        """Build a networkx DiGraph called CS_graph given the PMF_json dict

        Args:
            PMF_json (dict): python storage of the PMF JSON
            plot_CS (bool, optional): If True, stores a visual representation
            of the causal structure graph. Defaults to False.
        """
        # Get the Labs and Wires arrays
        data_dictionary = utils.extract_PMF_data(PMF_json)
        labs_array = data_dictionary["Labs_array"]
        wires_array = data_dictionary["Wires_array"]
        
        nodes = []
        edges = []
        map_playeridx2labidx = {"a":{},"x":{}}
        nodes_color = []
        nodes_label = {}
        player_index = 0
        # Iterate over all labs.
        for lab in labs_array:
            # Ignore the start and end labs.
            lab_idx = lab["Index"]
            if lab_idx == 0 or lab_idx == 1:
                pass
            else:
                # Add classical decision node
                player_a = player_index
                # Get the number of possible measurement axes (i.e. actions)
                number_of_measurement_axes = len(lab["Measurements"])
                nodes.append((player_a,
                              {"number_of_measurement_options": number_of_measurement_axes}
                              ))
                nodes_color.append((144/256,238/256,144/256))
                nodes_label[player_a] = "a" + str(lab_idx)
                map_playeridx2labidx["a"][lab_idx] = player_a
                # Add a classical outcome node.
                player_x = player_index + 1
                # Get the number of possible measurement outcomes (i.e. actions)
                number_of_measurement_outcomes = len(lab["Measurements"][0]["CPMaps"])
                nodes.append((player_x,
                              {"number_of_measurement_options": number_of_measurement_outcomes}
                              ))
                nodes_color.append((255/256,99/256,71/256))
                nodes_label[player_x] = "x" + str(lab_idx)
                map_playeridx2labidx["x"][lab_idx] = player_x
                # Add an edge between both classical nodes of the same lab
                edges.append((player_a,player_x))
                # Increment player_idx by 2
                player_index += 2

        edges.extend([
            (map_playeridx2labidx["x"][wire["From"]["LabIdx"]],
             map_playeridx2labidx["x"][wire["To"]["LabIdx"]])
            for wire in wires_array
            if wire["From"]["LabIdx"] > 1 and wire["To"]["LabIdx"] > 1
            ])

        # Graph plot with networkx
        self.CS_graph = nx.DiGraph()
        self.CS_graph.add_nodes_from(nodes)
        self.CS_graph.add_edges_from(edges)
        # Plot CS graph
        if plot_CS:
            self.plot_CS_graph(nodes_color,nodes_label)

    def _build_LO_order(self):
        """Build a linear order of the causal structure graph. Additionaly, 
        create a mapping from CS_graph nodes to LO nodes and store for every 
        LO node its predecessors and successors.
        """
        # Get linearisation of CS graph
        self.LO = nx.lexicographical_topological_sort(self.CS_graph)
        # maping (as a list) from a LO index to a CS index for players
        self.map_LOplayer2CSplayer = list(self.LO)
        # LO order indices # HERE maybe recall ancestors descendants
        self._predecessors = {}
        for i, player in enumerate(self.map_LOplayer2CSplayer):
            self._predecessors[i] = [self.map_LOplayer2CSplayer.index(CS_player)
                                    for CS_player
                                    in list(nx.transitive_closure(self.CS_graph).predecessors(player))]
        self._successors = {}
        for i, player in enumerate(self.map_LOplayer2CSplayer):
            self._successors[i] = [self.map_LOplayer2CSplayer.index(CS_player) 
                                  for CS_player in list(nx.transitive_closure(self.CS_graph).successors(player))]
        
    def _build_T(self):
        """Build the matrix map T in LO order mapping an incomplete history to
        an information-set or a complete history to a payoff array."""
        def _T_recursion(player_index, temp_history):
            """Recurse through all players to touch every possible history. 
            Store the tuples (player_index, history, informationset_index) in self.T

            Args:
                player_index (int): player index
                temp_history (numpy 1d array): current history in the recursion tree
            """
            history = copy.deepcopy(temp_history)
            # Get the array of unseen predecessors
            unseen_predecessors = [predecessor
                                   for predecessor
                                   in self._predecessors[player_index]
                                   if history[predecessor] == -1]
            if len(unseen_predecessors) > 0:
                next_predecessor = unseen_predecessors[0]
                # Touched each possible outcome of the predecessor, hence enter further layer of recursion
                for outcome in range(0, self.possible_decisions[self.map_LOplayer2CSplayer[next_predecessor]]):
                    history[next_predecessor] = outcome
                    _T_recursion(player_index, history)
            else:
                self.T.append((player_index,history,self._informationset_index))
                self._informationset_index += 1
                # If the current player is a leaf node (i.e. has no other 
                # successors in the CS graph) add the payoff node.
                if len(self._successors[player_index]) == 0:
                    for outcome in range(0, self.possible_decisions[self.map_LOplayer2CSplayer[player_index]]):
                        payoff_history = copy.deepcopy(history)
                        payoff_history[player_index] = outcome
                        self.T.append((-1, payoff_history,self._payoff_index))
                        self._payoff_index += 1
        # Now start with the actual function _build_T()
        self.T = []
        self._informationset_index = 0
        self._payoff_index = 0
        for player_index in range(0, self.number_of_players):
            _T_recursion(player_index, 
                         np.atleast_1d(np.full((self.number_of_players),fill_value=-1)))
        self.number_of_informationsets = self._informationset_index
        self.number_of_payoffs = self._payoff_index

    def _infoset_from_T(self,player,history):
        """Returns the index of the information set corresponding to the given
        history and player based on self.T.

        Args:
            player (int): Player index in the LO
            history (list): History corresponding to the searched information set

        Returns:
            int: Information set's index
        """
        if player != -1: # Player node
            LO_history = np.atleast_1d(np.full((self.number_of_players),fill_value=-1))
            predecessors = self._predecessors[player]
            LO_history[predecessors] = history[predecessors]
        else: # Payoff node
            LO_history = history
        #print(player, LO_history)
        informationset = [tuple[2]
                          for tuple
                          in self.T
                          if (tuple[0] == player and (tuple[1] == LO_history).all())]
        assert len(informationset) == 1, "Error: information-set is not a single value. I.e. there exist more than one tuple for the same information-set"
        return informationset[0]
   
    def _GEFII_recursion(self, temp_history):
        """Recursion used when building a GEFII dictionary.
        Players are indexed according to their position in the linear order (LO).

        Args:
            temp_history (list): History object

        Returns:
            dict: Dict representing either an information-set or an outcome
            node. The syntax is valid along our default GEFII jschema.
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
                children.append(self._GEFII_recursion(updated_history))
            return {"children" : children, "kind" : "choice", "information-set" : int(self._infoset_from_T(player, history)), "player" : int(player)}
        else: # Payoff
            self._informationset_increment_bis += 1
            return {"payoffs" : self._informationset_increment_bis , "kind" : "outcome"} # int(self._infoset_from_T(-1, history))

    def _convert_PMF_to_GEFII(self, PMF_json, plot_CS=False, validate_GEFII=False):
        """Converts a given PMF dictionary to a GEFII dictionary and sets
        useful member variables of the GEFII class object.

        Args:
            PMF_json (dict): PMF JSON dictionary to be converted from
            plot_CS (bool, optional): If True, stores a visual representation
            of the causal structure graph. Defaults to False.
            validate_GEFII (bool, optional): If True, checks that produced GEFII
            dictionary is well-formed and valid along the jschema given at
            during the class initialization. Defaults to False.
        """
        # Get CS graph including number of classical decisions/outcomes from a PMF json dictionary 
        self._build_CS_graph(PMF_json, plot_CS=plot_CS)
        # dictionary from CS_graph nodes to the number of decisions there # HERE recall possible_decisions to actions
        self.possible_decisions = dict(self.CS_graph.nodes(data="number_of_measurement_options",default=1))
        # Set LO_order, the mapping LO to CS as well as the dictionary of predecessors and one for successorsfor each LO node
        self._build_LO_order()
        # total number of players 
        self.number_of_players = len(self.map_LOplayer2CSplayer)
        # Build matrix T
        self._build_T()
        # Initialise GEFII tree
        assert self.number_of_players >= 1, "Error: there is no lab to be used in convert_PMF_to_GEFII"
        # Call _GEFII_recursion
        root_history = np.atleast_1d(np.full((self.number_of_players),fill_value=-1))
        self.GEFII_json = self._GEFII_recursion(root_history)
        if validate_GEFII:
            self.validate_GEFII(message=False)

    def validate_GEFII(self, message=False):
        """Validates the member variable GEFII_json with respect to the schema
        given while initializing this GEFII.

        Args:
            message (bool, optional): If True, prints whether the underlying
            GEFII dictionary is well-formed and valid. Defaults to False.
        """
        jsonschema.validate(instance=self.GEFII_json,schema=self.GEFII_schema)
        if message:
            print("GEFII is valid")

    def visualize_GEFII(self, plot_GEFII=False):
        """Visualizes the given spacetime game in extensive form with imperfect information.

        Args:
            plot_GEFII (bool, optional): If True, stores a visual 
            representation of the GEFII object. Defaults to False.
        """
        # Initialize nodes and edges for graph
        nodes = []
        edges = []
        nodes_color = []
        nodes_labels = {}
        self._node_index = 0

        # Fill nodes and edges from current
        def _GEFII_set_nodes_and_edges_reccursion(GEFII_json):
            this_index = self._node_index
            if GEFII_json["kind"] == "choice":
                nodes.append((this_index)) #, {GEFII_json["information-set"], GEFII_json["player"]}
                self._node_index += 1
                nodes_labels[this_index] = str(GEFII_json["information-set"])
                nodes_color.append("white") #(255/256,99/256,71/256)
                for child in GEFII_json["children"]:
                    node_index = _GEFII_set_nodes_and_edges_reccursion(child)
                    edges.append((this_index, node_index))
            elif GEFII_json["kind"] == "outcome":
                nodes.append((this_index)) #, (GEFII_json["payoffs"])
                self._node_index += 1
                nodes_labels[this_index] = str(GEFII_json["payoffs"])
                nodes_color.append("red") # (144/256,238/256,144/256)
            else:
                assert False, "Error: nor choice nor payoff node"
            return this_index
        _GEFII_set_nodes_and_edges_reccursion(self.GEFII_json)

        # Graph plot with networkx
        self.GEFII_graph = nx.DiGraph()
        self.GEFII_graph.add_nodes_from(nodes)
        self.GEFII_graph.add_edges_from(edges)
        # Plot graph
        if plot_GEFII:
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
            pos = nx.planar_layout(self.GEFII_graph, scale=2)
            pos = nx.kamada_kawai_layout(self.GEFII_graph, pos=pos)
            nx.draw_networkx(self.GEFII_graph, pos, **graph_options)

            # Set margins for the axes so that nodes aren't clipped
            ax = plt.gca()
            ax.margins(0.2)
            plt.axis("off")
            #plt.show()
            plt.savefig(str(self._PATH_TO_FIGURES+self.GEFII_name+"_GEFII_graph"))

    def plot_CS_graph(self, nodes_color, nodes_label):
        """Stores a png matplotlib plot of the causal structure graph of the underlying GEFII

        Args:
            nodes_color (array of plt color string): maps a color to each node in the CS graph
            nodes_label (array of strings): maps a string to each node in the CS graph
        """
        # Plot graph
        plt.figure()
        graph_options = {
            "font_size": 32,
            "node_size": 3000,
            "node_color": nodes_color, # "white",
            "labels": nodes_label,
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
        plt.savefig(str(self._PATH_TO_FIGURES+self.GEFII_name+"_CS_graph"))

    def save_GEFII_to_json(self):
        """Saves the current GEFII json
        """
        utils.save_to_json(self.GEFII_json, str(self._PATH_TO_GEFII_JSONS+self.GEFII_name+"_GEFII"))
