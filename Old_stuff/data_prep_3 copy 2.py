import os
from pathlib import Path
from astropy.io import fits
import numpy as np
import glob
import time
from multiprocessing import Pool, cpu_count
from Calculating_det_angles import estimate_source_angles_detectors
from Tools import tools
from tqdm import tqdm

def process_folder(folder):
    try:
        event_type, event = folder.split("_")
        year = '20' + event[2:4] + "/"
        target_string = "_tte_"
        file_pattern = str(source_data_set_path / folder / 'current' / f"*{target_string}*")
        NaI_detector = glob.glob(file_pattern)

        with fits.open(NaI_detector[0], memmap=True) as hdul:
            energy_channel_data = hdul[1].data
            all_count_data = hdul[2].data['COUNTS'].astype(float)

        data_array = []
        for i in bin_list:
            range_min = ti[0]
            range_max = ti[-1]
            bin_size = i
            bin_edges = np.arange(range_min, range_max, bin_size)
            hist, _ = np.histogram(all_count_data, bins=bin_edges)
            data_array.extend(hist)

        data_array = np.array(data_array)
        data_file_path = data_set_path / f"{event_type}_{event}"
        np.savetxt(str(data_file_path), data_array, fmt='%d', delimiter='\t')

    except Exception as e:
        print(f'error {e} in {folder}')
        traceback.print_exc()
        error_folders.append(folder)

start_time = time.time()

source_data_set_path = Path(r"C:\Users\arpan\OneDrive\Documents\GRB\data\500_data_set")
folders = [str(folder) for folder in os.listdir(source_data_set_path) if os.path.isdir(os.path.join(source_data_set_path, folder))]
bin_list = [0.01, 0.1, 0.5, 1, 5]
ti = [-50, 100]
t = ti[1] - ti[0]
data_no = sum(int(t / i) for i in bin_list)
print('number of data points', data_no)

dir_path = Path(tools.json_path(r'data_path.json'))
data_set_name = "dp01-04-2"
data_set_path = dir_path / data_set_name
data_set_path.mkdir(parents=True, exist_ok=True)

print('start')
print('total :', len(folders))

params_dict = {"bin list": bin_list, "time interval": ti, "number of data points": data_no, "data set name": data_set_name, "data set path": str(data_set_path)}
write_json_file = tools.write_json_file(params_dict, data_set_path / 'params.json')

error_folders = []

# Use multiprocessing
with Pool(processes=cpu_count()) as pool:
    for _ in tqdm(pool.imap_unordered(process_folder, folders), total=len(folders), desc="Processing folders", unit="folder"):
        pass

print('\n----------------------------------------------------------------------------\n\nevents', folders, ' in folder', data_set_path)
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Elapsed Time: {elapsed_time:.2f} seconds")