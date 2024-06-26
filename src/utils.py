import json

def save_to_json(dictionary, path):
    """Saves any dictionary to a json file within a given path.

    Args:
        dictionary (dict): Any well-formed JSON
        path (string): Path to store the JSON file at
    """
    # Save GEFII
    with open(path,"w", encoding="utf-8") as f:
        json.dump(dictionary,f, indent=4)

def load_GEFII_json(json_file, path):
    """Loads a JSON file of a game in extensive form with imperfect information
    into a python dictionnary.

    Args:
        json_file (string): Name of GEFII JSON file inside the path folder
        path (string): Path to GEFII JSON file's folder

    Returns:
        dict: Dictionary storage of the GEFII JSON object
    """
    with open(str(path + json_file), "r", encoding="utf-8") as GEFII_json:
        return json.load(GEFII_json)

def load_PMF_json(json_file, path):
    """Loads a JSON file in a given path into a python dictionnary.

    Args:
        json_file (string): Name of PMF JSON file inside the path folder
        path (string): Path to PMF JSON file's folder

    Returns:
        dict: Dictionary storage of the PMF JSON object
    """
    with open(str(path + json_file), "r", encoding="utf-8") as PMF_json:
        return json.load(PMF_json)

def extract_PMF_data(PMF_json):
    """Extracts the labs and wires data from a PMF json dictionary.

    Args:
        PMF_json (dict): PMF dictionary

    Returns:
        dict or array: Dictionary containing the labs and wires of a PMF
    """
    data_dictionary = {}
    # Get the three basic parts as dicts
    labs_array = PMF_json["ProcessMatrixFramework"]["Labs"]
    wires_array = PMF_json["ProcessMatrixFramework"]["Wires"]
    # Store the main dictionaries in the data_dictionary
    data_dictionary["Labs_array"] = labs_array
    data_dictionary["Wires_array"] = wires_array
    return data_dictionary
