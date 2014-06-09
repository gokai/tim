
import os
import subprocess
import mimetypes

from tkinter import *
from tkinter.ttk import *

from db import FileDatabase
from tkgraphics import SlideShow, Gallery
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
                'focus_next_row': lambda e: self.next_row(),
                'focus_prev_row': lambda e: self.prev_row(),
                'toggle_select': lambda e: self.selection_toggle(self.focus()),
                'toggle_area_select': lambda e: self.start_area_select()}
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
        g = Gallery(self.main.root, paths, (200, 200), self.slide)
        self.main.new_view(g)

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

    def quit(self):
        self.main.root.quit()
        self.main.root.destroy()

class Main(object):

    def __init__(self):
        self.root = Tk()
        self.root.title('GICM')
        self.root.focus_set()
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.menubar = Menu(self.root)
        self.root['menu'] = self.menubar
        self.menubar.add_command(command=self.quit, label='Quit')
        self.views = list()
        self.cur_view = 0
        kb.make_bindings(kb.appwide,{'quit':lambda e: self.quit(),
            'nview':lambda e: self.next_view()}, self.root.bind_all)


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

