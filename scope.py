
from PyMCP2221A import PyMCP2221A
import time
import matplotlib.pyplot as plt
import numpy as np


#settings
pointcount = 10000

# Create an instance of the PyMCP2221A class
print("connecting to device")
mcp2221 = PyMCP2221A.PyMCP2221A()

# Reset the device
print("resetting device")
mcp2221.Reset()
# Wait for 1 second
time.sleep(1)
# Re-create the instance of the PyMCP2221A class
print ("reconnecting to device")
while True:
    try:
        mcp2221 = PyMCP2221A.PyMCP2221A()
        break
    except IndexError:
        time.sleep(1)
        print ("trying again")


mcp2221.GPIO_Init()
mcp2221.GPIO_1_InputMode()
mcp2221.GPIO_2_InputMode()
mcp2221.GPIO_3_InputMode()

# Initialize the ADC channels 1, 2 and 3
mcp2221.ADC_1_Init()
mcp2221.ADC_2_Init()
mcp2221.ADC_3_Init()
raw_data = [[0] * pointcount, [0] * pointcount, [0] * pointcount]
data     = [[0] * pointcount, [0] * pointcount, [0] * pointcount]
timepoint = [0] * pointcount
plots = [0]*6

starttime = time.time()

for i in range(pointcount):
    try:
        #send samplecommand
        mcp2221.ADC_DataRead()

        timepoint[i] = time.time() - starttime

        raw_data[0][i] = mcp2221.ADC_1_data # ADC Data (10-bit) values
        raw_data[1][i] = mcp2221.ADC_2_data # ADC Data (10-bit) values
        raw_data[2][i] = mcp2221.ADC_3_data # ADC Data (10-bit) values
        if i % 100 == 99:
            print(f"sampled to value {i+1}")
    except:
        timepoint = timepoint[:i-1]
        raw_data[0], raw_data[1], raw_data[2] = raw_data[0][:i-1], raw_data[1][:i-1], raw_data[2][:i-1]
        print(f"an error happened during reading\nrescuing data read by now\nsaved {i-1} data points")
        break

data [0] = [i/2**10*3.3 for i in raw_data[0]]
data [1] = [i/2**10*3.3 for i in raw_data[1]]
data [2] = [i/2**10*3.3 for i in raw_data[2]]

# calculate the number of samples and the total time
n = len(data[0]) # assume data[0] and data[1] have the same length
t = timepoint[n-1] - timepoint[0]
# create a time array from 0 to t with n points
sampletime = np.linspace(0, t, n)

# plot the data in the time domain using subplots
plots[0] = plt.subplot(2, 3, 1) # first row, first column
plt.plot(sampletime, data[0], 'b-') # plot data[0] in blue
plt.xlabel('Time (s)') # label the x-axis
plt.ylabel('Channel 1') # label the y-axis

plots[1] = plt.subplot(2, 3, 2) # first row, second column
plt.plot(sampletime, data[1], 'r-') # plot data[1] in red
plt.xlabel('Time (s)') # label the x-axis
plt.ylabel('Channel 2') # label the y-axis

plots[2] = plt.subplot(2, 3, 3) # first row, second column
plt.plot(sampletime, data[2], 'g-') # plot data[1] in red
plt.xlabel('Time (s)') # label the x-axis
plt.ylabel('Channel 3') # label the y-axis

# apply fft to both channels and get the absolute values
fft0 = np.abs(np.fft.fft(data[0])) / n
fft1 = np.abs(np.fft.fft(data[1])) / n
fft2 = np.abs(np.fft.fft(data[2])) / n

# calculate the frequency array using fftfreq and deltat
freq = np.fft.fftfreq(n, t/n)

# plot the data in the frequency domain using subplots
plots[3] = plt.subplot(2, 3, 4) # second row, first column
plt.plot(freq, fft0, 'b-') # plot fft0 in blue
plt.xlabel('Frequency (Hz)') # label the x-axis
plt.ylabel('Channel 1') # label the y-axis

plots[4] = plt.subplot(2, 3, 5) # second row, second column
plt.plot(freq, fft1, 'r-') # plot fft1 in red
plt.xlabel('Frequency (Hz)') # label the x-axis
plt.ylabel('Channel 2') # label the y-axis

plots[5] = plt.subplot(2, 3, 6) # second row, second column
plt.plot(freq, fft2, 'g-') # plot fft1 in red
plt.xlabel('Frequency (Hz)') # label the x-axis
plt.ylabel('Channel 3') # label the y-axis

# adjust the layout and show the plot
plt.tight_layout()
# Show the final plot
plt.show()