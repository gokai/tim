__author__  = "Tachara (tortured.flame@gmail.com)"
__date__ = "$Date 2012/01/29 16:31:00 $"
__copyright__ = "Copyright (c) 2010 Tachara"

import os
import mimetypes
import itertools
from collections import deque
try:
    import readline
except ImportError:
    # the readline module is only imported to
    # make raw_input to behave with arrow keys
    pass

# non-standard modules should come with this file
# if not you can find them from sourceforge.com
from interpreter import CommandInterpreter as CI
from xfclib.manager import CollectionManager


class DataStore(list):
    def __init__(self, *args, **kwargs):
        self.s = super(DataStore, self)
        self.filt = None
        self.selected = deque()
        self.s.__init__(*args, **kwargs)
        
    def compare(self, item):
        for tag in self.filt[0]:
            if tag not in item["tags"]:
                return False
        return True

    def filter(self, filt, reverse=False):
        self.filt = (filt, reverse)
        if not reverse:
            it = itertools.ifilterfalse(self.compare, self)
        else:
            it = itertools.ifilter(self.compare, self)
        return it

    def remove_filter(self):
        self.filt = None
        return iter(self)

    def tag_compare(self, item):
        if "N/A" in item["tags"]:
            return 0
        else:
            return len(item["tags"])

    def reorder(self, order):
        if order == "asc":
            self.sort(key=lambda x: x["name"])
        elif order == "desc":
            self.sort(key=lambda x: x["name"], reverse = True)
        elif order == "tags":
            self.sort(key=self.tag_compare)

    def get_iter(self):
        if self.filt is not None:
            return self.filter(self.filt[0], self.filt[1])
        return iter(self)

    def clear_selection(self):
        self.selected.clear()

    def select(self, data):
        it = itertools.ifilterfalse(lambda i: i in self.selected, data)
        self.selected.extend(it)

    def unselect(self, data):
        if isinstance(data, list):
            it = itertools.ifilterfalse(lambda i: i not in self.selected, data)
            for item in it:
                self.selected.remove(item)

    def get_selected(self):
        return list(self.selected)

    def is_selected(self, data):
        return data in self.selected

    def __getitem__(self, i):
        if self.filt is not None:
            return tuple(self.get_iter())[i]
        else:
            return self.s.__getitem__(i)

    def __len__(self):
        if self.filt is not None:
            return len(tuple(self.get_iter()))
        else:
            return self.s.__len__()


class TableView(object):
    def __init__(self, content, keys, limit, width, sort=True,
            texts=None):
        """
        content         list of dictionaries to show
        keys            keys of a content dictionary to display
        width           max number of character for a line
        texts           texts to use instead of keys.
                        If None the keys are printed
        limit           number of items to display per page.
                        -1 means no limit.
        In addition to keys a page wide id(the number of the row startin from 0) 
        is displayed.
        """
        self.content = DataStore(content)
        if sort:
            self.content.sort(key = lambda f: f["name"])
        self.it = self.content.get_iter()
        self.keys = keys
        if texts is None:
            self.text = {}
            for key in keys:
                self.text[key] = key
        else:
            self.text = texts

        self.page = 0
        if limit == -1:
            self.last_page = 1
            self.limit = len(content)
        else:
            self.limit = limit
            self.last_page = len(content) / self.limit

        self.last_item = len(content)
        self.id_length = 3
        self.field_limit = (width - self.id_length)/len(keys)

    def get_content(self, ids):
        return ids

    def selection_view(self):
        return TableView(self.content.get_selected(), self.keys, self.limit,
                self.field_limit, True, self.text)

    def filter(self, filt, reverse = False):
        it = self.content.filter(filt, reverse)

        t = tuple(it)
        if self.page == -1:
            self.limit = len(t)
        else:
            self.page = 0
            self.last_page = len(t) / self.limit
        self.last_item = len(t)
        self.it = self.content.get_iter()

    def remove_filter(self):
        it = self.content.remove_filter()
        t = tuple(it)
        if self.page == -1:
            self.last_page = -1
            self.limit = len(t)
        else:
            self.page = 0
            self.last_page = len(t) / self.limit
        self.last_item = len(t)
        self.it = self.content.get_iter()

    def find_longest(self, items):
        li = sorted(items, key=lambda s: len(str(s)))
        return len(li[-1])

    def _print_header(self, lengths):
        li = deque()
        li.append("id".ljust(self.id_length))
        for key in self.keys:
            li.append(self.text[key].ljust(lengths[key]))
        header = " | ".join(li)
        header = " ".join(["|", header, "|"])
        print header

    def _print_footer(self, lengths):
        if self.page != -1:
            last = self.limit * (self.page + 1) + 1
            first = last - self.limit
            if self.page == self.last_page:
                add = len(self.content) % self.limit - 1
                if add == 0:
                    add = self.limit
                last = first + add

            footer = "%i - %i(%i) %s | %s %i(%i)" % (first, last,
                    self.last_item, self.text["files"],
                    self.text["page"],
                    self.page + 1, self.last_page + 1)
            print footer

    def _create_separator(self, lengths):
        add = 2
        sep = deque()
        sep.append("+")
        sep.append("".ljust(self.id_length + add, "-"))
        sep.append("+")
        for key in self.keys:
            sep.append("-".ljust(lengths[key] + add, "-"))
            sep.append("+")
        return "".join(sep)

    def next(self):
        if self.page == -1:
            return
        if self.page < self.last_page:
            self.page += 1

    def prev(self):
        if self.page == -1:
            return
        if self.page > 0:
            self.page -= 1

    def jump(self, page):
        if page > self.last_page:
            self.page = self.last_page
        elif page >= 0:
            self.page = page
        else:
            print "Page must be a positive integer"

    def info(self, li):
        for item in li:
            for key in sorted(item.keys()):
                print key + ":", item[key]
            print "".ljust(15, "-")
        raw_input(self.text["continue"])

    def print_filter(self):
        if self.content.filt is not None:
            description = "filter"
            if self.content.filt[1]:
                description = "search"
            print "Current {}: {}".format(description, self.content.filt[0]) 
        else:
            print "No filter applied."

    def show(self):
        i = 0
        a = 0
        first = 0
        last = self.last_item
        if self.page != -1:
            a = self.limit * self.page
            first = a
            last = a + self.limit
        
        fields = dict()
        for key in self.keys:
            content = self.content[a:a + self.limit]
            if key != "tags":
                li = map(lambda i: i[key], content)
            else:
                li = map(lambda i: ",".join(i[key]), content)
            li.append(self.text[key])
            fields[key] = self.find_longest(li)
            if fields[key] > self.field_limit:
                fields[key] = self.field_limit

        self._print_header(fields)
        separator = self._create_separator(fields)
        print separator
        it = itertools.islice(self.it, first, last)
        for item in it:
            li = deque()
            s = str(i)
            li.append(s.ljust(self.id_length))
            for key in self.keys:
                text = item[key]
                if key == "tags":
                    text = ",".join(item[key])
                li.append(str(text)[:fields[key]].
                        ljust(fields[key]))
                if len(str(item[key])) > fields[key]:
                    li[-1] = li[-1][:-3] + "..."
            line = " | ".join(li)
            line = " ".join(["|", line, "|"])
            print line
            print separator
            i += 1
            a += 1
        self._print_footer(fields)
        self.it = self.content.get_iter()

    def _is_id_li(self, li):
        try:
            return len(li) >= 1 and(li[0] in ["page", "all", "s"] or li[0].isdigit())
        except AttributeError:
            return False

    def parse_id_str(self, id_str):
        li = id_str.split(",")
        if not self._is_id_li(li):
            # nothing to parse
            print "Invalid id."
            return None

        nli = list()
        for item in li:
            if item == "page":
                start = self.page * self.limit
                end = start + self.limit
                if end > len(self.content):
                    end = len(self.content) - start
                nli.extend(self.content[start:end])
            elif item == "all":
                nli = self.content[:]
                break
            elif item == "s":
                li = self.content.selected
                nli.extend(li)
            else:
                if item.isdigit():
                    i = int(item)
                    if i < len(self.content):
                        if self.page != -1:
                            nli.append(self.content[i + self.page * self.limit])
                        else:
                            nli.append(self.content[i])
                else:
                    print item, "is not a number."
                    return list()

        return nli


class TagView(TableView):
    def __init__(self, content, keys, limit, width, sort,
            texts, search_func):
        TableView.__init__(self, content, keys, limit, width,
                sort, texts)
        self._search = search_func
        return
    
    def get_content(self, taglist):
        return self._search([t["name"] for t in taglist], False)


class ImageCollectionLibrary(object):
    def __init__(self, master_dir, settings, short_paths, lang):
        self.settings = settings
        self.text     = lang 
        self.man      = CollectionManager(master_dir, settings["master"],
                                          ".xic", short_paths)

    def moveFiles(self, files, destination):
        ids = [x["id"] for x in files]
        destCollId = self.man.getId(destination)
        ret = self.man.moveFiles(ids, destCollId)
        if ret.isError:
            print "Could not move:", ret.value
            return
        for f in files:
            self.view.content.remove(f)

    def update(self, name):
        i = self.man.getId(name)
        data = self.man.listFiles(name)[0]
        self.man.updateFileInfo(i, data)

    def createCollection(self, name):
        print self.text["create"]

        tags = ""
        while tags == "" or tags.isspace():
            tags = raw_input()
        message = self.man.createCollection(name, tags)
        if message.isError:
            print self.text["exists"] % name

    def deleteCollection(self, li):
        print "Delete(y/n)?"
        print " ", "  ".join(li)
        ans = raw_input()
        if ans != "y":
            return
        for name in li:
            i = self.man.getId(name)
            self.man.deleteCollection(i)
            print "Deleted", name

    def tagList(self, graphics):
        """generates a list of tags found in the database"""
    
        s = self.man.allTags()
        li = list(s)
        # TableView reguires the data to be in a list of
        # dictionaries which contain at least the keys given
        for i,item in enumerate(li):
            li[i] = dict(name = item)
    
        fields = ["name"]
        view = TagView(li, fields, self.settings["page"],
                self.settings["maxlen"], True, self.text,
                self.man.searchFiles)
        ci = ViewInterpreter(view, graphics, True)
        self.view = view
        ci.prompt = "tags > "
        ci.cmdloop()
        self.view = None

    def browseMaster(self, graphics):
        """Browse collections in the database"""
        colls = self.man.listCollections().value
        fields = self.settings["columns"]["collection"].split(",")
        view = TableView(colls, fields, self.settings["page"],
                self.settings["maxlen"], True, self.text)

        ci = CollectionInterpreter(view, graphics, 
                                   self.settings["always-print"], self)
        ci.add_command("browse", 
                lambda s: self.browseCollection(
                    view.get_content(view.parse_id_str(s))[0]["name"],
                    graphics),
                "Browse a single collection")
        ci.add_command("remove",
                lambda s: self.deleteCollection(
                    [d["name"] for d in 
                        view.get_content(view.parse_id_str(s))]),
                "Remove the listed collections collection.")

        self.view = view
        ci.prompt = "master > "
        ci.cmdloop()
        self.view = None
    # end browseMaster

    def removeImages(self, images):
        print self.text["edit-rm"] 
        for fi in images:
            print "   ", fi["name"]
        a = raw_input()
        if a == self.text["yes"]:
            self.man.removeFileFromCollection(images)
        elif a == self.text["no"]:
            pass

    def addImages(self, collection, images):
        """Adds the given images to the given collection.
        Returns False if the collection wasn't found."""
        if len(images) == 0:
            return True
        if isinstance(images, basestring):
            print images
            images = [images,]

        collId = self.man.getId(collection)
        if collid.isError:
            print collection, self.text["collection-not-found"]
            return False

        # ask if the user wants to add tags for the images
        print self.text["add-q"]
        ask = raw_input()
        ask_tags = ask == self.text["yes"]

        tags = "N/A"
        if ask_tags:
            tags =[]
        # looping over a copy to enable removing items from original
        for image in images[:]:
            if (os.path.isfile(image) and
                    "image" in mimetypes.guess_type(image)[0]):
                if ask_tags:
                    print self.text["add-tags"] % image
                    tags.append(raw_input())
            elif os.path.isdir(image):
                # a given path is a directory, ask if it should be  added
                print self.text["is-dir"] % image,
                ans = raw_input()
                if ans == self.text["yes"]:
                    self.addDirectory(image, collection)
                # remove the directory from the list of images
                images.remove(image)

        self.man.insertFiles(images, collId.value, tags)
        return True
    # end addImages
    
    def addTags(self, items, tags = None):

        if tags is None:
            print self.text["edit-list"]
            for item in items:
                print item["name"]

            print self.text["give-tags"]
            tags = raw_input()

        if tags.strip() == "":
            return

        for item in items:
            self.man.addTags(item["id"], tags.split(","))
            item["tags"] = ",".join(self.man.listTags(item["id"]))

    def removeTags(self, itemLi, tags = None):
        if tags is None:
            for item in itemLi:
                print "---"
                print self.text["edit-rt-current"], item["name"] + ":"
                print "\n".join(item["tags"])
                print self.text["edit-rt-q"]
                remTags = raw_input()
                remTags = remTags.split(",")
                message = self.man.removeTags(remTags, item["id"])
                item["tags"] = self.man.listTags(item["id"])
        else:
            for item in itemLi:
                message = self.man.removeTags(tags, item["id"])
                item["tags"] = ",".join(self.man.listTags(item["id"]))
                print message.value

    def browseCollection(self, name, graphics):
        """View contents of a collection."""
    
        ret = self.man.listFiles(name)
        files = ret.value

        if ret.isError:
            print name, self.text["collection-not-found"] 
            return

        fields = self.settings["columns"]["browse"].split(",")
        view = TableView(files, fields, self.settings["page"],
                self.settings["maxlen"], True, self.text)
        ci = CollectionInterpreter(view, graphics, self.settings["always-print"], self)
        self.view = view
        ci.prompt = name + " > "
        ci.cmdloop()
        self.view = None
    # end browseCollection
    
    def addDirectory(self, collName, directory):
        """adds the contents of a directory to a collection"""
    
        if not os.path.exists(directory):
            print self.text["not-exist"] % directory
            return
        elif not os.path.isdir(directory):
            print self.text["not-dir"] % directory
            return

        print self.text["add-dir"]
        answer = raw_input()
        tags = ""
        if answer == self.text["yes"]:
            print self.text["give-tags"]
            while tags == "":
                tags = raw_input()
        collId = self.man.getId(collName)
        if collId.isError:
            print collId.value
            return

        contentList = os.listdir(directory)
        li = []
        for item in contentList:
            path = os.path.join(directory, item)
            if os.path.isfile(path):
                li.append(path)    
        if tags != "":
            ret = self.man.insertFiles(li, collId.value, tags.split(","))
        else:
            ret = self.man.insertFiles(li, collId.value)
    
        print ret.value
    #end addDirectory
    
    def search(self, tags, s, graphics):
        """search files based on their tags"""
        
        comp = self.settings["search"]
        if s is not None:
            comp = s
    
        if comp == "exc":
            li = self.man.searchFiles(tagList, False)
        elif comp == "inc":
            li = self.man.searchFiles(tagList, True)
        else:
            print self.text["wrong-search"] % comp
            return

        if not li.isError:
            fields = self.settings["columns"]["search"].split(",")
            view = TableView(li.value, fields, self.settings["page"], 
                                     self.settings["maxlen"], True, self.text)
            ci = CollectionInterpreter(view, graphics, 
                                       self.settings["always-print"], self)
            ci.prompt = "search > "
            ci.cmdloop()
        else :
            print li.value, "search"
    

class ViewInterpreter(CI):
    """
    A command oriented interface that can view data with
    the given view object.
    view methods called:
        name            params   description
        ------------------------------------
        show            -        display the view
        filter          string   filter the views data
        jump            integer  jump to a part of the view
        next            -        move to the next part of the view
        prev            -        move to the previous part of the view
        select          integer  select an item specified by the integer 
                                 from the view. 
        selection_view  -        Return a (new) view that shows the selection
        parse_id_str    string   can return anything as long as the view itself can handle it
        get_content     list     should return a list of dictionaries
    """

    def __init__(self, view, graphics, always_print=False):
        """
        view            An object to view items
        graphics        An object that implements: gallery, slideshow
        always_print    If true view.show is called so that
                        the view is always displayed before prompt
        """

        CI.__init__(self)
        self.wait     = True
        self._print   = always_print
        self.view     = view
        self.graphics = graphics
        self.intro    = None

        if not always_print:
            self.add_command("print", lambda s: self.view.show(), "Print the current view.")

    def do_gallery(self, arg_str):
        ids = self.view.parse_id_str(arg_str)
        cont = self.view.get_content(ids)
        self.graphics.gallery(cont, select=self.view.content.select)

    def do_slide(self, arg_str):
        ids = self.view.parse_id_str(arg_str)
        cont = self.view.get_content(ids)
        self.graphics.slideshow(cont)

    def do_ls(self, arg_str):
        view = self.view.selection_view()
        ci = ViewInterpreter(view, self.graphics, self._print)
        ci.prompt = "selection > "
        ci.cmdloop()

    def do_rf(self, arg_str):
        self.view.remove_filter()

    def do_filter(self, filt):
        if filt != "":
            self.view.filter(filt.split(","))
        else:
            self.view.print_filter()

    def do_find(self, filt):
        if filt != "":
            self.view.filter(filt.split(","), True)
        else:
            self.view.print_filter()

    def do_reorder(self, arg_str):
        self.view.content.reorder(arg_str)

    def do_select(self, arg_str):
        li = self.view.parse_id_str(arg_str)
        self.view.content.select(li)

    def do_cls(self, arg_str):
        self.view.content.clear_selection()

    def preloop(self):
        if self._print:
            self.view.show()

    def postcmd(self, stop, line):
        if not self._print:
            return stop

        if "help" in line and self.wait:
            raw_input("press enter.")
        if "quit" not in line and self._print:
            self.view.show()
        return stop

    def do_info(self, arg_str):
        i = self.view.parse_id_str(arg_str)
        self.view.info(i)

    def do_jump(self, arg_str):
        if not arg_str.isdigit():
            print self.text["not-number"].format(number)
            return
        page = int(arg_str)
        self.view.jump(page - 1)

    def do_prev(self, arg_str):
        self.view.prev()

    def do_next(self, arg_str):
        self.view.next()

    def do_setup(self):
        """Change settings interactively."""
        print self.text["setup-current"]
        for key in self.settings.keys():
            if type(self.settings[key]) != dict:
                print key + ":", self.settings[key]
            else:
                print key + ":"
                for sub in self.settings[key]:
                    print "\t" + sub + ":", self.settings[key][sub]

        print self.text["setup-set"]
        ans = ""
        while ans != "q":
            ans = raw_input()
            value = ans.split()
            if len(value) == 2:
                if ":" in value[0]:
                    value[0] = value[0].split(":")
                    self.settings[value[0][0]][value[0][1]] = value[1]
                else:
                    self.settings[value[0]] = value[1]

        self.settings.write()


class CollectionInterpreter(ViewInterpreter):
    def __init__(self, view, graphics, always_print, library):
        ViewInterpreter.__init__(self, view, graphics, always_print)
        self.library = library

    def do_addtags(self, arg_str):
        arg_li = arg_str.split()
        if len(arg_li) > 0:
            target = arg_li[0]
        else:
            print "not enough arguments."
            return
        tags = None
        if len(arg_li) > 1:
            tags = " ".join(arg_li[1:])
        target = self.view.parse_id_str(target)
        if target is not None:
            self.library.addTags(target, tags)

    def do_rmtags(self, arg_str):
        arg_li = arg_str.split()
        if len(arg_li) > 0:
            target = arg_li[0]
        else:
            return
        tags = None
        if len(arg_li) > 1:
            tags = " ".join(arg_li[1:])
        target = self.view.parse_id_str(target)
        self.library.removeTags(target, tags.split(","))

    def do_remove(self, arg_str):
        ids   = self.view.parse_id_str(arg_str)
        files = self.view.get_content(ids)
        self.library.removeImages(files)
        for f in files:
            self.view.content.remove(f)

    def do_move(self, arg_str):
        arg_li = arg_str.split()
        if len(arg_li) < 2:
            print "not enough arguments"
            return
        target = arg_li[1]
        id_str = arg_li[0]
        ids = self.view.parse_id_str(id_str)
        files = self.view.get_content(ids)
        self.library.moveFiles(files, target)


class CicmInterpreter(CI):
    def __init__(self, wd, settings, graphics, library):
        CI.__init__(self)
        self.settings  = settings
        self.graphics  = graphics
        self.work_dir  = wd
        self.library   = library

    def do_gallery(self, content):
        """Shows a gallery of the collection given."""
        self.graphics.gallery(content)

    def do_slide(self, args):
        """Shows a sorted slideshow of the collection given"""
        names = args.split(",")
        content = []
        for name in names:
            content.append({"name": name, "id":""})
        self.graphics.sortedSlide(content)

    def do_rslide(self, content):
        self.graphics.randomSlide(content)

    def do_browse(self, collection):
        """Browse the files of a collection"""
        self.library.browseCollection(collection, self.graphics)

    def do_collections(self, arg_str):
        self.library.browseMaster(self.graphics)

    def do_tags(self, arg_str):
        self.library.tagList(self.graphics)

    def do_create(self, name):
        self.library.createCollection(name)

    def do_delete(self, name):
        self.library.deleteCollection(name)

    def do_search(self, arg_str):
        arg_li = arg_str.split()
        if len(arg_li) >= 1:
            tags = arg_li[0]
        else:
            print "no tags given."
            return
        mode = None
        if len(arg_li) >= 2 and arg_li[-1] in ("exc", "inc"):
           mode = arg_li[-1] 
        elif len(arg_li) >= 2:
           tags = " ".join(arg_li)

        self.library.search(tags, mode, self.graphics)

    def do_viewdir(self, directory):
        self.graphics.viewDir(directory, self.work_dir, self.library)
       
    def do_addimages(self, arg_str):
        arg_li = arg_str.split()
        collection = arg_li[0]
        self.library.addImages(collection, arg_li[1:])

    def do_addfolder(self, arg_str):
        arg_li     = arg_str.split()
        if len(arg_li) < 1:
            print "not enough arguments"
            return
        collection = arg_li[0]
        directory  = arg_li[1]
        self.library.addDirectory(collection, directory)

    def do_create(self, collection):
        self.library.createCollection(collection)

    def do_delete(self, collection):
        self.library.deleteCollection((collection,))
