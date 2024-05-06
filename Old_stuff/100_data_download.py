# importing all needed functions
import os
import io
from contextlib import redirect_stdout
from astropy.io import fits
import os
import glob
from astropy.io import fits
from Calculating_det_angles import estimate_source_angles_detectors #importing ma'ams function
from Tools import tools

data_set_path = r"C:\Users\arpan\OneDrive\Documents\GRB\data\500_data_set"

import pandas as pd
df = pd.read_csv('output.csv')

print(df.info())

# Shuffle the DataFrame
df_shuffled = df.sample(frac=1, random_state=42)  # Set random_state for reproducibility

event_counter = {'GRB' : 0, 'SFLARE': 0 , 'TGF': 0, 'SGR':0,'DISTPAR':0}
event_limit = 500

# Get a list of all folders in the specified directory
folders = [folder for folder in os.listdir(data_set_path) if os.path.isdir(os.path.join(data_set_path, folder))]
folder_names = []
for folder in folders:
    bn_name = folder.split('_')[0]
    event_counter[bn_name] += 1
    folder_names.append(folder.split('_')[1])

print("events already dowloaded\n",event_counter)

event_counter = {'GRB' : 0, 'SFLARE': 0 , 'TGF': 0, 'SGR':0,'DISTPAR':0}

event_type, name = [], []
for index, row in df_shuffled.iterrows():
    f = 0
    for folder in folders:
        bn_name = folder.split('_')[1]
        if bn_name == row['event_name']:
            event_counter[row['event_type']] += 1
            f = 1
            break
    if f == 1:
        continue

    if row['event_type'] in event_counter and not(row['event_name'] in folder_names):  
        if event_counter[row['event_type']] < event_limit:
            event_counter[row['event_type']] += 1
            event_type.append(row['event_type'])
            name.append(row['event_name'])

print(event_counter)

# for i,j in zip(event_type,name):
    # print(i,j)
#     pass
print(len(event_type))
print(len(name))
event_list = name
event_types = event_type

dir_path = tools.json_path(r'data_path.json')

for event_name,event_type in zip(event_list,event_types):
    # if event_type == 'GRB' or event_type == 'TGF' or event_type == 'SFLARE':
    #     continue
    temp_path = os.path.join(dir_path, r'temp')
    tools.create_folder(temp_path)

    event = event_name
    year = '20'+event[2:4]+"/"

    # URL of the file you want to download
    url = 'wget -q -nH --no-check-certificate --cut-dirs=7 -r -l0 -c -N -np -A "*_trigdat_*" -R "index"* -erobots=off --retr-symlinks https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/triggers/'+year+event+'/current/'
    tools.run_wget_download(url,temp_path)

    # Finding Trigdat file
    trig_string = "_trigdat_"
    trig_pattern = os.path.join(temp_path,'current', f"*{trig_string}*")
    trigdat_file = glob.glob(trig_pattern)

    # Get the spacecraft pointing from here 
    event_filename = trigdat_file[0]

    # Getting the RA and DEC
    with fits.open(event_filename, memmap=True) as pha_list:
        ra_obj,dec_obj = (pha_list[0].header['RA_OBJ']),(pha_list[0].header['DEC_OBJ'])

    trap = io.StringIO()
    with redirect_stdout(trap):
        brightest_nai, bright_nais, brightest_bgo = estimate_source_angles_detectors.angle_to_grb(ra_obj,dec_obj,event_filename) # Getting the values

    # URL of the tte file to download
    url = 'wget -q -nH --no-check-certificate --cut-dirs=7 -r -l0 -c -N -np -A "*_tte_'+brightest_nai+'_*" -R "index"* -erobots=off --retr-symlinks https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/triggers/'+year+event+'/current/'
    # Construct the wget command
    tools.run_wget_download(url,os.path.join(data_set_path,event_type + '_' + event))
    print(len(event_list[event_list.index(event_name):]))