# importing all needed functions
import os
import shutil
import json
from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
from fast_histogram import histogram1d
import matplotlib as mpl
import matplotlib.pyplot as plt
import math
from astropy.io import ascii
import matplotlib.patches as mpatches
from matplotlib import rc,rcParams
from astropy.table import Table
# %matplotlib inline
# %matplotlib notebook
from astropy.io import fits
from numpy import arange
import json
import subprocess
from Calculating_det_angles import estimate_source_angles_detectors #importing ma'ams function
import matplotlib.image as mpimg

# Getting the path the data directory from json file
# Specify the path to your JSON file
json_file_path = "data_path.json"

# Read the JSON file
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Access the path from the JSON data
path_value = data.get("data_path", "")

# Print or use the path as needed
print("data_path:", path_value)

# List of samples to go through
sample_list = []    #['GRB_bn100507577','GRB_bn101227195','GRB_bn120227725','GRB_bn130623488','GRB_bn160919613','GRB_bn220730659','GRB_bn110819665']
for filename in os.listdir(path_value):
    if "GRB" in filename:
        sample_list.append(filename)

print('number of samples to graph', len(sample_list))

# List of bins in which the sample will be binned
bin_list = [0.01,0.1,1,2,5]

for sample in sample_list:

    # Accessing the sample path
    folder_path = os.path.join(path_value, sample)
    print(folder_path)
    
    # Finding most suitable detector    # finding all TTE files
    directory_path = os.path.join(folder_path,"current")
    target_string = "_tte_n"
    trig_string = "_trigdat_"

    # Finding Trigdat file
    trig_pattern = os.path.join(directory_path, f"*{trig_string}*")
    trigdat_file = glob.glob(trig_pattern)

    # Get the spacecraft pointing from here 
    event_filename = trigdat_file[0]

    # Getting the RA and DEC
    pha_list = fits.open(event_filename, memmap=True)
    ra_obj,dec_obj = (pha_list[0].header['RA_OBJ']) ,	(pha_list[0].header['DEC_OBJ'])
    print(ra_obj,dec_obj)

    # Use the glob module to search for TTE files in the directory
    file_pattern = os.path.join(directory_path, f"*{target_string}*")
    matching_files = glob.glob(file_pattern)

    print('from trigdat file',event_filename.split('\\')[-1]) # just to verify that the correct file is checked to get the ra and dec

    brightest_nai, bright_nais, brightest_bgo = estimate_source_angles_detectors.angle_to_grb(ra_obj,dec_obj,event_filename) # Getting the values

    # till here

    for string in matching_files:
        if '_'+brightest_nai+'_' in string:
            NaI_detector = string

    print('NaI_detector used',NaI_detector)

    hdul = fits.open(NaI_detector)

    # fetchinng data
    energy_channel_data = hdul[1].data
    all_count_data = np.array(hdul[2].data)

    # getting counts accross all energy channels
    counts = [float(sublist[0]) for sublist in all_count_data]

    # Create a subplot grid
    fig, axs = plt.subplots(len(bin_list), 1,figsize=(10,7 * len(bin_list)))
    # fig, axs = plt.subplots(len(bin_list)*2, 1,figsize=(10,7 * len(bin_list * 2))) # uncomment if plotting using both numpy and matplotlib

    # Flatten the 2D array of subplots to simplify indexing
    axs = axs.flatten()
    sb=0

    for i in bin_list:
        # choosing subplot index
        ax = axs[sb]
        sb=sb+1

        # Define the range and number of bins
        range_min = min(counts)
        range_max = max(counts)

        if i == 0.1:
            range_min = -10
            range_max =  10
            

        bin_size = i

        # Create bin edges
        bin_edges = np.arange(range_min, range_max, bin_size)

        # Finding energy channel range
        energy_channel_range = f"{energy_channel_data[0][1]:.2f} to {energy_channel_data[-1][-1]:.2f}KeV"

        # Create the histogram using numpy.histogram
        hist, edges = np.histogram(counts, bins=bin_edges)
            
        # Plot the histogram using numpy takes less time
        ax.plot(edges[1:],hist)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Counts')
        bin_size_str=str(" ;bin size:"+str(bin_size))
        ax.set_title(f'NaI detector {brightest_nai} light curve ' + energy_channel_range+f";bin size = {bin_size_str}s")

        # Add a vertical line at x=0
        ax.axvline(x=0, color='red', linestyle='--',linewidth=0.5)

        # ax = axs[sb]
        # sb=sb+1
        
        # # Plot the histogram using matplotlib.pyplot.hist takes more time
        # ax.hist(counts, bins=bin_edges,histtype='step', edgecolor='k', alpha=0.7, linewidth=1)
        # ax.set_xlabel('Time (s)')
        # ax.set_ylabel('Counts')
        # bin_size_str=str(" ;bin size:"+str(bin_size))
        # ax.set_title(f'NaI detector {brightest_nai} light curve ' + energy_channel_range+f";bin size = {bin_size_str}s")

        # # Add a vertical line at x=0
        # ax.axvline(x=0, color='red', linestyle='--',linewidth=0.5)

    # Save the plot to a JPEG file
    save_path = os.path.join(folder_path, 'NaI_detector_light_curves.jpg')
    print(save_path)
    plt.savefig(save_path)
    print('save figure at ',save_path)