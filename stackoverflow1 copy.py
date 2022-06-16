
#https://stackoverflow.com/questions/34817328/creating-frames-in-tkinter
import tkinter as tk


class MainApp(tk.Frame):

    def __init__(self, parent):

        tk.Frame.__init__(self, parent, bg="blue")
        self.parent = parent

        button = tk.Button(parent, text="a button")
        button.pack()


root = tk.Tk()
root.geometry("200x200+300+300")
root.config(background="yellow")
app = MainApp(root)
app.pack(fill="both", expand=True)
root.mainloop()