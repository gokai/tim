
import os
import subprocess
import mimetypes

from tkinter import *
from tkinter.ttk import *

from db import FileDatabase
from tkgraphics import SlideShow, Gallery

class BaseView(object):

    def __init__(self):
        self.root = Tk()
        self.root.title('GICM')
        self.root.bind_all('<Control-q>', lambda e: self.quit())
        self.root.focus_force()
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.menubar = Menu(self.root)
        self.root['menu'] = self.menubar
        self.menubar.add_command(command=self.quit, label='Quit')
        self.create_view()
        self.bind_events()

    def display(self):
        self.root.mainloop()

    def bind_events(self):
        pass

    def quit(self):
        self.root.quit()
        self.root.destroy()

class FileView(BaseView):

    def __init__(self, files, keys):
        self.files = files
        self.keys = keys
        self.tree_ids = dict()
        self.images = list()
        self.img_view = None
        self.gall = None
        super(FileView, self).__init__()

    def create_view(self):
        self.view = Treeview(self.root, columns=self.keys[1:])
        self.view.grid(column=0, row=0, sticky=(N, S, W, E))

        self.view.heading('#0', text=self.keys[0])
        for key in self.keys[1:]:
            self.view.heading(key, text=key)

        self.index = 0
        self.root.after(50, self.load_row)

    def bind_events(self):
        slide_fun = lambda e: self.slide()
        self.view.bind('<Double-1>',slide_fun)
        self.view.bind('<s>', slide_fun)
        self.view.bind('<g>', self.gallery)

    def get_selection_paths(self):
        sel = self.view.selection()
        fli = (self.tree_ids[i] for i in sel)
        return [os.path.join(f['path'], f['name']) for f in fli]

    def slide(self, indexes=None):
        paths = self.get_selection_paths()
        if indexes is not None:
            paths = [paths[i] for i in indexes]
        if self.gall is None:
            self.root.rowconfigure(1, weight=0)
        ss = SlideShow(self.root, paths)
        ss.winfo_width=self.root.winfo_width
        ss.winfo_height= lambda : self.root.winfo_height()/2
        ss.grid(column=0, row=1)
        ss.focus_set()
        ss.bind('<q>', lambda e: ss.destroy())
        if self.img_view is not None:
            self.img_view.destroy()
        self.img_view = ss

    def gallery(self, event=None):
        if self.gall is not None:
            self.gall.destroy()
        paths = self.get_selection_paths()
        self.root.rowconfigure(1, weight=1)
        g = Gallery(self.root, paths, (200, 200), self.slide)
        g.winfo_width = self.root.winfo_width
        g.winfo_height = lambda : self.root.winfo_height()/2
        g.grid(column=0, row=1, sticky=(N, W, S, E))
        g.focus_set()
        g.bind('<q>', lambda e: g.destroy())
        self.gall = g

    def load_row(self):
        f = self.files[self.index]
        tid = self.view.insert('', 'end', text=f[self.keys[0]], values=(','.join(f[self.keys[1]]),))
        self.tree_ids[tid] = f
        self.index += 1
        if self.index < len(self.files):
            self.root.after_idle(self.load_row)

if __name__ == "__main__":
    db = FileDatabase('/media/files/koodi/tagged_file_manager/master.sqlite')
    li = db.search_by_tags(['nsfw'])
    gui = FileView(li[:500], ('name', 'tags'))
    gui.display()

