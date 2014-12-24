
import os
import subprocess
import mimetypes

from tkinter import *
from tkinter.ttk import *

from db import FileDatabase
from tkgraphics import SlideShow, Gallery
from tkeditview import EditView
from tagview import TagView
import keybindings as kb

class FileView(Treeview):

    def __init__(self, main, files, keys):
        self.files = files
        self.keys = keys
        self.file_tree_ids = dict()
        self.images = list()
        self.main = main
        super(FileView, self).__init__(self.main.root, columns=self.keys[1:])
        self.area_select = False
        self.create_view()
        self.bind_events()

    def create_view(self):
        self.heading('#0', text=self.keys[0])
        for key in self.keys[1:]:
            self.heading(key, text=key)

        self.index = 0
        self.after(50, self.load_row)

    def start_area_select(self):
        self.area_select = not self.area_select
        self.selection_add(self.focus())

    def bind_events(self):
        actions = {'slide': lambda e: self.slide(),
                'gallery': lambda e: self.gallery(),
                'edit': lambda e: self.edit(),
                'focus_next_row': lambda e: self.next_row(),
                'focus_prev_row': lambda e: self.prev_row(),
                'toggle_select': lambda e: self.selection_toggle(self.focus()),
                'toggle_area_select': lambda e: self.start_area_select(),
                'edit_tags':lambda e: self.edit_tags(),
        }
        kb.make_bindings(kb.fileview, actions, self.bind)

    def get_selection_paths(self):
        sel = self.selection()
        fli = (self.file_tree_ids[i] for i in sel)
        return [os.path.join(f['path'], f['name']) for f in fli]

    def slide(self, indexes=None):
        paths = self.get_selection_paths()
        if indexes is not None:
            paths = [paths[i] for i in indexes]
        ss = SlideShow(self.main.root, paths)
        self.main.new_view(ss)

    def gallery(self):
        paths = self.get_selection_paths()
        g = Gallery(self.main.root, paths, (256, 256), self.slide)
        self.main.new_view(g)

    def edit_tags(self, indexes=None):
        fli = [self.file_tree_ids[i] for i in self.selection()]
        if indexes is not None:
            fli = [fli[i] for i in indexes]
        e = EditView(self.main.root, fli, update=self.update, image_view=SlideShow,
                full_view=self.slide)
        self.main.new_view(e)

    def prev_row(self):
        focused = self.focus()
        nitem = ''
        if focused == '':
            nitem = self.get_children()[0]
        else:
            nitem = self.prev(focused)
        if nitem != '':
            self.move_focus(nitem)

    def next_row(self):
        focused = self.focus()
        nitem = ''
        if focused == '':
            nitem = self.get_children()[0]
        else:
            nitem = self.next(focused)
        if nitem != '':
            self.move_focus(nitem)

    def move_focus(self, nitem):
        self.focus(nitem)
        if self.area_select:
            self.selection_add(nitem)
        self.see(nitem)

    def load_row(self):
        f = self.files[self.index]
        tid = self.insert('', 'end', text=f[self.keys[0]], values=(','.join(f[self.keys[1]]),))
        self.file_tree_ids[tid] = f
        self.index += 1
        if self.index < len(self.files):
            self.after_idle(self.load_row)

    def update(self):
        pass

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

    def new_view(self, view):
        self.views.append(view)
        if len(self.views) > 2:
            self.paned_win.forget(self.views[self.cur_view])
        self.cur_view = len(self.views) - 1
        if len(self.views) == 1:
            self.paned_win.add(view, weight=1)
        else:
            self.paned_win.add(view, weight=5)

        view.focus_set()

    def remove_view(self, view):
        self.views.remove(view)
        self.paned_win.forget(view)
        if len(self.views) >= 2:
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
    li = db.search_by_tags(['abstract'])[:100]
    tags = db.list_tags()
    gui = Main()
    view = TagView(gui, tags)
    gui.new_view(view.view)
    gui.new_view(FileView(gui, li, ('name', 'tags')))
    gui.display()

