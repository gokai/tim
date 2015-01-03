
import os
import subprocess
import mimetypes

from tkinter import Tk, Menu, N, S, W, E, HORIZONTAL
from tkinter.ttk import PanedWindow, Entry

from db import FileDatabase
from tkgraphics import gallery_with_slideshow
from tkeditview import EditView
from tagview import TagView
from gui2db import Gui2Db

import keybindings as kb

class Main(object):

    def __init__(self):
        root = Tk()
        self.paned_win = PanedWindow(root, orient=HORIZONTAL)
        self.root = self.paned_win
        root.title('GICM')
        root.focus_set()
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        self.menubar = Menu(self.root)
        root['menu'] = self.menubar
        self.menubar.add_command(command=self.quit, label='Quit')
        self.views = list()
        self.cur_view = 0
        self.delete_current_view = lambda e: self.remove_view(self.views[self.cur_view]) 
        kb.make_bindings(kb.appwide,{'quit':lambda e: self.quit(),
            'next_view':lambda e: self.next_view(), 'delete_view': self.delete_current_view},
            self.root.bind_all)
        self.paned_win.grid(row=0, column=0, sticky=(N, S, W, E))
        self._root = root

    def sidebar(self, widget):
        self.sidebar = widget
        self.paned_win.add(widget, weight=1)

    def new_view(self, view):
        self.views.append(view)
        if len(self.views) > 1:
            self.paned_win.forget(self.views[self.cur_view])
        self.cur_view = len(self.views) - 1
        self.paned_win.add(view, weight=5)

        view.focus_set()

    def remove_view(self, view):
        self.views.remove(view)
        self.paned_win.forget(view)
        if len(self.views) >= 1:
            self.views[-1].focus_set()
            self.cur_view -= 1
            self.paned_win.add(self.views[self.cur_view], weight=5)
        else:
            self.quit()

    def next_view(self):
        self.paned_win.forget(self.views[self.cur_view])
        self.cur_view += 1
        if self.cur_view >= len(self.views):
            self.cur_view = 1
        new_view = self.views[self.cur_view]
        self.paned_win.add(new_view, weight=5)
        new_view.focus_set()

    def display(self):
        self._root.mainloop()

    def quit(self):
        self._root.destroy()

if __name__ == "__main__":
    db = FileDatabase('master.sqlite')
    gui = Main()

    li = db.search_by_tags(['abstract'])[:100]

    glue = Gui2Db(db, gui)

    tags = db.list_tags()
    view = TagView(gui, db, tags)
    view.view.bind('<<TagViewSearch>>', glue.search)

    paths = [os.path.join(d['path'], d['name']) for d in li]
    gal = gallery_with_slideshow(gui.root, paths, gui.new_view)
    gal.bind('<Control-a>', lambda e: glue.add_tags(e, view))

    gui.sidebar(view.view)
    gui.new_view(gal)
    gui.display()

