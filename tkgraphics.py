
__author__  = "tachara (tortured.flame@gmail.com)"

import os
import sys
from math import floor

try:
    from Tkinter import *
    from ttk import *
except ImportError:
    from tkinter import *
    from tkinter.ttk import *

from PIL import Image
from PIL.ImageTk import PhotoImage

import keybindings as kb
def resize(image, target_height, target_width):
    image.thumbnail((target_width, target_height), Image.BILINEAR)

class SlideShow(Label):

    def __init__(self, root, paths, pos=0):
        self.paths = paths
        self.img = paths[pos]
        self.pos = pos
        super(SlideShow, self).__init__(root)
        self.root = root
        self.make_view()
        self.bind('<Expose>', lambda e: self.reload())
        actions = {'next':lambda e: self.next(), 'prev':lambda e: self.prev(),
                'reload':lambda e: self.reload()}
        kb.make_bindings(kb.slideshow, actions, self.bind)

    def reload(self):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if self._pil_image is None or h != self.prev_h or w != self.prev_w:
            self.prev_h = h
            self.prev_w = w
            if self._pil_image == None:
                self._pil_image = Image.open(self.img)
            img = self._pil_image.copy()
            resize(img, h, w)
            self.photo = PhotoImage(img)
            self['image'] = self.photo

    def make_view(self):
        self._tid = None
        self._pil_image = None
        self.prev_w = 0
        self.prev_h = 0
        self['anchor'] = CENTER
        self.reload()

    def next(self):
        self.pos += 1
        if self.pos >= len(self.paths):
            self.pos = 0
        self.img = self.paths[self.pos]
        self._pil_image = None
        self.reload()
        if self._tid is not None:
            self._tid = self.after(self.delay, self.next())

    def prev(self):
        self.pos -= 1
        if self.pos < 0:
            self.pos = len(self.paths) - 1
        self.img = self.paths[self.pos]
        self._pil_image = None
        self.reload()
        if self._tid is not None:
            self._tid = self.after(self.delay, self.next)

    def start(self, delay):
        self.delay = delay*1000
        self._tid = self.after(self.delay, self.next)

    def stop(self):
        self.after_cancel(self._tid)


    
class Gallery(Canvas):

    def __init__(self, root, paths, thumb_size, activate_func):
        """thumb_size = (w, h)"""
        self.paths = paths
        self.thumb_w = thumb_size[0]
        self.thumb_h = thumb_size[1]
        self.photos = list()
        self.selection = list()
        super(Gallery, self).__init__(root)
        self.make_view()
        self.make_bindings()
        self.activate_func = activate_func
        self.configure(takefocus=1)

    def make_bindings(self):
        self.bind('<Expose>', lambda e: self.reload())
        actions = {'slide': self.activate,
                'clear_selection': lambda e: self.clear_selection(),
                'cursor_up':self.cursor_up,
                'cursor_right':self.cursor_right,
                'cursor_left':self.cursor_left,
                'cursor_down':self.cursor_down,}
        self.bind('<Button-4>', self.scroll)
        self.bind('<Button-5>', self.scroll)
        kb.make_bindings(kb.gallery, actions, self.bind)

    def make_view(self):
        self.style = Style()
        self.style.configure('Cursor.TLabel', background='red')
        self.style.configure('Selected.TLabel', background='blue')
        self.style.configure('TLabel', padding=3)
        self['yscrollincrement'] = 10
        self.prev_w = self.winfo_width()
        self.load_pos = 0
        self.row = 0
        self.column = 0
        self.cursor = (0, 0, -1)
        self.max_columns = self.calculate_max_columns()
        self.after(100, self.load_next)

    def activate(self, e):
        self.activate_func(self.selection)
        self.focus_set()
        self.make_bindings()

    def get_path(self, item_id):
        return self.paths[item_id]

    def clear_selection(self):
        self.dtag('selected', 'selected')
        for index in self.selection:
            self.photos[index].configure(style='TLabel')
        self.selection.clear()

    def button_callback(self, event, column, row):
        if event.num == 1:
            prev_item = self.photos[self.cursor[2]]
            self.remove_cursor(prev_item, event.state)
            self.set_cursor(event.widget, column, row)

    def scroll(self, event):
        if event.num == 4 and self.canvasy(0) > -5:
            self.yview(SCROLL, -5, UNITS)
        elif (event.num == 5 and
              self.canvasy(self.winfo_height()) < self.bbox(self.photos[-1].cid)[3] + 5):
            self.yview(SCROLL, 5, UNITS)

    def reload(self):
        w = self.winfo_width()
        if w != self.prev_w:
            self.prev_w = w
            self.max_columns = self.calculate_max_columns()
            self.repos = 0
            self.repos_col = 0
            self.repos_row = 0
            self.after_idle(self.reposition_next)

    def reposition_next(self):
        if len(self.photos) > 0:
            photo = self.photos[self.repos]
            new_x, new_y = self.calculate_pos(self.repos_col, self.repos_row)
            self.coords(photo.cid, new_x, new_y)
            if self.repos == self.cursor[2]:
                self.cursor = (self.repos_col, self.repos_row, self.repos)
            col, row = self.repos_col, self.repos_row
            photo.bind('<Button-1>', lambda e: self.button_callback(e, col, row))
            self.repos_col += 1

        if self.repos_col >= self.max_columns:
            self.repos_row += 1
            self.repos_col = 0
        if self.repos < len(self.photos) - 1:
            self.repos += 1
            self.after_idle(self.reposition_next)

    def calculate_max_columns(self):
        w = self.winfo_width()
        return floor(w/(self.thumb_w + 8))

    def calculate_pos(self, column, row):
        x = column * self.thumb_w + self.thumb_w/2 + 8*column + 5
        y = row * self.thumb_h + self.thumb_h/2 + 8*row + 5
        return x,y

    def load_next(self):
        try:
            img = Image.open(self.paths[self.load_pos])
            resize(img, self.thumb_h, self.thumb_w)
            photo = PhotoImage(img)
            label = Label(image=photo)
            label.img = photo
            label.index = self.load_pos
            label.bind('<Button-4>', lambda e: self.yview(SCROLL, -1, UNITS))
            label.bind('<Button-5>', lambda e: self.yview(SCROLL, 1, UNITS))
            col, row = self.column, self.row
            label.bind('<Button-1>', lambda e: self.button_callback(e, col, row))
            label.bind('<Double-Button-1>', self.activate)
            self.photos.append(label)
            x, y = self.calculate_pos(self.column, self.row)
            label.cid = self.create_window(x, y, window=label)
            self.addtag_withtag(label.cid, 'label')
            self.column += 1
        except OSError:
            print(self.paths[self.load_pos])
        if self.column >= self.max_columns:
            self.row += 1
            self.column = 0
        if self.load_pos < len(self.paths) - 1:
            self.load_pos += 1
            self.after_idle(self.load_next)
        bbox = self.bbox(self.photos[-1].cid)
        self['scrollregion'] = (0, -5, 0, bbox[3])

    def cursor_up(self, e):
        column = self.cursor[0]
        row = self.cursor[1] - 1
        if row < 0:
            row = 0
        self.move_cursor(column, row, e.state)

    def cursor_down(self, e):
        row = self.cursor[1] + 1
        column = self.cursor[0]
        if row * self.max_columns + column >= len(self.photos):
            row = floor((len(self.photos) - 1)/self.max_columns)
            column = (len(self.photos) - 1 - row * self.max_columns)
        self.move_cursor(column, row, e.state)

    def cursor_right(self, e):
        row = self.cursor[1]
        column = self.cursor[0] + 1
        if column > self.max_columns:
            column = 0
            row += 1
        self.move_cursor(column, row, e.state)

    def cursor_left(self, e):
        row = self.cursor[1]
        column = self.cursor[0] - 1
        if column < 0:
            column = self.max_columns
            row -= 1
        self.move_cursor(column, row, e.state)

    def move_cursor(self, column, row, state = 0x0):
        prev_item = self.photos[self.cursor[2]]
        if self.cursor[2] != -1:
            self.remove_cursor(prev_item, state)
        new_index = column + row * self.max_columns
        item = self.photos[new_index]
        self.set_cursor(item, column, row)

    def set_cursor(self, item, column, row, index=None):
        item.configure(style='Cursor.TLabel')
        self.cursor = (column, row, index or row*self.max_columns + column)
        self.addtag_withtag('selected', item.cid)
        self.view_item(item)
        self.selection.append(item.index)

    def remove_cursor(self, item, state):
        # control key was down -> selection
        if state & 0x0004:
            item.configure(style='Selected.TLabel')
        else:
            if 'selected' in self.gettags(item.cid):
                self.selection.remove(item.index)
            item.configure(style='TLabel')
            self.dtag(item.cid, 'selected')

    def view_item(self, item):
        bbox = self.bbox(item.cid)
        max_y = self.canvasy(self.winfo_height())
        min_y = self.canvasy(0)
        bottom = (bbox[3] - max_y)
        top = bbox[1] - min_y
        n = 0
        if bottom > 0:
            n = bottom/int(self['yscrollincrement'])
        if top < 0:
            n = top/int(self['yscrollincrement'])
        self.yview_scroll(int(n), UNITS)



if __name__ == "__main__":
    from db import FileDatabase

    db = FileDatabase('/media/files/koodi/tagged_file_manager/master.sqlite')
    li = db.search_by_tags(['tausta'])
    li = db.get_full_paths(li)
    tk = Tk()

    tk.bind('<Control-q>', lambda e: tk.quit())
    tk.rowconfigure(0, weight=1)
    tk.columnconfigure(0, weight=1)
    if sys.argv[1] == 'slide':
        ss = SlideShow(tk, li)
        ss.focus_set()
        ss.grid(column=0, row=0, sticky=(N, W, E, S))
    elif sys.argv[1] == 'gallery':
        g = Gallery(tk, li, (180,180), lambda l: show(l))
        def show(li):
            ss = SlideShow(tk, [g.get_path(i) for i in li])
            ss.focus_set()
            ss.winfo_width = g.winfo_width
            ss.winfo_height = g.winfo_height
            ss.grid(column=0, row=0)
            ss.bind('<q>', lambda e: ss.destroy())
            ss.bind('<Destroy>', lambda e: g.focus_set())

        g.grid(column=0, row=0, sticky=(N, W, E, S))
        g.focus_set()
        sb = Scrollbar(tk, command = g.yview)
        g['yscrollcommand'] = sb.set
        sb.grid(column=1, row=0, sticky=(N,S))
    tk.mainloop()

