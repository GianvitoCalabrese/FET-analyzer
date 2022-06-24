import os
import numpy as np
import scipy.interpolate
import scipy.signal
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import cv2
from github_custom_module.cust_mod import Folder_Path, db_conn, cycle

try:
    import tkinter as tk                # python 3
    from tkinter import filedialog
    from tkinter import font as tkfont  # python 3
except ImportError:
    import Tkinter as tk     # python 2
    from Tkinter import filedialog
    import tkFont as tkfont  # python 2

class Transistor:
    def __init__(self):
        pass

class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, PageOne, PageTwo):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()

    def set_fld_path(self):
        Folder_Path.set_folder_path()
        print(Folder_Path.set_folder_path())
        tree = ET.parse('sample.xml')
        self.root = tree.getroot()   
        self.n_x = int(self.root.attrib['n_x'])
        self.n_y = int(self.root.attrib['n_y'])
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.img = np.zeros([self.n_x*80,  self.n_y*80,  3],  np.uint8)

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is the start page", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        button1 = tk.Button(self, text="Go to Page One",
                            command=lambda: controller.show_frame("PageOne"))
        button2 = tk.Button(self, text="Go to Page Two",
                            command=lambda: controller.show_frame("PageTwo"))
        button3 = tk.Button(self, text="Set the Folder Path",
                            command=lambda: controller.set_fld_path())
        button1.pack()
        button2.pack()
        button3.pack()




class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is page 1", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button1 = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("StartPage"))
        button2 = tk.Button(self, text="wf_map",
                           command=lambda: PageOne.wf_map(self))

        button1.pack()
        button2.pack()

    def wf_map(self):
        for child in self.controller.root:
            data_gm = 0
            vds_list = 0
            name = child.get('id')
            serves_for = child.get('serves_for')
            ch_l = int(child[0].text)
            print(name)
            self.controller.img = cv2.rectangle(self.controller.img, ((int(name[1]))*80-80, (self.controller.n_y - int(name[0]))*80),
                            ((int(name[1]))*80, (self.controller.n_y - int(name[0]))*80-80), db_conn(ch_l).db_conn(loc_host="127.0.0.1" , user = "root" , db ="tutorial_sql", db_tab="gate_polimi"), -1)
            self.controller.img = cv2.putText(self.controller.img, name, ((
            int(name[1]))*80 - 80, (self.controller.n_y - int(name[0]))*80-10), self.controller.font, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imwrite('map.png', self.controller.img)


class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is page 2", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button1 = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("StartPage"))
        
        button1.pack()

    



if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()