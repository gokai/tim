
import os
import subprocess
import mimetypes

from tkinter import *
from tkinter.ttk import *

from db import FileDatabase
from tkgraphics import SlideShow, Gallery

class FileView(Frame):

    def __init__(self, main, files, keys):
        self.files = files
        self.keys = keys
        self.tree_ids = dict()
        self.images = list()
        self.main = main
        self.img_view = None
        self.gall = None
        super(FileView, self).__init__(main.root)
        self.create_view()
        self.bind_events()

    def create_view(self):
        self.view = Treeview(self.main.root, columns=self.keys[1:])
        self.view.grid(column=0, row=0, sticky=(N, S, W, E))

        self.view.heading('#0', text=self.keys[0])
        for key in self.keys[1:]:
            self.view.heading(key, text=key)

        self.index = 0
        self.after(50, self.load_row)

    def bind_events(self):
        slide_fun = lambda e: self.slide()
        self.view.bind('<Double-1>',slide_fun)
        self.view.bind('<s>', slide_fun)
        self.view.bind('<g>', self.gallery)


    def quit(self):
        self.main.root.quit()
        self.main.root.destroy()

    def get_selection_paths(self):
        sel = self.view.selection()
        fli = (self.tree_ids[i] for i in sel)
        return [os.path.join(f['path'], f['name']) for f in fli]

    def slide(self, indexes=None):
        paths = self.get_selection_paths()
        if indexes is not None:
            paths = [paths[i] for i in indexes]
        ss = SlideShow(self.main.root, paths)
        self.main.new_view(ss)

    def gallery(self, event=None):
        paths = self.get_selection_paths()
        g = Gallery(self.main.root, paths, (200, 200), self.slide)
        self.main.new_view(g)

    def load_row(self):
        f = self.files[self.index]
        tid = self.view.insert('', 'end', text=f[self.keys[0]], values=(','.join(f[self.keys[1]]),))
        self.tree_ids[tid] = f
        self.index += 1
        if self.index < len(self.files):
            self.after_idle(self.load_row)

class Main(object):

    def __init__(self):
        self.root = Tk()
        self.root.title('GICM')
        self.root.bind_all('<Control-q>', lambda e: self.quit())
        self.root.bind_all('<Control-w>', lambda e: self.next_view())
        self.root.focus_set()
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.menubar = Menu(self.root)
        self.root['menu'] = self.menubar
        self.menubar.add_command(command=self.quit, label='Quit')
        self.views = list()
        self.cur_view = 0

    def new_view(self, view):
        # 'puskurit' ala vim, mahd. tabit/listaus näkyviin
        if len(self.views) >= 1:
            self.views[-1].grid_remove()
        self.views.append(view)
        view.grid(column=0, row=0, sticky=(N, W, S, E))
        view.focus_set()
        view.bind('q', lambda e: self.remove_view(view))
        self.cur_view = len(self.views) - 1

    def remove_view(self, view):
        view.destroy()
        self.views.remove(view)
        if len(self.views) >= 1:
            self.views[-1].grid()
            self.views[-1].focus_set()
            self.cur_view -= 1
        else:
            self.quit()

    def next_view(self):
        old_view = self.views[self.cur_view]
        old_view.grid_remove()
        self.cur_view += 1
        if self.cur_view >= len(self.views):
            self.cur_view = 0
        new_view = self.views[self.cur_view]
        new_view.grid()
        new_view.focus_set()

    def display(self):
        self.root.mainloop()

    def quit(self):
        self.root.destroy()

if __name__ == "__main__":
    db = FileDatabase('/media/files/koodi/tagged_file_manager/master.sqlite')
    li = db.search_by_tags(['nsfw'])
    gui = Main()
    gui.new_view(FileView(gui, li[:500], ('name', 'tags')))
    gui.display()

