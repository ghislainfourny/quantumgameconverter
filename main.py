import EPMF_class as epmf
import GEFI_class as gefi
import utils as utils

def main():
    # List of EPMF instances available in the folder "0_Oxygen/EPMF"
    file_names = ["instance_simpleA1",
                  "instance_doubleA1",
                 "instance_EPR_AnB",
                 "instance_EPR_A2B",
                 "instance_EPR_A2nB",
                 "instance_EPR_C2A2nB",
                 "instance_EPR_C2AnB",
                 "instance_simpleAloop"]
    # Select which one to run
    file_name = file_names[6]
    # Loads the selected EPMF into a dictionary 
    PMF_json = utils.load_PMF_json(str(file_name + ".json"))
    # Create EPMF class object and produces the corresponding PMF graph in folder "3_Figures"
    EPMF = epmf.EPMF(PMF_json, str("3_Figures/"+file_name), PLOT=True)
    # TODO Get the probabilities for given measurement axis and measurement outcome.
    # TODO EPMF.get_probabilities()
    
    # Initialise a GEFI object
    GEFI = gefi.GEFI()
    # Maps from the EPMF to the GEFI and stores the corresponding causal structure (CS) graph in "3_Figures"
    GEFI_json = GEFI.map_PMF2GEFI(PMF_json, str("3_Figures/"+file_name), PLOT=True)
    # Check if the produced object is well-formed and valid given the GEFI JSON schema
    GEFI.GEFI_validate(GEFI_json, True)
    # Store the GEFI graph in "3_Figures"
    GEFI.visualize_GEFI(GEFI_json, str("3_Figures/"+file_name), PLOT=True) # FAIL -> want a tree like representation
    # Save GEFI in a JSON file in folder "0_Oxygen/GEFI"
    utils.save_to_json(GEFI_json,"0_Oxygen/GEFI/PMF2GEFI_1.json")

if __name__ == "__main__":
    main()
