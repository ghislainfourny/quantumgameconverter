import json

def save_to_json(dictionary, path):
    """Saves any dictionary to a json file with a given path"""
    # Save GEFI
    with open(path,"w") as f:
        json.dump(dictionary,f, indent=4)
        
def load_GEFI_json(json_file):
    """Loads a JSON file of a Game in extensive form with imperfect information into a python dictionnary. 
    """
    with open(str("0_Oxygen/GEFI/" + json_file), "r") as GEFI_1:
        return json.load(GEFI_1)

def load_PMF_json(json_file):
    """Loads a JSON file into a python dictionnary. Only loads from folder 0_Oxygen. TODO
    """
    with open(str("0_Oxygen/EPMF/" + json_file), "r") as PMF_1:
        return json.load(PMF_1)
    
def extract_PMF_data(PMF_json):
    """Function to be used to extract the necessary data from a PMF json dictionary."""
    data_dictionary = {}
    # Get the three basic parts as dicts
    Labs_array = PMF_json["ProcessMatrixFramework"]["Labs"]
    Wires_array = PMF_json["ProcessMatrixFramework"]["Wires"]
    
    # Store the main dictionaries in the data_dictionary
    data_dictionary["Labs_array"] = Labs_array
    data_dictionary["Wires_array"] = Wires_array
    return data_dictionary

def main():
    PMF_json = load_PMF_json("instance_bis1.json")
    data_dictionary = extract_PMF_data(PMF_json)
    
if __name__ == "__main__":
    main()