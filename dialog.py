
from tkinter import Toplevel, Listbox, Canvas, StringVar, N, S, W, E, EXTENDED, NW, HORIZONTAL, SCROLL, UNITS
from tkinter.ttk import Label, Button, Scrollbar, Frame

from tagview import NameView

class ListDialog(object):
    def __init__ (self, master, items, message, accept_func):
        self.accept_func = accept_func

        self.top = Toplevel(master)
        self.top.transient(master)
        self.top.rowconfigure(0, weight=1)
        self.top.rowconfigure(1, weight=3)
        self.top.rowconfigure(2, weight=0)
        self.top.columnconfigure(0, weight=1)
        self.top.columnconfigure(1, weight=1)
        self.top.resizable(width=True, height=True)

        self.frame = Frame(self.top)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=0)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=0)
        self.frame.grid(row=0, column=0, sticky=(N, S, W, E), columnspan=2)
        self.canvas = Canvas(self.frame)
        self.canvas.create_text(0, 0, text=message, anchor=NW)
        self.canvas.grid(row=0, column=0, sticky=(N, W, S, E))

        self.vscroll = Scrollbar(self.frame, command=self.canvas.yview)
        self.vscroll.grid(row=0, column=1, sticky=(N, S))
        self.canvas['yscrollcommand'] = self.vscroll.set

        self.hscroll = Scrollbar(self.frame, command=self.canvas.xview, orient=HORIZONTAL)
        self.hscroll.grid(row=1, column=0, sticky=(W, E), columnspan=2)
        self.canvas['xscrollcommand'] = self.hscroll.set

        self.canvas['scrollregion'] = self.canvas.bbox('all')
        self.canvas.bind('<Button-4>', self.scroll)
        self.canvas.bind('<Button-5>', self.scroll)
        self.canvas.bind('<MouseWheel>', self.scroll)

        self.view = NameView(self.top, sorted(items))
        self.view.widget.grid(row=1, column=0, columnspan=2, sticky=(N, W, E, S))

        self.delbutton = Button(self.top, text='Ok', command=self.accept )
        self.cancelbutton = Button(self.top, text='Cancel', command=self.cancel)
        self.delbutton.grid(row=2, column=0)
        self.cancelbutton.grid(row=2, column=1)
        self.view.widget.focus_set()

    def accept(self):
        self.accept_func(self.view.selection())
        self.top.destroy()

    def cancel(self):
        self.result = None
        self.top.destroy()

    def scroll(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview(SCROLL, -1, UNITS)
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview(SCROLL, 1, UNITS)
