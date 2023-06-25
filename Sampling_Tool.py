
from PyMCP2221A import PyMCP2221A
import time
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk 
import threading
import serial

class window (tk.Tk):
    grid_buttons : list[list[list[tk.Button]]]
    def __init__(self):
        global xvalues
        global yvalues
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

        grid_frame = tk.Frame(self)
        grid_frame.pack()

        self.rows = rows = 4
        self.cols = cols = 5
        xvalues = [[0] * cols for _ in range(rows)]
        yvalues = [[0] * cols for _ in range(rows)]
        self.grid_buttons = [[[None]*4 for c in range(cols)] for r in range(rows)]  # 2D array to store the button references

        # Create the grid of cells with buttons
        for i in range(rows):
            for j in range(cols):
                # Create a button and associate it with array coordinates
                grid_pos = tk.Frame(grid_frame)

                button1 = tk.Button(grid_pos, text="", command=lambda row=i, col=j, dir=0: self.button_set_field(row, col, dir))
                self.grid_buttons[i][j][0] = button1
                button1.grid(row=0, column=1)

                button2 = tk.Button(grid_pos, text="", command=lambda row=i, col=j, dir=2: self.button_set_field(row, col, dir))
                self.grid_buttons[i][j][2] = button2
                button2.grid(row=2, column=1)

                button3 = tk.Button(grid_pos, text="", command=lambda row=i, col=j, dir=1: self.button_set_field(row, col, dir))
                self.grid_buttons[i][j][1] = button3
                button3.grid(row=1, column=0)

                button4 = tk.Button(grid_pos, text="", command=lambda row=i, col=j, dir=3: self.button_set_field(row, col, dir))
                self.grid_buttons[i][j][3] = button4
                button4.grid(row=1, column=2)

                grid_pos.grid(row=i, column=j)

    def button_set_field(self, row, col, dir):
        global movingAverageRingBuffer
        direction = dir % 2
        if direction == 0:
            xvalues[row][col] = (-1 if dir == 0 else 1)*np.average(movingAverageRingBuffer)
        else:
            yvalues[row][col] = (-1 if dir == 1 else 1)*np.average(movingAverageRingBuffer)
        self.grid_buttons[row][col][direction].config(text="ok")
        self.grid_buttons[row][col][direction + 2].config(text="ok")


    def button_clicked(self, row, col, dir):
        # Update the button text and the corresponding array position
        button = self.grid_buttons[row][col][dir]
        button_text = button.cget("text")
        new_text = "X" if button_text == "" else ""
        button.config(text=new_text)
        self.update_array(row, col, dir, new_text)

    def update_array(self, row, col, dir, new_text):
        # Update the 2D array with the new text
        # Replace this with your own logic to update the actual data structure
        print(f"Updating array position ({row}, {col}, {dir}) with '{new_text}'")


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
movingAverageRingBuffer = [0]*50
RunADC = True

xvalues : list[list[float]] = [[]]
yvalues : list[list[float]] = [[]]

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
    ser = serial.Serial('/dev/ttyUSB0', 250000)
    ser.flush()
    ser.readline().decode().strip()
    #mcp2221.ADC_DataRead()
    movingAverageIndex = 0
    while True:
        try:
            #send samplecommand
            currentValue = voltageToField(adcToVoltage(12, 2.5, int(ser.readline().decode().strip())))
            timepoint.append( time.time() - starttime)
            data.append(currentValue) # ADC Data (10-bit) values
            movingAverageRingBuffer[movingAverageIndex] = currentValue
            movingAverageIndex +=1
            if movingAverageIndex >= len(movingAverageRingBuffer):
                movingAverageIndex = 0
            if len(timepoint) % 100 == 0:
                MCP2221status = f"sampled to value {len(timepoint)}"
            #mcp2221.ADC_DataRead()
        except OSError:
            MCP2221status = f"an error happened during reading\nrescuing data read by now\nsaved {len(timepoint)} data points"
            break
        if not RunADC:
            MCP2221status = "halted sampling"
            break

def samplethread():
#    mcp2221a = connect_MCP2221()
#    initMCP2221A(mcp2221a)
    sampleloop(None)






def plot():
    """
        function to plot data from global arrays data and timepoints
    """
    global data
    global timepoint
    L_data = data.copy()
    L_timepoint = timepoint.copy()



    # calculate the number of samples and the total time
    n = min(len(L_data), len(L_timepoint))
    L_data = L_data[1:n-1]
    L_timepoint = L_timepoint[1:n-1]
    n = len(L_data)
    t = L_timepoint[n-1] - L_timepoint[0]

    plt.subplot(1, 2, 1) # first row, second column
    plt.plot(L_timepoint, L_data, 'r-') # plot data[1] in red
    plt.xlabel('Time (s)') # label the x-axis
    plt.ylabel('Magnetic Field (T)') # label the y-axis

    # apply fft to both channels and get the absolute values
    fft1 = np.abs(np.fft.fft(L_data)) / n

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
    
    # Create a meshgrid from the array shape
    X, Y = np.meshgrid(np.arange(len(xvalues[0])), np.arange(len(xvalues)))

    # Convert the xvalues and yvalues arrays to numpy arrays
    U = np.array(xvalues)
    V = np.array(yvalues)

    # Create a new figure and axis
    fig, ax = plt.subplots()

    # Plot the vectors using the quiver function
    ax.quiver(X, Y, U, V)

    # Customize the plot as desired
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Sensor Data Vector Plot')

    # Show the plot
    plt.show()

if (__name__ == "__main__"):
    adc_thread = threading.Thread(target=samplethread)
    adc_thread.daemon = True  # Allow the thread to exit when the main program finishes
    adc_thread.start()        # start sampling thread
    win = window()
    win.mainloop()            # run UI
    RunADC = False            # close sampling thread when UI is closed
    adc_thread.join()