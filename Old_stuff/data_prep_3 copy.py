# importing all needed functions
import os
from pathlib import Path
from astropy.io import fits
import numpy as np
import glob
import time
from Calculating_det_angles import estimate_source_angles_detectors  # importing ma'am's function
from Tools import tools
import traceback
from tqdm import tqdm  # for progress bar


def process_folder(folder,bin_list):
    try:
        event_type, event = folder.split("_")
        year = '20' + event[2:4] + "/"

        # Use the glob module to search for TTE files in the directory
        target_string = "_tte_"
        file_pattern = str(source_data_set_path / folder / 'current' / f"*{target_string}*")
        NaI_detector = glob.glob(file_pattern)


        # fetching data
        with fits.open(NaI_detector[0], memmap=True) as hdul:
            # energy_channel_data = hdul[1].data
            all_count_data = hdul[2].data

        counts = [float(sublist[0]) for sublist in all_count_data]

        data_array = []

        for i in bin_list:
            # Define the range and number of bins
            range_min = ti[0]
            range_max = ti[-1]
                
            bin_size = i

            # Create bin edges
            bin_edges = np.arange(range_min, range_max, bin_size)

            # Create the histogram using numpy.histogram
            hist, edges = np.histogram(counts, bins=bin_edges)

            data_array = data_array + list(hist)

        data_array = np.array(data_array[:])

        # Save the 2D array to a text file
        data_file_path = data_set_path / f"{event_type}_{event}"
        np.savetxt(str(data_file_path), data_array, fmt='%d', delimiter='\t')

    except Exception as e:
        print(f'error {e} in {folder}')
        traceback.print_exc()
        error_folders.append(folder)

# Measure execution time
start_time = time.time()

# name of the data set
source_data_set_path = Path(r"C:\Users\arpan\OneDrive\Documents\GRB\data\500_data_set")


# Get a list of all folders in the specified directory
folders = [str(folder) for folder in os.listdir(source_data_set_path) if os.path.isdir(os.path.join(source_data_set_path, folder))]
# list of bin sizes
bin_list = [0.01, 0.1, 0.5, 1, 5]  # [0.01, 0.1, 0.5, 1, 5]

# time interval around trigger
ti = [-50, 100]
t = ti[1] - ti[0]

# number of datapoints in a light curve
data_no = sum(int(t / (i)) for i in bin_list)
print('number of data points', data_no)

dir_path = Path(tools.json_path(r'data_path.json'))
data_set_name = "dp01-04-2"

# creating the data set folder
data_set_path = dir_path / data_set_name
data_set_path.mkdir(parents=True, exist_ok=True)

print('start')
print('total :', len(folders))

# Writing the parameters to a json file
params_dict = {"bin list": bin_list, "time interval": ti, "number of data points": data_no, "data set name": data_set_name, "data set path": str(data_set_path)}
write_json_file = tools.write_json_file(params_dict, data_set_path / 'params.json')

error_folders = []

# Process the folders sequentially
for folder in tqdm(folders[0:10], desc="Processing folders", unit="folder"):
    process_folder(folder,bin_list)

print('\n----------------------------------------------------------------------------\n\nevents', folders, ' in folder', data_set_path)
end_time = time.time()

# Calculate and print the elapsed time
elapsed_time = end_time - start_time
print(f"Elapsed Time: {elapsed_time:.2f} seconds")

print("errors occured in:",error_folders)

import os
import shutil

def delete_folders(directory, folder_list):
    for folder in folder_list:
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            try:
                shutil.rmtree(folder_path)
                print(f"Deleted folder: {folder}")
            except Exception as e:
                print(f"Error deleting folder {folder}: {str(e)}")
        else:
            print(f"{folder} is not a folder or does not exist.")

directory = Path(r"C:\Users\arpan\OneDrive\Documents\GRB\data\500_data_set")
folders = error_folders

delete_folders(directory, folders)