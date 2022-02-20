import os
import numpy as np
import scipy.interpolate
import scipy.signal
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import cv2
from github_custom_module.cust_mod import Folder_Path, db_conn, cycle

w = 5*10**-6  # channel_width

Folder_Path.set_folder_path()

tree = ET.parse('sample.xml')
root = tree.getroot()
n_x = int(root.attrib['n_x'])
n_y = int(root.attrib['n_y'])
font = cv2.FONT_HERSHEY_SIMPLEX
img = np.zeros([n_x*80,  n_y*80,  3],  np.uint8)


for child in root:
    data_gm = 0
    vds_list = 0
    name = child.get('id')
    serves_for = child.get('serves_for')
    ch_l = int(child[0].text)
    print(name)
    img = cv2.rectangle(img, ((int(name[1]))*80-80, (n_y - int(name[0]))*80),
                        ((int(name[1]))*80, (n_y - int(name[0]))*80-80), db_conn(ch_l).db_conn(loc_host="127.0.0.1" , user = "root" , db ="tutorial_sql", db_tab="gate_polimi"), -1)
    img = cv2.putText(img, name, ((
        int(name[1]))*80 - 80, (n_y - int(name[0]))*80-10), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imwrite('map.png', img)
    try:
        for file in os.listdir('.'):
            if file.find(name) > -1 and file.find("tr") > -1:
                data_gm = np.genfromtxt(file, skip_header=1, skip_footer=1,
                                        names=True, delimiter='\t', dtype='float64')
                vds_list = np.unique([row[0] for row in data_gm if ~np.isnan(row[0])])
        for z in vds_list:
            x = []
            y = []
            cycle(dtable = data_gm, z=z, x=x, y=y)
            plt.plot(x[0:len(x)-1], np.diff(y)/(np.diff(x)*w), label=z, linewidth=0.5)
            f = scipy.interpolate.interp1d(
                x[0:len(x)-1], np.diff(y)/(np.diff(x)*w), fill_value="extrapolate", kind='slinear')
            xx_0 = np.linspace(min(x), max(x), 5000)
            yy_0 = f(xx_0)
            nan_wh = list(map(tuple, np.where(np.logical_not(np.isfinite(yy_0)))))
            print(nan_wh)
            yy_1 = np.delete(yy_0, nan_wh)
            xx_1 = np.delete(xx_0, nan_wh)
            window = scipy.signal.gaussian(200, 60)
            smoothed = scipy.signal.convolve(yy_1, window / window.sum(), mode='same')
            plt.plot(xx_1, smoothed, 'r--', linewidth=1)
            # print(xx[np.argmin(smoothed)])
        plt.legend(title='$\mathregular{V_{DS} (V)}$', title_fontsize=13)
        plt.title('$\mathregular{g_{m} vs V_{GS}}$', fontsize=20)
        plt.xlabel('$\mathregular{V_{GS} (V)}$', fontsize=15)
        plt.ylabel('$\mathregular{g_{m} (S/m)}$', fontsize=15)
        plt.ylim(yy_0[np.argmin(smoothed)]-50, yy_0[np.argmax(smoothed)]+20)
        plt.savefig(name + 'gm.pdf')
        plt.close()
    except:
        print("An exception occurred")

#plt.scatter(freq_max, s=area, c=colors, alpha=0.5)
