
from tkinter import Toplevel, Listbox, StringVar, N, S, W, E, EXTENDED
from tkinter.ttk import Label, Button

class ListDialog(object):
    def __init__ (self, master, items, message, accept_func):
        self.listvar = StringVar()
        self.listvar.set(' '.join(items))
        self.accept_func = accept_func
        self.items = items

        self.top = Toplevel(master)
        self.top.transient(master)
        self.top.rowconfigure(0, weight=1)
        self.top.rowconfigure(1, weight=3)
        self.top.rowconfigure(2, weight=0)
        self.top.columnconfigure(0, weight=1)
        self.top.columnconfigure(1, weight=1)
        self.top.resizable(width=True, height=True)

        self.label = Label(self.top, text=message)
        self.label.grid(row=0, column=0, columnspan=2, sticky=(N, W))

        self.listbox = Listbox(self.top, selectmode=EXTENDED, listvariable=self.listvar)
        self.listbox.grid(row=1, column=0, columnspan=2, sticky=(N, W, E, S))

        self.delbutton = Button(self.top, text='Ok', command=self.accept )
        self.cancelbutton = Button(self.top, text='Cancel', command=self.cancel)
        self.delbutton.grid(row=2, column=0)
        self.cancelbutton.grid(row=2, column=1)

    def accept(self):
        result = self.listbox.curselection()
        self.accept_func([self.items[i] for i in result])
        self.top.destroy()

    def cancel(self):
        self.result = None
        self.top.destroy()
