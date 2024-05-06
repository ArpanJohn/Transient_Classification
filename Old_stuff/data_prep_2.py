# importing all needed functions
import os
import shutil
import json
from astropy.io import fits
import numpy as np
import glob
import json
import subprocess
from Calculating_det_angles import estimate_source_angles_detectors #importing ma'ams function


# getting all the event names
from bs4 import BeautifulSoup
def extract_strings(html_file_path):
    try:
        # Open and read the HTML file
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract all strings from the HTML content
        all_strings = soup.stripped_strings

        event_names = []

        # Print the extracted strings
        for string in all_strings:
            if 'bn' in string:
                # print(string)
                event_names.append(string)
    except FileNotFoundError:
        print(f"File '{html_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    print('number of available transients: ',len(event_names))
    return event_names

# Replace 'path/to/your/file.html' with the path to your HTML file
html_file_path = 'C:/Users/arpan/Downloads/HEASARC_Browse_.html'
event_names = extract_strings(html_file_path)[50:55]
print(event_names)
print(len(event_names))

# list of events and transient type and data set name
event_list = event_names
transient_type = 'GRB'
data_set_name = '14.01-5_'
# list of bin sizes
bin_list = [0.001,0.005,0.01,0.1,0.5,1,5]

# number of datapoints in a light curve
data_no = 20000

# ratio of pre-trigger to post-trigger
r = 0.25

# Getting the path the data directory from json file
# Specify the path to your JSON file
json_file_path = "data_path.json"

# Read the JSON file
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Access the path from the JSON data
path_value = data.get("data_path", "")

def create_folder(folder): # to create the file to store data in
    print(folder)
    try:
        shutil.rmtree(folder)
        print(f"Folder '{folder}' and its contents removed successfully.")
    except FileNotFoundError:
        print(f"Folder '{folder}' not found.")
    except OSError as e:
        print(f"An error occurred: {e} \n also", print(folder))
    try:
        os.mkdir(folder)
        print(f"Folder '{folder}' created successfully.")
    except FileExistsError:
        print(f"Folder '{folder}' already exists.")
    except Exception as e:
        print(f"An error occurred: {e}")

def run_wget(wget_command):
    try:
        # Run the wget command
        subprocess.run(wget_command, shell=True, check=True)
        print(f"Downloaded {wget_command.split('/')[-3:]} to {download_folder}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading the file: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# creating the data set folder
data_set_folder = os.path.join(path_value,data_set_name+transient_type)
create_folder(data_set_folder)

for name in event_list:

    # create a temporary folder to store the trigdat and fits files before analysis
    folder_name = 'temp'
    name = name
    year = '20'+name[2:4]+"/"

    folder_path = os.path.join(path_value, folder_name)

    create_folder(folder_path)
    
    # URL of the file you want to download
    url1 = 'wget -q -nH --no-check-certificate --cut-dirs=7 -r -l0 -c -N -np -A "*_trigdat_*" -R "index"* -erobots=off --retr-symlinks https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/triggers/'+year+name+'/current/'

    # Directory where you want to save the downloaded file
    download_folder = folder_path

    # Construct the wget command
    wget_command1 = f"{url1} -P {download_folder}"
    run_wget(wget_command1)

    # Finding Trigdat file
    trig_string = "_trigdat_"
    trig_pattern = os.path.join(folder_path,'current', f"*{trig_string}*")
    trigdat_file = glob.glob(trig_pattern)
    
    # Get the spacecraft pointing from here 
    event_filename = trigdat_file[0]

    # Getting the RA and DEC
    with fits.open(event_filename, memmap=True) as pha_list:
        ra_obj,dec_obj = (pha_list[0].header['RA_OBJ']) ,	(pha_list[0].header['DEC_OBJ'])
        print(ra_obj,dec_obj)

    brightest_nai, bright_nais, brightest_bgo = estimate_source_angles_detectors.angle_to_grb(ra_obj,dec_obj,event_filename) # Getting the values
    
    # URL of the file you want to download
    url1 = 'wget -q -nH --no-check-certificate --cut-dirs=7 -r -l0 -c -N -np -A "*_tte_'+brightest_nai+'_*" -R "index"* -erobots=off --retr-symlinks https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/triggers/'+year+name+'/current/'

    # Construct the wget command
    wget_command1 = f"{url1} -P {download_folder}"
    run_wget(wget_command1)

    target_string = "_tte_"

    path = os.path.join(folder_path,'current')
    # Use the glob module to search for TTE files in the directory
    file_pattern = os.path.join(path, f"*{target_string}*")
    NaI_detector = glob.glob(file_pattern)

    print('NaI_detector used',NaI_detector[0])

    # fetchinng data
    with fits.open(NaI_detector[0]) as hdul:
        energy_channel_data = hdul[1].data
        all_count_data = np.array(hdul[2].data)

    # getting counts accross all energy channels
    counts = [float(sublist[0]) for sublist in all_count_data]

    data_array = []

    for i in bin_list:
        # Define the range and number of bins
        range_min = -data_no * i * r
        range_max =  data_no * i * (1-r)
            
        bin_size = i

        # Create bin edges
        bin_edges = np.arange(range_min, range_max, bin_size)

        # Finding energy channel range
        energy_channel_range = f"{energy_channel_data[0][1]:.2f} to {energy_channel_data[-1][-1]:.2f}KeV"

        # Create the histogram using numpy.histogram
        hist, edges = np.histogram(counts, bins=bin_edges)

        data_array.append(hist)

    data_array = np.array(data_array)

    # Save the 2D array to a text file
    data_set_path = os.path.join(data_set_folder,name+'_'+transient_type)
    np.savetxt(data_set_path, data_array, fmt='%d', delimiter='\t')

# Read the 2D array back from the text file
# loaded_data = np.loadtxt(data_set_path, dtype=int, delimiter='\t')

# Getting the path the data directory from json file
# Specify the path to your JSON file
# json_file_path = "data_path.json"

# # Read the JSON file
# with open(json_file_path, 'r') as file:
#     data = json.load(file)

# # Access the path from the JSON data
# path_value = data.get("data_path", "")

# data_set_folder = os.path.join(path_value,'test_data_set_GRB')

# data_list = os.listdir(data_set_folder)

# print(data_list)