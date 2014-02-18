__author__  = "Tachara (tortured.flame@gmail.com)"
__date__ = "$Date 2010/31/03 18:07:00 $"
__copyright__ = "Copyright (c) 2010 Tachara"

import sys
import os
import subprocess
from collections import deque
from random import choice, shuffle
import mimetypes
import itertools
try:
    import readline
except ImportError:
    # the readline module is only imported to
    # make raw_input behave better
    pass


# non-standard modules should come with this file
# if not you can find them from sourceforge.com
from db import FileDatabase
from settings import Settings, Text
from graphics import SlideShow, Gallery

def get_file_dir():
    """Finds the absolute path to cicm files"""
    return os.path.abspath(os.path.dirname(__file__))

class ImageView(object):
    def __init__(self):
        path = get_file_dir()
        os.chdir(path)
        self.settings = Settings(os.path.join(path, "cicm.xml"))
        paths = Settings(os.path.join(path, self.settings["paths"]))
        self.store = FileDatabase(self.settings["master"])
        self.text = Text(self.settings["lang"], path)
        self._selected = list()
        self._files = list()

    def openInApplication(self, fi, flags = None):
        """ opens a file in a external application"""
        fileToOpen = self.man.constructFilePath([fi,]).value[0]
        appName = self.settings["external"]
        args = [appName]
        if flags is not None:
            args.append(flags)
        args.append(fileToOpen)
        return subprocess.Popen(args)

    def select(self, data):
        """Selects a file with propertie in data
        Add the data of a file with a given name, id
        or data to self._selected.
        Needs a string with the name or id of a file or 
        a data dictionary used in the internal data structure"""
        if type(data) == dict and data not in self._selected:
            self._selected.append(data)
            return
        if type(data) == list:
            self._selected.extend(data)
        elif data in self._selected:
            return

        for fi in self._files:
            if ((fi["name"] == data or fi["id"] == data) and 
                    not self.isSelected(fi)):
                self._selected.append(fi)
                break

    def unselect(self, data):
        """Removes a selected item"""
        if self.isSelected(data):
            self._selected.remove(data)

    def clearSelected(self):
        self.selected = []

    def isSelected(self, item):
        if not isinstance(item, dict):
            for fi in self._files:
                if fi["name"] == item:
                    return True
            return False
        else:
            return item in self._selected

    def slideshow(self, li, pos=0):
        if "path" not in li[0].keys():
            l = list()
            for c in li:
                l.extend(self.store.list_files_in_collection(c["name"]))
            li = l
        files = self.store.get_full_paths(li)
        show = SlideShow(files, self.settings["window"]["width"],\
            self.settings["window"]["height"], self.settings["delay"],
            pos, self.settings["window"]["bg"], toolbar = self.settings["toolbar"])
        show.display()

    def listFiles(self, colls):
        li = deque()
        if ":" not in colls[0]["id"]:
            filelists = map(self.man.listFiles, [x["name"] for x in colls])
            map(li.extend, [c.value for c in filelists])
        else:
           li = colls
        return list(li)

    def sortedSlide(self, cont, pos = 0):
        li = self.listFiles(cont)
        li.sort(key=lambda fi: fi["name"])
        self.slideshow(li, pos)

    def randomSlide(self, cont):
        """creates a randomized slideshow"""
        li = self.listFiles(cont)
        shuffle(li)
        self.slideshow(li)

    def gallery(self, cont, limit=0, page=0, select = None):
        """ creates a thumbnail gallery of the given files.
        cont        a list of the file or collection dictionaries or a name of a collection.
        limit       the number of images shown per page
        page        the starting page
        select      True enables selecting files from the gallery
        first_index an index for an image wanted to be seen on the page"""
        if isinstance(cont, list):
            if len(cont) == 0:
                return
            if isinstance(cont[0], dict) and "path" not in cont[0].keys():
                tmp = map(self.store.list_files_in_collection, [x["name"] for x in cont])
                cont = list()
                map(cont.extend, tmp)
            elif isinstance(cont[0], basestring):
                cont = map(self.store.list_files_in_collection, cont)
            else:
                cont = None
        elif isinstance(cont, basestring):
            cont = self.store.list_files_in_collection(cont)
        else:
            print cont, type(cont), "is not a valid argument for ImageView.gallery"
            return

        cont.sort(key=lambda c: c["name"])

        if limit == 0:
            limit = self.settings["gallery"]["thumbs"]

        paths = self.store.get_full_paths(cont)
        gallery = Gallery(paths, cont, limit,
            self.settings["gallery"]["thumbWidth"], self.settings["gallery"]["thumbHeight"],
            self.settings["window"]["width"],
            self.settings["window"]["height"],
            page = page, bgcolor = self.settings["window"]["bg"],
            toolbar = self.settings["toolbar"])
        gallery.display()
        if select is not None:
            items = gallery.getSelectedItems()
            select(items)

    def viewDir(self, directory, calldir, library):
        """Creates a thumbnail gallery of a given directory"""
        # Change to the directory in which cicm was called.
        # Allows the use of relative paths.
        os.chdir(calldir)
        directory = os.path.abspath(directory)

        content = os.listdir(directory)
        images = list()
        info = list()
        for f in content:
            path = os.path.join(directory, f)
            # make sure the path points to a file and that the file is
            # an image.
            if (os.path.isfile(path) and mimetypes.guess_type(path)[0] and
                    "image" in mimetypes.guess_type(path)[0]):
                images.append(path)
                # the gallery class requires a list of dictionaries
                info.append({"name":f, "path":directory, "type":"Text/Other"})


        self._files = info
        self.gallery(info, select = self.select)
        
        # change back to the cicm dir to allow adding
        # selected files to a collection
        os.chdir(get_file_dir())
        if len(self._selected) > 0:
            print self.text["add-selected"]
            ans = raw_input()
            if ans == self.text["yes"]:
                # ask the user which collection to add
                print self.text["which-collection"]
                library.viewCollections()
                ans = raw_input()

                # make a list of image paths from the selected files
                paths = [d["path"] for d in self._selected]
                # ask the collection until an existing one is given
                while not library.addImages(ans, paths):
                    ans = raw_input()

