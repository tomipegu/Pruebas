# Libraries
import pandas as pd
import math
import os


# =========
# Functions
# =========

def vars_csv_to_dict(path):
    """
    Load all the csv files corresponding to Variable data, convert them to Pandas Dataframe
    and store them in a Python dictionary.

    INPUT
    =====
    path: str. Path of the folder containing the csv files.

    RETURN
    ======
    d_vars: dict. Dictionary containing the values for each variable in the model.
                  {<Variable Name>: dataframe}
    """
    # Dictionary for storing the info of each variable
    d_vars = {}

    # Extracting the filename of all the files in the folder and
    # processing those that correspond to variables.
    for dir in os.listdir(path):
        # Checking if the file corresponds to a variable
        if dir.startswith("v"):
            # Extracting the name of the variable
            var_name = dir.split(".")[0].strip()
            # Converting the csv file to a Python Dataframe
            df = pd.read_csv(path + "/" + dir)
            # Storing the variable info in a Python dictionary
            d_vars[var_name] = df
    
    return d_vars
            

