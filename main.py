import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from scipy import signal
from flask import Flask, redirect, url_for, render_template, request

sudoPassword = '****'
command = 'mount -t cifs -o username=*****,password=****** //192.168.0.100/OpenHardwareMonitor /home/daff/Documents/OpenHardwareGLADoS'
p = os.system('echo %s|sudo -S %s' % (sudoPassword, command))


def ListaTotal():
    listFileRAW = os.listdir("/home/daff/Documents/OpenHardwareGLADoS/")
    listFile=[]
    for item in listFileRAW:
        if item.find("OpenHardwareMonitorLog") != -1:
            listFile.append(item)
    return listFile

def Analitic(listFileA, hora):
    fileRAW = f"/home/daff/Documents/OpenHardwareGLADoS/{listFileA}"

    archivoRAW = pd.read_csv(fileRAW, low_memory=False) 
    archivoRAW = archivoRAW.drop(0)
    archivoRAW["Unnamed: 0"] = pd.to_datetime(archivoRAW["Unnamed: 0"], format="%m/%d/%Y %H:%M:%S")

    archivoRAW = archivoRAW.rename(columns={'Unnamed: 0': 'Time','/amdcpu/0/temperature/0': 'CPU Temp','/atigpu/0/temperature/0': 'GPU Temp','/atigpu/0/load/0': 'GPU Load','/amdcpu/0/load/0': 'CPU Load'})
    
    try:
        archivoHorasSelect = archivoRAW['Time'].dt.hour.to_numpy()
        archivoHorasSelect = np.where(archivoHorasSelect == int(hora))

        lim1 = np.min(archivoHorasSelect)
        lim2 = np.max(archivoHorasSelect)
    except:
        lim1 = 0
        lim2 = np.shape(archivoRAW['Time'].to_numpy())[0]
    

    def parce(columna,DataFrame,limitInf,limitSup,aFloat):
        val = DataFrame[columna][limitInf:limitSup].to_numpy()
        val = np.delete(val,0)

        if aFloat:
            val = val.astype(np.float64)
            val = np.round_(val, decimals = 2) 
        return val

    T = parce("Time",archivoRAW,lim1,lim2,False)
    CT = parce("CPU Temp",archivoRAW,lim1,lim2,True)
    CL = parce("CPU Load",archivoRAW,lim1,lim2,True)
    GT = parce("GPU Temp",archivoRAW,lim1,lim2,True)
    GL = parce("GPU Load",archivoRAW,lim1,lim2,True)

    fig, ax = plt.subplots(figsize=(50, 30))


    fs = 500  # Sampling frequency
    fc = 10  # Cut-off frequency of the filter #Tocar Esto si algo falla o no se ve como quiero + alto mas frecuencia + picos #base 1
    w = fc / (fs / 2) # Normalize the frequency
    b, a = signal.butter(5, w, 'low')
    output = signal.filtfilt(b, a, CT)
    ax.plot(T, output, color='b', label='CPU Temp')
    output = signal.filtfilt(b, a, CL)
    ax.plot(T, output, color='g', label='CPU Load')
    output = signal.filtfilt(b, a, GT)
    ax.plot(T, output, color='r', label='GPU Temp')
    output = signal.filtfilt(b, a, GL)
    ax.plot(T, output, color='k', label='GPU Load')


    xStep = int(lim2 / 35)

    plt.xlabel("Time", fontsize=30)
    plt.ylabel("Load/Temp", fontsize=30)
    plt.yticks(np.arange(0, 105, step=5), fontsize=30)

    plt.xticks(fontsize=30, rotation = 45)#T[np.arange(lim1, lim2-1, step=xStep)],
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

    plt.legend(loc = 'upper left', fontsize = 30)
    plt.ylim([0, 105])
    plt.grid()
    plt.ioff()
    plt.savefig("Graph.svg", bbox_inches = 'tight')
    #plt.show()
    return None
#Analitic("OpenHardwareMonitorLog-2021-11-15.csv", 16)


app = Flask(__name__,template_folder="/home/daff/Documents/OpenHardwareServerScripts")

@app.route("/", methods=['GET', 'POST'])
def index():
    
    if request.method == 'POST':
        if request.form.get('result') == 'Result':
            return redirect("/result") 
        else:
            pass # unknown
    elif request.method == 'GET':
        return redirect("/home")
    
    return render_template("index.html")

@app.route("/home", methods=['GET', 'POST'])
def parameterGraph():
    listFile = ListaTotal()
    
    dateListFile = ""
    for x in range(len(listFile)):
        dateListFile += f" <option value='{listFile[x]}'>{listFile[x]}</option>"
    
    dateList = ""
    for x in range(0,24):
        dateList += f" <option value='{x}'>{x}:00</option>"
    
    formularioHTML = f"""
            <html>
                <body>
                    <h3>Harware Monitor GLADoS<h3/>
                    <form method="post" action="/home">
                        <label for="dateListFile">Elegi una lista:</label>
                        <select name="dateListFile" id="dateListFile">
                            {dateListFile}
                        </select>
                        <br><br>
                        <label for="dateList">Elegi una hora:</label>
                        <select name="dateList" id="dateList">
                            {dateList}
                        </select>
                        <br><br>
                        <input type="submit" value="Result" name="result"/>
                    </form>
                </body>
            </html>"""
    
    if request.method == 'POST':
        dateListFile_Select = request.form['dateListFile']
        dateList_Select = request.form['dateList']
        print(dateListFile_Select,dateList_Select)
        Analitic(dateListFile_Select, dateList_Select)
        
        return render_template("Graph.html")
    

    return formularioHTML
   

if __name__ == "__main__":
    app.run("0.0.0.0")
    
