
__author__  = "Tachara (tortured.flame@gmail.com)"
__version__ = "0.9.8.5"
__date__ = "$Date 2010/24/06 14:18:05 $"
__copyright__ = "Copyright (c) 2010 Tachara"

import sys
import os
import random
import itertools
import gzip
import xml.etree.ElementTree as ET
from collections import namedtuple

from collection import Collection, MasterCollection
# Create a return value type
rval = namedtuple('XfclibReturnValue', 'isError value')

class CollectionManager:

    def __init__(self, masterPath, masterName, extension, paths):
        """sets the basic settings"""
        self._master = masterName
        self._masterPath = masterPath
        path = os.path.join(masterPath, masterName + ".xcc")
        if not os.path.exists(path):
            self.createMaster(path)

        self._masterColl = MasterCollection(path)
        self._ext = extension
        self.paths = paths
    # end __init__
    
    def changeMasterCollection(self, name):
        """Change the master collection used to the one specified by name.
        name   a name of the master collection to use"""
        self._master = name
        path = os.path.join(self._masterPath, name + ".xcc")
        if not os.path.exists(path):
            self.createMaster(path)

        self._masterColl = Collection(path)

    def listCollections(self):
        """ returns a list of collecions
        in the database, containing the name of the collection,
        the tags given, their id and their file count"""
        return rval(isError=False, value=list(self._masterColl.content()))
    # end listCollections
    
    def listFiles(self, collName):
        """ Returns a list of files in the collection.
        The list contains dictionaries with the following structure:
        {"name":"imageName",
            "tags":"imageTags", 
            "path":"pathToImage",
            "type":"imageExtension", 
            "collection":"collctionName",
            "id":"fileId"}
        """
        path = os.path.join(self._masterColl.path, collName + self._ext)
        if not os.path.exists(path):
            return rval(isError=True, value="Collection " + collName + " not foud")
        collection = Collection(path, self._masterColl)
        return rval(isError=False, value=list(collection.content()))
    # end listFiles
    
    def allTags(self):
        """Returns a set of all tags used"""
        colls = self.listCollections()
        s = set()
        fiLi = list()
        for coll in colls.value:
            fiLi.extend(self.listFiles(coll["name"]).value)
            for tag in coll["tags"].split(","):
                s.add(tag)
        for fi in fiLi:
            for tag in fi["tags"].split(","):
                s.add(tag)
        return rval(isError=False, value=s)
    #end listTags
    
    def getId(self, name):
        """ get the id of an item"""
        
        i = self._masterColl.identify(name)

        if i != None:
            return rval(isError=False, value=i)

        colls = self._masterColl.content()
        for coll in colls:
            path = os.path.join(self._masterColl.path, coll["name"] + self._ext)
            c = Collection(path, self._masterColl)
            i = c.identify(name)
            if i != None:
                return rval(isError=False, value=i)
        return rval(isError=True, value="Name " + name + " not found")
    # end getId
    
    def getName(self, itemId):
        """ finds the name of an item
        based on its id"""

        collList = self.listCollections()
        files = []
        for coll in collList.value:
            if itemId == coll['id']:
                return rval(isError=False, value=coll['name'])

            files.extend(self.listFiles(coll['name']).value)
            
        for fi in files:
            if itemId == fi['id']:
                name = fi['name']
                if not fi['type'] == 'Text/Other':
                    name += "." + fi['type']
                return rval(isError=False, value=name)

        return rval(isError=True, value="id not found")
    # end getName
    
    def _generateBaseId(self):
        """generates a base for file and 
        collection ids"""
            
        idLi = []
        while len(idLi) < 30:
            idLi.append(random.randint( 0, 9))
        return idLi
    # end generateBaseId
    
    def _generateFileId(self, name, collectionId):
        """ generates a unique id for a file.
        the generate logic is the following:
        take the collection id and add a name
        dependant number for it"""
    
        base = self._generateBaseId(name)
        fileId = "{}:{}".format(collectionId, "".join(base))
                
        return fileId
    # end generateFileId
    
    def _generateCollectionId(self, name):
        """generates an unique id for a collection"""
        idLi = []
        base = self._generateBaseId()
        idLi = base[:10]
    
        collId = ""
        for x in idLi:
            collId += "%i" % (x)
        return collId
    # end generateCollectionId
    
    def createMaster(self, name):
        """Creates a new master collection."""
        if ".xcc" not in name:
            f = gzip.open(name + ".xcc", "w")
        else:
            f = gzip.open(name, "w")
            name = os.path.split(name)
            name = os.path.splitext(name[1])

        elem = ET.Element("master")
        path = "./colls/" + name[0]
        elem.set("path", path)
        try:
            os.mkdir(path)
        except:
            pass
        tree = ET.ElementTree(elem)
        tree.write(f)

    def createCollection(self, name, tags):
        """Creates a collection file name.ext
        where ext is defined by the ui
        and gives it a basic description"""
        
        # generate an id for the collection
        collId = self._generateCollectionId(name)
        
        path = os.path.join(self._masterColl.path, name + self._ext)
        if not os.path.exists(path):
            data = dict(id=collId, tags=tags)
            coll = Collection(path, self._masterColl, data)
            coll.write()
            self._masterColl.write()
            return rval(isError=False, value="Collection " + name.split(".")[0] + "created")
        else:
            return rval(isError=True, value="Collection exists")
    # end createCollection 

    def exportCollection(self, collName, exportPath, files = False):
        """Creates an importable file of a collection
        The file contains all info about the collection
        If collId is given the collection will be parsed
        if coll is given it has to be a Collection object"""
        path = os.path.join(self._masterColl.path, collName + self._ext)
        coll = Collection(path, self._masterColl)
        coll.export(exportPath,files)

    def importCollection(self, fname):
        """Imports a collection.
        Creates a new collection file and adds
        the data into the master collection"""
        tree = ET.ElementTree()
        f = gzip.open(fname, "r")
        tree.parse(f)
        desc = tree.find("description")
        data = dict()
        for elem in desc:
            data[elem.tag] = elem.text

        data["id"] = tree.getroot().get("id")
        coll = Collection(data["name"] + self._ext, self._masterColl, data)
        for elem in tree.getroot():
            if elem.tag == "description":
                continue
            fdata = dict()
            for subelem in elem:
                fdata[subelem.tag] = subelem.text 
            fdata["type"] = os.path.splitext(data["name"])[1]
            fdata["id"] = elem.get("id")
            coll.add(fdata)
        coll.write()
        self._masterColl.write()
    
    def deleteCollection(self, removeId):
        """Removes a collection from the database.
        Also removes the collection file. Won't
        delete images in the collection"""

        cont = self._masterColl.content()
        rem = ""
        found = False
        for coll in cont:
            if coll["id"] == removeId:
                found = True
                name = os.path.join(self._masterColl.path, coll["name"] + self._ext)
                rem = Collection(name, self._masterColl)
                name = coll["name"]

        if found:
            rem.delete()
            self._masterColl.write()
            return rval(isError=False, value="Collection " + name + " removed")
        else:
            return rval(isError=False, value="Nothing to remove.")
    # end of deleteCollection
    
    def _exists(self, fi_li, files):
        """ Check if fi_li is already in files.
        Returns an iterable containing the ones that aren't in files
        """
        paths = self.constructFilePath(files) 
        it = itertools.ifilterfalse(lambda f: f in paths, fi_li)
        return it

    def insertFiles(self, fileNames, collId, tags = "N/A"):
        """ inserts files to a collection
        and gives them tags if they are specified
        if not N/A is given instead"""
        name = os.path.join(self._masterColl.path, self._masterColl[collId]["name"] + self._ext)
        collName = name.split(".")[0]
        coll = Collection(name, self._masterColl)
        names = list()
        collCont = coll.content()
        it = self._exists(fileNames, collCont)
        included = 0

        for i,fileName in enumerate(it):
            # get name and path for file
            (path,name) = os.path.split(os.path.abspath(fileName))
            data = dict()

            #give it a location
            if path == "":
                path = os.getcwd()
            for key in self.paths.keys():
                if self.paths[key] in path:
                    path = path.replace(self.paths[key], key)
            data["path"] = path

            # give it an id
            na = name
            names.append(name)
            (na, ext) = os.path.splitext(name)
            data["id"] = self._generateFileId(na, collId)
            data["type"] = ext
            data["name"] = na
            if ext == "":
                data["type"] = "Text/Other"
    
            # insert tags
            if isinstance(tags, str):
                data["tags"] = tags
            else:
                if len(tags) > i:
                    data["tags"] = tags[i].strip()
                else:
                    data["tags"] = tags[0].strip()
            coll.add(data)
        # end for

        coll.write()
        self._masterColl.write()
        return rval(isError=False, value="file(s):\n %s \ninserted to %s" %
                        ("\n".join(names), collName))
    # end insertFiles
    
    def getData(self, i):
        """Fetches data about an item with the id i"""
        if ":" in i:
            (ci, tmp) = i.split(":")
            name = self._masterColl[ci]["name"]
            coll = Collection(name + self._ext, self._masterColl)
            if i in coll.ids():
                return rval(isError=False, value=coll[i])
        else:
            if i in self._masterColl.ids():
                return rval(isError=False, value=self._masterColl[i])
        return rval(isError=False, value="item not found")

    def constructCollectionPath(self, colls):
        paths = list()
        for collection in colls:
            name = self.getName(collection)
            path = os.path.join(self._masterColl.path, name.value + self._ext)
            paths.append(path)

        return paths #TODO
        
    def constructFilePath(self, fileDicLi):
        """ constructs the full absolute path to
        the given files and returns it as a list.
        """
    
        def constructPath(fileDic):
            fileName = fileDic["name"]
            if fileDic["type"] != "Text/Other":
                fileName += fileDic["type"]
    
            path = fileDic["path"]
            for key in self.paths.keys():
                if key in path[:len(key)]:
                    path = path.replace(key,self.paths[key])
            if path[0] == '.':
                path = os.path.abspath(path)
            path = os.path.realpath(path)
            path = os.path.normcase(path)
            fullPath = os.path.join(path, fileName)
            return fullPath

        fullPathLi = itertools.imap(constructPath, fileDicLi)

        return rval(isError=False, value=list(fullPathLi))
    # end constructFilePath
    
    def changeTags(self, itemId, tags):
        if ':' in itemId:
            collId, tmp = itemId.split(":")
            path = self.constructCollectionPath([collId])[0]
            coll = Collection(path, self._masterColl)
            coll.change_tags(itemId, tags)
            coll.write()
            return rval(isError=False, value="File tags updated")
        elif ':' not  in itemId:
            self._masterColl.change_tags(itemId, tags)
            self._masterColl.write()
            return rval(isError=False, value="Collection tags updated")
    # end changeTags

    def addTags(self, itemId, tags):
        """add tags to an item"""

        if len(tags) == 0:
            tags = ["N/A"]

        s = set(tags)
        tags = [t.strip() for t in s]
        if ':' in itemId:
            collid, tmp = itemId.split(":")
            path = self.constructCollectionPath([collid])[0]
            coll = Collection(path, self._masterColl)
            coll.add_tags(itemId, tags)
            coll.write()
            return rval(isError=False, value="File tags updated")
        elif ':' not  in itemId:
            self._masterColl.add_tags(itemId, tags)
            self._masterColl.write()
            return rval(isError=False, value="Collection tags updated")
    # end updateTags
    
    def listTags(self, itemId):
        """lists tags for a given item"""
        item = ""
        if ':' in itemId:
            collid, tmp = itemId.split(":")
            path = self.constructCollectionPath([collid])[0]
            coll = Collection(path, self._masterColl)
            item = coll[itemId]
        else:
            item = self._masterColl[itemId]
    
        tagList = item["tags"]
        return tagList #TODO
    # end listTags
    
    def removeTags(self, tags, itemId):
        """ removes tags from a file or a collection"""

        # remove empty space from tags
        for i,tag in enumerate(tags):
            tags[i] = tag.strip()

        if ":" in itemId:
            collid, tmp = itemId.split(":")
            path = self.constructCollectionPath([collid])[0]
            coll = Collection(path, self._masterColl)
            coll.remove_tags(itemId, tags)
            coll.write()
        elif ":" not in itemId:
            self._masterColl.remove_tags(itemId, tags)
            self._masterColl.write()
        return rval(isError=False, value="Tags removed")
    #end remonveTags

    def filterFiles(self, files, filters, reverse = False):
        """Removes files matching the conditions filters
        If reverse is true the files not matching will be removed"""
        
        # gather collection info into a handy dictionary
        colls = self.listCollections()
        collDicts = dict()
        for coll in colls.value:
            collDicts[coll["name"]] = coll

        for f in files[:]:
            count = 0
            for c in filters:
                if c in f["tags"].split(",") or c == f["collection"]\
                    or c in collDicts[f["collection"]]["tags"].split(","):
                        if f in files and not reverse:
                            files.remove(f)
                        elif reverse:
                            count += 1

            if reverse and count < len(filters) and f in files:
                files.remove(f)

        return rval(isError=False, value=files)
    #end filterFiles

    def searchFiles(self, conditions, inc):
        colls = self.listCollections()
        files = []
        collDicts = dict()
        for coll in colls.value:
            files.extend(self.listFiles(coll["name"]).value)
            collDicts[coll["name"]] = coll
        
        li = []
        count = len(conditions)
        for f in files:
            i = 0
            for c in conditions:
                if (c in f["tags"].split(",") or c == f["collection"]
                        or c in collDicts[f["collection"]]["tags"].split(",")) :
                    if inc:
                        li.append(f)
                    elif not inc:
                        i += 1
                        if i == count:
                            li.append(f)

        return rval(isError=False, value=li)
    # end searchFiles
    
    def renameCollection(self, collId, newName):
        """ renames a collection to newName.
        Also renames the collection file"""

        oldName = self.getName(collId)
        coll = Collection(oldName + self._ext, self._masterColl)
        coll.rename(newName)

        self._masterColl.write()
        return rval(isError=False, value="Collection renamed")
    # end renameCollection
    
    def removeFileFromCollection(self,files):
        """Removes a file from a collection,
        but won't remove the file from disk"""

        collId = files[0]["id"].split(":")[0]
        name = self._masterColl[collId]["name"]
        path = os.path.join(self._masterColl.path, name + self._ext)
        coll = Collection(path, self._masterColl)
        for f in files:
            coll.remove(f["id"])
        coll.write()
        self._masterColl.write()
        return rval(isError=False, value="files removed from collection")
    # end removeFileFromCollection

    def moveCollection(self, collId, destination):
        """Moves a collection from it's specified place.
        """
        pass

    def moveFiles(self, fileIds, destCollId):
        """Moves the listed files from their collection to destColl."""

        collId = fileIds[0].split(":")[0]
        collName = self._masterColl[collId]["name"]
        print "Source:", collName
        path = os.path.join(self._masterColl.path, collName + self._ext)
        coll = Collection(path, self._masterColl)
        destCollName = self._masterColl[destCollId]["name"] + self._ext
        if type(destCollName) == tuple:
            return rval(isError=False, value="Collection not found.")
        destPath = os.path.join(self._masterColl.path, destCollName )
        destColl = Collection(destPath, self._masterColl)

        for id in fileIds:
            # get the data of the file and remove it
            fileData = coll[id]
            coll.remove(id)

            # change the collection part of the file id
            fileData["id"] = "%s:%s" % (destCollId, id.split(":")[1])

            # add the file to the new collection
            destColl.add(fileData)

        coll.write()
        destColl.write()

    def updateFileInfo(self, collId, data):
        """Updates the file data.
        First makes sure that the info given is valid"""

        name = self.getName(collId)
        if name.isError:
            return name
        coll = Collection(name.value + self._ext, self._masterColl)
        fiLi = coll.content()

        for fi in fiLi:
            name = fi["name"]
            if  fi["type"] != "Text/Other":
                name += fi["type"]
            path = os.path.join(data["path"], name)
            if os.path.exists(path):
                for key in self.paths.keys():
                    if self.paths[key] in path:
                        path = path.replace(self.paths[key], key)
                        break
                coll[fi["id"]]["path"] = os.path.split(path)[0]
            else:
                fullPath = self.constructFilePath([fi])[0]
                if not os.path.exists(fullPath):
                    coll.remove(fi["id"])
        coll.write()
