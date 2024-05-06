# Importing all needed functions
import os
import io
from contextlib import redirect_stdout
from astropy.io import fits
import glob
from Calculating_det_angles import estimate_source_angles_detectors  # Importing ma'am's function
from Tools import tools
import threading
from queue import Queue

data_set_path = r"D:\GRB data\500_data_set"
import pandas as pd

df = pd.read_csv('output.csv')
print(df.info())

# Shuffle the DataFrame
df_shuffled = df.sample(frac=1, random_state=42)  # Set random_state for reproducibility

event_counter = {'GRB': 0, 'SFLARE': 0, 'TGF': 0, 'SGR': 0, 'DISTPAR': 0}
event_limit = 2000

# Get a list of all folders in the specified directory
folders = [folder for folder in os.listdir(data_set_path) if os.path.isdir(os.path.join(data_set_path, folder))]

folder_names = []
for folder in folders:
    bn_name = folder.split('_')[0]
    event_counter[bn_name] += 1
    folder_names.append(folder.split('_')[1])

print("events already downloaded\n", event_counter)

# quit()

event_counter = {'GRB': 0, 'SFLARE': 0, 'TGF': 0, 'SGR': 0, 'DISTPAR': 0}
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

    if row['event_type'] in event_counter and not (row['event_name'] in folder_names):
        if event_counter[row['event_type']] < event_limit:
            event_counter[row['event_type']] += 1
            event_type.append(row['event_type'])
            name.append(row['event_name'])

print('events to download\n',event_counter)

print(len(event_type))
print(len(name))

event_list = name
event_types = event_type

dir_path = tools.json_path(r'data_path.json')

# Function to process a single event
def process_event(event_name, event_type,thread_num):
    try:
        temp_thread = r'temp'+ str(thread_num)
        temp_path = os.path.join(dir_path, temp_thread)
        tools.create_folder(temp_path)
        event = event_name
        year = '20' + event[2:4] + "/"

        # URL of the file you want to download
        url = 'wget -q -nH --no-check-certificate --cut-dirs=7 -r -l0 -c -N -np -A "*_trigdat_*" -R "index*" -erobots=off --retr-symlinks https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/triggers/' + year + event + '/current/'
        tools.run_wget_download(url, temp_path)

        # Finding Trigdat file
        trig_string = "_trigdat_"
        trig_pattern = os.path.join(temp_path, 'current', f"*{trig_string}*")
        trigdat_file = glob.glob(trig_pattern)

        # Get the spacecraft pointing from here
        event_filename = trigdat_file[0]

        # Getting the RA and DEC
        with fits.open(event_filename, memmap=True) as pha_list:
            ra_obj, dec_obj = (pha_list[0].header['RA_OBJ']), (pha_list[0].header['DEC_OBJ'])


        brightest_nai, bright_nais, brightest_bgo = estimate_source_angles_detectors.angle_to_grb(ra_obj, dec_obj,event_filename)

        # URL of the tte file to download
        url = 'wget -q -nH --no-check-certificate --cut-dirs=7 -r -l0 -c -N -np -A "*_tte_' + brightest_nai + '_*" -R "index*" -erobots=off --retr-symlinks https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/triggers/' + year + event + '/current/'

        # Construct the wget command
        tools.run_wget_download(url, os.path.join(data_set_path, event_type + '_' + event))
        # Print the size of the queue
        print(event_queue.qsize()) 
    except Exception as e:
        print(f"Error processing event {event_name}: {e}")

# Create a queue to store the events
event_queue = Queue()

# Function to run the worker threads
def worker(thread_num):
    print(f"Worker thread {thread_num} started.")
    while True:
        # Get an event from the queue
        event_name, event_type = event_queue.get()

        # Process the event
        process_event(event_name, event_type,thread_num)

        # Signal that the task is completed
        event_queue.task_done()
        print(f"Worker thread {thread_num} processed event {event_name}.")

# Create and start the worker threads
num_threads = 128
threads = []
for i in range(num_threads):
    worker_thread = threading.Thread(target=worker, args=(i,), daemon=True)
    worker_thread.start()
    threads.append(worker_thread)

# Add events to the queue
for event_name, event_type in zip(event_list, event_types):
    event_queue.put((event_name, event_type))

# Wait for all events to be processed
event_queue.join()
print("All events have been processed.")

# Wait for all threads to finish
for thread in threads:
    thread.join()

print('done')