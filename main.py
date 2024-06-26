from src import PMF_class as pmf
from src import GEFII_class as gefii
from src import utils
PATH_TO_FIGURES = "src/Figures_PNG/"
PATH_TO_GEFII_JSONS = "src/GEFII_JSONs/"
PATH_TO_PMF_JSONS = "src/PMF_JSONs/"


def main():
    """Main works as an example how to use our library."""
    # List of example PMF instances currently available in folder "src/PMF_JSONs"
    file_names = ["instance_simpleA1",
                  "instance_doubleA1",
                  "instance_EPR_AnB",
                  "instance_EPR_A2B",
                  "instance_EPR_A2nB",
                  "instance_EPR_C2A2nB",
                  "instance_EPR_C2AnB",
                  "instance_simpleAloop"
                  ]
    # Select a quantum experiment
    user_chosen_file = 2
    file_name = file_names[user_chosen_file]
    # Loads the selected PMF into a dictionary
    PMF_json = utils.load_PMF_json(str(file_name+".json"), PATH_TO_PMF_JSONS)
    # Creates PMF class object and produces the corresponding PMF graph in the figures folder
    PMF = pmf.PMF(PATH_TO_PMF_JSONS, PMF_json, file_name, PATH_TO_FIGURES, plot_PMF=True)

    # Create a GEFII object based on the PMF_json object.
    GEFII = gefii.GEFII(PATH_TO_GEFII_JSONS, PATH_TO_FIGURES, PMF_json,
                        file_name, plot_CS=True,plot_GEFII=True
                        )
    # Checks if the produced object is well-formed and valid given the GEFII JSON schema.
    GEFII.validate_GEFII(message=True)
    # Stores the GEFII graph in the figures folder
    GEFII.visualize_GEFII(plot_GEFII=True) # FAIL -> want a tree like representation
    # Saves the GEFII in a JSON file in the GEFII JSON folder
    GEFII.save_GEFII_to_json()
    
if __name__ == "__main__":
    main()
