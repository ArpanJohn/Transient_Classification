# importing all needed functions
import os
from astropy.io import fits
import numpy as np
import glob
import time
from Calculating_det_angles import estimate_source_angles_detectors #importing ma'ams function
from Tools import tools
import traceback

# Measure execution time
start_time = time.time()

# name of the data set
source_data_set_path = r"C:\Users\arpan\OneDrive\Documents\GRB\data\500_data_set"

# Get a list of all folders in the specified directory
folders = [str(folder) for folder in os.listdir(source_data_set_path) if os.path.isdir(os.path.join(source_data_set_path, folder))]

# list of bin sizes
bin_list = [0.01,0.1,0.5,1,5] #[0.001,0.005,0.01,0.1,0.5,1,5]

# time interval around trigger
ti = [-50,100]
t = ti[1] - ti[0]

# number of datapoints in a light curve
data_no = int(t / min(bin_list)) 
print('number of data point' , data_no)
 
dir_path = tools.json_path(r'data_path.json')
data_set_name = "dp3-1d-8"

# creating the data set folder
data_set_path = os.path.join(dir_path,data_set_name)
tools.create_folder(data_set_path)
print('start')
print('total : ',len(folders))
c = 0

# Writing the parameters to a json file
params_dict = {"bin list" : bin_list, "time interval" : ti, "number of data points" : data_no, "data set name" : data_set_name, "data set path" : data_set_path}
write_json_file = tools.write_json_file(params_dict,os.path.join(data_set_path,'params.json'))

error_folders = []

for folder in folders:
    try:
        event_type,event = folder.split("_")
        year = '20'+event[2:4]+"/"

        # Use the glob module to search for TTE files in the directory
        target_string = "_tte_"
        file_pattern = os.path.join(source_data_set_path,folder,'current', f"*{target_string}*")
        NaI_detector = glob.glob(file_pattern)

        # print('NaI_detector used',NaI_detector[0])

        # fetchinng data
        with fits.open(NaI_detector[0], memmap=True) as hdul:
            energy_channel_data = hdul[1].data.copy()
            all_count_data = hdul[2].data
            # all_count_data = np.array(hdul[2].data.copy())

        print(all_count_data.shape)
        print(all_count_data)
        quit()
        # getting counts accross all energy channels
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

        data_array = np.array(data_array)

        # Save the 2D array to a text file
        data = os.path.join(data_set_path,event_type+'_'+event)
        np.savetxt(data, data_array, fmt='%d', delimiter='\t')
        c += 1
        print(f'saved to {data} : {len(folders)-c} remaining', end = '\r')
    except Exception as e:
        print(f'error {e} in ',folder)
        traceback.print_exc()
        error_folders.append(folder)

print('\n----------------------------------------------------------------------------\n\nevents', folders, ' in folder', data_set_path)

end_time = time.time()

# Calculate and print the elapsed time
elapsed_time = end_time - start_time
print(f"Elapsed Time: {elapsed_time:.2f} seconds")

print("errors occured in:")
for folder in error_folders:
    print(folder)