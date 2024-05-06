# importing all needed functions
import os
from astropy.io import fits
import numpy as np
import glob
import time
import threading
from Tools import tools
import random

class dp_3_1d(threading.Thread):
    def __init__(self,threadID,folders,source_data_set_path,data_set_path):
        threading.Thread.__init__(self)
        self.threadID=threadID
        # setting the parameters
        self.folders = folders
        self.source_data_set_path = source_data_set_path
        self.data_set_path = data_set_path

        # list of bin sizes
        self.bin_list = [0.001,0.005,0.01,0.1,0.5,1,5]

        # time interval around trigger
        self.ti = [-5,20]
        self.t = self.ti[1] - self.ti[0]

        # number of datapoints in a light curve
        self.data_no = int(self.t / min(self.bin_list)) 
        print('number of data point' , self.data_no)
        
        print('starting thread ' , threadID)
        print('total : ',len(self.folders))

    def run(self):
        c = 0
        for folder in self.folders:
            try:
                event_type,event = folder.split("_")

                # Use the glob module to search for TTE files in the directory
                target_string = "_tte_"
                file_pattern = os.path.join(self.source_data_set_path,folder,'current', f"*{target_string}*")
                NaI_detector = glob.glob(file_pattern)

                # print('NaI_detector used',NaI_detector[0])

                # fetchinng data
                with fits.open(NaI_detector[0], memmap=True) as hdul:
                    # energy_channel_data = hdul[1].data.copy()
                    all_count_data = np.array(hdul[2].data.copy())

                # getting counts accross all energy channels
                counts = [float(sublist[0]) for sublist in all_count_data]

                data_array = []

                for i in self.bin_list:
                    # Define the range and number of bins
                    range_min = self.ti[0]
                    range_max = self.ti[-1]
                        
                    bin_size = i

                    # Create bin edges
                    bin_edges = np.arange(range_min, range_max, bin_size)

                    # Create the histogram using numpy.histogram
                    hist, edges = np.histogram(counts, bins=bin_edges)

                    data_array = data_array + list(hist)

                data_array = np.array(data_array)

                # Save the 2D array to a text file
                data = os.path.join(self.data_set_path,event_type+'_'+event)
                np.savetxt(data, data_array, fmt='%d', delimiter='\t')
                c += 1
                print(f'saved to {data} : {len(self.folders)-c} remaining in thread:',self.threadID)#, end = '\r')
            except Exception as e:
                print(f'error {e} in ',folder)


# Measure execution time
start_time = time.time()

# setting the parameters
# name of the data set
source_data_set_path = r"C:\Users\arpan\OneDrive\Documents\GRB\data\100_data_set"

dir_path = tools.json_path(r'data_path.json')
data_set_name = "dp3-1d-6"

# creating the data set folder
data_set_path = os.path.join(dir_path,data_set_name)
tools.create_folder(data_set_path)

# Get a list of all folders in the specified directory
folders = [str(folder) for folder in os.listdir(source_data_set_path) if os.path.isdir(os.path.join(source_data_set_path, folder))]
random.shuffle(folders)

# splitting the folers between threads
folders1,folders2 = np.array_split(folders,2)

threadLock = threading.Lock()
threads=[]

# Creating threads
thread1 = dp_3_1d(1,folders1,source_data_set_path,data_set_path)
thread2 = dp_3_1d(2,folders2,source_data_set_path,data_set_path)

# starting threads
thread1.start()
threads.append(thread1)
thread2.start()
threads.append(thread2)


# wait for all the threads to complete
for t in threads:  
    t.join()



print('\n----------------------------------------------------------------------------\n\nevents', folders, ' in folder', data_set_path)

end_time = time.time()

# Calculate and print the elapsed time
elapsed_time = end_time - start_time
print(f"Elapsed Time: {elapsed_time:.2f} seconds")