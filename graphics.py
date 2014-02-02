# The graphical classes of cicm

__author__  = "Tachara (tortured.flame@gmail.com)"
__date__ = "$Date 2011/19/05 18:17:00 $"
__copyright__ = "Copyright (c) 2010 Tachara"

from collections import deque
import os

import pygtk
import gtk
import gobject
import pango
import glib

class Graphics(object):
    """An abstract base class for the graphical parts of cicm"""
    
    def __init__(self, width, height, bgcolor = "black", toolbar = False):
        self.imageSetup = {"width":1,"height":1}
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.box = gtk.VBox()
        self.window.add(self.box)
        self.w = width
        self.h = height
        self.pageNum = 0
        self.end = False
        self.window.set_default_size(self.w,self.h)

        self.keys = {gtk.gdk.keyval_from_name('q'): self.quit,
                     gtk.gdk.keyval_from_name('n'): self.next,
                     gtk.gdk.keyval_from_name('p'): self.prev,
                     gtk.gdk.keyval_from_name('r'): self.redraw,
                     gtk.gdk.keyval_from_name('s'): self.toggleTimer,
                     gtk.gdk.keyval_from_name('f'): self.toggleFullscreen}

        self.window.connect("key_press_event", self.keyPress)
        self.window.connect("window_state_event",self.state)
        self.window.connect("configure_event", self.state)
        self.window.connect("destroy", self.quit)
        self.window.set_resizable(True)
        self.window.set_size_request(150,150)
        self.window.set_focus_chain([self.box])

        try:
            color = gtk.gdk.color_parse(bgcolor)
        except ValueError:
            color = gtk.gdk.color_parse("black")

        self.window.modify_bg(gtk.STATE_NORMAL, color)
        self.use_toolbar = toolbar
        if toolbar:
            self._make_toolbar()
        else:
            self._toolbar_h = 0
        self.full = False
        self.run = False


    def _make_toolbar(self):
        handlebox = gtk.HandleBox()
        toolbar = gtk.Toolbar()
        handlebox.add(toolbar)

        full_button = gtk.ToolButton(gtk.STOCK_FULLSCREEN)
        full_button.connect("clicked", self.toggleFullscreen)

        jump_button = gtk.ToolButton(gtk.STOCK_JUMP_TO)
        jump_button.connect("clicked", self._query, int, self.jump)

        quit_button = gtk.ToolButton(gtk.STOCK_QUIT)
        quit_button.connect("clicked", self.quit)

        space = gtk.SeparatorToolItem()

        toolbar.insert(full_button, -1)
        toolbar.insert(jump_button, -1)
        toolbar.insert(space, -1)
        toolbar.insert(quit_button, -1)
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        self._toolbar_h = 60
        
        self.box.pack_start(handlebox, expand=False)
        self._toolbar = toolbar

    def _bnext(self, widget):
        self.next()

    def _bprev(self, widget):
        self.prev()

    def _query(self, widget, t, func):
        """Ask user of an input of type t"""

        window = gtk.Dialog()

        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
        button = gtk.Button()
        button.add(img)
        window.action_area.pack_start(button)
        entry = gtk.Entry()
        entry.set_activates_default(True)
        def callback(widget, text):
            data = text.get_text()
            try:
                data = t(data)
            except ValueError:
                label = gtk.Label("Virhe")
                label.show()
                window.vbox.pack_start(label)
                return
            func(data)
            window.destroy()
        # callback end

        if t == int:
            entry.set_text(str(self.pageNum))

        button.connect("clicked", callback, entry)
        button.set_can_default(True)
        window.set_default(button)
        window.vbox.pack_start(entry)
        window.show_all()

    def jump(self, page):
        raise NotImplemented

    def display(self):
        self.window.show_all()
        gtk.main()
    
    def toggleFullscreen(self, widget = None):
        if self.full:
            if self.use_toolbar:
                # if using toolbar -> change the fullscreen button icon
                self._toolbar.get_nth_item(2).set_stock_id(gtk.STOCK_FULLSCREEN)
            self.window.unfullscreen()
            self.full = False
        elif not self.full:
            if self.use_toolbar:
                # if using toolbar -> change the fullscreen button icon
                self._toolbar.get_nth_item(2).set_stock_id(
                        gtk.STOCK_LEAVE_FULLSCREEN)
            self.window.fullscreen()
            self.full = True

    def keyPress(self, widget, event, data = None):
        if event.keyval in self.keys.keys():
            self.keys[event.keyval]()
    
    def state(self, widget, data = None):
        self.redraw()

    def countScale(self, width, height):
        """Calculates a scale float for image handling methods.
           width is the width of the image.
           height is the height of the image.
        """
        scale = 1
        if width > height:
            scale = self.w/float(width)
            if height*scale > float(self.h - self._toolbar_h):
                scale = (self.h - self._toolbar_h)/float(height)
        elif height >= width:
            scale = (self.h - self._toolbar_h)/float(height)
            if width*scale > float(self.w):
                scale = self.w/float(width)

        return scale
    
    def loadImage(self, fto = None, ign_setup = False):
        if fto is None:
            pass
        else:
            self.buff = gtk.gdk.pixbuf_new_from_file(fto)

        width = self.buff.get_width()
        height = self.buff.get_height()
        th = self._toolbar_h
        if ign_setup:
            (self.w, self.h) = self.window.get_size()
        else:
            self.w = self.imageSetup["width"]
            self.h = self.imageSetup["height"]
            self._toolbar_h = 0

        sc = self.countScale(width, height)
        buff = self.buff.scale_simple(int(width * sc),int(height * sc),
                gtk.gdk.INTERP_BILINEAR)
    
        (self.w, self.h) = self.window.get_size()
        self._toolbar_h = th
        return buff

    def toggleTimer(self):
        self.run = not self.run
        if self.run:
            self.timer = gobject.timeout_add_seconds(self.delay, self.next)
        else:
            try:
                gobject.source_remove(self.timer)
            except Exception:
                pass

    def quit(self, widget = None):
        #self.end = True
        self.window.destroy()
        gtk.main_quit()

class SlideShow(Graphics):
    """Generates a slideshow of the given images"""

    
    def __init__(self, li, windowWidth,windowHeight, delay, pos, bgcolor, toolbar):
        Graphics.__init__(self, windowWidth, windowHeight, bgcolor, toolbar)
        self.imageSetup = {"columns":1,"rows":1}
        self.fLi = li
        self.pageNum = pos
        fto = self.fLi[self.pageNum]

        self.buff = gtk.gdk.pixbuf_new_from_file(fto)

        self.curr = gtk.Image()
        self.curr.set_from_pixbuf(self.buff)
        self.frame = gtk.AspectFrame(xalign = 0.5, yalign = 0.5,obey_child = True)
        self.frame.set_shadow_type(gtk.SHADOW_NONE)
        self.frame.add(self.curr)
        self.window.set_title(fto)
        self.box.pack_start(self.frame)
        self.delay = delay
        self.run = False

        self.curr.show()
        return

    def _make_toolbar(self):
        Graphics._make_toolbar(self)
        next_button = gtk.ToolButton(gtk.STOCK_GO_FORWARD)
        next_button.connect("clicked", self._bnext)

        prev_button = gtk.ToolButton(gtk.STOCK_GO_BACK)
        prev_button.connect("clicked", self._bprev)

        self._toolbar.insert(prev_button, 0)
        self._toolbar.insert(next_button, 1)

    def prev(self):
        self.pageNum -= 1
    
        if self.pageNum < 0:
            self.quit()
            return
        else:
            fto = self.fLi[self.pageNum]

        self.buff = self.loadImage(fto, True)
        self.curr.set_from_pixbuf(self.buff)
        self.window.set_title(fto)
        return
    
    def next(self):
        self.pageNum += 1

        if(self.pageNum >= len(self.fLi)):
            self.quit()
            return False

        fto = self.fLi[self.pageNum]
        if not os.path.exists(fto):
            print "%s not found, skipping" % fto
            return self.next()

        self.buff = self.loadImage(fto, True)
        self.curr.set_from_pixbuf(self.buff)
        self.window.set_title(fto)
        return True #required to run the slideshow
    
    def keyPress(self, widget, event):
        if event.keyval == gtk.gdk.keyval_from_name('j'):
            self._query(widget, int, self.jump)
        Graphics.keyPress(self, widget, event)

    def jump(self, page):
        self.pageNum =  page - 1
        self.next()

    def redraw(self):
        buff = self.loadImage(ign_setup = True)
        self.curr.set_from_pixbuf(buff)
        return

class Gallery(Graphics):
    """Generates a thumbnail gallery of the given images"""

    def __init__(self, li, info, lim, thumbWidth, thumbHeight, width, height, page = 0,
            delay = 10, bgcolor = "black", toolbar = False):
        Graphics.__init__(self, width, height, bgcolor, toolbar)

        self.imageSetup["width"] = thumbWidth
        self.imageSetup["height"] = thumbHeight
        self.delay = delay
        self.pageLimit = lim
        # last displayed index
        self.lastDisp = lim - 1
        self.pageNum = page
        self.content = li
        self.names = info
        self.i = 0
        self.loading = False
        self.selectedPaths = []

        self.keydict = {}
        self.keydict["up"] = (gtk.gdk.keyval_from_name("k"), 
                gtk.gdk.keyval_from_name("Up"))
        self.keydict["down"] = (gtk.gdk.keyval_from_name("j"), 
                gtk.gdk.keyval_from_name("Down"))
        self.keydict["left"] = (gtk.gdk.keyval_from_name("h"), 
                gtk.gdk.keyval_from_name("Left"))
        self.keydict["right"] = (gtk.gdk.keyval_from_name("l"), 
                gtk.gdk.keyval_from_name("Right"))
        self.keydict["activate"] = (gtk.gdk.keyval_from_name("Return"), 
                gtk.gdk.keyval_from_name("space"))


        self.buffs = gtk.ListStore(gtk.gdk.Pixbuf)
        self.scroll = gtk.ScrolledWindow()

        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # initialize the view
        self.makeView()
        cells = self.view.get_cells()
        for cell in cells:
            try:
                cell.set_sensitive(True)
                cell.set_property("follow-state", True)
                cell.set_property("mode", gtk.CELL_RENDERER_MODE_ACTIVATABLE)
            except Exception:
                pass


        self.box.pack_start(self.scroll)
        self.box.set_focus_chain([self.scroll])
        self.scroll.add(self.view)
        self.setLoading(True)
        glib.idle_add(self._load)
        return

    def redraw(self):
        return

    def _load(self):
        if self.pageLimit > 0 and self.i == self.lastDisp:
            if self.i == len(self.content) - 1:
                self.setLoading(False)
            return False

        if self.i < len(self.content):
            if not os.path.exists(self.content[self.i]):
                print self.content[self.i], "not found, skipping"
                self.content.pop(self.i)
                self.names.pop(self.i)
                return True
            else:
                try:
                    buff = self.loadImage(self.content[self.i])
                    row = (buff, )
                except Exception as ex:
                    print "Failed to load", self.names[self.i]["name"]
                    print ex
                    self.content.pop(self.i)
                    self.names.pop(self.i)
                    return True
            self.i += 1
            self.progress.set_fraction(self.i/float(len(self.content)))
            self.buffs.append(row)
            return True
        else:
            self.setLoading(False)
            return False

    def setLoading(self, status):
        """If status is True, shows the user that more images are being loaded.
           removes the notice when given False"""

        if status and not self.loading:
            self.status = gtk.Statusbar()
            self.status.set_has_resize_grip(False)
            self.progress = gtk.ProgressBar()
            self.status.pack_start(self.progress)
            self.box.pack_start(self.status,expand=False)
            self.progress.set_fraction(0.0)
            self.progress.set_text("Loading")
            self.progress.show()
            self.status.show()
            self.loading = True
        elif not status:
            self.loading = False
            self.progress.hide()
            self.status.hide()

    def _prevRow(self, path):
        """Finds the path above given path.
           Needed with IconView"""
        new_path = path
        row = self.view.get_item_row(path)
        # I found no way to calculate the new path for vertical
        # movement so the new item is sought with loops
        while new_path[0] > 0 and self.view.get_item_row(new_path) == row:
            new_path = (new_path[0] - 1,)
        if new_path[0] < 0:
            new_path = (0,)
        column = self.view.get_item_column(path)
        while self.view.get_item_column(new_path) != column:
            new_path = (new_path[0] - 1,)
            if new_path[0] < 0:
                new_path = path
                break
        return new_path

    def _nextRow(self, path):
        """Finds the path below given path.
           Needed with IconView"""
        new_path = path
        row = self.view.get_item_row(path)
        while self.view.get_item_row(new_path) == row:
            new_path = (new_path[0] + 1,)
        column = self.view.get_item_column(path)
        new_path = (new_path[0] + column,)
        return new_path

    def _moveCursor(self, direction, shift, control):
        """Moves the cursor to its new place.
           direction is one of 8, 2, 4, 6 and meaning up, down, left, right
           """
        cursor = self.view.get_cursor()
        if cursor is None:
            new_path = (0,)
            path = (0,)
        else:
            path = cursor[0]
            if direction == 8:
                new_path = self._prevRow(path)
            elif direction == 2:
                new_path = self._nextRow(path)
            elif direction == 4:
                new_path = (path[0] - 1,)
            elif direction == 6:
                new_path = (path[0] + 1,)

        if new_path[0] < 0:
            new_path = (0,)
        elif new_path[0] >= len(self.buffs):
            new_path = path

        self._setCursor(new_path, path, shift, control)

    def _setCursor(self, new_path, path, shift, control):
        """Sets the cursor on the gallerys view to 
           the new_path specified. 
           """
        cells = self.view.get_cells()
        self.view.set_cursor(new_path, cells[0], start_editing=False)

        # Make the item visible. False -> move only as much as required
        # to show the item.
        self.view.scroll_to_path(new_path, False, 0.0, 0.0)

        if shift:
            self.select()
            self.togglePathSelected(new_path)
        elif control:
            if path is not None and path not in self.selectedPaths:
                self.view.unselect_path(path)
            self.view.select_path(new_path)
        elif not control:
            self.view.unselect_all()
            self.selectedPaths = []
            self.view.select_path(new_path)

    def _view(self, view, path):
        width, height = self.window.get_size()
        i = self._pathToIndex(path)

        slide = SlideShow(self.content, width, height, self.delay, i, "black", self.use_toolbar)
        slide.display()

    def mouse(self, widget, event):
        shift = event.state & gtk.gdk.SHIFT_MASK
        control = event.state & gtk.gdk.CONTROL_MASK
        click_path = widget.get_path_at_pos(int(event.x), int(event.y))
        if event.type == gtk.gdk.BUTTON_PRESS:
            cursor = widget.get_cursor()
            path = None
            if cursor is not None:
                path = cursor[0]
            self._setCursor(click_path, path, shift, control)
        elif event.type == gtk.gdk._2BUTTON_PRESS:
            widget.item_activated(click_path)

        return True

    def keyPress(self, widget, event):
        shift = event.state & gtk.gdk.SHIFT_MASK
        control = event.state & gtk.gdk.CONTROL_MASK
        if (gtk.gdk.keyval_to_lower(event.keyval) in
                self.keydict["up"]):
            self._moveCursor(8, shift, control)
        elif (gtk.gdk.keyval_to_lower(event.keyval) in
                self.keydict["down"]):
            self._moveCursor(2, shift, control)
        elif (gtk.gdk.keyval_to_lower(event.keyval) in
                self.keydict["right"]):
            self._moveCursor(6, shift, control)
        elif (gtk.gdk.keyval_to_lower(event.keyval) in
                self.keydict["left"]):
            self._moveCursor(4, shift, control)
        elif (event.keyval in self.keydict["activate"]):
            cursor = self.view.get_cursor()
            path = cursor[0]
            self.view.item_activated(path)
        elif (event.keyval == gtk.gdk.keyval_from_name("s")
                and control):
            cursor = self.view.get_cursor()
            path = cursor[0]
            self.togglePathSelected(path)

        Graphics.keyPress(self, widget, event)
        return True

    def togglePathSelected(self, path):
        if path not in self.selectedPaths:
            self.selectedPaths.append(path)
            self.view.select_path(path)
        else:
            self.selectedPaths.remove(path)
            self.view.unselect_path(path)

    def getSelectedItems(self):
        items = []
        for path in self.selectedPaths:
            ind = self._pathToIndex(path)
            items.append(self.names[ind])
        return items

    def makeView(self):
        """Initializes the gallerys view widget.
           called by __init__."""
        self.view = gtk.IconView(self.buffs)
        self.view.set_pixbuf_column(0)
        self.view.set_text_column(-1)
        self.view.set_spacing(0)
        self.view.set_property("row-spacing", 0)
        self.view.set_property("column-spacing", 0)
        self.view.set_selection_mode(gtk.SELECTION_MULTIPLE)

        self.view.connect("item-activated", self._view)
        self.view.connect("button-press-event", self.mouse)

        self.view.connect("drag_begin", self._dragBegin)

    def _dragBegin(self, widget, context, data):
        print widget, context, data

    def next(self):
        if self.pageLimit <= 0 or self.lastDisp == len(self.content) + 1:
            return
        self.buffs.clear()
        self.view.set_model(self.buffs)
        self.lastDisp += self.pageLimit
        if self.lastDisp > len(self.content) - 1:
            self.lastDisp = len(self.content) - 1
        self.setLoading(True)
        glib.idle_add(self._load)

    def prev(self):
        if self.pageLimit <= 0 or self.lastDisp == self.pageLimit - 1:
            return
        self.buffs.clear()
        self.view.set_model(self.buffs)
        self.lastDisp -= self.pageLimit
        self.i -= 2*self.pageLimit
        if self.i < 0:
            self.i = 0
        if self.lastDisp < self.pageLimit - 1:
            self.lastDisp = self.pageLimit - 1
        self.setLoading(True)
        glib.idle_add(self._load)

    def _pathToIndex(self, path):
        """Finds the index in content corresponding to path"""
        return path[0] 

    def jump(self, page):
        pass

    def quit(self, widget=None):
        Graphics.quit(self)
