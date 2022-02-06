import numpy as np
import scipy.interpolate
import scipy.signal
import matplotlib.pyplot as plt
import os
import xml.etree.ElementTree as ET
import cv2


def gate(i):
    switcher = {
        100: (0, 0, 255),
        200: (0, 255, 0),
        300: (255, 255, 50),
        500: (255, 20, 117)
    }
    return switcher.get(i)


w = 5*10**-6  # channel_width
os.chdir("C:/Users/tele1/OneDrive/Desktop/polimi/Data/T gate/Data_1")
tree = ET.parse('sample.xml')
root = tree.getroot()

n_x = int(root.attrib['n_x'])
n_y = int(root.attrib['n_y'])
font = cv2.FONT_HERSHEY_SIMPLEX
img = np.zeros([n_x*80,  n_y*80,  3],  np.uint8)

for child in root:
    data_gd = 0
    vgs_list = 0
    name = child.get('id')
    ch_l = int(child[0].text)
    print(name)
    try:
        for file in os.listdir('.'):
            print(file)
            if file.find(name) > -1 and file.find("out") > -1:
                data_gd = np.genfromtxt(file, skip_header=1, skip_footer=1,
                                        names=True, delimiter='\t', dtype='float64')
                vgs_list = np.unique([row[0] for row in data_gd if ~np.isnan(row[0])])
        for z in vgs_list:
            x = []
            y = []
            for row in data_gd:
                if row[0] == z and row[1] != 0:
                    x.append(row[1])
                    y.append(row[3])
            plt.plot(x[0:len(x)-1], np.diff(y)/(np.diff(x)*w), label=z, linewidth=0.5)
            f = scipy.interpolate.interp1d(
                x[0:len(x)-1], np.diff(y)/(np.diff(x)*w), fill_value="extrapolate", kind='slinear')
            xx = np.linspace(min(x), max(x), 5000)
            yy = f(xx)
            window = scipy.signal.gaussian(200, 60)
            smoothed = scipy.signal.convolve(yy, window / window.sum(), mode='same')
            plt.plot(xx, smoothed, 'r--', linewidth=1)
            # print(xx[np.argmin(smoothed)])
        plt.legend(title='$\mathregular{V_{GS} (V)}$', title_fontsize=13)
        plt.title('$\mathregular{g_{d} vs V_{DS}}$', fontsize=20)
        plt.xlabel('$\mathregular{V_{DS} (V)}$', fontsize=15)
        plt.ylabel('$\mathregular{g_{d} (S/m)}$', fontsize=15)
        #plt.ylim(yy[np.argmin(smoothed)]-50, yy[np.argmax(smoothed)]+20)
        plt.savefig(name + 'gd.pdf')
        plt.close()
    except:
        print("An exception occurred")
