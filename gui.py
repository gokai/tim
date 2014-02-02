#-*- coding: UTF-8 -*-
__author__  = "Tachara (tortured.flame@gmail.com)"
__date__ = "$Date 2011/23/09 16:04:00 $"
__copyright__ = "Copyright (c) 2011 Tachara"

import os
import subprocess
import mimetypes

import gtk
import gobject
import pango

from ui import ImageView, get_file_dir
from graphics import SlideShow, Gallery

_MIN = 0
_MAX = pow(10, 10)
_INCREMENT = 1
_PAGE_MULTIP = 5

class DataStore(gtk.ListStore):

    def __init__(self, data, keys, types, info = None):
        """
           data   the data to store
           keys   keys from data to use
           types  types of the keys
           info   extra data to store
        """
        types.append(int)
        self._len = len(types) - 1
        super(DataStore, self).__init__(*types)
        self.info = list()
        if not isinstance(info, list) and info is not None:
            info = list(info)

        self._keys = keys
        self._extra = info
        self.data = list()
        self.add(data)

    def get_info(self, tree_iter, key):
        if len(self.info) == 0:
            return None

        ind = self.get_value(tree_iter, self._len)
        info = self.info[ind][key]
        return info

    def update(self, new):
        """Changes existing data to match new data"""
        self.add(new)

    def add(self, data):
        """Stores new data.
           data   The data to add. Must be compatible with the initial data.
        """
        begin = len(self.data)
        for i,item in enumerate(data, start = begin):
            if item in self.data:
                for row in self:
                    path = row.path
                    it = self.get_iter(path)
                    if self.get_value(it, self._len) == self.data.index(item):
                        values = list()
                        for x, key in enumerate(self._keys):
                            self.set_value(it, x, item[key])
            else:
                self.data.append(item)
                li = list()
                for key in self._keys:
                    li.append(item[key])
                li.append(i)
                self.append(li)

                if self._extra:
                    d = dict()
                    if "index" in self._extra:
                        d["index"] = i
                    for key in self._extra:
                        if key in item.keys():
                            d[key] = item[key]
                    self.info.append(d)

class DataDisplay(object):
    def __init__(self, data, keys, types, text):
        """
        data  list of dictionaries containeng the data to be displayed
        keys  keys of the dictionary that should be shown
        types  defines the types of the fields shown
        text  a dictionary of texts to use

        To display: Add disp.scroll to wherever you want.
        """

        info = ("id", "index")
        self.store = DataStore(data, keys, types, info)

        view = gtk.TreeView(self.store)
        for i, key in enumerate(keys):
            column = gtk.TreeViewColumn(text[key])
            column.set_sort_column_id(i)
            column.set_resizable(True)
            if types[i] is bool:
                cr = gtk.CellRendererToggle()
            else:
                cr = gtk.CellRendererText()
                cr.set_property("width-chars", 30)
                cr.set_property("ellipsize", pango.ELLIPSIZE_END)
            column.pack_start(cr)
            column.set_attributes(cr, text=i)
            view.append_column(column)


        self.view = view
        self.view.set_headers_clickable(True)
        self.view.set_enable_search(False)
        self.view.set_search_column(0)

        scroll = gtk.ScrolledWindow()
        scroll.add(view)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll = scroll

    def set_actions(self, actions):
        """Defines the actions for the treeview."""
        for action in actions:
            if len(action) == 2:
                self.view.connect(action[0], action[1])
            else:
                self.view.connect(action[0], action[1], action[2])

    def get_selected(self):
        selection = self.view.get_selection()
        model, it = selection.get_selected()
        if it == None:
            return None
        ind = self.store.get_info(it, "index")
        data = self.store.data[ind]
        data["index"] = ind
        return data

    def select(self, li):
        for item in li:
            self.view.select((item["index"],))

    def update(self, data):
        self.store.update(data)

class Query(object):
    def __init__(self, title, data_model, container, use_float = True):
        """
        title       title for the created window
        data_model  a dictionary containing description of the 
                    data to be collected
                    format: data_model = {"fields":{"field_name":type/value},
                                "buttons":{"label":action}}
        container   a dictionay to which the collected data is stored
        use_float   if true number values will be returned as float
        """
        self.float = use_float
        self.altered = False
        self.window = gtk.Dialog()
        self.window.set_title(title)
        self.scroll = gtk.ScrolledWindow()
        self.box = gtk.VBox()

        self.scroll.add_with_viewport(self.box)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.window.set_size_request(300,300)

        # a dictionary to store the objects created (data retrieval)
        self.data = dict()

        # create the objects
        for field in data_model["fields"].keys():
            t = type(data_model["fields"][field])
            if t == int:
                self.box.pack_start(self._create_int_field(field, self.data,
                        data_model["fields"][field]))
            elif t == dict:
                self.box.pack_start(self._create_dict_field(field, self.data,
                        data_model["fields"][field]))
            elif t == bool:
                self.box.pack_start(self._create_bool_field(field,
                    data_model["fields"][field], self.data))
            elif data_model["fields"][field] == "choose":
                # not implemented yet
                self.box.pack_start(self._create_choice_field(field, self.data,
                        data_model["fields"][field]))
            elif t == type(None):
                self.box.pack_start(self._create_label(field))
            else:
                self.box.pack_start(self._create_str_field(field, self.data,
                        data_model["fields"][field]))

        # create buttons
        for key in data_model["buttons"].keys():
            button = self._create_button(key, data_model["buttons"][key])
            self.window.action_area.pack_start(button)

        button = gtk.Button(stock = gtk.STOCK_OK)
        button.connect("clicked", self.store, container)
        self.window.action_area.pack_start(button)

        button = gtk.Button(stock = gtk.STOCK_CANCEL)
        button.connect("clicked", self.close, False)

        self.window.vbox.pack_start(self.scroll)
        self.window.action_area.pack_start(button)
        self.window.connect("delete-event", gtk.main_quit)

    def _create_button(self, name, cb_data):
        action = cb_data[0]
        if len(cb_data) > 1:
            args = cb_data[1:]
        else:
            args = []
        button = gtk.Button(name)
        if "gtk-" in name:
            button.set_use_stock(True)
        button.connect("clicked", action, *args)
        return button
        
    def _create_str_field(self, name, data, value = None):

        box = gtk.HBox()
        entry = gtk.Entry()
        label = gtk.Label(name)
        box.pack_start(label)
        box.pack_start(entry)
        data[name] = entry

        if value != None and type(value) != type:
            entry.set_text(value)

        return box

    def _create_int_field(self, name, data, value = 0):

        box = gtk.HBox()
        label = gtk.Label(name)
        box.pack_start(label)

        if type(value) == type:
            value = 0

        adj = gtk.Adjustment(value, _MIN, _MAX, _INCREMENT, _PAGE_MULTIP)
        button = gtk.SpinButton(adj)
        data[name] = button

        box.pack_start(button)

        return box

    def _create_dict_field(self, name, data, model):
        frame = gtk.Frame()
        frame.set_label(name)
        box = gtk.VBox()
        data[name] = dict()
        for field in model:
            t = type(model[field])
            if t == int:
                box.pack_start(self._create_int_field(field, data[name], 
                    model[field]))
            elif t == dict:
                box.pack_start(self._create_dict_field(field, data[name],
                    model[field]))
            else:
                box.pack_start(self._create_str_field(field, data[name],
                    model[field]))
        frame.add(box)
        return frame

    def _create_bool_field(self, name, value, data):
        button = gtk.CheckButton(name, False)
        button.set_active(value)
        data[name] = button
        return button

    def _create_label(self, text, markup = None):
        label = gtk.Label(text)
        if markup != None:
            label.set_markup(markup)
        return label

    def _create_choice_field(self, name, values = None):
        pass

    def _gather_data(self, data, container):
        for key in data.keys():
            t = type(data[key])
            if t == dict:
                self._gather_data(data[key], container[key])
            elif t == gtk.Entry:
                container[key] = data[key].get_text()
            elif t == gtk.SpinButton:
                if self.float:
                    container[key] = data[key].get_value()
                else:
                    container[key] = int(data[key].get_value())
            elif t == gtk.CheckButton:
                container[key] = data[key].get_active()

    def store(self, button, container):
        self._gather_data(self.data, container)
        self.close(altered = True)

    def close(self, data = None, altered = False):
        self.altered = altered
        self.window.hide_all()
        gtk.main_quit()

    def main(self):
        self.window.show_all()
        gtk.main()

class Base(object):
    def __init__(self, edit_name, buttons):
        self.window = gtk.Window()
        self._title = "GICM"
        self._edit_name = edit_name
        self._edit_buttons = buttons
        self.window.set_title(self._title)
        self.window.set_size_request(450,300)
        self.window.connect("delete-event", self.quit)
        self.window.connect("key-press-event", self.key_press)


    def multi_edit(self, widget = None, data = None):
        if data is None:
            return
        
        model = {"fields":{}, "buttons":{}}
        for item in data:
            model["fields"][item["name"]] = {"tags":item["tags"]}
        query = Query(self._title, model, model["fields"], False)
        query.main()
        if not query.altered:
            return

        for field in model["fields"].items():
            for item in data:
                if item["name"] == field[0]:
                    self.man.changeTags(item["id"], field[1])
                    break

            
    def edit(self, widget):
        item = self.disp.get_selected()
        title = " ".join([self._title, item["name"]])
        model = {}
        if self._edit_buttons is None:
            model["buttons"] = {}
        else:
            model["buttons"] = self._edit_buttons
        
        if self._edit_name:
            model["fields"] = {"name":item["name"], "tags":item["tags"]}
        else:
            model["fields"] = {"tags":item["tags"]}
        query = Query(title, model, model["fields"], use_float=False)
        query.main()
        if query.altered:
            if self.man is not None:
                self.man.changeTags(item["id"], model["fields"]["tags"])
                if self._edit_name:
                    self.man.renameCollection(item["id"], model["fields"]["name"])
            else:
                self.ui.man.changeTags(item["id"], model["fields"]["tags"])
                if "name" in model["fields"].keys() and model["fields"]["name"] != item["name"]:
                    self.ui.man.renameCollection(item["id"], model["fields"]["name"])
            item["tags"] = list(set(model["fields"]["tags"].split(",")))
            self.disp.update([item])

    def key_press(self, widget, event):
        if event.state & gtk.gdk.CONTROL_MASK:
            if event.keyval == gtk.gdk.keyval_from_name("q"):
                self.quit()
        elif event.keyval == gtk.gdk.keyval_from_name('j'):
            sel = self.disp.view.get_selection()
            model, it = sel.get_selected()
            if it == None:
                it = model.get_iter_first()
            else:
                it = model.iter_next(it)
            if isinstance(it, gtk.TreeIter):
                path = model.get_path(it)
                self.disp.view.set_cursor_on_cell(path)
        elif event.keyval == gtk.gdk.keyval_from_name('k'):
            sel = self.disp.view.get_selection()
            model, it = sel.get_selected()
            if it == None:
                it = model.get_iter_first()
            else:
                prev = None
                i = model.get_iter_first()
                s = model.get_string_from_iter(it)
                while model.get_string_from_iter(i) != s:
                    prev = i
                    i = model.iter_next(i)
                it = prev
            if isinstance(it, gtk.TreeIter):
                path = model.get_path(it)
                self.disp.view.set_cursor_on_cell(path)
        elif event.keyval == gtk.gdk.keyval_from_name('e'):
            self.edit(None)


    def quit(self, *args):
        self.window.destroy()
        gtk.main_quit()

    def main(self):
        self.window.show_all()
        gtk.main()

class View(Base):
    def __init__(self, cont, ui):
        super(View, self).__init__(False, None)
        self.ui = ui
        self._edit_buttons = None
        self.man = None

        keys = ["name", "tags", "collection"]
        types = [str, str, str]
        disp = DataDisplay(cont, keys, types, self.ui.text)
        actions = [("row-activated", self._view)]
        disp.set_actions(actions)
        self.disp = disp
        self.box = gtk.VBox()

        self.make_toolbar()
        self.box.pack_start(disp.scroll)
        self.window.add(self.box)

    def make_toolbar(self):
        self.toolbar = gtk.Toolbar()
        
        # Gallery button
        gal_button = gtk.ToolButton()
        img = gtk.Image()
        path = os.path.join(get_file_dir(), "icon_gallery.svg")
        buff = gtk.gdk.pixbuf_new_from_file_at_size(path, 20, 20)
        img.set_from_pixbuf(buff)
        gal_button.set_icon_widget(img)
        gal_button.set_label(self.ui.text["commands"]["gallery"].capitalize())
        gal_button.connect("clicked", self._gallery)

        # slideshow button
        slide_button = gtk.ToolButton()
        img = gtk.Image()
        path = os.path.join(get_file_dir(), "icon_slide.svg")
        buff = gtk.gdk.pixbuf_new_from_file_at_size(path, 20, 20)
        img.set_from_pixbuf(buff)
        slide_button.set_icon_widget(img)
        slide_button.set_label(self.ui.text["commands"]["slide"].capitalize())
        slide_button.connect("clicked", self._slide)

        # quit button
        quit_button = gtk.ToolButton(gtk.STOCK_QUIT)
        quit_button.connect("clicked", self.quit)
        self.box.pack_start(self.toolbar, expand=False)

        # insert the buttons to the toolbar
        self.toolbar.insert(gal_button, -1)
        self.toolbar.insert(slide_button, -1)
        self.toolbar.insert(quit_button, -1)

    def _slide(self, widget):
        self.ui.slide(self.disp.store.data)

    def _gallery(self, widget):
        self.ui.gallery(self.disp.store.data, select=self.disp.select)

    def _update_main(self):
        selected = self.ui.disp.get_selected()
        data = self.ui.man.listFiles(selected["name"])
        self.disp.update(data)

    def _view(self, treeview, path, view_column):
        fdict = self.disp.get_selected()
        self.ui.slideshow(self.disp.store.data, pos = fdict["index"])

class GUI(ImageView, Base):

    def __init__(self):
        buttons = {gtk.STOCK_ADD:(self._add_images,)}
        Base.__init__(self, True, buttons)
        ImageView.__init__(self)
        box = gtk.VBox()
        self._add_toolbar(box)
        d = get_file_dir()

        collections = self.man.listCollections()
        used = ["name", "tags", "fc"]
        types = [str, str, int]
        self.disp = DataDisplay(collections.value, used, types, self.text)
        actions = [("row-activated", self.browse)]
        self.disp.set_actions(actions)
        self.disp.window = self.window
        box.pack_start(self.disp.scroll)

        self.window.add(box)
        self.window.set_focus_child(self.disp.scroll)

    def _add_toolbar(self, box):
        handlebox = gtk.HandleBox()
        toolbar = gtk.Toolbar()

        handlebox.add(toolbar)
        box.pack_start(handlebox, expand=False)

        # gallery button
        gal_button = gtk.ToolButton()
        img = gtk.Image()
        path = os.path.join(get_file_dir(), "icon_gallery.svg")
        buff = gtk.gdk.pixbuf_new_from_file_at_size(path, 20, 20)
        img.set_from_pixbuf(buff)
        gal_button.set_icon_widget(img)
        gal_button.set_label(self.text["commands"]["gallery"].capitalize())
        gal_button.connect("clicked", self._gallery)

        # slideshow button
        slide_button = gtk.ToolButton()
        img = gtk.Image()
        path = os.path.join(get_file_dir(), "icon_slide.svg")
        buff = gtk.gdk.pixbuf_new_from_file_at_size(path, 20, 20)
        img.set_from_pixbuf(buff)
        slide_button.set_icon_widget(img)
        slide_button.set_label(self.text["commands"]["slide"].capitalize())
        slide_button.connect("clicked", self._slide)

        # collection properties
        prop_button = gtk.ToolButton(gtk.STOCK_PROPERTIES)
        prop_button.connect("clicked", self.edit)

        space = gtk.SeparatorToolItem()

        # preferences button
        pref_button = gtk.ToolButton(gtk.STOCK_PREFERENCES)
        pref_button.connect("clicked", self.setup)

        # new collection button
        new_button = gtk.ToolButton(gtk.STOCK_NEW)
        new_button.connect("clicked", self._create_collection)

        # quit button
        quit_button = gtk.ToolButton(gtk.STOCK_QUIT)
        quit_button.connect("clicked", self.quit)

        # insert buttons to toolbar
        toolbar.insert(gal_button, -1)
        toolbar.insert(slide_button, -1)
        toolbar.insert(prop_button, -1)
        toolbar.insert(space, -1)
        toolbar.insert(pref_button, -1)
        toolbar.insert(new_button, -1)
        toolbar.insert(quit_button, -1)

    def _create_collection(self, w):
        data = {"name":"", "tags":""}
        model = {"fields":data, "buttons":{}}
        query = Query(self._title, model, data, use_float=False)
        query.main()
        if query.altered:
            self.man.createCollection(data["name"], data["tags"])
            self._update_main()

    def _delete_collection(self, w):
        pass

    def _slide(self, widget, cont = None, rand = False, pos = 0):
        if type(cont) == str:
            cont = self.man.listFiles(cont).value
        elif cont == None:
            coll_dict = self.disp.get_selected()
            cont = self.man.listFiles(coll_dict["name"]).value

        if rand:
            self.randomSlide(cont)
        else:
            self.slideshow(cont, pos = pos)

    def _gallery(self, widget):
        coll_dict = self.disp.get_selected()
        if coll_dict == None:
            return
        self._files = self.man.listFiles(coll_dict["name"]).value
        self.gallery(self._files, select = True)

    def browse(self, treeview, path, view_column):
        coll_dict = self.disp.get_selected()
        cont = self.man.listFiles(coll_dict["name"]).value
        view = View(cont, self)
        view.main()

    def _update_main(self):
        data = self.man.listCollections().value
        self.disp.update(data)

    def _response_cb(self, dialog, response, coll_dict):
        if response == gtk.RESPONSE_ACCEPT:
            files = dialog.get_filenames()
            self.man.insertFiles(files, coll_dict["id"])
            self._update_main()

        dialog.hide()
        dialog.destroy()

    def _add_images(self, widget):
        coll_dict = self.disp.get_selected()
        fq = gtk.FileChooserDialog(title = self._title)
        fq.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        fq.set_select_multiple(True)
        filt = gtk.FileFilter()
        filt.add_pixbuf_formats()
        fq.set_filter(filt)
        fq.add_button(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        fq.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        fq.connect("response", self._response_cb, coll_dict)
        fq.set_destroy_with_parent(True)
        fq.show()


    def setup(self, widget = None):
        model = {"fields":self.settings, "buttons":{}}
        query = Query(self._title, model, self.settings, use_float=False)
        query.main()
        if query.altered:
            self.settings.write()
            self._update_main()

    def search(self):
        data = {"fields":{self.text["tags"]:""},
                "buttons":{}}
        query = Query(self._title + self.text["commands"]["search"].capitalize(),
                data, data["fields"], False)
        query.main()

        if query.altered:
            tags = data["fields"][self.text["tags"]].split(',')
            comp = self.settings["search"]
        
            if comp == "exc":
                li = self.man.searchFiles(tags, False).value
            elif comp == "inc":
                li = self.man.searchFiles(tags, True).value
            else:
                return

            view = View(li, self)
            view.main()


    def key_press(self, widget, event):
        if event.state & gtk.gdk.CONTROL_MASK:
            pass
        if event.keyval == gtk.gdk.keyval_from_name('g'):
            self._gallery(None)
        elif event.keyval == gtk.gdk.keyval_from_name('s'):
            coll = self.disp.get_selected()
            self._slide(None, coll["name"])
        elif event.keyval == gtk.gdk.keyval_from_name('r'):
            coll = self.disp.get_selected()
            self._slide(None, coll["name"], rand = True)
        elif event.keyval == gtk.gdk.keyval_from_name('f'):
            self.search()
        elif event.keyval == gtk.gdk.keyval_from_name('e'):
            if len(self._selected) > 0:
                self.multi_edit(data=self._selected)
                return

        super(GUI, self).key_press(widget, event)

    def quit(self, *args):
        self.window.destroy()
        gtk.main_quit()
