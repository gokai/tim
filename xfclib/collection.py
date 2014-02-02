
__author__  = "Tachara (tortured.flame@gmail.com)"
__date__ = "$Date 2010/24/06 14:18:05 $"
__copyright__ = "Copyright (c) 2010 Tachara"

import xml.etree.cElementTree as ET
import os
import shutil
import gzip

class BaseCollection(object):
    """Abstarct base class"""
    def __init__(self, path):
        self.fname = path
        self._data = dict()
        self._data["content"] = dict()
        self._data["names"] = dict()
        with gzip.open(self.fname) as f:
            self.parse(f)

    def parse(self,fi):
        self._tree = ET.ElementTree()
        self._tree.parse(fi)
        root = self._tree.getroot()
        self.gather_data(root)

    def content(self):
        """Returns a tuple of the collections content."""
        return tuple(self._data["content"].values())

    def add_tags(self, i, new_tags):
        """Add tags to an item"""
        new_tags.extend(self._data["content"][i]["tags"])
        if "N/A" in new_tags:
            new_tags.remove("N/A")
        
        new_tags = set(new_tags)
        self.change_tags(i, new_tags)

    def change_tags(self, i, new_tags):
        """Change items tags to new_tags.
           new_tags should be an iterable of tags."""
        self._data["content"][i]["tags"] = list(new_tags)

    def remove_tags(self, i, rem_tags):
        """Removes tags from an item. 
           rem_tags should be an iterable of tags."""
        tags = self._data["content"][i]["tags"]
        for tag in tags[:]:
            if tag in rem_tags:
                tags.remove(tag)

        if len(tags) == 0:
            tags.append("N/A")
        self.change_tags(i, tags)

    def ids(self):
        """Returns a list of ids in the collection"""
        return self._data["content"].keys()

    def identify(self, name):
        """Returns the id of an item or None"""
        if name in self._data["names"].keys():
            return self._data["names"][name]
        return None

    def __getitem__(self, key):
        return self._data["content"][key]
        
    def __setitem__(self, key, value):
        if self._ismaster:
            self._data["content"][key] = value
        else:
            self._data[key] = value

    def remove(self, i):
        root = self._tree.getroot()
        for elem in root:
            if "id" in elem.attrib.keys() and elem.attrib["id"] == i:
                root.remove(elem)
        self._data["content"].pop(i, "") 

    def base_add(self, elem, data):
        self._data["content"][data["id"]] = data
        elem.attrib["id"] = data["id"]
        nameelem = ET.SubElement(elem, "name")
        nameelem.text = data["name"]
        tagelem = ET.SubElement(elem, "tags")
        if len(data["tags"].strip()) == 0:
            data["tags"] = "N/A"
        tagelem.text = data["tags"]

    def backup(self):
        """Creates a copy of the previous contents.
           Overwrites the old backup file."""
        shutil.copy2(self.fname, self.fname + "~")


class MasterCollection(BaseCollection):
    def __init__(self, path):
        super(MasterCollection, self).__init__(path)

    def gather_data(self, root):
        self.path = root.get("path")
        for elem in root.iter("collection"):
            info = dict()
            info["id"] = elem.attrib["id"]

            for subelem in elem:
                if subelem.text.isdigit():
                    text = int(subelem.text)
                else:
                    text = subelem.text

                info[subelem.tag] = text
            info["tags"] = info["tags"].split(",")
            self._data["content"][elem.attrib["id"]] = info
            self._data["names"][info["name"]] = info["id"]

    def add(self, data):
        elem = ET.SubElement(root, "collection")
        fc = ET.SubElement(elem, "fc")
        fc.text = "0"
        data["fc"] = "0"
        base_add(elem, data)

    def write(self):
        """Writes the collection data to disk."""
        self.backup()
        root = self._tree.getroot()
        for elem in root.iter("collection"):
            i = elem.attrib["id"]
            for subelem in elem:
                subelem.text = str(self._data["content"][i][subelem.tag])
            

class Collection(BaseCollection):
    def __init__(self, path, masterColl, newData = None):
        self._master = masterColl
        if newData is not None:
            fpath, name = os.path.split(path)
            self._new(name, masterColl, newData)
        super(Collection,self).__init__(path)

    def gather_data(self, root):
        self._data["id"] = root.get("id")
        self._data["name"] = self._master[self._data["id"]]["name"]
        self._data["tags"] = self._master[self._data["id"]]["tags"]
        for elem in root.iter("file"):
            fi = dict()
            fi["id"] = elem.attrib["id"]
            fi["collection"] = self._data["name"]
            for subelem in elem[:]:
                if subelem.text == None:
                    elem.remove(subelem)
                    continue
                fi[subelem.tag] = subelem.text
            n, t = os.path.splitext(fi["name"])
            if t == "":
                t = "Text/Other"
            fi["type"] = t
            fi["name"] = n
            fi["tags"] = fi["tags"].split(",")
            self._data["content"][fi["id"]] = fi
            self._data["names"][fi["name"]] = fi["id"]

    def _new(self, name, masterColl, data):
        """Creates a new collection from data.
           Data has to be a dictionary with at least
           the keys id and tags."""
        if not os.path.exists(masterColl.path):
            os.mkdir(masterColl.path)
        path = os.path.join(masterColl.path, name)
        shutil.copy("./colls/skeleton.xic.base", path)
        f = gzip.open(path, "r")
        tree = ET.ElementTree()
        tree.parse(f)
        tree.getroot().attrib["id"] = data["id"]
        data["name"] = os.path.splitext(name)[0]
        masterColl.add(data)
        f = gzip.open(path, "w")
        tree.write(f)

    def add(self, data):
        """Adds a new item to the collection"""
        root = self._tree.getroot()

        elem = ET.SubElement(root, "file")
        path = ET.SubElement(elem, "path")
        path.text = data["path"]
        fc = self._master[self._data["id"]]["fc"]
        self._master[self._data["id"]]["fc"] = str(int(fc) + 1)
        base_add(elem,data)


    def remove(self, i):
        """Removes an item from the collection"""
        super(Collection,self).remove(i)
        fc = self._master[self._data["id"]]["fc"]
        fc = str(int(fc) - 1)
        self._master[self._data["id"]]["fc"] = fc

    def rename(self, name):
        """Renames the collection."""
        self._data["name"] = name
        self._master[self._data["id"]]["name"] = name
        ext = os.path.splitext(self.fname)[1]
        shutil.move(self.fname , name + ext)
        self.fname = name

    def delete(self):
        """Deletes the collection."""
        os.remove(self.fname)
        self._master.remove(self._data["id"])

    def export(self, path, files = False):
        """Makes an importable version of the collection.
        Can either move the files with the collection or
        just create a collection file and let the user worry
        about the rest. Removes the collection from master
        collection.
        """

        if files:
            dest = os.path.join(path, self._data["name"])
            for f in self._data["content"].itervalues():
                if f["type"] != "Text/Other":
                    t = f["type"]
                else:
                    t = ""
                src = os.path.join(f["path"], f["name"] + t)
                shutil.copy2(src, dest)

        tree = ET.ElementTree(self._tree.getroot())
        tree.getroot().set("id", self._data["id"])
        desc = ET.SubElement(tree.getroot(), "description")
        fc = ET.SubElement(desc, "fc")
        fc.text = self._master[self._data["id"]]["fc"]
        tags = ET.SubElement(desc, "tags")
        tags.text = ",".join(self._data["tags"])
        name = ET.SubElement(desc, "name")
        name.text = self._data["name"]
        f = gzip.open(self.fname + ".exp", "w")
        tree.write(f, encoding="UTF-8")

        self.delete()

    def write(self):
        """Writes the collection data to disk."""
        self.backup()
        self._master[self._data["id"]]["tags"] = self._data["tags"]
        self._master[self._data["id"]]["name"] = self._data["name"]
        root = self._tree.getroot()
        for elem in root.iter("file"):
            i = elem.attrib["id"]
            fi = self._data["content"][i]
            fi["tags"] = ",".join(fi["tags"])
            for subelem in elem:
                if subelem.tag == "name":
                    ext = ""
                    if fi["type"] != "Text/Other":
                        ext = fi["type"]
                    subelem.text = fi["name"] + ext
                else:
                    subelem.text = str(fi[subelem.tag])
                        
        f = gzip.open(self.fname, "w")
        self._tree.write(f, encoding="UTF-8")
        f.close()
