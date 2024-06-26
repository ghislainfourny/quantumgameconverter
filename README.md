# Mapping embedded process matrices to spacetime games

Repository described in the semester thesis "Mapping embedded process matrices to spacetime games" by Florian Pauschitz and supervised by Ghislain Fourny (2023).

Requirements are in the requierements.txt file.

## Execution

To run the converter you can either use a pre-existing PMF quantum experiment or add your own. To add your own place the PMF JSON file in folder "src/PMF_JSONs/", add the path in main.py and run ```python main.py```.  

Outputs are:  
- the PMF, the causal structure and the GEFII graphs in png format in folder "src/Figures_PNG/"  
- the GEFII JSON file in folder "src/GEFII_JSONs/".  

The code output whether the input PMF JSON and the output GEFII JSON files are well-formed and valid given the JSON schemas stored in their respective folders "PMF_JSONs/" and GEFII_JSONs/"

## Results
Take a look at the outputs for an example quantum experiment. It is defined as:  
1. Lab A and B both receive an input state from lab Start.    
2. They both choose a measurement basis and execute a measurement.  
3. Finally, they send their output states to End.  

Process matrix framework graph:  
<img src="/src/Figures_PNG/instance_EPR_AnB_PMF_graph.png" width="256"/>

Causal structure graph:  
<img src="/src/Figures_PNG/instance_EPR_AnB_CS_graph.png" width="256"/>

Game in extensive form with imperfect information graph:  
<img src="/src/Figures_PNG/instance_EPR_AnB_GEFII_graph.png" width="512"/>
