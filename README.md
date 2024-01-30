# Mapping embedded process matrices to spacetime games

Repository described in the semester thesis "Mapping embedded process matrices to spacetime games" by Florian Pauschitz and supervised by Ghislain Fourny (2023).

Requirements are in the requierements.txt file.

## Execution

To run the converter place the PMF JSON file in folder "0_Oxygen/EPMF", add the path to this file in main.py and run ```python main.py```.  
The ouput is, on one side, the GEFI JSON file in folder "0_Oxygen/GEFI", and on the other side the PMF graph, the causal structure graph as well as the GEFI graph in png format in folder "3_Figures".

## Results
Take a look at the results given a quantum experiment defined as:  
1. Lab A and B both receive an input state from lab Start.    
2. They both choose a measurement basis and execute a measurement.  
3. Finally, they send their output states to End.  

Process matrix framework graph:  
<img src="/3_Figures/instance_EPR_AnB_PMF_graph.png" width="256"/>

Causal structure graph:  
<img src="/3_Figures/instance_EPR_AnB_CS_graph.png" width="256"/>

Game in extensive form with imperfect information graph:  
<img src="/3_Figures/instance_EPR_AnB_GEFI_graph.png" width="512"/>
