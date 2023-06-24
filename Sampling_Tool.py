
from PyMCP2221A import PyMCP2221A
import time
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk 
import threading

class window (tk.Tk):
    def __init__(self):
        super().__init__()
        self.title = "Sensorauswertung"
        self.status = tk.Label(self)
        self.value  = tk.Label(self)
        self.stopButton = tk.Button(self, text="stop sampling", command=self.stop_sampling)
        self.plotButton = tk.Button(self, text="plot", command=plot)

        self.status.pack()
        self.value.pack()
        self.stopButton.pack()
        self.plotButton.pack()


    def mainloop(self, n: int = 0) -> None:
        self.update_value()
        self.update_status()
        super().mainloop(n)

    def stop_sampling(self):
        global RunADC 
        RunADC = False

    def update_value(self):
        global currentValue
        # Update the label text with the ADC value
        Bfield = np.round(currentValue * 1000, 3)
        self.value.config(text=f"current magnetic field: {Bfield} mT")

        # Schedule the next update
        self.value.after(100, self.update_value)


    def update_status(self):
        global MCP2221status
        # Update the label text with the ADC value
        self.status.config(text=MCP2221status)

        # Schedule the next update
        self.status.after(100, self.update_status)
    


MCP2221status = "nothing"
currentValue = 0
raw_data =  []
data     =  []
timepoint = []
movingAverageRingBuffer = [0]*200
RunADC = True

def connect_MCP2221() -> PyMCP2221A.PyMCP2221A:
    global MCP2221status
    # Create an instance of the PyMCP2221A class
    MCP2221status = "connecting to device"
    while True:
        try:
            mcp2221 = PyMCP2221A.PyMCP2221A()
            break
        except IndexError:
            time.sleep(1)
            MCP2221status = "connection failed, trying again"

    # Reset the device
    MCP2221status = "resetting device"
    mcp2221.Reset()
    # Wait for 1 second
    time.sleep(1)
    # Re-create the instance of the PyMCP2221A class
    MCP2221status = "reconnecting to device"
    while True:
        try:
            mcp2221 = PyMCP2221A.PyMCP2221A()
            break
        except IndexError:
            time.sleep(1)
    MCP2221status = "reconnecting to device, might take some time"
    return mcp2221

def initMCP2221A(mcp2221 : PyMCP2221A.PyMCP2221A) -> None:
    global MCP2221status
    MCP2221status = "initialising"
    mcp2221.GPIO_Init()
    mcp2221.GPIO_3_InputMode()

    # Initialize the ADC channel 2
    mcp2221.ADC_3_Init()

def sample(mcp2221 : PyMCP2221A.PyMCP2221A) -> int:
        mcp2221.ADC_DataRead()
        return mcp2221.ADC_3_data

def adcToVoltage(bits : int, Vref : float, adcvalue : int) -> float:
    return adcvalue * Vref /(2**bits)

def voltageToField(voltage : float) -> float:
    gain = 120
    return (voltage - 0.6) / gain


starttime = time.time()
def sampleloop(mcp2221 : PyMCP2221A.PyMCP2221A):
    global MCP2221status
    global data
    global timepoint
    global currentValue
    global movingAverageRingBuffer
    mcp2221.ADC_DataRead()
    movingAverageIndex = 0
    while True:
        try:
            #send samplecommand
            currentValue = voltageToField(adcToVoltage(10, 3.3, mcp2221.ADC_3_data))
            timepoint.append( time.time() - starttime)
            data.append(currentValue) # ADC Data (10-bit) values
            movingAverageRingBuffer
            movingAverageIndex +=1
            if movingAverageIndex >= len(movingAverageRingBuffer):
                movingAverageIndex = 0
            if len(timepoint) % 100 == 0:
                MCP2221status = f"sampled to value {len(timepoint)}"
            mcp2221.ADC_DataRead()
        except OSError:
            MCP2221status = f"an error happened during reading\nrescuing data read by now\nsaved {len(timepoint)} data points"
            break
        if not RunADC:
            MCP2221status = "halted sampling"
            break

def samplethread():
    mcp2221a = connect_MCP2221()
    initMCP2221A(mcp2221a)
    sampleloop(mcp2221a)






def plot():
    """
        function to plot data from global arrays data and timepoints
    """
    global data
    global timepoint

    # calculate the number of samples and the total time
    n = len(data)
    t = timepoint[n-1] - timepoint[0]

    plt.subplot(1, 2, 1) # first row, second column
    plt.plot(timepoint, data, 'r-') # plot data[1] in red
    plt.xlabel('Time (s)') # label the x-axis
    plt.ylabel('Magnetic Field (T)') # label the y-axis

    # apply fft to both channels and get the absolute values
    fft1 = np.abs(np.fft.fft(data)) / n

    fft1 = np.multiply(20, np.log10(fft1))

    # calculate the frequency array using fftfreq and deltat
    freq = np.fft.fftfreq(n, t/n)

    plt.subplot(1, 2, 2) # second row, second column
    plt.plot(freq, fft1, 'r-') # plot fft1 in red
    plt.xlabel('Frequency (Hz)') # label the x-axis
    plt.ylabel('DB') # label the y-axis

    # adjust the layout and show the plot
    plt.tight_layout()
    # Show the final plot
    plt.show()

if (__name__ == "__main__"):
    adc_thread = threading.Thread(target=samplethread)
    adc_thread.daemon = True  # Allow the thread to exit when the main program finishes
    adc_thread.start()
    win = window()
    win.mainloop()
    RunADC = False
    adc_thread.join()